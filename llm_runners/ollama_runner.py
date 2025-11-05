import datetime
import json
from typing import Optional, List, Iterator, Callable

import requests
from langchain_ollama import OllamaEmbeddings
from ollama import ChatResponse, Client

from domain import MessageProgress
from llm_runners.llm_runner import LLMRunner, RANDOM_SEED
from utils import utc_now
from logger import logger


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
        self.client = Client(host=host)

    def list_chat_models(self) -> List[str]:
        completion_models = []
        for model in [x.model for x in self.client.list().models]:
            model_info = json.loads(
                requests.post(
                    self.host + '/api/show',
                    data='{"model": "' + model + '"}',
                    headers={'Content-Type': 'application/json'}
                ).content
            )
            if 'completion' in model_info['capabilities']:
                completion_models.append(model)
        return completion_models

    def run_text_completion_streaming(self, model: str, messages: List[dict], update_callback: Callable[[MessageProgress], None], options: dict = None):
        if options is None:
            options = {}
        _options = {"seed": RANDOM_SEED}
        _options.update(options)

        response: Iterator[ChatResponse] = self.client.chat(
            model=model,
            messages=messages,
            stream=True,
            options=_options,
        )
        assistant_text = ''
        num_chunks = 0
        last_timestamp: Optional[datetime.datetime] = None
        # TODO: better speed visualisation?
        for chunk in response:
            current_timestamp = utc_now()
            assistant_text += chunk['message']['content']
            num_chunks += 1
            if last_timestamp is not None:
                if update_callback is not None:
                    update_callback(
                        MessageProgress( 1, (current_timestamp - last_timestamp).total_seconds(),
                                        num_chunks))
            last_timestamp = current_timestamp
        return assistant_text

    def run_text_completion_simple(self, model: str, messages: List[dict], options: dict = None):
        if options is None:
            options = {}
        _options = {"seed": RANDOM_SEED}
        _options.update(options)

        response: ChatResponse = self.client.chat(
            model=model,
            messages=messages,
            stream=False,
            options=_options,
        )

        return response['message']['content']

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
        installed_models = self.client.list().models
        if not self.is_model_installed(model):
            logger.error(f"[LLM_MODEL_NOT_FOUND]_{model}_{utc_now().isoformat()}")
            raise ValueError(
                f"Model {repr(model)} not installed! Available models: {';'.join([x.model for x in installed_models])}")

    def is_model_installed(self, model) -> bool:
        installed_models = self.client.list().models
        return model in [x.model for x in installed_models] and model is not None

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

