import json
import threading
import time
import unittest

import urllib3
from flask import Flask

from app_modules import kb_module
from test.mock_classes import MockKBService, MockKBStore, MockDocSource, MockLLMRunner

http = urllib3.PoolManager()

HOST = "127.0.0.1"
PORT = 5101


def run_flask():
    app = Flask(__name__, template_folder="flask-resources/templates", static_folder='static')

    app.config['SECRET_KEY'] = ''
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assistant_rooms.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    mock_store = MockKBStore()
    kbs = [
        mock_kb_config('mock1'),
        mock_kb_config('mock2'),
        mock_kb_config('mock3'),
    ]
    for kb in kbs:
        mock_store.upsert(kb)

    mock_kb_service = MockKBService(
        mock_store,
        MockDocSource("test_type", "test_name"), MockLLMRunner())
    kb_module.KBModule(mock_kb_service).apply_routes(app)
    app.run(debug=True, use_reloader=False, host=HOST, port=PORT)


def mock_kb_config(name):
    return {'convertors': [], 'embedding': {}, 'name': name, 'selection': []}


flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()
for _ in range(20):
    try:
        http.request('GET', f"http://{HOST}:{PORT}")
    except Exception:
        time.sleep(0.5)


class KBServiceAPITest(unittest.TestCase):
    def test_control_api(self):
        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/kb_service/control/start").data.decode('utf-8')
        )
        self.assertEqual(response, {'command': 'start'})
        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/kb_service/control/stop").data.decode('utf-8')
        )
        self.assertEqual({'command': 'stop'}, response)

    def test_service_status(self):
        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/kb_service/status").data.decode('utf-8')
        )
        self.assertEqual({'status': 'test'}, response)

    def test_kb_list(self):
        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/kb").data.decode('utf-8')
        )
        self.assertEqual([mock_kb_config('mock1'), mock_kb_config('mock2'), mock_kb_config('mock3')], response)

    def test_kb_config(self):
        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/kb/mock1/config").data.decode('utf-8')
        )
        self.assertEqual(mock_kb_config('mock1'), response)

    def test_kb_status(self):
        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/kb/mock1/status").data.decode('utf-8')
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
        http.request("POST", f"http://{HOST}:{PORT}/api/kb/put", json=kb_config)
        print(http.request('GET', f"http://{HOST}:{PORT}/api/kb/new_kb/config").data.decode('utf-8'))
        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/kb/new_kb/config").data.decode('utf-8')
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
        http.request("POST", f"http://{HOST}:{PORT}/api/kb/put", json=kb_config)
        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/kb/new_kb/config").data.decode('utf-8')
        )
        self.assertEqual(response, kb_config)
        response = json.loads(http.request('GET', f"http://{HOST}:{PORT}/api/kb/new_kb/delete").data.decode('utf-8'))
        self.assertEqual({"status": "success", "text": "Knowledge base deleted!"}, response)

    def test_doc_path(self):
        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/doc/**").data.decode('utf-8')
        )
        expected = [
            {'is_dir': False, 'is_file': True, 'path': 'test_name/ducks.pdf'},
            {'is_dir': False, 'is_file': True, 'path': 'test_name/file.unsupported'},
            {'is_dir': False, 'is_file': True, 'path': 'test_name/frogs.md'},
            {'is_dir': False, 'is_file': True, 'path': 'test_name/geese.pdf'},
            {'is_dir': False, 'is_file': True, 'path': 'test_name/same_ducks.pdf'},
            {'is_dir': False, 'is_file': True, 'path': 'test_name/storks.pdf'},
            {'is_dir': False, 'is_file': True, 'path': 'test_name/water_birds.pdf'}
        ]
        self.assertEqual(expected, response)

    def test_doc_sources(self):
        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/doc_sources").data.decode('utf-8')
        )
        self.assertEqual({'name': 'test_name', 'type': 'test_type'}, response)

    def test_kb_tesseract_languages(self):
        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/kb/tesseract_languages").data.decode('utf-8')
        )
        self.assertIn("eng", response)


if __name__ == '__main__':
    unittest.main()
