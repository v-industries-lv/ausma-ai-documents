import datetime
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Tuple

from langchain_core.embeddings import Embeddings

from domain import MessageProgress
from generation_guard import GenerationGuard
from logger import logger
from settings import Settings
from utils import utc_now

RANDOM_SEED = 42
MAX_TOKENS_LIMIT = 32000

class LLMRunner(ABC):
    def __init__(self, runner_type: str):
        self.runner_type = runner_type
        self.last_update: Optional[datetime.datetime] = None
        self.cached_models: Optional[List[dict]] = None

    @abstractmethod
    def get_models_with_capabilities(self) -> List[dict]:
        pass

    def refresh_model_cache(self):
        # Make the cache stale as opposed to clearing cached models. Prevents concurrent users from clearing each others model list while refreshing.
        self.last_update = None
        self.cached_models = self.get_models_with_capabilities()

    def supports_thinking(self, model: str) -> Optional[bool]:
        available_thinking_models = [x["model"] for x in self.get_models_with_capabilities() if "thinking" in x["capabilities"]]
        if model in available_thinking_models:
            return True
        return False

    def supports_vision(self, model: str) -> Optional[bool]:
        available_vision_models = [x["model"] for x in self.get_models_with_capabilities() if "vision" in x["capabilities"]]
        if model in available_vision_models:
            return True
        return False

    def list_chat_models(self):
        available_completion_models = [x["model"] for x in self.get_models_with_capabilities() if "completion" in x["capabilities"]]
        if len(available_completion_models) == 0:
            logger.error(f"{type(self)}: Could not find any completion models!")
        return available_completion_models

    def is_model_installed(self, model) -> bool:
        return model in [x["model"] for x in self.get_models_with_capabilities()]

    @abstractmethod
    def convert_messages_for_api(self, messages: List[dict]) -> List[dict]:
        pass

    @abstractmethod
    def pull_model(self, model) -> bool:
        pass

    @abstractmethod
    def remove_model(self, model) -> bool:
        pass

    def check_model_installed(self, model):
        if not self.is_model_installed(model):
            logger.error(f"[LLM_MODEL_NOT_FOUND]_{model}_{utc_now().isoformat()}")
            raise ValueError(
                f"Model {repr(model)} not installed! Available models: {';'.join([x["model"] for x in self.get_models_with_capabilities()])}")

    @abstractmethod
    def run_text_completion_streaming(self, model: str, messages: List[dict], is_stopped: Callable[[], bool],
                                      gen_guard: Optional[GenerationGuard], update_callback: Callable[[MessageProgress], None],
                                      options: dict = None, thinking_flag=None) -> Tuple[str, str, bool]:
        pass

    @abstractmethod
    def run_text_completion_simple(self, model: str, messages: List[dict], options: dict = None, thinking_flag=None):
        pass

    @abstractmethod
    def get_embedding(self, embedding_config) -> Optional[Embeddings]:
        pass

    @staticmethod
    @abstractmethod
    def from_dict(config: dict):
        pass

    @abstractmethod
    def get_options(self, model):
        pass

    @staticmethod
    def from_settings(settings: Settings):
        result = []

        # importing locally to avoid cyclic imports
        from llm_runners.ollama_runner import OllamaRunner
        from llm_runners.debug_runner import DebugRunner
        from llm_runners.openai_runner import OpenAIRunner
        from llm_runners.remote_runner import RemoteRunner
        from llm_runners.mistral_runner import MistralRunner

        runner_classes = [OllamaRunner, DebugRunner, OpenAIRunner, RemoteRunner, MistralRunner]

        for item in settings.get_llm_runners():
            for runner_cls in runner_classes:
                if item.get("active"):
                    try:
                        runner = runner_cls.from_dict(item)
                    except Exception as e:
                        logger.error(f"An error occured while making a LLM runner from settings. Error: {e}")
                        continue
                    if runner is not None:
                        result.append(runner)
        return result

    @staticmethod
    def message_exception(e: Exception):
        message_text = "\n\n"
        message_text += "---\n\n"
        message_text += "SYSTEM: \n\n"
        message_text += f"LLM generation has failed: {e}\n\n"
        message_text += "Please try another prompt and/or model in a different chatroom.\n\n"
        message_text += "---\n\n"
        return message_text


