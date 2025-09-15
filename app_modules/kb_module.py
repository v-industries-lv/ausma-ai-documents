import os
import shutil

from typing import Dict, Any

from flask import request, Flask
import json

from knowledge_base import KnowledgeBase
from knowledge_base_service import KnowledgeBaseService
from logger import logger

class KBModule:
    def __init__(self, kb_service: KnowledgeBaseService):
        self.kb_service = kb_service

    @staticmethod
    def parse(kb_config: dict):
        parsed_config = kb_config.copy()
        try:
            parsed_config = dict(parsed_config)
            key_types = {"name": str, "store": str, "selection": list, "convertors": list, "embedding": dict}
            for key, expected_type in key_types.items():
                parsed_config[key] = expected_type(parsed_config[key])
            selection_list = []
            for selection in parsed_config["selection"]:
                selection_list.append(str(selection))
            convertors_list = []
            for convertor in parsed_config["convertors"]:
                convertor_dict: Dict[str, Any] = {
                    "conversion": str(convertor["conversion"])
                }
                if convertor["conversion"] in ["ocr_llm", "llm"]:
                    convertor_dict["model"] = str(convertor["model"])
                    convertor_dict["seed"] = int(convertor["seed"])
                    convertor_dict["temperature"] = float(convertor["temperature"])

                convertors_list.append(convertor_dict.copy())
            parsed_config["convertors"] = convertors_list
            parsed_config["embedding"] = dict(parsed_config["embedding"])
            parsed_config["embedding"]["model"] = str(parsed_config["embedding"]["model"])
        except Exception as e:
            logger.error(f"Failed to parse kb config {kb_config}. Error: {e}")
        finally:
            return parsed_config

    @staticmethod
    def validate_kb_config(kb_config: dict):
        if not isinstance(kb_config, dict):
            logger.error(f"KB config is not a dict!")
            return False
        def _key_type_check(kb_config, check_key, check_type):
            if not check_key in kb_config.keys():
                logger.error(f"KB config missing key {check_key}")
                return False
            if not isinstance(kb_config[check_key], check_type):
                logger.error(f"KB config key {check_key} value is not {check_type}. Got: {type(kb_config[check_key])}")
                return False
            return True
        # General type check
        key_types = {"name": str, "store": str,"selection": list,"convertors": list,"embedding": dict}
        for key, expected_type in key_types.items():
            if not _key_type_check(kb_config, key, expected_type):
                return False
            if not len(kb_config[key]) > 0:
                logger.error(f"KB config key {key} value is empty.")
                return False

        # Selection check
        for selection in kb_config["selection"]:
            if not isinstance(selection, str):
                logger.error(f"KB config key \"selection\" list item is not {str}. Got: {type(selection)}")
                return False

        # Convertor specific check
        for convertor in kb_config["convertors"]:
            if not isinstance(convertor, dict):
                logger.error(f"KB config key \"convertors\" list item is not {dict}. Got: {type(convertor)}")
                return False
            if convertor.get("conversion") is None:
                logger.error(f"Convertor in \"convertors\" is missing key \"\" or it is None!")
                return False
            else:
                if convertor["conversion"] not in ["raw", "ocr", "ocr_llm", "llm"]:
                    logger.error(f"Convertor {convertor["conversion"]} is invalid!")
                    return False
                if convertor["conversion"] in ["ocr_llm", "llm"]:
                    allowed_key_types = {"conversion": str, "model": str, "seed": int, "temperature": float}
                    for key, value in convertor.items():
                        if key not in allowed_key_types.keys():
                            logger.error(f"Convertor key \"{key}\" is not allowed! Expected: {allowed_key_types.keys()}")
                            return False
                        if not isinstance(convertor[key], allowed_key_types[key]):
                            logger.error(f"Convertor key \"{key}\" value cannot be {type(convertor[key])}! Expected: {allowed_key_types[key]}")
                            return False

        return True

    def apply_routes(self, app: Flask):
        # KB service
        @app.route('/kb_service/control/start')
        def kb_service_start():
            self.kb_service.start()
            return {"command": "start"}

        @app.route('/kb_service/control/stop')
        def kb_service_stop():
            self.kb_service.stop()
            return {"command": "stop"}

        @app.route('/kb_service/status')
        def kb_service_status():
            return self.kb_service.service_status()

        # Knowledge bases
        @app.route('/kb/')
        def kb_list():
            # TODO: use service or list knowledge_bases folder?
            # TODO: add reference to specific KBStore?
            return [x.to_dict() for x in self.kb_service.kb_store.list()]

        @app.route('/kb/put', methods=['POST'])
        def kb_put():
            raw_kb_config = request.get_json()
            kb_config = KBModule.parse(raw_kb_config)
            if not KBModule.validate_kb_config(kb_config):
                return app.response_class(
                    response=json.dumps({"status": "error", "text": "Failed to add knowledge base!"}, indent=2),
                    mimetype='application/json'
                )
            self.kb_service.kb_store.upsert(KnowledgeBase.from_dict(kb_config))
            return app.response_class(
                response=json.dumps({"status": "success", "text": "Knowledge base added!"}, indent=2),
                mimetype='application/json'
            )

        @app.route('/kb/<name>/delete')
        def kb_delete(name):
            kb = self.kb_service.kb_store.get(name)
            if kb is not None:
                if self.kb_service.kb_store.delete(kb):
                    return app.response_class(
                        response=json.dumps({"status": "success", "text": "Knowledge base deleted!"}, indent=2),
                        mimetype='application/json'
                    )
                else:
                    return app.response_class(
                        response=json.dumps({"status": "error", "text": f"Failed to delete knowledge base {name}!"}, indent=2),
                        mimetype='application/json'
                    )
            return app.response_class(
                response=json.dumps({"status": "error", "text": "Knowledge base not found!"}, indent=2),
                mimetype='application/json'
            )

        @app.route('/kb/<name>/config')
        def kb_config(name):
            kb = self.kb_service.kb_store.get(name)
            if kb is None:
                return app.response_class(
                    response=json.dumps({"status": "error", "text": "Knowledge base not found!"}, indent=2),
                    mimetype='application/json'
                )
            return app.response_class(
                response=json.dumps(kb.to_dict(), indent=2),
                mimetype='application/json'
            )

        @app.route('/kb/<name>/status')
        def kb_status(name):
            status = self.kb_service.kb_status(name)
            if status is None:
                return app.response_class(
                    response=json.dumps({"status": "error", "text": "Knowledge base not found!"}, indent=2),
                    mimetype='application/json'
                )
            return app.response_class(
                response=json.dumps(status, indent=2),
                mimetype='application/json'
            )

        # Documents
        @app.route('/doc/<path>')
        def doc_path(path):
            return sorted(self.kb_service.doc_source.list(path))

        @app.route('/doc_sources')
        def doc_sources():
            return self.kb_service.doc_source.to_dict()
