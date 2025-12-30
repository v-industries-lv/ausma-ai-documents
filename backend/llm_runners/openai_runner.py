import datetime
import json
import os.path
import shutil
from typing import Optional, List, Callable, Tuple

import requests
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from domain import MessageProgress
from generation_guard import GenerationGuard
from llm_runners.llm_runner import LLMRunner, MAX_TOKENS_LIMIT

from logger import logger

from utils import utc_now


class OpenAIRunner(LLMRunner):
    @staticmethod
    def from_dict(config: dict):
        runner = None
        try:
            if config.get('type') == 'openai':
                runner = OpenAIRunner(api_key=config["api_key"])
        except Exception as e:
            logger.error(f"Could not create Ollama runner from config. Reason: {e}")
        return runner

    def __init__(self, api_key: str):
        self.host_api = "https://api.openai.com/v1"
        self.api_key = api_key
        self._model_list_file = "openai_models.json"
        if os.path.exists(self._model_list_file):
            with open(self._model_list_file, "r") as fh:
                self.models: List[str] = sorted(set(json.load(fh)))
        else:
            self.models: List[str] = ["gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"]
            self._save_models()
        self.cached_openai_models: Optional[List[str]] = None
        self.last_update: Optional[datetime.datetime] = None
        self.get_openai_models()


    def _save_models(self):
        temp_file = self._model_list_file + ".tmp"
        with open(temp_file, "w") as fh:
            json.dump(self.models, fh, indent=2)
        shutil.move(temp_file, self._model_list_file)

    def list_chat_models(self):
        online_models = self.get_openai_models()
        _models = []
        for model in self.models:
            if model in online_models:
                _models.append(model)
            else:
                logger.error(f"OpenAIRunner: Could not find model {model} online")
        return _models

    def get_openai_models(self) -> List[str]:
        if self.last_update is None or datetime.datetime.now(datetime.UTC) - self.last_update > datetime.timedelta(days=1):
            response = json.loads(
                requests.get(
                    f"{self.host_api}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                ).content
            )
            self.cached_openai_models = [x["id"] for x in response["data"]]
            self.last_update = datetime.datetime.now(datetime.UTC)
        return self.cached_openai_models

    def is_model_installed(self, model) -> bool:
        response = json.loads(
            requests.get(
                f"{self.host_api}/models/{model}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            ).content
        )
        return response.get("id") == model

    def pull_model(self, model) -> bool:
        if self.is_model_installed(model):
            if model not in self.models:
                self.models.append(model)
                self._save_models()
            return True
        return False

    def remove_model(self, model) -> bool:
        if model in self.models:
            self.models.remove(model)
            self._save_models()
            return True
        return False

    def run_text_completion_streaming(self, model: str, messages: List[dict], is_stopped: Callable[[], bool],
                                      gen_guard: GenerationGuard,
                                      update_callback: Callable[[MessageProgress], None], options: dict = None) -> Tuple[Optional[str], bool]:
        failed_status = False
        if options is None:
            options = {}
        _options = {"max_output_tokens": MAX_TOKENS_LIMIT}
        _options.update(options)
        # OpenAI does not support seed
        if "seed" in _options.keys():
            _options.pop("seed")
        if gen_guard is None:
            gen_guard = GenerationGuard()
        url = f"{self.host_api}/responses"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "input": messages,
            "stream": True,
            **_options
        }
        assistant_text = ''
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
                            return assistant_text, True
                        if not line:
                            continue
                        decoded_line = line.decode("utf-8").strip()
                        if decoded_line == "[DONE]":
                            break

                        if decoded_line.startswith("data:"):
                            data_str = decoded_line[len("data:"):].strip()
                            event = json.loads(data_str)
                            etype = event.get("type")

                            if etype == "response.error":
                                raise (Exception(f"{event["error"]["message"]}"))
                            elif etype == "response.completed":
                                break
                            elif etype == "response.output_text.delta":
                                current_timestamp = utc_now()
                                if etype == "response.output_text.delta":
                                    chunk_text = event["delta"]
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
            if len(assistant_text) > 0:
                assistant_text += LLMRunner.message_exception(e)
            logger.error(f"Error occured while generating response. Error: {e}")
            failed_status = True
        if len(assistant_text) == 0:
            raise (ValueError("LLM generated empty response! Please check logs!"))

        return assistant_text, failed_status


    def run_text_completion_simple(self, model: str, messages: List[dict], options: dict = None):
        if options is None:
            options = {}
        _options = {"max_output_tokens": MAX_TOKENS_LIMIT}
        _options.update(options)
        # OpenAI does not support seed
        if "seed" in _options.keys():
            _options.pop("seed")

        url = f"{self.host_api}/responses"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "input": messages,
            "stream": False,
            **_options
        }

        with requests.post(url, headers=headers, json=payload, stream=True) as r:
            return r.json()["output"][0]["content"][0]["text"]

    def get_embedding(self, embedding_config) -> Optional[Embeddings]:
        if self.is_model_installed(embedding_config["model"]):
            return OpenAIEmbeddings(model=embedding_config["model"], api_key=SecretStr(self.api_key))
        return None

    def supports_thinking(self, model: str) -> Optional[bool]:
        """
        OpenAI library does not provide a way to tell programmatically if the model is reasoning (thinking) or not.
        """
        return None
