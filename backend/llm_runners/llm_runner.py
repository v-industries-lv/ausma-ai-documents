import json
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Tuple
import datetime
import os

from app_modules.multimodal_chat_module import MMChatModule
from convertors.llm_contexts import ChatContext
from domain import RoomMessage, MessageProgress
from langchain_core.embeddings import Embeddings

from generation_guard import GenerationGuard
from logger import logger
from room_states import RoomState
from settings import Settings, RAGSettings
from utils import utc_now, list_of_b64_from_paths
from reranker import rerank

RANDOM_SEED = 42
MAX_TOKENS_LIMIT = 32000

class LLMRunner(ABC):
    @abstractmethod
    def list_chat_models(self):
        pass

    @abstractmethod
    def is_model_installed(self, model) -> bool:
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
                f"Model {repr(model)} not installed! Available models: {';'.join([x.model for x in self.list_chat_models()])}")

    def chat(self, ctx: ChatContext, room_state: RoomState,
             user_input: dict,
             gen_guard: Optional[GenerationGuard],
             update_callback: Optional[Callable] = None,
             history: Optional[List[RoomMessage]] = None,
             rag_settings: RAGSettings = None) -> Tuple[str, str]:

        def rag_context_builder(rag_sources: dict):
            rag_tag_start = "<rag_source>"
            rag_tag_end = "</rag_source>"
            context_text_rag = "\n\nThe following text is context provided by RAG: \n"
            return context_text_rag + "\n" + '\n'.join([rag_tag_start + x["content"] + rag_tag_end for x in rag_sources])


        context_text_no_rag = "\n\nRAG did not find any relevant documents..."

        failed_status = False
        try:
            llm_model = ctx.llm_model
            self.check_model_installed(llm_model)
            user_content = user_input.get("content")
            if user_content is None or len(user_content) == 0:
                raise(ValueError("No text provided!"))
            context = ""
            reranked_rag_sources = None
            if ctx.kb is not None:
                embedding_model = ctx.kb.embedding_config["model"]
                self.check_model_installed(embedding_model)
                retrieved_documents = ctx.kb.rag_lookup(
                    self.get_embedding,
                    user_input["content"],
                    rag_settings.rag_document_count,
                )
                logger.info(f"RAG used in room {room_state.room_id}! Document count: {str(len(retrieved_documents))}")
                raw_rag_sources = [{"id": x[0].id, "similarity_score": x[1], "metadata": x[0].metadata,
                                    "content": x[0].page_content}
                                   for x in retrieved_documents]
                rag_context = ""
                reranked_rag_sources = rerank(raw_rag_sources, self.get_embedding(ctx.kb.embedding_config), rag_settings)
                if len(reranked_rag_sources) > 0:
                    rag_context = rag_context_builder(reranked_rag_sources)
                    logger.info(f"After reranking documents of room {room_state.room_id}, relevant document count: {str(len(reranked_rag_sources))}")

                if len(rag_context) == 0:
                    rag_context = context_text_no_rag
                    logger.info(f"RAG result in {room_state.room_id}: No relevant documents found!")
                context += rag_context

            user_message = {
                'role': 'user',
                'content': user_input["content"] + context,
            }
            images = user_input.get("images", [])
            supports_vision = self.supports_vision(llm_model)
            if supports_vision:
                user_message["images"] = list_of_b64_from_paths( [os.path.join(MMChatModule.UPLOAD_FOLDER, f) for f in images])
            elif len(images)>0:
                logger.warning(f"Ignoring images passed to a model that does not support vision. Model: {llm_model}")

            if len(history) == 0:
                messages = [ctx.get_system_message(), user_message]
            else:
                messages = []
                for message_item in history:
                    context = ""
                    if message_item.rag_sources is not None:
                        rag_sources_used = json.loads(message_item.rag_sources)
                        if rag_sources_used is not None:
                            if len(rag_sources_used) > 0:
                                context += rag_context_builder(rag_sources_used)
                            else:
                                context += context_text_no_rag
                    message = {"role": message_item.role}
                    message.update(json.loads(message_item.content))
                    if supports_vision:
                        msg_images = message.get("images", [])
                        message["images"] = list_of_b64_from_paths(
                            [os.path.join(MMChatModule.UPLOAD_FOLDER, f) for f in msg_images])
                    message["content"] += context
                    messages.append(message)

                messages.append(user_message)

            # TODO: implement think handling.
            # Right now either always sets it as False
            # Or leaves as None when thinking is not supported by the llm runner
            think_mode = self.supports_thinking(llm_model)
            if think_mode is not None:
                think_mode = False

            assistant_text, failed_status = self.run_text_completion_streaming(
                model=llm_model,
                messages=messages,
                is_stopped=room_state.is_stopped,
                gen_guard=gen_guard,
                update_callback=update_callback,
                think_mode=think_mode,
                options=ctx.options
            )
        except Exception as e:
            logger.error(f"[CHAT_FATAL]{room_state.room_id}", e)
            raise e
        if failed_status:
            room_state.stop()
        return assistant_text, json.dumps(reranked_rag_sources)

    @abstractmethod
    def run_text_completion_streaming(self, model: str, messages: List[dict], is_stopped: Callable[[], bool], gen_guard: Optional[GenerationGuard], update_callback: Callable[[MessageProgress], None], options: dict = None, think_mode=None) -> Tuple[Optional[str], bool]:
        pass

    @abstractmethod
    def run_text_completion_simple(self, model: str, messages: List[dict], options: dict = None, think_mode=None):
        pass

    @abstractmethod
    def get_embedding(self, embedding_config) -> Optional[Embeddings]:
        pass

    @abstractmethod
    def supports_thinking(self, model: str) -> Optional[bool]:
        pass

    @abstractmethod
    def supports_vision(self, model: str) -> Optional[bool]:
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
        runner_classes = [OllamaRunner, DebugRunner, OpenAIRunner, RemoteRunner]

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
    @staticmethod
    def from_dict(config: dict) -> Optional[LLMRunner]:
        from llm_runners.debug_runner import DebugRunner
        from llm_runners.ollama_runner import OllamaRunner
        from llm_runners.openai_runner import OpenAIRunner
        from llm_runners.remote_runner import RemoteRunner

        if config.get("active"):
            if config["type"] == "ollama":
                return OllamaRunner.from_dict(config)
            elif config["type"] == "openai":
                return OpenAIRunner.from_dict(config)
            elif config["type"] == "remote":
                return RemoteRunner.from_dict(config)
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
        self.runners = runners
        self._cached_models = None
        self._last_cached = None

    def list_chat_models(self):
        models = []
        if self._cached_models is not None and datetime.datetime.now(
                datetime.UTC) - self._last_cached < datetime.timedelta(days=1):
            return self._cached_models
        self._last_cached = datetime.datetime.now(datetime.UTC)
        for runner in self.runners:
            runner_models = []
            try:
                runner_models = runner.list_chat_models()
            except Exception as e:
                logger.error(f"An error occured trying to list models. Error: {e}")
            models += runner_models
        self._cached_models = models
        return models

    def refresh_model_cache(self):
        # Make the cache stale as opposed to clearing cached models. Prevents concurrent users from clearing each others model list while refreshing.
        self._last_cached = datetime.datetime(1970, 1, 1, tzinfo=datetime.UTC)
        self.list_chat_models()

    def run_text_completion_streaming(self, model: str, messages: List[dict], is_stopped: Callable[[], bool], gen_guard: Optional[GenerationGuard], update_callback: Callable[[MessageProgress], None], options: dict = None, think_mode=None) -> Tuple[Optional[str], bool]:
        if options is None:
            options = {}
        for runner in self.runners:
            if runner.is_model_installed(model):
                return runner.run_text_completion_streaming(model, messages, is_stopped, gen_guard, update_callback, options, think_mode=think_mode)
        return None, True

    def run_text_completion_simple(self, model: str, messages: List[dict], options: dict = None, think_mode=None):
        if options is None:
            options = {}
        for runner in self.runners:
            if runner.is_model_installed(model):
                return runner.run_text_completion_simple(model, messages, options, think_mode=think_mode)
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
