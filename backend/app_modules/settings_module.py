import json
from typing import Callable

from flask import request, Flask

from settings import Settings
from settings import RESTORE_DEFAULT


class SettingsModule:
    def __init__(self, settings: Settings):
        self.settings = settings

    def apply_routes(self, app: Flask, update_callback: Callable[[str], None]):
        @app.route('/api/config/')
        @app.route('/api/config')
        def all_config():
            return app.response_class(
                response=json.dumps(self.settings.get_all(), indent=2),
                mimetype='application/json'
            )

        @app.route('/api/config/<name>', methods=['GET'])
        def get_config(name):
            return app.response_class(
                response=json.dumps(self.settings[name], indent=2),
                mimetype='application/json'
            )

        @app.route('/api/config/<name>', methods=['POST'])
        def set_config(name):
            try:
                self.settings[name] = request.get_json()
                update_callback(name)
                return app.response_class(
                    response=json.dumps(self.settings[name], indent=2),
                    mimetype='application/json'
                )
            except Exception as e:
                return app.response_class(
                    response=json.dumps({"text": f"Failed to set {name}! Error: {e}"}),
                    mimetype='application/json'
                )

        @app.route('/api/config/restore_default_settings', methods=['GET'])
        def restore_default_settings():
            try:
                self.settings.restore_defaults()
                update_callback(RESTORE_DEFAULT)
                return app.response_class(
                    response=json.dumps({"text": "Settings restored to defaults!"}),
                    mimetype='application/json'
                )
            except Exception as e:
                return app.response_class(
                    response=json.dumps({"text": f"Failed to restore default settings. Reason: {e}"}),
                    mimetype='application/json'
                )


