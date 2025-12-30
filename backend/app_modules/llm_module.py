from flask import request, Flask
import json
from llm_runners.llm_runner import LLMRunner
from logger import logger

class LLMModule:
    def __init__(self, llm_runners: LLMRunner):
        self.llm_runners = llm_runners

    def apply_routes(self, app: Flask):
        @app.route('/api/llm_runners/models', methods=['GET'])
        def list_models():
            try:
                return app.response_class(
                    response=json.dumps({"chat_models": self.llm_runners.list_chat_models()}, indent=2),
                    mimetype='application/json'
                )
            except Exception as e:
                logger.error(f"Failed to list models from llm runers. Error: {e}")
                return app.response_class(
                    response=json.dumps({"status": "failed", "text": f"{e}"}, indent=2),
                    mimetype='application/json'
                )

        @app.route('/api/llm_runners/models/pull', methods=['POST'])
        def pull_llm():
            data = request.get_json()
            try:
                if self.llm_runners.pull_model(data["model"]):
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
                if self.llm_runners.remove_model(data["model"]):
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