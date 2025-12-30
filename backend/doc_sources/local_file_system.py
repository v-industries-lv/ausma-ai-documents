import datetime
import glob
import os
from typing import List, Dict, Union, Optional

from convertors.document_file import DocumentFile
from doc_sources.doc_source import DocSource
from logger import logger
from utils import from_posix_path, to_posix_path


class LocalFileSystemSource(DocSource):
    def __init__(self, name: str, root_path: str, cache_hashes: bool = True,
                 cache_dir: str = DocSource.DEFAULT_CACHE_DIR):
        super().__init__("local_fs", name, cache_hashes, cache_dir)
        self.root_path: str = root_path
        os.makedirs(from_posix_path(self.root_path), exist_ok=True)

    def _list(self, pattern: str) -> List[Dict[str, Union[str, bool]]]:
        posix_pattern = to_posix_path(pattern)
        if pattern.startswith(self.name):
            posix_pattern = posix_pattern[len(self.name):].lstrip("/")
        paths = []
        dir_to_crawl = self.root_path if posix_pattern == "" else os.path.join(self.root_path,
                                                                               from_posix_path(posix_pattern))
        dir_to_crawl = from_posix_path(dir_to_crawl)
        if not DocSource._is_glob_pattern(posix_pattern):
            if os.path.isdir(dir_to_crawl):
                # Pattern that lists the directory
                dir_to_crawl = os.path.join(dir_to_crawl, "*")
            if os.path.isfile(dir_to_crawl):
                # Listing path to a file it returns path to this file
                return [
                    {
                        "path": to_posix_path(pattern),
                        "is_file": True,
                        "is_dir": False
                    }
                ]
        for x in glob.glob(os.path.join(dir_to_crawl), recursive=True):
            paths.append(
                {
                    "path": to_posix_path(self.name + os.sep + os.path.relpath(x, self.root_path)),
                    "is_file": os.path.isfile(x),
                    "is_dir": os.path.isdir(x)
                }
            )
        paths = [x for x in paths if not x["path"].endswith('/.')]
        return paths

    # noinspection PyUnreachableCode
    def get(self, path: str) -> Optional[DocumentFile]:
        target_doc_source_name, doc_path = to_posix_path(path).split("/", maxsplit=1)
        if target_doc_source_name != self.name:
            return None
        full_doc_path = os.path.join(from_posix_path(self.root_path), from_posix_path(doc_path))
        document = None
        try:
            cached_hash = None
            has_changed = False
            last_modified: datetime.datetime = datetime.datetime.fromtimestamp(os.path.getmtime(full_doc_path))
            file_size: int = os.path.getsize(full_doc_path)
            cached_hash_info: dict = self.hash_cache.get(full_doc_path)

            if cached_hash_info is not None:
                is_modified = last_modified != datetime.datetime.fromisoformat(cached_hash_info["last_modified"])
                is_file_size_changed = cached_hash_info["file_size"] != file_size

                if not is_modified and not is_file_size_changed:
                    cached_hash = cached_hash_info["hash"]
                else:
                    has_changed = True

            document = DocumentFile.create(
                doc_source_name=self.name,
                doc_source_root=from_posix_path(self.root_path),
                file_path=str(full_doc_path),
                precalc_file_hash=cached_hash,
                last_modified=last_modified,
                file_size=file_size,
            )
            if document is not None:
                document.has_changed = has_changed
        except Exception as e:
            logger.error(f"Failed while retrieving document {doc_path} from DocSource {self.name}. Error: {e}")
        finally:
            return document

    def to_dict(self) -> dict:
        output_dict = super().to_dict()
        output_dict["root_path"] = to_posix_path(self.root_path)
        return output_dict
