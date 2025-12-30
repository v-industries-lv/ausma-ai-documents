import datetime
import json
import os
from pathlib import Path
import shutil
from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Dict

from langchain_core.embeddings import Embeddings

from convertors.convertor_result import ConvertorResult
from convertors.document_file import DocumentFile
from logger import logger
from settings import Settings, DEFAULT_KNOWLEDGE_BASE, RAGSettings
from utils import compute_folder_hash, from_posix_path


class KnowledgeBase(ABC):
    DEFAULT_CACHE_DIR = os.path.join(".cache", "kb_check_cache")

    def __init__(self, kb_dict: dict):
        self.name: str = kb_dict["name"]
        self.full_name: str = self.name
        self.selection: List[str] = kb_dict["selection"]
        self.convertor_configs: List[dict] = kb_dict["convertors"]
        self.embedding_config: dict = kb_dict["embedding"]
        self.languages = kb_dict.get("languages", ["eng"])
        cache_dir = os.path.join(".cache", "kb_check_cache")
        self.cache_file = os.path.join(cache_dir, from_posix_path(self.name) + ".json")

    def _create_embedding(self, embedding_source: Callable[[dict], Embeddings]):
        return embedding_source(self.embedding_config)

    def is_checked(self, doc: DocumentFile):
        cache_file = self.cache_file
        if os.path.exists(cache_file):
            with open(cache_file, "r") as fh:
                cache = json.load(fh)
            doc_cache = cache.get(doc.get_document_path())
            if doc_cache is not None:
                if doc_cache.get("last_checked") is not None:
                    return True
        return False

    def update_checked(self, doc: DocumentFile):
        cache_file = self.cache_file
        os.makedirs(Path(cache_file).parent, exist_ok=True)
        cache = {}
        if os.path.exists(cache_file):
            with open(cache_file, "r") as fh:
                cache = json.load(fh)
        cache.update(
            {
                doc.get_document_path(): {
                    "last_checked": datetime.datetime.now(datetime.UTC).isoformat()
                }
            }
        )
        temp_cache_file = cache_file + ".temp"
        with open(temp_cache_file, "w") as fh:
            json.dump(cache, fh, indent=2)
        shutil.move(temp_cache_file, cache_file)

    @abstractmethod
    def rag_lookup(self, embedding_source: Callable[[dict], Embeddings], query: str, document_count: int):
        pass

    @abstractmethod
    def store_convertor_result(self, embedding_source: Callable[[dict], Embeddings], convertor_result: ConvertorResult, rag_settings: RAGSettings):
        pass

    @abstractmethod
    def has_full_document(self, embedding_source: Callable[[dict], Embeddings], doc: DocumentFile) -> bool:
        pass

    @abstractmethod
    def has_full_convertor_result(self, embedding_source: Callable[[dict], Embeddings],
                                  convertor_result: ConvertorResult) -> bool:
        pass

    @abstractmethod
    def add_doc_path(self, embedding_source: Callable[[dict], Embeddings], doc: DocumentFile,
                     force_check: bool = False):
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    def clear(self) -> bool:
        try:
            self.clear_cache()
            return True
        except Exception:
            return False

    def clear_cache(self):
        cache_file = self.cache_file
        if os.path.exists(cache_file):
            os.remove(cache_file)

    def needs_refresh(self, new_kb) -> bool:
        for existing_selection in self.selection:
            if existing_selection not in new_kb.selection:
                return True
        if new_kb.name != self.name:
            return True
        if new_kb.convertor_configs != self.convertor_configs:
            return True
        if new_kb.embedding_config != self.embedding_config:
            return True
        return False

    @staticmethod
    def validate_document_source(convertor: ConvertorResult) -> bool:
        extra_string_list = []
        if convertor.model is not None:
            extra_string_list = [convertor.model]
        folder_hash = compute_folder_hash(convertor.output_path, extra_string_list=extra_string_list)
        if not os.path.exists(convertor.output_path):
            logger.info(f"Data {convertor.output_path} does not exist.")
            return False
        if folder_hash != convertor.result_hash:
            logger.warning(f"Document folder {convertor.output_path} contents have been altered.")
            logger.warning(f"Original hash: {convertor.result_hash}, current hash: {folder_hash}")
            return False
        return True

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return (self.to_dict()) == (other.to_dict())
        return False

    def __repr__(self):
        return type(self).__name__ + "(" + str(self.to_dict()) + ")"


class AddressedKnowledgeBase(KnowledgeBase):
    def __init__(self, kb: KnowledgeBase, prefix: str):
        super().__init__(kb.to_dict())
        self.kb = kb
        self.prefix = prefix
        self.full_name = self.prefix + kb.full_name
        if kb.cache_file.startswith(KnowledgeBase.DEFAULT_CACHE_DIR):
            self.cache_file = os.path.join(KnowledgeBase.DEFAULT_CACHE_DIR, from_posix_path(self.name) + ".json")
        else:
            self.cache_file = kb.cache_file

    @staticmethod
    def create(kb: KnowledgeBase, prefix: str):
        if isinstance(kb, AddressedKnowledgeBase):
            return AddressedKnowledgeBase(kb.kb, prefix + kb.prefix)
        else:
            return AddressedKnowledgeBase(kb, prefix)

    def clear(self):
        self.kb.clear()

    def rag_lookup(self, embedding_source: Callable[[dict], Embeddings], query: str, document_count: int):
        return self.kb.rag_lookup(embedding_source, query, document_count)

    def store_convertor_result(self, embedding_source: Callable[[dict], Embeddings], convertor_result: ConvertorResult, rag_settings: RAGSettings):
        self.kb.store_convertor_result(embedding_source, convertor_result, rag_settings)

    def has_full_document(self, embedding_source: Callable[[dict], Embeddings], doc: DocumentFile) -> bool:
        return self.kb.has_full_document(embedding_source, doc)

    def has_full_convertor_result(self, embedding_source: Callable[[dict], Embeddings],
                                  convertor_result: ConvertorResult) -> bool:
        return self.kb.has_full_convertor_result(embedding_source, convertor_result)

    def add_doc_path(self, embedding_source: Callable[[dict], Embeddings], doc: DocumentFile,
                     force_check: bool = False):
        self.kb.add_doc_path(embedding_source, doc, force_check)

    def to_dict(self) -> dict:
        return {**self.kb.to_dict(), "full_name": self.full_name}


