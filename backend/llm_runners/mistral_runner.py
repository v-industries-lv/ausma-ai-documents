from typing import Optional, List, Callable, Tuple
import json
from langchain_core.embeddings import Embeddings
from langchain_mistralai import MistralAIEmbeddings
import datetime
import os
from domain import MessageProgress
from generation_guard import GenerationGuard
import shutil
import requests
from logger import logger
from pydantic import SecretStr

from llm_runners.llm_runner import LLMRunner
from utils import utc_now


class MistralRunner(LLMRunner):
    def convert_messages_for_api(self, messages: List[dict]) -> List[dict]:
        api_compatible_messages = []
        for message in messages:
            if message["role"] == "user":
                if 'images' in message:
                    content = [{"type": "text", "text": message["content"]}]
                    content += [{"type": "image_url", "image_url": f"data:image/png;base64,{x}"} for x in message["images"]]
                else:
                    content = message["content"]

                api_compatible_messages.append(
                    {
                        'role': 'user',
                        'content': content
                    }
                )
            else:
                api_compatible_messages.append(message)
        return api_compatible_messages

    def get_options(self, model):
        # No specific options yet
        return {}

    @staticmethod
    def from_dict(config: dict):
        runner = None
        try:
            if config.get('type') == 'mistralai':
                runner = MistralRunner(api_key=config["api_key"])
        except Exception as e:
            logger.error(f"Could not create MistralAI runner from config. Reason: {e}")
        return runner

    def __init__(self, api_key):
        super().__init__("mistralai")
        self.host_api = "https://api.mistral.ai/v1"
        self.api_key = api_key
        self._model_list_file = "mistralai_models.json"
        if os.path.exists(self._model_list_file):
            with open(self._model_list_file, "r") as fh:
                self.cached_models: List[dict] = json.load(fh)
        else:
            self.cached_models: List[dict] = [
                {
                    "model": "mistral-large-latest",
                    "capabilities": ["completion", "vision"],
                    "runner_type": self.runner_type,
                },
                {
                    "model": "mistral-medium-latest",
                    "capabilities": ["completion", "vision"],
                    "runner_type": self.runner_type,
                },
                {
                    "model": "mistral-small-latest",
                    "capabilities": ["completion", "vision", "thinking"],
                    "runner_type": self.runner_type,
                },
                {
                    "model": "mistral-embed",
                    "capabilities": ["embedding"],
                    "runner_type": self.runner_type,
                }
            ]
            self._save_models()
        self.get_models_with_capabilities()
        
    def _save_models(self):
        temp_file = self._model_list_file + ".tmp"
        with open(temp_file, "w") as fh:
            json.dump(self.cached_models, fh, indent=2)
        shutil.move(temp_file, self._model_list_file)

    def pull_model(self, model) -> bool:
        if self.is_model_installed(model):
            if model not in self.cached_models:
                self.cached_models.append(model)
                self._save_models()
            return True
        return False

    def remove_model(self, model) -> bool:
        if model in self.cached_models:
            self.cached_models.remove(model)
            self._save_models()
            return True
        return False

    def run_text_completion_streaming(self, model: str, messages: List[dict], is_stopped: Callable[[], bool],
                                      gen_guard: Optional[GenerationGuard],
                                      update_callback: Callable[[MessageProgress], None], options: dict = None, thinking_flag=None) -> Tuple[str, str, bool]:

        failed_status = False
        api_messages = self.convert_messages_for_api(messages)
        if options is None:
            options = {}
        _options = self.get_options(model)
        _options.update(options)
        if gen_guard is None:
            gen_guard = GenerationGuard()

        url = f"{self.host_api}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "stream": True,
            "messages": api_messages
        }
        # TODO
        # Default is off for now
        if thinking_flag is not None:
            logger.warning(f"Reasoning not supported yet. Asked mode: {thinking_flag}")

        assistant_text = ''
        thinking_text = ''
        num_chunks = 0
        last_timestamp: Optional[datetime.datetime] = None
        try:
            with requests.post(url, headers=headers, json=payload, stream=True) as r:
                if r.status_code != 200:
                    err = r.json()
                    raise Exception(
                        f"{err['type']}: {err['message']} (code={err.get('code')})"
                    )
                for line in r.iter_lines(decode_unicode=True):
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

                    if not line.startswith("data: "):
                        continue

                    current_timestamp = utc_now()
                    data = line[6:]

                    if data == "[DONE]":
                        break

                    event = json.loads(data)

                    delta = event["choices"][0]["delta"]

                    chunk_text = delta.get("content")

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

        url = f"{self.host_api}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": api_messages,
            "stream": False,
            "options": _options
        }
        if thinking_flag is not None:
            logger.warning(f"Reasoning not supported yet. Asked mode: {thinking_flag}")

        with requests.post(url, headers=headers, json=payload, stream=True) as r:
            # Only "content" is relevant for RAG document prep.
            result = r.json()
            logger.info(result)
            return result["choices"][0]["message"]["content"]

    def get_embedding(self, embedding_config) -> Optional[Embeddings]:
        available_embedding_models = [x["model"] for x in self.get_models_with_capabilities() if "embedding" in x["capabilities"]]
        if embedding_config.get("model") in available_embedding_models:
            # We still check, if model is actually available, because it could be cached, but removed at server side
            if self.is_model_installed(embedding_config["model"]):
                return MistralAIEmbeddings(model=embedding_config["model"], api_key=SecretStr(self.api_key))
        return None

    def get_models_with_capabilities(self) -> List[dict]:
        if self.last_update is None or datetime.datetime.now(datetime.UTC) - self.last_update > datetime.timedelta(
                days=1):
            response = json.loads(
                requests.get(
                    f"{self.host_api}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                ).content
            )
            serverside_models = [x["id"] for x in response["data"]]
            # Leave only defined models
            self.cached_models = [x for x in self.cached_models if x["model"] in serverside_models]
            self.last_update = datetime.datetime.now(datetime.UTC)
        return self.cached_models
    