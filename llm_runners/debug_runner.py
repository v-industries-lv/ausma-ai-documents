from typing import Optional, Callable, List
import json
import time
from logger import logger
from langchain_core.embeddings import Embeddings

from domain import MessageProgress
from llm_runners.llm_runner import LLMRunner


class DebugRunner(LLMRunner):
    def remove_model(self, model) -> bool:
        return False

    def pull_model(self, model) -> bool:
        return False

    def is_model_installed(self, model) -> bool:
        return model in self.list_chat_models()

    def run_text_completion_streaming(self, model: str, messages: List[dict], update_callback: Callable[[MessageProgress], None], options: dict = None):
        return DebugRunner._mock_output()

    def run_text_completion_simple(self, model: str, messages: List[dict], options: dict = None):
        return DebugRunner._mock_output()

    @staticmethod
    def from_settings(settings: dict):
        runner = None
        try:
            if settings.get('type') == 'debug':
                runner = DebugRunner()
        except Exception as e:
            logger.error(f"Could not create Debug runner from config. Reason: {e}")
        return runner

    def __init__(self):
        pass

    def list_chat_models(self):
        return ["debug_lorem_ipsum", "debug_code", "debug_markdown"]

    def get_embedding(self, embedding_config: dict) -> Optional[Embeddings]:
        return None

    def supports_thinking(self, model: str) -> Optional[bool]:
        if self.is_model_installed(model) is not None:
            return True
        return None

    @staticmethod
    def _mock_output():
        time.sleep(2)
        assistant_text = """
    <h1>Lorem Ipsum</h1>
    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. </p>
    <h2>Lorem Ipsum</h2>
    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. </p>
    <ul>
    <li>Lorem Ipsum</li>
    <li>Lorem Ipsum</li>
    <li>Lorem Ipsum</li>
    <li>Lorem Ipsum</li>
    </ul>
    
    
            """
        source_example = {"document": "example_doc.pdf", "page": 42,
                          "text": "Lorem ipsum, lorem ipsum, lorem ipsum."}
        rag_sources = json.dumps([source_example, source_example, source_example])
        train_of_thought = "I think therefore I think."
        return assistant_text, rag_sources, train_of_thought
