import json
import os.path
import threading
import time
import unittest

from flask import Flask

from app_modules.settings_module import SettingsModule
from settings import Settings

import urllib3
http = urllib3.PoolManager()

HOST = "127.0.0.1"
PORT = 5100
if os.path.exists('settings/mock_current.conf'):
    os.remove('settings/mock_current.conf')

def mock_handle_settings_updated(string: str) -> None:
    return

def run_flask():
    app = Flask(__name__, template_folder="flask-resources/templates", static_folder='static')

    app.config['SECRET_KEY'] = ''
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assistant_rooms.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    SettingsModule(Settings(defaults='settings/mock_default.conf', active='settings/mock_current.conf')).apply_routes(
        app, mock_handle_settings_updated)
    app.run(debug=True, use_reloader=False, host=HOST, port=PORT)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()
for _ in range(20):
    try:
        http.request('GET', f"http://{HOST}:{PORT}")
    except Exception:
        time.sleep(0.5)

class SettingsModuleAPITest(unittest.TestCase):
    def setUp(self):
        if os.path.exists('settings/mock_current.conf'):
            os.remove('settings/mock_current.conf')
        http.request("GET", f"http://{HOST}:{PORT}/api/config/restore_default_settings")

    def test_list_config(self):
        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/config").data.decode('utf-8')
        )
        with open("settings/mock_initialized_default.conf", "r") as f:
            default_config = json.load(f)
        self.assertEqual(default_config, response)

    def test_get_specific_config(self):
        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/config/default_llm_runner").data.decode('utf-8')
        )
        with open("settings/mock_initialized_default.conf", "r") as f:
            default_config = json.load(f)
        self.assertEqual(response, default_config["default_llm_runner"])

    def test_set_specific_config(self):
        llm_runner = {
            'host': 'http://localhost:11434',
            'name': 'default_ollama_runner',
            'type': 'ollama'
        }
        http.request("POST", f"http://{HOST}:{PORT}/api/config/default_llm_runner", json=llm_runner)
        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/config/default_llm_runner").data.decode('utf-8')
        )

        self.assertEqual(response, llm_runner)

    def test_restore_defaults(self):
        new_llm_runner = [{"type": "ollama", "host": "localhost:1234", "name": "test_runner_name"}]
        http.request("POST", f"http://{HOST}:{PORT}/api/config/llm_runners", json=new_llm_runner)
        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/config").data.decode('utf-8')
        )
        self.assertEqual(new_llm_runner, response["llm_runners"])

        http.request("GET", f"http://{HOST}:{PORT}/api/config/restore_default_settings")

        response = json.loads(
            http.request('GET', f"http://{HOST}:{PORT}/api/config").data.decode('utf-8')
        )
        with open("settings/mock_initialized_default.conf", "r") as f:
            default_config = json.load(f)
        self.assertEqual(default_config, response)



