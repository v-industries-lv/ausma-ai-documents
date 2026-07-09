import threading
import time
import unittest

from llm_runners.llm_runner import LLMRunner
from test.mock_remote_runner import run_flask, http, HOST, PORT
from llm_runners.remote_runner import RemoteRunner

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

for _ in range(20):
    try:
        http.request('GET', f"http://{HOST}:{PORT}")
        print("Test server up!")
        break
    except Exception:
        time.sleep(0.5)

class RemoteRunnerTest(unittest.TestCase):

    def test_embeddings(self):
        runner = RemoteRunner(f"http://{HOST}:{PORT}/api")
        self.assertIsNone(runner.get_embedding(embedding_config={}))

        embedding = runner.get_embedding(embedding_config={"model": "test_model"})
        self.assertEqual([[1, 2, 3], [4, 5, 6], [7, 8, 9]], embedding.embed_documents(["mock_text", "mock_text", "mock_text"]))
        self.assertEqual([1, 2, 3], embedding.embed_query("mock_text"))

    def test_simple_completion(self):
        runner = RemoteRunner(f"http://{HOST}:{PORT}/api")
        result = runner.run_text_completion_simple(
            model="test_model",
            messages=[{}],
        )
        self.assertEqual("This is simple completion text.", result)

    def test_simple_completion_error(self):
        runner = RemoteRunner(f"http://{HOST}:{PORT}/api")
        try:
            runner.run_text_completion_simple(
                model="test_model_error",
                messages=[{}],
            )
        except Exception as e:
            self.assertEqual("RemoteRunner error: Error: invalid model.", str(e))
            return
        self.assertTrue(False)

    def test_streaming_completion(self):
        runner = RemoteRunner(f"http://{HOST}:{PORT}/api")
        def mock_bool_callable():
            return False
        def mock_message_progress_callable(x):
            pass

        result, _ = runner.run_text_completion_streaming(
            model="test_model",
            messages=[{}],
            is_stopped=mock_bool_callable,
            gen_guard=None,
            update_callback=mock_message_progress_callable,
        )
        self.assertEqual("This is streaming output!", result)

    def test_streaming_completion_error(self):
        runner = RemoteRunner(f"http://{HOST}:{PORT}/api")
        def mock_bool_callable():
            return False
        def mock_message_progress_callable(x):
            pass

        result, _ = runner.run_text_completion_streaming(
            model="test_model_error",
            messages=[{}],
            is_stopped=mock_bool_callable,
            gen_guard=None,
            update_callback=mock_message_progress_callable,
        )
        err_text = "This is streaming"
        err_text += LLMRunner.message_exception(Exception("Remote runned has encountered an error: Error: test error state reached!"))
        self.assertEqual(err_text, result)

    def test_list_chat_models(self):
        runner = RemoteRunner(f"http://{HOST}:{PORT}/api")
        result = runner.list_chat_models()
        self.assertListEqual(
            ['test_model', 'test_model_thinking', 'test_model_vision'],
            result
        )

    def test_is_model_installed(self):
        runner = RemoteRunner(f"http://{HOST}:{PORT}/api")
        self.assertTrue(runner.is_model_installed("test_model"))

    def test_pull_model(self):
        runner = RemoteRunner(f"http://{HOST}:{PORT}/api")
        self.assertTrue(runner.pull_model("new_model"))

    def test_remove_model(self):
        runner = RemoteRunner(f"http://{HOST}:{PORT}/api")
        self.assertTrue(runner.remove_model("remove_model"))

    def test_supports_thinking(self):
        runner = RemoteRunner(f"http://{HOST}:{PORT}/api")
        self.assertTrue(runner.supports_thinking("test_model_thinking"))

    def test_supports_vision(self):
        runner = RemoteRunner(f"http://{HOST}:{PORT}/api")
        self.assertTrue(runner.supports_vision("test_model_vision"))


if __name__ == '__main__':
    unittest.main()