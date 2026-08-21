import datetime
import json
from typing import Optional, List, Callable, Tuple

from langchain_core.embeddings import Embeddings

from domain import MessageProgress
from generation_guard import GenerationGuard

from llm_runners.llm_runner import LLMRunner, MAX_TOKENS_LIMIT
from logger import logger
import requests

from utils import utc_now


class RemoteRunner(LLMRunner):
    class RemoteEmbeddings(Embeddings):
        def __init__(self, url: str, model: str):
            if model is None:
                raise ValueError("No model provided!")
            self.url = url
            self.model = model

        def embed_documents(self, texts):
            payload = {"inputs": texts, "model": self.model}

            r = requests.post(
                f"{self.url}/embed",
                json=payload
            )
            print(r)
            return r.json()["embeddings"]

        def embed_query(self, text):
            return self.embed_documents([text])[0]

    def get_models_with_capabilities(self) -> List[dict]:
        if self.last_update is None or datetime.datetime.now(datetime.UTC) - self.last_update > datetime.timedelta(
                days=1):
            model_list = json.loads(requests.get(f"{self.url}/models/list_with_capabilities").content)
            models = []
            for model_item in model_list:
                model_info = json.loads(
                    requests.post(
                        self.url + '/models/show',
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

    def __init__(self, url: str, options: dict = None):
        super().__init__("remote")
        self.url = url
        self.options = options
        self.get_models_with_capabilities()

    def get_options(self, model):
        # Not implemented
        return None

    def pull_model(self, model) -> bool:
        payload = {"model": model}
        headers = {
            "Content-Type": "application/json"
        }
        r = requests.post(
            f"{self.url}/models/pull",
            headers=headers,
            json=payload
        )
        return r.json()

    def remove_model(self, model) -> bool:
        payload = {"model": model}
        headers = {
            "Content-Type": "application/json"
        }
        r = requests.post(
            f"{self.url}/models/remove",
            headers=headers,
            json=payload
        )
        return r.json()

    def run_text_completion_streaming(self, model: str, messages: List[dict], is_stopped: Callable[[], bool],
                                      gen_guard: Optional[GenerationGuard],
                                      update_callback: Callable[[MessageProgress], None], options: dict = None,
                                      thinking_flag=None) -> Tuple[str, str, bool]:
        failed_status = False
        if options is None:
            options = {}
        _options = {"max_output_tokens": MAX_TOKENS_LIMIT}
        _options.update(options)
        api_messages = self.convert_messages_for_api(messages)
        if gen_guard is None:
            gen_guard = GenerationGuard()
        url = f"{self.url}/generate"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "input": api_messages,
            "stream": True,
            **_options
        }
        if thinking_flag is not None:
            logger.warning(f"Reasoning not supported yet. Asked mode: {thinking_flag}")
        assistant_text = ''
        thinking_text = ''
        num_chunks = 0
        last_timestamp: Optional[datetime.datetime] = None
        try:
            with requests.post(url, headers=headers, json=payload, stream=True) as r:
                if r.status_code != 200:
                    logger.error(f"STATUS: {r.status_code}. Message: {r.text}")
                    failed_status = True
                else:
                    for line in r.iter_lines():
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
                        decoded_line = line.decode("utf-8").strip()
                        if len(decoded_line) == 0:
                            continue
                        response = json.loads(decoded_line)
                        if response["status"] == "done":
                            break

                        elif response["status"] == "error":
                            raise ValueError(f"Remote runned has encountered an error: {response["content"]}")

                        elif response["status"] == "generating":
                            current_timestamp = utc_now()
                            chunk_text = response["content"]
                            num_chunks += 1
                            gen_guard.accumulate_tokens(chunk_text)
                            assistant_text += chunk_text
                            if last_timestamp is not None:
                                if update_callback is not None:
                                    update_callback(
                                        MessageProgress("generating", 1,
                                                        (current_timestamp - last_timestamp).total_seconds(),
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
                        else:
                            print(line)
        except Exception as e:
            if update_callback is not None:
                update_callback(
                    MessageProgress("error", 0, 0, num_chunks,
                                    message=f"{e}")
                )
            # If some generation happened, but was stopped no reason to not give user what was generated. With caveats.
            if len(assistant_text) > 0:
                assistant_text += LLMRunner.message_exception(e)
            logger.error(f"Error occured while generating response. Error: {e}")
            failed_status = True
        if len(assistant_text) == 0:
            raise (ValueError("LLM generated empty response! Please check logs!"))

        return assistant_text, thinking_text, failed_status

    def run_text_completion_simple(self, model: str, messages: List[dict], options: dict = None, thinking_flag=None):
        if options is None:
            options = {}
        _options = {"max_output_tokens": MAX_TOKENS_LIMIT}
        _options.update(options)
        api_messages = self.convert_messages_for_api(messages)
        # OpenAI does not support seed
        if "seed" in _options.keys():
            _options.pop("seed")

        url = f"{self.url}/generate"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "input": api_messages,
            "stream": False,
            **_options
        }
        if thinking_flag is not None:
            logger.warning(f"Reasoning not supported yet. Asked mode: {thinking_flag}")
        with requests.post(url, headers=headers, json=payload) as r:
            response = r.json()
            if response["status"] == "error":
                raise Exception(f"RemoteRunner error: {response["content"]}")
            return r.json()["content"]

    def get_embedding(self, embedding_config) -> Optional[Embeddings]:
        available_embedding_models = [x["model"] for x in self.get_models_with_capabilities() if "embedding" in x["capabilities"]]
        if embedding_config.get("model") in available_embedding_models:
            if self.is_model_installed(embedding_config.get("model")):
                return RemoteRunner.RemoteEmbeddings(self.url, model=embedding_config.get("model"))
        return None

    @staticmethod
    def from_dict(config: dict):
        runner = None
        try:
            if config.get('type') == 'remote':
                runner = RemoteRunner(config['url'])
        except Exception as e:
            logger.error(f"Could not create RemoteRunner from config. Reason: {e}")
        return runner

    def convert_messages_for_api(self, messages: List[dict]) -> List[dict]:
        return messages
