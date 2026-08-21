from flask import request, Flask
import json
from llm_runners.llm_runner import SuperRunner
from logger import logger

class LLMModule:
    def __init__(self, super_llm_runner: SuperRunner):
        self.super_llm_runner = super_llm_runner

    def apply_routes(self, app: Flask):
        @app.route('/api/llm_runners', methods=['GET'])
        def list_runners():
            try:
                return app.response_class(
                    response=json.dumps([x.runner_type for x in self.super_llm_runner.runners], indent=2),
                    mimetype='application/json'
                )
            except Exception as e:
                logger.error(f"Failed to list llm runers. Error: {e}")
                return app.response_class(
                    response=json.dumps({"status": "failed", "text": f"{e}"}, indent=2),
                    mimetype='application/json'
                )

        @app.route('/api/llm_runners/models', methods=['GET'])
        def list_models():
            try:
                return app.response_class(
                    response=json.dumps({"chat_models": self.super_llm_runner.list_chat_models()}, indent=2),
                    mimetype='application/json'
                )
            except Exception as e:
                logger.error(f"Failed to list models from llm runers. Error: {e}")
                return app.response_class(
                    response=json.dumps({"status": "failed", "text": f"{e}"}, indent=2),
                    mimetype='application/json'
                )

        @app.route('/api/llm_runners/models_with_capabilities', methods=['GET'])
        def list_models_full():
            try:
                return app.response_class(
                    response=json.dumps(self.super_llm_runner.get_models_with_capabilities(), indent=2),
                    mimetype='application/json'
                )
            except Exception as e:
                logger.error(f"Failed to list models from llm runers. Error: {e}")
                return app.response_class(
                    response=json.dumps({"status": "failed", "text": f"{e}"}, indent=2),
                    mimetype='application/json'
                )

        @app.route('/api/llm_runners/models/refresh', methods=['GET'])
        def refresh_llms():
            try:
                logger.info("Refreshing models...")
                self.super_llm_runner.refresh_model_cache()
                return app.response_class(
                    response=json.dumps({"status": "success"}, indent=2),
                    mimetype='application/json'
                )
            except Exception as e:
                logger.error(f"Failed to refresh models. Error: {e}")
                return app.response_class(
                    response=json.dumps({"status": "failed", "text": f"{e}"}, indent=2),
                    mimetype='application/json'
                )

        @app.route('/api/llm_runners/models/pull', methods=['POST'])
        def pull_llm():
            data = request.get_json()
            try:
                if self.super_llm_runner.pull_model(data["model"]):
                    logger.info(f"Pulled model {data["model"]}")
                    return app.response_class(
                        response=json.dumps({"status": f"Model {data["model"]} pulled successfully!"}, indent=2),
                        mimetype='application/json'
                    )
            except Exception as e:
                logger.error(f"Exception thrown while pulling a model. Error: {e}")
            return app.response_class(
                response=json.dumps({"status": f"Failed to pull model {data["model"]}!"}, indent=2),
                mimetype='application/json'
            )

        @app.route('/api/llm_runners/models/remove', methods=['POST'])
        def remove_model():
            data = request.get_json()
            try:
                if self.super_llm_runner.remove_model(data["model"]):
                    logger.info(f"Pulled model {data["model"]}")
                    return app.response_class(
                        response=json.dumps({"status": f"Model {data["model"]} pulled successfully!"}, indent=2),
                        mimetype='application/json'
                    )
            except Exception as e:
                logger.error(f"Exception thrown while pulling a model. Error: {e}")
            return app.response_class(
                response=json.dumps({"status": f"Failed to pull model {data["model"]}!"}, indent=2),
                mimetype='application/json'
            )