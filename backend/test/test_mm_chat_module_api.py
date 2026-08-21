import json
import os.path
import shutil
import threading
import time
import unittest
from io import BytesIO
from PIL import Image
from flask import Flask

from app_modules.multimodal_chat_module import MMChatModule

import urllib3
http = urllib3.PoolManager()

HOST = "127.0.0.1"
PORT = 5103
if os.path.exists('instance/'):
    shutil.rmtree('instance/')

def mock_handle_settings_updated(string: str) -> None:
    return

def run_flask():
    app = Flask(__name__, template_folder="flask-resources/templates", static_folder='static')

    app.config['SECRET_KEY'] = ''
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assistant_rooms.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    MMChatModule().apply_routes(app)
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
        if os.path.exists('instance/'):
            shutil.rmtree('instance/')

    @staticmethod
    def get_mock_image_binary(random_pixel=0):
        pattern = [
            [0, 255, 0],
            [255, random_pixel, 255],
            [0, 255, 0],
        ]

        image = Image.new("L", (3, 3))
        image.putdata([pixel for row in pattern for pixel in row])
        buf = BytesIO()
        image.save(buf, format="JPEG")

        return buf.getvalue()


    def test_upload_chat_files(self):
        fields = [
            ("files", ("photo1.jpg", SettingsModuleAPITest.get_mock_image_binary(random_pixel=0), "image/jpeg")),
            ("files", ("photo2.jpg", SettingsModuleAPITest.get_mock_image_binary(random_pixel=127), "image/jpeg")),
            ("files", ("photo3.jpg", SettingsModuleAPITest.get_mock_image_binary(random_pixel=255), "image/jpeg")),
        ]
        print(fields)
        response = json.loads(
            http.request(
                'POST',
                f"http://{HOST}:{PORT}/api/upload_chat_files",
                fields=fields, encode_multipart=True

            ).data.decode('utf-8')
        )

        self.assertIn("files", response)
        self.assertEqual(3, len(response["files"]))

        self.assertEqual(669, len(http.request(
            'GET',
            f"http://{HOST}:{PORT}/instance/blobs/multimodal_input/{response["files"][0]["new_filename"]}",
        ).data))