import os
import shutil
import unittest

from llm_runners.llm_runner import SuperRunner
from mock_classes import MockLLMRunner, MockEmbedding

class SuperLLMRunnerTest(unittest.TestCase):
    def test_get_runner_by_model(self):
        super_runner = SuperRunner(
            [
                MockLLMRunner(),
            ]
        )
        runner = super_runner.get_runner_by_model("test_model")
        self.assertEqual("mock_runner", runner.runner_type)

    def test_get_runners_by_type(self):
        super_runner = SuperRunner(
            [
                MockLLMRunner(),
                MockLLMRunner(),
                MockLLMRunner(),
            ]
        )
        runners = super_runner.get_runners_by_type("mock_runner")
        self.assertEqual(3, len(runners))

    def test_is_model_installed(self):
        super_runner = SuperRunner(
            [
                MockLLMRunner(),
            ]
        )
        self.assertTrue(super_runner.is_model_installed("test_model"))
        self.assertFalse(super_runner.is_model_installed("does_not_exist"))

    def test_get_options(self):
        super_runner = SuperRunner(
            [
                MockLLMRunner(),
            ]
        )
        self.assertEqual({'mock_opt': 'mock_val'}, super_runner.get_options("test_model"))
        self.assertIsNone(super_runner.get_options("does_not_exist"))

    def test_supports_vision(self):
        super_runner = SuperRunner(
            [
                MockLLMRunner(),
            ]
        )
        self.assertTrue(super_runner.supports_vision("test_model_vision"))

    def test_supports_thinking(self):
        super_runner = SuperRunner(
            [
                MockLLMRunner(),
            ]
        )
        self.assertTrue(super_runner.supports_thinking("test_model_thinking"))

    def test_manage_models(self):
        super_runner = SuperRunner(
            [
                MockLLMRunner(),
            ]
        )
        self.assertTrue(super_runner.pull_model("new_test_model"))
        self.assertEqual(['test_model', 'test_model_vision', 'test_model_thinking', 'new_test_model'], super_runner.list_chat_models())
        self.assertTrue(super_runner.remove_model("new_test_model"))
        super_runner.refresh_model_cache()
        self.assertEqual(['test_model', 'test_model_vision', 'test_model_thinking'], super_runner.list_chat_models())

    def test_get_embedding(self):
        super_runner = SuperRunner(
            [
                MockLLMRunner(),
            ]
        )
        embedding = super_runner.get_embedding({"model": "test_embedding"})

        self.assertIsInstance(embedding, MockEmbedding)

    def test_convert_messages_for_api(self):
        super_runner = SuperRunner(
            [
                MockLLMRunner(),
            ]
        )
        messages = super_runner.convert_messages_for_api([{"role": "user", "content": "test"}])
        self.assertEqual([{"role": "user", "content": "test"}], messages)


if __name__ == '__main__':
    unittest.main()