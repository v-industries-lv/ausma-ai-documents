import json
import os
import shutil
from abc import ABC, abstractmethod
from typing import List, Dict, Union, Optional

from convertors.document_file import DocumentFile
from settings import Settings
from utils import to_posix_path


class DocSource(ABC):
    DEFAULT_CACHE_DIR = os.path.join(".cache", "doc_hash_cache")
    FORBIDDEN_NAME_SYMBOLS = [
        "/",
        "\\",
        "*",
        "?",
        "[",
        "]",
    ]

    def __init__(self, source_type: str, name: str, cache_hashes: bool = True, cache_dir: str = DEFAULT_CACHE_DIR):
        self.type: str = source_type
        for x in DocSource.FORBIDDEN_NAME_SYMBOLS:
            if x in name:
                raise (ValueError(
                    f"DocSource name cannot contain {DocSource.FORBIDDEN_NAME_SYMBOLS} characters! Given name: {name}"))
        self.name: str = name
        self.hash_cache: dict = {}
        self.hash_cache_path = None
        if cache_hashes:
            os.makedirs(cache_dir, exist_ok=True)
            self.hash_cache_path = os.path.join(cache_dir, name + ".json")
            if os.path.exists(self.hash_cache_path):
                with open(self.hash_cache_path, "r") as fh:
                    self.hash_cache = json.load(fh)

    def update_cache(self, doc: DocumentFile):
        self.hash_cache.update(
            {
                doc.get_document_path(): {
                    "hash": doc.file_hash,
                    "last_modified": doc.last_modified.isoformat(),
                    "file_size": doc.file_size
                }
            }
        )
        self._save_cache()

    def _save_cache(self):
        temp_cache = self.hash_cache_path + ".temp"
        with open(temp_cache, "w") as fh:
            json.dump(self.hash_cache, fh, indent=2)
        shutil.move(temp_cache, self.hash_cache_path)

    def clear_cache(self):
        self.hash_cache.clear()
        self._save_cache()

    @abstractmethod
    def _list(self, pattern: str) -> List[Dict[str, Union[str, bool]]]:
        pass

    def list_items(self, pattern: str) -> List[Dict[str, Union[str, bool]]]:
        # Filtering files and folder. Symlink and other behaviour not implemented.
        return [x for x in self._list(pattern) if x["is_file"] == True or x["is_dir"] == True]

    def list_files(self, pattern: str) -> List[str]:
        return [x["path"] for x in self._list(pattern) if x["is_file"] == True]

    @abstractmethod
    def get(self, path: str) -> Optional[DocumentFile]:
        pass

    def to_dict(self):
        return {
            "type": self.type,
            "name": self.name
        }

    @staticmethod
    def _is_glob_pattern(path_str):
        return any(char in path_str for char in ['*', '?', '['])

    @staticmethod
    def from_settings(settings: Settings):
        doc_sources = []
        for doc_source_config in settings.get_doc_sources():
            if doc_source_config["doc_source_type"] == "local_fs":
                from doc_sources.local_file_system import LocalFileSystemSource
                doc_sources.append(
                    LocalFileSystemSource(name=doc_source_config["name"], root_path=doc_source_config["root_path"])
                )
        return doc_sources


class SuperDocSource(DocSource):
    def __init__(self, name: Optional[str] = "", doc_sources: Optional[List[DocSource]] = None,
                 cache_hashes: bool = True, cache_dir: str = DocSource.DEFAULT_CACHE_DIR):
        super().__init__("super_type", "" if name is None else name, cache_hashes, cache_dir)
        self.doc_sources = [] if doc_sources is None else [x for x in doc_sources if x.name is not None or x.name != ""]

    def _list(self, pattern: str) -> List[Dict[str, Union[str, bool]]]:
        if pattern == "*":
            return [{"path": x.name, "is_file": False, "is_dir": True} for x in self.doc_sources]
        paths = []
        if len(to_posix_path(pattern).split("/")) == 1 and not DocSource._is_glob_pattern(pattern):
            for doc_source in self.doc_sources:
                if doc_source.name == pattern:
                    return doc_source._list("*")
            return []

        for doc_source in self.doc_sources:
            first_level = to_posix_path(pattern).split("/")[0]
            if first_level != doc_source.name and first_level != "**":
                continue
            paths += [
                {
                    "path": self.name + "/" + to_posix_path(x["path"]) if len(self.name) > 0 else to_posix_path(
                        x["path"]),
                    "is_file": x["is_file"],
                    "is_dir": x["is_dir"]
                } for x in doc_source._list(pattern)
            ]
        paths = [x for x in paths if not x["path"].endswith('/.')]
        return paths

    def get(self, path: str) -> Optional[DocumentFile]:
        # FIXME: returning first doc path with get() is wrong. Tries to create DocumentFile, but crashes when path is wrong.
        _, doc_path = to_posix_path(path).split("/", maxsplit=1) if len(self.name) > 0 else (None, path)
        document = None
        for doc_source in self.doc_sources:
            document = doc_source.get(doc_path)
            if document is not None:
                return document
        return document

    def to_dict(self) -> List[dict]:
        return [x.to_dict() for x in self.doc_sources]

    def update_cache(self, doc: DocumentFile):
        for doc_source in self.doc_sources:
            if doc_source.name == doc.doc_source_name:
                doc_source.update_cache(doc)