class SuperRunner(LLMRunner):
    def get_models_with_capabilities(self) -> List[dict]:
        models = []
        for runner in self.runners:
            models += runner.get_models_with_capabilities()
        return models

    def convert_messages_for_api(self, messages: List[dict]) -> List[dict]:
        # SuperRunner does not require message formatting
        return messages

    @staticmethod
    def from_dict(config: dict) -> Optional[LLMRunner]:
        from llm_runners.debug_runner import DebugRunner
        from llm_runners.ollama_runner import OllamaRunner
        from llm_runners.openai_runner import OpenAIRunner
        from llm_runners.remote_runner import RemoteRunner
        from llm_runners.mistral_runner import MistralRunner

        if config.get("active"):
            if config["type"] == "ollama":
                return OllamaRunner.from_dict(config)
            elif config["type"] == "openai":
                return OpenAIRunner.from_dict(config)
            elif config["type"] == "remote":
                return RemoteRunner.from_dict(config)
            elif config["type"] == "mistralai":
                return MistralRunner.from_dict(config)
            elif config["type"] == "debug":
                return DebugRunner.from_dict(config)
        return None

    def remove_model(self, model) -> bool:
        model_removed = False
        for runner in self.runners:
            if runner.is_model_installed(model):
                runner.remove_model(model)
                model_removed = True
        return model_removed

    def is_model_installed(self, model) -> bool:
        for runner in self.runners:
            is_installed = runner.is_model_installed(model)
            if is_installed:
                return True
        return False

    def get_options(self, model):
        for runner in self.runners:
            is_installed = runner.is_model_installed(model)
            if is_installed:
                return runner.get_options(model)
        return None

    def __init__(self, runners: List[LLMRunner]):
        super().__init__("super")
        self.runners = runners

    def list_chat_models(self):
        models = []
        for runner in self.runners:
            try:
                models += runner.list_chat_models()
            except Exception as e:
                logger.error(f"An error occured trying to list models from runner {runner.runner_type}. Error: {e}")
        return models

    def refresh_model_cache(self):
        for runner in self.runners:
            runner.refresh_model_cache()

    def run_text_completion_streaming(self, model: str, messages: List[dict], is_stopped: Callable[[], bool],
                                      gen_guard: Optional[GenerationGuard], update_callback: Callable[[MessageProgress], None],
                                      options: dict = None, thinking_flag=None) -> Tuple[str, str, bool]:
        if options is None:
            options = {}
        runner = self.get_runner_by_model(model)
        if runner is not None:
            return runner.run_text_completion_streaming(model, messages, is_stopped, gen_guard, update_callback, options, thinking_flag=thinking_flag)
        return '', '', True

    def run_text_completion_simple(self, model: str, messages: List[dict], options: dict = None, thinking_flag=None):
        if options is None:
            options = {}
        runner = self.get_runner_by_model(model)
        if runner is not None:
            return runner.run_text_completion_simple(model, messages, options, thinking_flag=thinking_flag)
        return None

    def get_embedding(self, embedding_config: dict) -> Optional[Embeddings]:
        for runner in self.runners:
            embedding = runner.get_embedding(embedding_config)
            if embedding is not None:
                return embedding
        return None

    def supports_thinking(self, model: str) -> Optional[bool]:
        for runner in self.runners:
            supports_thinking = runner.supports_thinking(model)
            if supports_thinking is not None:
                return supports_thinking
        return None

    def supports_vision(self, model: str) -> Optional[bool]:
        for runner in self.runners:
            supports_vision = runner.supports_vision(model)
            if supports_vision is not None:
                return supports_vision
        return None

    def pull_model(self, model) -> bool:
        model_ready = False
        for runner in self.runners:
            if model_ready:
                break
            try:
                model_ready = runner.pull_model(model)
            except Exception:
                pass
        return model_ready

    def get_runners_by_type(self, runner_type) -> List[LLMRunner]:
        return [x for x in self.runners if x.runner_type == runner_type]

    def get_runner_by_model(self, model) -> Optional[LLMRunner]:
        for runner in self.runners:
            if runner.is_model_installed(model):
                return runner
        return None