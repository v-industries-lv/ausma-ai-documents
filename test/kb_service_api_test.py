import json
import threading
import time
import unittest
from config import app
from app_modules import kb_module
from mock_classes import MockKBService, MockKBStore, MockDocSource, MockLLMRunner, MockKnowledgeBase

import urllib3
http = urllib3.PoolManager()

HOST = "http://127.0.0.1:5000"

def run_flask():
    mock_store = MockKBStore()
    mock_store.kb_list = [
        MockKnowledgeBase("", "mock1", [], [], {}, ),
        MockKnowledgeBase("", "mock2", [], [], {}, ),
        MockKnowledgeBase("", "mock3", [], [], {}, ),
    ]
    mock_kb_service = MockKBService(
        mock_store,
        MockDocSource("test_type", "test_name"), MockLLMRunner())
    kb_module.KBModule(mock_kb_service).apply_routes(app)
    app.run(debug=True, use_reloader=False, host="127.0.0.1", port=5000)
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()
for _ in range(20):
    try:
        http.request('GET', HOST)
    except Exception:
        time.sleep(0.5)

class KBServiceAPITest(unittest.TestCase):
    def test_control_api(self):
        response = json.loads(
            http.request('GET', f"{HOST}/kb_service/control/start").data.decode('utf-8')
        )
        self.assertEqual(response, {'command': 'start'})
        response = json.loads(
            http.request('GET', f"{HOST}/kb_service/control/stop").data.decode('utf-8')
        )
        self.assertEqual({'command': 'stop'}, response)

    def test_service_status(self):
        response = json.loads(
            http.request('GET', f"{HOST}/kb_service/status").data.decode('utf-8')
        )
        self.assertEqual({'status': 'test'}, response)

    def test_kb_list(self):
        response = json.loads(
            http.request('GET', f"{HOST}/kb").data.decode('utf-8')
        )
        self.assertEqual([{'name': 'mock1'}, {'name': 'mock2'}, {'name': 'mock3'}], response)

    def test_kb_config(self):
        response = json.loads(
            http.request('GET', f"{HOST}/kb/mock1/config").data.decode('utf-8')
        )
        self.assertEqual({'name': 'mock1'}, response)

    def test_kb_status(self):
        response = json.loads(
            http.request('GET', f"{HOST}/kb/mock1/status").data.decode('utf-8')
        )
        self.assertEqual({'not_processed_documents': [], 'processed_documents': []}, response)

    def test_kb_put(self):
        kb_config = {
              "name": "new_kb",
              "store": "chroma",
              "selection": ["**/*"],
              "convertors": [
                {
                  "conversion": "raw"
                }
              ],
              "embedding":
                {
                  "model": "bge-m3:latest"
                }
          }
        http.request("POST", f"{HOST}/kb/put", json=kb_config)
        print(http.request('GET', f"{HOST}/kb/new_kb/config").data.decode('utf-8'))
        response = json.loads(
            http.request('GET', f"{HOST}/kb/new_kb/config").data.decode('utf-8')
        )
        print(response)
        self.assertEqual(response, kb_config)

    def test_kb_delete(self):
        kb_config = {
            "name": "new_kb",
            "store": "chroma",
            "selection": ["**/*"],
            "convertors": [
                {
                    "conversion": "raw"
                }
            ],
            "embedding":
                {
                    "model": "bge-m3:latest"
                }
        }
        http.request("POST", f"{HOST}/kb/put", json=kb_config)
        response = json.loads(
            http.request('GET', f"{HOST}/kb/new_kb/config").data.decode('utf-8')
        )
        self.assertEqual(response, kb_config)
        response = json.loads(http.request('GET', f"{HOST}/kb/new_kb/delete").data.decode('utf-8'))
        self.assertEqual({"status": "success", "text": "Knowledge base deleted!"}, response)

    def test_doc_path(self):
        response = json.loads(
            http.request('GET', f"{HOST}/doc/**").data.decode('utf-8')
        )
        expected = [
            'ducks.pdf',
            'file.unsupported',
            'frogs.md',
            'geese.pdf',
            'same_ducks.pdf',
            'storks.pdf',
            'water_birds.pdf'
        ]
        self.assertEqual(expected, response)

    def test_doc_sources(self):
        response = json.loads(
            http.request('GET', f"{HOST}/doc_sources").data.decode('utf-8')
        )
        self.assertEqual({'name': 'test_name', 'type': 'test_type'}, response)

if __name__ == '__main__':
    unittest.main()