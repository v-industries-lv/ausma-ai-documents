import json
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Tuple
from domain import RoomMessage, MessageProgress
from langchain_core.embeddings import Embeddings
from logger import logger
from knowledge_base import KnowledgeBase
from utils import utc_now


class ChatContext:
    def __init__(self, llm_model: str, system_prompt: str, rag_document_count: int, kb: KnowledgeBase):
        self.llm_model = llm_model
        self.system_prompt = system_prompt
        self.rag_document_count = rag_document_count
        self.kb = kb


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

    def chat(self, ctx: ChatContext, room_id: str, user_input: str,
             update_callback: Optional[Callable] = None,
             history: Optional[List[RoomMessage]] = None) -> Tuple[str, str, str]:
        if history is None:
            history = []
        try:
            llm_model = ctx.llm_model
            self.check_model_installed(llm_model)
            context = ""
            relevant_documents = []
            if ctx.kb is not None:
                embedding_model = ctx.kb.embedding_config["model"]
                self.check_model_installed(embedding_model)
                relevant_documents = ctx.kb.rag_lookup(
                    self.get_embedding,
                    user_input,
                    ctx.rag_document_count
                )
                if len(relevant_documents) > 0:
                    context += "\n\nThe following text is context provided by RAG: \n" + '\n'.join(
                        [document[0].page_content for document in relevant_documents])
                    logger.info(f"RAG used in room {room_id}! Document count: {str(len(relevant_documents))}")
                else:
                    logger.info(f"RAG used in room {room_id}! No relevant documents found!")
                    context += "RAG did not find any relevant documents..."
            user_message = {
                'role': 'user',
                'content': user_input + context,
            }
            if len(history) == 0:
                sys_message = {
                    'role': 'system',
                    'content': ctx.system_prompt
                }
                messages = [sys_message, user_message]
            else:
                messages = []
                for message_item in history:
                    messages.append(
                        {
                            "role": message_item.role,
                            "content": message_item.content,
                        }
                    )
                messages.append(user_message)
            rag_sources = json.dumps(
                [{"id": x[0].id, "similarity_score": x[1], "metadata": x[0].metadata, "content": x[0].page_content} for
                 x in
                 relevant_documents])

            # TODO: thinking handling think=True, temperature handling
            assistant_text = self.run_text_completion_streaming(llm_model, messages, update_callback)
            # TODO: handle thinking
            train_of_thought = ''
            # if hasattr(response, "thinking"):
            #     train_of_thought = response['message']['thinking']
            messages.append({"role": "assistant", "content": assistant_text})
        except Exception as e:
            logger.error(f"[CHAT_FATAL]{room_id}", e)
            # TODO: better exception handling
            raise()

        return assistant_text, rag_sources, train_of_thought

    @abstractmethod
    def run_text_completion_streaming(self, model: str, messages: List[dict], update_callback: Callable[[MessageProgress], None], options: dict = None):
        pass

    @abstractmethod
    def run_text_completion_simple(self, model: str, messages: List[dict], options: dict = None):
        pass

    @abstractmethod
    def get_embedding(self, embedding_config) -> Optional[Embeddings]:
        pass

    @abstractmethod
    def supports_thinking(self, model: str) -> Optional[bool]:
        pass

    @staticmethod
    def from_settings_list(settings: List[dict]):
        result = []

        # importing locally to avoid cyclic imports
        from llm_runners.ollama_runner import OllamaRunner
        from llm_runners.debug_runner import DebugRunner
        from llm_runners.hf_runner import HFRunner
        runner_classes = [OllamaRunner, HFRunner, DebugRunner]

        for item in settings:
            for runner_cls in runner_classes:
                try:
                    runner = runner_cls.from_settings(item)
                except Exception as e:
                    logger.error(f"An error occured while making a LLM runner from settings. Error: {e}")
                    continue
                if runner is not None:
                    result.append(runner)
        return result


class SuperRunner(LLMRunner):
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

    def __init__(self, runners: List[LLMRunner]):
        self.runners = runners

    def list_chat_models(self):
        models = []
        for runner in self.runners:
            runner_models = []
            try:
                runner_models = runner.list_chat_models()
            except Exception as e:
                logger.error(f"An error occured trying to list models. Error: {e}")
            models += runner_models
        return models

    def run_text_completion_streaming(self, model: str, messages: List[dict], update_callback: Callable[[MessageProgress], None], options: dict = None):
        if options is None:
            options = {}
        for runner in self.runners:
            if runner.is_model_installed(model):
                return runner.run_text_completion_streaming(model, messages, update_callback, options)
        return None

    def run_text_completion_simple(self, model: str, messages: List[dict], options: dict = None):
        if options is None:
            options = {}
        for runner in self.runners:
            if runner.is_model_installed(model):
                return runner.run_text_completion_simple(model, messages, options)
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
