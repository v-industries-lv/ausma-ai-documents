import copy
import json
import os.path
import shutil
from typing import List, Optional

from logger import logger
from utils import is_valid_host, from_posix_path

# setting keys
DEFAULT_KNOWLEDGE_BASE = "default_knowledge_base"
DEFAULT_SYSTEM_PROMPT = 'default_system_prompt'
DEFAULT_LLM_RUNNER = 'default_llm_runner'
DEFAULT_KBSTORE = 'default_kbstore'
DEFAULT_DOC_SOURCE = 'default_doc_source'

SUPPORTED_LLM_RUNNERS = ["debug", "ollama", "huggingface", "openai"]
SUPPORTED_KBSTORES = ["chroma"]
SUPPORTED_DOC_SOURCES = ["local_fs"]

LLM_RUNNERS = 'llm_runners'
KBSTORES = "kbstores"
DOC_SOURCES = "doc_sources"
RESTORE_DEFAULT = "restore_default"
RAG_SETTINGS = "rag_settings"
GENERATION_GUARD = "generation_guard"

class Settings:
    def __init__(self, defaults='defaults.conf', active='current.conf'):
        self.active = active
        self.defaults = defaults
        settings = Settings._read_settings(defaults)
        settings.update(Settings._read_settings(active))
        self.settings = settings

        # If active does not exist, we assume fresh install or current config being deleted
        if not os.path.exists(self.active):
            self.initialize_defaults()


    def get(self, item, default=None):
        return self.settings.get(item, default)

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        errors = Settings._validate(key, value)
        if len(errors) == 0:
            self.settings[key] = value
            self.save()
        else:
            raise(Exception(f"Errors:\n{[str(e) for e in errors]}"))

    @staticmethod
    def _validate(key, value):
        errors = []
        if key == LLM_RUNNERS:
            def check_llm_runner(config):
                if not isinstance(config, dict):
                    errors.append(
                        TypeError(f"LLM runner config must be a dict type, got {type(config)} instead."))
                else:
                    if "type" not in config.keys():
                        errors.append(
                            ValueError(f"LLM runner config key \"type\" not found"))
                    else:
                        if not isinstance(config["type"], str):
                            errors.append(
                                TypeError(
                                    f"LLM runner config key \"type\" value must be a str type, got {config["type"]} instead.")
                            )
                        if config["type"] not in SUPPORTED_LLM_RUNNERS:
                            errors.append(
                                TypeError(
                                    f"LLM runner type {config["type"]} not in supported list: {SUPPORTED_LLM_RUNNERS}")
                            )
                    if "name" not in config.keys():
                        errors.append(
                            ValueError(f"LLM runner config key \"name\" not found"))
                    else:
                        if not isinstance(config["name"], str):
                            errors.append(
                                ValueError(f"LLM runner name must by 'str' type! Got: {type(config["name"])}"))
                        else:
                            if len(config["name"]) == 0:
                                errors.append(
                                    ValueError(f"LLM runner name cannot be empty!"))
                    if "host" in config.keys():
                        if not is_valid_host(config["host"]):
                            errors.append(
                                ValueError(f"LLM runner host {config["host"]} is invalid."))


            if not isinstance(value, list):
                check_llm_runner(value)
            else:
                for llm_runner_config in value:
                    check_llm_runner(llm_runner_config)
                # Check duplicates for valid items
                if len(errors)==0:
                    if len(set([x["name"] for x in value])) != len([x["name"] for x in value]):
                        errors.append(
                            ValueError(f"LLM runner config list contains duplicates by name! Given: {value}"))

        elif key == DEFAULT_SYSTEM_PROMPT:
            if not isinstance(value, str):
                errors.append(
                    TypeError(f"Key {DEFAULT_SYSTEM_PROMPT} value must be a str type, got {type(value)} instead.")
                )
        elif key in DEFAULT_LLM_RUNNER:
            errors.append(
                ValueError(f"Changing this value not allowed!")
            )
        elif key in DEFAULT_KBSTORE:
            errors.append(
                ValueError(f"Changing this value not allowed!")
            )
        elif key in DEFAULT_KNOWLEDGE_BASE:
            errors.append(
                ValueError(f"Changing this value not allowed!")
            )
        elif key in DEFAULT_DOC_SOURCE:
            errors.append(
                ValueError(f"Changing this value not allowed!")
            )
        return errors

    def save(self):
        tmp_file = self.active + '.tmp'
        with open(tmp_file, 'w') as f:
            f.write(json.dumps(self.settings, indent=2))
        # only replace the settings when they are fully written
        shutil.move(tmp_file, self.active)

    def get_all(self):
        # just to make sure noone modifies the local structure
        return copy.deepcopy(self.settings)

    def _get_items(self, name)-> Optional[List[dict]]:
        value = self.get(name, []).copy()
        if type(value) == list:
            return value
        else:
            return [value]

    def get_llm_runners(self)-> Optional[List[dict]]:
        return self._get_items(LLM_RUNNERS)

    def get_kbstores(self)-> Optional[List[dict]]:
        return self._get_items(KBSTORES)

    def get_doc_sources(self)-> Optional[List[dict]]:
        return self._get_items(DOC_SOURCES)

    def initialize_defaults(self):
        self.initialize_default_llm_runner()
        self.initialize_default_kbstore()
        self.initialize_default_doc_source()

    def initialize_default_llm_runner(self):
        default_llm_runner = self.settings.get(DEFAULT_LLM_RUNNER)
        if default_llm_runner is not None:
            self.settings[LLM_RUNNERS] = [default_llm_runner]
        else:
            logger.error(f"Default llm runner not defined!")

    def initialize_default_kbstore(self):
        default_kbstore = self.settings.get(DEFAULT_KBSTORE)
        if default_kbstore is not None:
            os.makedirs(from_posix_path(default_kbstore["kb_store_folder"]), exist_ok=True)
            self.settings[KBSTORES] = [default_kbstore]

        else:
            logger.error(f"Default knowledge base store not defined!")

    def initialize_default_doc_source(self):
        default_doc_source = self.settings.get(DEFAULT_DOC_SOURCE)
        if default_doc_source is not None:
            self.settings[DOC_SOURCES] = [default_doc_source]

        else:
            logger.error(f"Default document source not defined!")

    @staticmethod
    def _read_settings(path):
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                if type(data) == dict:
                    return data
                else:
                    raise ValueError('Expected dictionary, got ' + str(type(data)))
        except Exception as e:
            logger.warning('ignoring settings file ' + path, exc_info=e)
            return {}

    def restore_defaults(self):
        self.settings = Settings._read_settings(self.defaults)
        self.initialize_defaults()
        self.save()

class RAGSettings:
    def __init__(self, rag_settings):
        self.rag_document_count = rag_settings["rag_document_count"]
        self.rag_char_chunk_size = rag_settings["rag_char_chunk_size"]
        self.rag_char_overlap = rag_settings["rag_char_overlap"]
        self.rag_similarity_score_threshold = rag_settings["rag_similarity_score_threshold"]
        self.rag_score_margin = rag_settings["rag_score_margin"]
        self.rag_cosine_distance_irrelevance_threshold = rag_settings["rag_cosine_distance_irrelevance_threshold"]

    @staticmethod
    def from_settings(settings: Settings):
        return RAGSettings(settings[RAG_SETTINGS])