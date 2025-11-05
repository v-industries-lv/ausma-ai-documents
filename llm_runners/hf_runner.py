import datetime
import os
from typing import Optional, List, Callable

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from domain import MessageProgress
from llm_runners.llm_runner import LLMRunner
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from transformers import pipeline
from huggingface_hub import snapshot_download
from threading import Thread

from utils import utc_now
from logger import logger

class HFRunner(LLMRunner):
    def __init__(self, api_token):
        self.api_token = api_token
        self.model_cache = ".hf_model_cache"
        os.makedirs(self.model_cache, exist_ok=True)
        os.makedirs(os.path.join(self.model_cache, ".locks"), exist_ok=True)
        # Cleanup if needed
        self._cleanup()

    @staticmethod
    def from_dict(config: dict):
        runner = None
        try:
            if config.get('type') == 'huggingface':
                runner = HFRunner(config['api_token'])
        except Exception as e:
            logger.error(f"Could not create HuggingFace transformers runner from config. Reason: {e}")
        return runner

    def _cleanup(self):
        for delete_item in [x for x in os.listdir(self.model_cache) if x.endswith(".delete")]:
            os.remove(delete_item)
        for delete_item in [x for x in os.listdir(os.path.join(self.model_cache, ".locks")) if x.endswith(".delete")]:
            os.remove(delete_item)

    def _get_local_model_path(self, model: str) -> str:
        model_local_folder = "models--" + "--".join(model.split("/"))
        snapshot_folder = os.path.join(
            os.getcwd(),
            self.model_cache,
            model_local_folder,
            "snapshots"
        )
        for snapshot in os.listdir(snapshot_folder):
            if "config.json" in os.listdir(os.path.join(snapshot_folder, snapshot)):
                return os.path.join(snapshot_folder, snapshot)
        return model

    def list_chat_models(self):
        models = ["/".join((x.split("--"))[1:]) for x in os.listdir(self.model_cache) if not x.startswith(".")]
        return models

    def is_model_installed(self, model) -> bool:
        if not os.path.exists(self.model_cache):
            return False
        models = ["/".join((x.split("--"))[1:]) for x in os.listdir(self.model_cache) if not x.startswith(".")]
        if model in models:
            return True
        return False

    def run_text_completion_streaming(self, model: str, messages: List[dict],
                                      update_callback: Callable[[MessageProgress], None], options: dict = None):
        if options is None:
            options = {}
        _options = options.copy()
        tokenizer = AutoTokenizer.from_pretrained(self._get_local_model_path(model), device_map="auto",
                                                  local_files_only=True,

                                                  )
        llm_model = AutoModelForCausalLM.from_pretrained(self._get_local_model_path(model), device_map="auto",
                                                         local_files_only=True,
                                                         )

        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
        generation_args = {
            "streamer": streamer,
            "text_inputs": messages,
        }
        if options.get("max_new_tokens") is None:
            input_tokens = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            input_ids = tokenizer(input_tokens, return_tensors="pt").input_ids
            max_new_tokens = tokenizer.model_max_length - input_ids.shape[1]
            max_new_tokens = max(1024, max_new_tokens)  # Optional cap
            _options = {"max_new_tokens": max_new_tokens}
        generation_args.update(_options)
        generator = pipeline("text-generation", model=llm_model, tokenizer=tokenizer)
        thread = Thread(
            target=generator,
            kwargs=generation_args,
        )
        thread.start()

        assistant_text = ''
        num_chunks = 0
        last_timestamp: Optional[datetime.datetime] = None
        # TODO: better speed visualisation?
        for text_token in streamer:
            current_timestamp = utc_now()
            assistant_text += text_token
            num_chunks += 1
            if last_timestamp is not None:
                if update_callback is not None:
                    update_callback(
                        MessageProgress(1, (current_timestamp - last_timestamp).total_seconds(),
                                        num_chunks))
            last_timestamp = current_timestamp

        # Ensure the generation thread completes
        thread.join()
        return assistant_text

    def run_text_completion_simple(self, model: str, messages: List[dict], options: dict = None):
        if options is None:
            options = {}
        _options = options.copy()
        tokenizer = AutoTokenizer.from_pretrained(self._get_local_model_path(model), device_map="auto",
                                                  local_files_only=True,

                                                  )
        llm_model = AutoModelForCausalLM.from_pretrained(self._get_local_model_path(model), device_map="auto",
                                                         local_files_only=True,
                                                         )
        if options.get("max_new_tokens") is None:
            input_tokens = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            input_ids = tokenizer(input_tokens, return_tensors="pt").input_ids
            max_new_tokens = tokenizer.model_max_length - input_ids.shape[1]
            max_new_tokens = max(1024, max_new_tokens)  # Optional cap
            _options = {"max_new_tokens": max_new_tokens}
        generator = pipeline("text-generation", model=llm_model, tokenizer=tokenizer)
        result: List[dict] = generator(messages, **_options)[0]["generated_text"]
        return result[-1]["content"]

    def get_embedding(self, embedding_config) -> Optional[Embeddings]:
        model_path = self._get_local_model_path(embedding_config["model"])

        try:
            embedding = HuggingFaceEmbeddings(
                model=model_path,
            )
            return embedding
        except Exception as e:
            logger.error(e)
            return None

    def supports_thinking(self, model: str) -> Optional[bool]:
        """
        No programmatic way to tell therefore returning None as in we cannot tell. Could be done by running tests on
        freshly pulled models looking for <think> or similar tags inside responses
        """
        return None

    def pull_model(self, model):
        try:
            result = snapshot_download(repo_id=model, cache_dir=self.model_cache, token=self.api_token)
        except Exception as e:
            logger.error(e)
            return False
        if len(result) > 0:
            return True
        return False

    def remove_model(self, model) -> bool:
        hf_model_folder = "models--"+"--".join(model.split("/"))
        if os.path.exists(os.path.join(self.model_cache, hf_model_folder)):
            os.rename(
                os.path.join(self.model_cache, hf_model_folder),
                os.path.join(self.model_cache, hf_model_folder)+".delete",
            )
            os.rename(
                os.path.join(os.path.join(self.model_cache, ".locks"), hf_model_folder),
                os.path.join(os.path.join(self.model_cache, ".locks"), hf_model_folder) + ".delete",
            )
            self._cleanup()
            return True
        else:
            return False