class KBStore(ABC):
    def __init__(self, store_type: str, name: str, kb_store_folder: str):
        self.type = store_type
        self.name = name
        self.kb_store_folder = from_posix_path(kb_store_folder)
        self._kbs: Dict[str, KnowledgeBase] = {}
        self.is_initialized = os.path.exists(self.kb_store_folder)

    def refresh(self):
        self._kbs = self._load()

    @abstractmethod
    def _load(self) -> Dict[str, KnowledgeBase]:
        pass

    def list(self) -> List[KnowledgeBase]:
        kb_list = [*self._kbs.values()]
        kb_list.sort(key=lambda kb: kb.name)
        return kb_list

    @abstractmethod
    def upsert(self, kb_config: dict) -> bool:
        pass

    def delete(self, name: str) -> bool:
        return self._kbs.pop(name, None) is not None

    def get(self, name: str) -> Optional[KnowledgeBase]:
        return self._kbs.get(name)

    @staticmethod
    def from_settings(settings: Settings):
        kb_stores = []
        for kb_store_config in settings.get_kbstores():
            if kb_store_config["store_type"] == "chroma":
                from kb.chroma import ChromaKBStore
                kb_store = ChromaKBStore(name=kb_store_config["name"],
                                         kb_store_folder=kb_store_config["kb_store_folder"])
                if not kb_store.is_initialized:
                    # Ensures kb_store.kb_store_folder and knowledge base config
                    kb_store.upsert(settings[DEFAULT_KNOWLEDGE_BASE])
                kb_stores.append(kb_store)
        return kb_stores


class SuperKBStore(KBStore):
    def __init__(self, kb_stores: List[KBStore]):
        # Need to initialize first due to SuperKBStore overriding list() from KBStore
        self.kb_stores: List[KBStore] = kb_stores

        super().__init__("super", "super_store", "knowledge_bases")
        self.refresh()

    def _load(self) -> Dict[str, AddressedKnowledgeBase]:
        kbs = {}
        for kb_store in self.kb_stores:
            for kb in kb_store._load().values():
                akb = AddressedKnowledgeBase.create(kb, kb_store.name + "/")
                kbs[akb.name] = akb
        return kbs

    def _get(self, name: str) -> Optional[AddressedKnowledgeBase]:
        for kb_store in self.kb_stores:
            kb = kb_store.get(name)
            if kb is not None:
                return AddressedKnowledgeBase.create(kb, kb_store.name + "/")
        return None

    def get(self, name: str) -> Optional[AddressedKnowledgeBase]:
        if "/" in name:
            return self._get_by_full_name(name)
        else:
            return self._get(name)

    def _get_by_full_name(self, full_name: str) -> Optional[AddressedKnowledgeBase]:
        arr = full_name.split("/", 1)
        if len(arr) > 1:
            kb_name, name = arr
            for kb_store in self.kb_stores:
                if kb_store.name == kb_name:
                    if isinstance(kb_store, SuperKBStore):
                        kb = kb_store._get_by_full_name(name)
                    else:
                        kb = kb_store.get(name)
                    if kb is not None:
                        return AddressedKnowledgeBase.create(kb, kb_store.name + "/")
        return None

    def _upsert_by_full_name(self, full_name, kb_config: dict) -> bool:
        arr = full_name.split("/", 1)
        if len(arr) > 1:
            kb_name, name = arr
            for kb_store in self.kb_stores:
                if kb_store.name == kb_name:
                    if isinstance(kb_store, SuperKBStore):
                        done = kb_store._upsert_by_full_name(name, kb_config)
                    else:
                        done = kb_store.upsert(kb_config)
                    if done:
                        return True
        return False

    def _upsert(self, kb_config: dict) -> bool:
        for kb_store in self.kb_stores:
            if kb_store.upsert(kb_config):
                return True
        return False

    def upsert(self, kb_config: dict) -> bool:
        try:
            if "full_name" in kb_config:
                return self._upsert_by_full_name(kb_config["full_name"], kb_config)
            else:
                return self._upsert(kb_config)
        except Exception as e:
            print(f"Failed to upsert {kb_config.get("name")}. Error: {e}")
        finally:
            self.refresh()
        return False

    def _delete(self, full_name: str) -> bool:
        arr = full_name.split("/", 1)
        if len(arr) > 1:
            kb_name, name = arr
            for kb_store in self.kb_stores:
                if kb_store.name == kb_name:
                    if isinstance(kb_store, SuperKBStore):
                        done = kb_store._delete(name)
                    else:
                        done = kb_store.delete(name)
                    if done:
                        return True
        return False

    def delete(self, full_name: str) -> bool:
        kb_store: Optional[KBStore] = None
        try:
            return self._delete(full_name)
        except Exception as e:
            print(f"Failed to delete {full_name} from {kb_store.name}. Error: {e}")
        finally:
            self.refresh()
        return False
