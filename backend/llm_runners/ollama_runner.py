import datetime
import json
from typing import Optional, List, Callable, Tuple

import requests
from langchain_ollama import OllamaEmbeddings

from domain import MessageProgress
from llm_runners.llm_runner import LLMRunner, RANDOM_SEED, MAX_TOKENS_LIMIT
from utils import utc_now
from logger import logger
from generation_guard import GenerationGuard


class OllamaRunner(LLMRunner):
    @staticmethod
    def from_dict(config: dict):
        runner = None
        try:
            if config.get('type') == 'ollama':
                runner = OllamaRunner(config['host'])
        except Exception as e:
            logger.error(f"Could not create Ollama runner from config. Reason: {e}")
        return runner

    def __init__(self, host: str):
        if host.endswith('/'):
            host = host[:-1]
        self.host = host

    def list_chat_models(self) -> List[str]:
        completion_models = []
        model_list = json.loads(requests.get(f"{self.host}/api/tags").content)["models"]
        for model in model_list:
            model_info = json.loads(
                requests.post(
                    self.host + '/api/show',
                    data='{"model": "' + model["model"] + '"}',
                    headers={'Content-Type': 'application/json'}
                ).content
            )
            if 'completion' in model_info['capabilities']:
                completion_models.append(model["model"])
        return completion_models

    def run_text_completion_streaming(self, model: str, messages: List[dict], is_stopped: Callable[[], bool],
                                      gen_guard: Optional[GenerationGuard],
                                      update_callback: Callable[[MessageProgress], None], options: dict = None) -> Tuple[Optional[str], bool]:
        failed_status = False
        if options is None:
            options = {}
        _options = {"seed": RANDOM_SEED, "num_predict": MAX_TOKENS_LIMIT}
        _options.update(options)
        if gen_guard is None:
            gen_guard = GenerationGuard()
        url = f"{self.host}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": _options
        }
        assistant_text = ''
        num_chunks = 0
        last_timestamp: Optional[datetime.datetime] = None
        try:
            with requests.post(url, json=payload, stream=True) as r:
                if r.status_code != 200:
                    logger.error(f"STATUS: {r.status_code}. Message: {r.text}")
                    failed_status = True
                for line in r.iter_lines():
                    if is_stopped():
                        assistant_text += "[STOP]"
                        if update_callback is not None:
                            update_callback(
                                MessageProgress("error", 0, 0, num_chunks,
                                            message="LLM model has been stopped")
                            )
                        return assistant_text, True
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
                    if len(chunk_text) == 0:
                        chunk_text = msg.get("thinking", "")
                    num_chunks += 1
                    gen_guard.accumulate_tokens(chunk_text)
                    assistant_text += chunk_text
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
                        return assistant_text, True
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

        return assistant_text, failed_status

    def run_text_completion_simple(self, model: str, messages: List[dict], options: dict = None):
        if options is None:
            options = {}
        _options = {"seed": RANDOM_SEED, "num_predict": MAX_TOKENS_LIMIT}
        _options.update(options)

        url = f"{self.host}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": _options
        }

        with requests.post(url, json=payload, stream=True) as r:
            # Only "content" is relevant for RAG document prep.
            return r.json()["message"]["content"]


    def get_embedding(self, embedding_config: dict) -> Optional[OllamaEmbeddings]:
        allowed_parameters = ["model"]
        filtered_embedding_config = {parameter: embedding_config[parameter] for parameter in allowed_parameters if embedding_config.get(parameter) is not None}
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

    def is_model_installed(self, model) -> bool:
        model_list = json.loads(requests.get(f"{self.host}/api/tags").content)["models"]
        return model in [x["model"] for x in model_list] and model is not None

    def supports_thinking(self, model: str) -> Optional[bool]:
        if self.is_model_installed(model):
            model_info = json.loads(
                requests.post(
                    f"{self.host}/api/show",
                    data=json.dumps({"model": model}),
                    headers={'Content-Type': 'application/json'}
                ).content
            )
            return "thinking" in model_info["capabilities"]
        return None

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

