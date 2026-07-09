import json
from typing import List, Dict

import urllib3
from flask import Flask, request, Response, stream_with_context

http = urllib3.PoolManager()

HOST = "127.0.0.1"
PORT = 5102


def run_flask():
    app = Flask(__name__, template_folder="flask-resources/templates", static_folder='static')

    app.config['SECRET_KEY'] = ''
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assistant_rooms.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    MODELS = [
        {
            "model": "test_model",
            "capabilities": [
                "completion",
            ],
        },
        {
            "model": "test_model_thinking",
            "capabilities": [
                "completion",
                "thinking"
            ],
        },
        {
            "model": "test_model_vision",
            "capabilities": [
                "completion",
                "vision"
            ],
        },
    ]

    @app.route("/")
    def status():
        return app.response_class(
            response="Mock remote runner is working.",
            status = 200,
        )

    @app.route("/api/models/list", methods=["GET"])
    def list_models():
        return app.response_class(
            response=json.dumps(
                [
                    "test_model",
                    "test_model_thinking",
                    "test_model_vision",
                ],
                indent=2
            ),
            status=200,
            mimetype='application/json'
        )

    @app.route("/api/models/show", methods=["POST"])
    def model_details():
        data = request.get_json()
        show_model = data.get("model")
        if show_model is None:
            return app.response_class(
                response=json.dumps(None),
                status=400,
                mimetype='application/json'
            )

        for model_info in MODELS:
            if show_model == model_info["model"]:
                return app.response_class(
                    response=json.dumps(
                        model_info,
                        indent=2
                    ),
                    status=200,
                    mimetype='application/json'
                )
        return app.response_class(
            response=json.dumps(None),
            status=400,
            mimetype='application/json'
        )

    @app.route("/api/models/pull", methods=["POST"])
    def pull_model():
        data = request.get_json()
        if data["model"] == "new_model":
            return app.response_class(
                    response=json.dumps(True),
                    status=200,
                    mimetype='application/json'
                )
        else:
            return app.response_class(
                response=json.dumps(False),
                status=400,
                mimetype='application/json'
            )

    @app.route("/api/models/remove", methods=["POST"])
    def remove_model():
        data = request.get_json()
        if data["model"] == "remove_model":
            return app.response_class(
                response=json.dumps(True),
                status=200,
                mimetype='application/json'
            )
        else:
            return app.response_class(
                response=json.dumps(False),
                status=400,
                mimetype='application/json'
            )

    @app.route("/api/embed", methods=["POST"])
    def embed_documents():
        data = request.get_json()
        mock_output = []
        for index, input in enumerate(data["inputs"]):
            mock_output.append([1+(index*3),2+(index*3),3+(index*3)])

        model = data.get("model", None)
        if model is None:
            return app.response_class(
                response=json.dumps(
                    {
                        "error": "Missing embedding model!"
                    },
                    indent=2
                ),
                status=400,
                mimetype='application/json'
            )

        return app.response_class(
            response=json.dumps(
                {
                    "embeddings": mock_output
                },
                indent=2
            ),
            status=200,
            mimetype='application/json'
        )

    @app.route("/api/generate", methods=["POST"])
    def generate():
        data = request.get_json()
        model: str = data.get("model")
        messages: List[Dict] = data.get("messages")
        if data.get("stream"):
            def event_stream():
                try:
                    for index, token in enumerate(["This", " is", " streaming", " output", "!"]):
                        if index==3 and model == "test_model_error":
                            raise ValueError("Error: test error state reached!")
                        yield json.dumps({"status": "generating", "content": token})+"\n"
                    yield json.dumps({"status": "done"})+"\n"
                except GeneratorExit:
                    print("Client disconnected")
                    raise
                except Exception as e:
                    print(e)
                    yield json.dumps({"status": "error", "content": f"{e}"})+"\n"

            return Response(stream_with_context(event_stream()), status=200, mimetype="text/event-stream")
        if model == "test_model_error":
            return app.response_class(
                response=json.dumps(
                    {
                        "status": "error",
                        "content": "Error: invalid model.",
                    },
                    indent=2
                ),
                status=400,
                mimetype='application/json'
            )
        return app.response_class(
            response=json.dumps(
                {
                    "status": "done",
                    "content": "This is simple completion text.",
                },
                indent=2
            ),
            status=200,
            mimetype='application/json'
        )



    app.run(debug=True, use_reloader=False, host=HOST, port=PORT)

if __name__ == "__main__":
    run_flask()