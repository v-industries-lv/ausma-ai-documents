import datetime
import json
import random
from typing import Optional, List, Callable, Tuple

import requests
from langchain_ollama import OllamaEmbeddings

from domain import MessageProgress
from llm_runners.llm_runner import LLMRunner
from utils import utc_now
from logger import logger
from generation_guard import GenerationGuard


class OllamaRunner(LLMRunner):
    def convert_messages_for_api(self, messages: List[dict]) -> List[dict]:
        return messages

    def get_models_with_capabilities(self) -> List[dict]:
        if self.last_update is None or datetime.datetime.now(datetime.UTC) - self.last_update > datetime.timedelta(
                days=1):
            model_list = json.loads(requests.get(f"{self.host}/api/tags").content)["models"]
            models = []
            for model_item in model_list:
                model_info = json.loads(
                    requests.post(
                        self.host + '/api/show',
                        data='{"model": "' + model_item["model"] + '"}',
                        headers={'Content-Type': 'application/json'}
                    ).content
                )
                models.append(
                    {
                        "model": model_item["model"],
                        "capabilities": model_info['capabilities'],
                        "runner_type": self.runner_type,
                    }
                )
            self.cached_models = models
            self.last_update = datetime.datetime.now(datetime.UTC)
        return self.cached_models

    @staticmethod
    def from_dict(config: dict):
        runner = None
        try:
            if config.get('type') == 'ollama':
                runner = OllamaRunner(
                    config['host'],
                    config.get('seed', 42),
                    config.get('num_predict', 8000),
                    config.get('num_ctx', 16000)
                )
        except Exception as e:
            logger.error(f"Could not create Ollama runner from config. Reason: {e}")
        return runner

    def get_options(self, model):
        return {
            "seed": self.seed,
            "num_predict": self.num_predict,
            "num_ctx": self.num_ctx,
        }
    def __init__(self, host: str, seed: int, num_predict: int, num_ctx: int):
        super().__init__("ollama")
        if host.endswith('/'):
            host = host[:-1]
        self.host = host
        # Although ollama treats "0" as random seed, we explicitly set it and
        self.seed = seed if seed != 0 else random.randint(1, 2147483647)
        self.num_predict = num_predict
        self.num_ctx = num_ctx
        self.get_models_with_capabilities()

    def run_text_completion_streaming(self, model: str, messages: List[dict], is_stopped: Callable[[], bool],
                                      gen_guard: Optional[GenerationGuard],
                                      update_callback: Callable[[MessageProgress], None], options: dict = None, thinking_flag=None) -> Tuple[str, str, bool]:
        failed_status = False
        if options is None:
            options = {}
        options.update(options)
        api_messages = self.convert_messages_for_api(messages)
        if gen_guard is None:
            gen_guard = GenerationGuard()
        url = f"{self.host}/api/chat"
        payload = {
            "model": model,
            "messages": api_messages,
            "stream": True,
            "options": options,
        }
        if thinking_flag is not None:
            payload.update({"think": thinking_flag})
        assistant_text = ''
        thinking_text = ''
        num_chunks = 0
        last_timestamp: Optional[datetime.datetime] = None
        try:
            with requests.post(url, json=payload, stream=True) as r:
                if r.status_code != 200:
                    logger.error(f"STATUS: {r.status_code}. Message: {r.text}")
                    failed_status = True

                # Electron app gets stuck here if you use defaults (chunk_size=512), chunk_size=None fixes this for some reason.
                for line in r.iter_lines(chunk_size=None):
                    if is_stopped():
                        assistant_text += "[STOP]"
                        if update_callback is not None:
                            update_callback(
                                MessageProgress("error", 0, 0, num_chunks,
                                            message="LLM model has been stopped")
                            )
                        return assistant_text, thinking_text, True
                    if not line:
                        continue
                    current_timestamp = utc_now()
                    data = json.loads(line.decode("utf-8"))

                    if data.get("done"):
                        break
                    if data.get("error"):
                        raise(Exception(f"{data["error"]}"))

                    msg = data.get("message", {})

                    # Clears check buffer, if llm switched from thinking to content generation
                    # This switch indicates progression and that thinking phase was working as intended
                    gen_guard.think_content_switch(msg.get("content", ""), msg.get("thinking", ""))
                    chunk_text = msg.get("content", "")
                    if len(chunk_text) > 0:
                        assistant_text += chunk_text
                    else:
                        chunk_text = msg.get("thinking", "")
                        thinking_text += chunk_text
                    num_chunks += 1
                    gen_guard.accumulate_tokens(chunk_text)

                    if last_timestamp is not None:
                        if update_callback is not None:
                            update_callback(
                                MessageProgress("generating", 1, (current_timestamp - last_timestamp).total_seconds(),
                                                num_chunks))
                    if gen_guard.is_infinite_generation():
                        if update_callback is not None:
                            update_callback(
                                MessageProgress("error", 0, 0, num_chunks,
                                        message="LLM model has entered an infinite loop and response generation has been stopped. Please try another prompt or model.")
                            )
                        assistant_text += gen_guard.message_infinite_loop()
                        logger.error(
                            "LLM model has entered an infinite loop and response generation has been stopped. Please try another prompt or model.")
                        return assistant_text, thinking_text, True
                    last_timestamp = current_timestamp
        except Exception as e:
            if update_callback is not None:
                update_callback(
                    MessageProgress("error", 0, 0, num_chunks,
                            message=f"{e}")
                )
            # If some generation happened, but was stopped no reason to not give user what was generated. With caveats.
            if len(assistant_text)>0:
                assistant_text += LLMRunner.message_exception(e)
            logger.error(f"Error occured while generating response. Error: {e}")
            failed_status = True
        if len(assistant_text)==0:
            raise(ValueError("LLM generated empty response! Please check logs!"))

        return assistant_text, thinking_text, failed_status

    def run_text_completion_simple(self, model: str, messages: List[dict], options: dict = None, thinking_flag=None):
        if options is None:
            options = {}
        _options = self.get_options(model)
        _options.update(options)
        api_messages = self.convert_messages_for_api(messages)

        url = f"{self.host}/api/chat"
        payload = {
            "model": model,
            "messages": api_messages,
            "stream": False,
            "options": _options
        }
        if thinking_flag is not None:
            payload.update({"think": thinking_flag})

        with requests.post(url, json=payload, stream=True) as r:
            # Only "content" is relevant for RAG document prep.
            result = r.json()
            return result["message"]["content"]


    def get_embedding(self, embedding_config: dict) -> Optional[OllamaEmbeddings]:
        allowed_parameters = ["model"]
        filtered_embedding_config = {parameter: embedding_config[parameter] for parameter in allowed_parameters if
                                     embedding_config.get(parameter) is not None}
        available_embedding_models = [x["model"] for x in self.get_models_with_capabilities() if "embedding" in x["capabilities"]]
        if filtered_embedding_config.get("model") in available_embedding_models:
            try:
                return OllamaEmbeddings(base_url=self.host, validate_model_on_init=True, **filtered_embedding_config)
            except ValueError as ve:
                # validation error is OK, if model is not expected to be in this runner
                if not "validation error" in str(ve):
                    logger.error(ve)
            except Exception as e:
                logger.error(e)
        return None

    def check_model_installed(self, model):
        model_list = json.loads(requests.get(f"{self.host}/api/tags").content)["models"]
        if not self.is_model_installed(model):
            logger.error(f"[LLM_MODEL_NOT_FOUND]_{model}_{utc_now().isoformat()}")
            raise ValueError(
                f"Model {repr(model)} not installed! Available models: {';'.join([x["model"] for x in model_list])}")

    def pull_model(self, model):
        # {"status": "success" or "error": "<error message>"}
        response = json.loads(
            requests.post(
                self.host + '/api/pull',
                data=json.dumps({"name": model, "stream": False}),
                headers={'Content-Type': 'application/json'}
            ).content
        )
        if "error" in response.keys():
            return False
        return True

    def remove_model(self, model) -> bool:
        response = json.loads(
            requests.post(
                self.host + '/api/delete',
                data=json.dumps({"name": model}),
                headers={'Content-Type': 'application/json'}
            ).content
        )
        if "error" in response.keys():
            return False
        return True

