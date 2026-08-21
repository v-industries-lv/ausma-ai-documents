from typing import Optional, Callable, List, Tuple
import time

from generation_guard import GenerationGuard
from logger import logger
from langchain_core.embeddings import Embeddings

from domain import MessageProgress
from llm_runners.llm_runner import LLMRunner


class DebugRunner(LLMRunner):
    def get_models_with_capabilities(self) -> List[dict]:
        return self.cached_models

    def remove_model(self, model) -> bool:
        return False

    def convert_messages_for_api(self, messages: List[dict]) -> List[dict]:
        return messages

    def pull_model(self, model) -> bool:
        return False

    def run_text_completion_streaming(self, model: str, messages: List[dict], is_stopped: Callable[[], bool],
                                      gen_guard: GenerationGuard, update_callback: Callable[[MessageProgress], None],
                                      options: dict = None, thinking_flag=None) -> Tuple[str, str, bool]:
        return DebugRunner._mock_output()

    def run_text_completion_simple(self, model: str, messages: List[dict], options: dict = None, thinking_flag=None) -> str:
        return DebugRunner._mock_output()[0]

    @staticmethod
    def from_dict(config: dict):
        runner = None
        try:
            if config.get('type') == 'debug':
                runner = DebugRunner()
        except Exception as e:
            logger.error(f"Could not create Debug runner from config. Reason: {e}")
        return runner

    def get_options(self, model):
        return {
            "option1": 123,
            "option2": "abc",
            "option3": None,
        }

    def __init__(self):
        super().__init__("debug")
        self.cached_models = [
            {
                "model": "debug_lorem_ipsum",
                "capabilities": ["completion"],
                "runner_type": self.runner_type,
            },
            {
                "model":  "debug_code",
                "capabilities": ["completion"],
                "runner_type": self.runner_type,
            },
            {
                "model": "debug_markdown",
                "capabilities": ["completion"],
                "runner_type": self.runner_type,
            },
        ]

    def get_embedding(self, embedding_config: dict) -> Optional[Embeddings]:
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
        return assistant_text, 'thinking of text', False
