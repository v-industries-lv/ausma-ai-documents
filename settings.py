import copy
import json
import os.path
import shutil
from typing import List

from logger import logger
from utils import is_valid_host

# setting keys
LLM_RUNNERS = 'llm_runners'
DEFAULT_KNOWLEDGE_BASE = "default_knowledge_base"
DEFAULT_SYSTEM_PROMPT = 'default_system_prompt'
SUPPORTED_LLM_RUNNERS = ["debug", "ollama", "huggingface"]

class Settings:
    def __init__(self, defaults='defaults.conf', active='current.conf'):
        self.active = active
        self.defaults = defaults
        settings = Settings._read_settings(defaults)
        settings.update(Settings._read_settings(active))
        self.settings = settings
        # Initialize default knowledge base only if it is the first time initializing settings (no current.conf).
        # If default knowledge base is deleted after initialization it can be restored by restoring defaults.
        if not os.path.exists(self.active):
            self.initialize_default_knowledge_base()


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

        if key == DEFAULT_SYSTEM_PROMPT:
            if not isinstance(value, str):
                errors.append(
                    TypeError(f"Key {DEFAULT_SYSTEM_PROMPT} value must be a str type, got {type(value)} instead.")
                )
        if key == DEFAULT_KNOWLEDGE_BASE:
            errors.append(
                ValueError(f"Changing default knowledge base not allowed!")
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

    # specific keys
    def get_runners(self) -> List[dict]:
        # Prevent bypassing __setitem__ if working on returned value
        value = self.get(LLM_RUNNERS, []).copy()
        if type(value) == list:
            return value
        else:
            return [value]

    def initialize_default_knowledge_base(self):
        default_kb = self.settings.get(DEFAULT_KNOWLEDGE_BASE)
        if default_kb is not None:
            default_chroma_kb_folder = os.path.join("knowledge_bases", "chroma", "default")
            if os.path.exists(default_chroma_kb_folder):
                shutil.rmtree(default_chroma_kb_folder)
            os.makedirs(default_chroma_kb_folder, exist_ok=True)
            with open(os.path.join(default_chroma_kb_folder, "config.json"), "w") as fh:
                json.dump(default_kb, fh, indent=2)
        else:
            logger.error(f"Default knowledge base not defined!")

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
        self.initialize_default_knowledge_base()
        self.save()