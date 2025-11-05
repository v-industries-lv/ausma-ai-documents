import json
import os.path
import shutil
from typing import Optional, List, Callable

import requests
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from openai.types.chat import ChatCompletionMessageParam
from pydantic import SecretStr

from domain import MessageProgress
from llm_runners.llm_runner import LLMRunner, RANDOM_SEED

from logger import logger
from openai import OpenAI

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
        self.client: OpenAI = OpenAI(api_key=api_key)
        self._model_list_file = "openai_models.json"
        if os.path.exists(self._model_list_file):
            with open(self._model_list_file, "r") as fh:
                self.models: List[str] = sorted(set(json.load(fh)))
        else:
            self.models: List[str] = ["gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"]
            self._save_models()

    def _save_models(self):
        temp_file = self._model_list_file + ".tmp"
        with open(temp_file, "w") as fh:
            json.dump(self.models, fh, indent=2)
        shutil.move(temp_file, self._model_list_file)

    def list_chat_models(self):
        response = json.loads(
            requests.get(
                f"https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {self.client.api_key}"}
            ).content
        )
        online_models = [x["id"] for x in response["data"]]
        _models = []
        for model in self.models:
            if model in online_models:
                _models.append(model)
            else:
                logger.error(f"OpenAIRunner: Could not find model {model} online")
        return _models

    def is_model_installed(self, model) -> bool:
        response = json.loads(
            requests.get(
                f"https://api.openai.com/v1/models/{model}",
                headers={"Authorization": f"Bearer {self.client.api_key}"}
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

    def run_text_completion_streaming(self, model: str, messages: List[ChatCompletionMessageParam],
                                      update_callback: Callable[[MessageProgress], None], options: dict = None):

        _options = {
            "seed": RANDOM_SEED
        }
        _options.update(options)
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            **_options
        )
        assistant_text = ''
        num_chunks = 0
        # TODO: better speed visualisation?
        # No t/s for openai, network latency is much greater than token generation time.
        for chunk in response:
            delta = chunk.choices[0].delta.content
            assistant_text += "" if delta is None else delta
            num_chunks += 1
            if update_callback is not None:
                update_callback(
                    MessageProgress(None, None,
                                    num_chunks))
        return assistant_text


    def run_text_completion_simple(self, model: str, messages: List[ChatCompletionMessageParam], options: dict = None):
        _options = {
            "seed": RANDOM_SEED
        }
        _options.update(options)
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            **_options
        ).choices[0].message.content

    def get_embedding(self, embedding_config) -> Optional[Embeddings]:
        if self.is_model_installed(embedding_config["model"]):
            return OpenAIEmbeddings(model=embedding_config["model"], api_key=SecretStr(self.client.api_key))
        return None

    def supports_thinking(self, model: str) -> Optional[bool]:
        """
        OpenAI library does not provide a way to tell programmatically if the model is reasoning (thinking) or not.
        """
        return None
