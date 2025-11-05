import json
import os
import glob
import shutil

from langchain_core.embeddings import Embeddings
from typing import Optional, Any, List, Tuple, Callable, Dict, Union

from typing_extensions import Self
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore, VST
from convertors.convertor_result import ConvertorResult
from convertors.document_file import DocumentFile
from domain import MessageProgress
from knowledge_base_service import KnowledgeBaseService
from knowledge_base import KBStore, KnowledgeBase, DocSource, to_posix_path
from llm_runners.llm_runner import LLMRunner

class MockKnowledgeBase(KnowledgeBase):
    def __init__(self, store: str, name: str, selection: List[str], convertor_configs: List[dict],
                 embedding_config: dict):
        super().__init__(store, {"name": name, "selection": selection, "convertors": convertor_configs, "embedding": embedding_config})
    def rag_lookup(self, embedding_source: Callable[[dict], Embeddings], query: str, document_count: int):
        pass
    def store_convertor_result(self, embedding_source: Callable[[dict], Embeddings], convertor_result: ConvertorResult):
        pass
    def has_full_document(self, embedding_source: Callable[[dict], Embeddings], doc: DocumentFile) -> bool:
        pass
    def has_full_convertor_result(self, embedding_source: Callable[[dict], Embeddings],
                                  convertor_result: ConvertorResult) -> bool:
        pass
    def add_doc_path(self, embedding_source: Callable[[dict], Embeddings], doc: DocumentFile, path: str):
        pass
    def to_dict(self) -> dict:
        return {"name": self.name}
    def save_kb_config(self):
        pass


class MockLLMRunner(LLMRunner):
    @staticmethod
    def from_dict(config: dict):
        return MockLLMRunner()

    def pull_model(self, model) -> bool:
        return True

    def remove_model(self, model) -> bool:
        return True

    def list_chat_models(self):
        pass
    def is_model_installed(self, model) -> bool:
        return True

    def run_text_completion_streaming(self, model: str, messages: List[dict],
                                      update_callback: Callable[[MessageProgress], None], options: dict = None):
        pass
    def run_text_completion_simple(self, model: str, messages: List[dict], options: dict = None):
        pass
    def get_embedding(self, embedding_config) -> Optional[Embeddings]:
        pass
    def supports_thinking(self, model: str) -> Optional[bool]:
        pass

class MockKBStore(KBStore):

    def __init__(self):
        self.kb_list = []
        super().__init__("mock", "mock_store", "knowledge_base/mock")


    def delete(self, kb: KnowledgeBase) -> bool:
        self.kb_list.remove(kb)
        return True

    def _save_kb_config(self, kb: KnowledgeBase) -> bool:
        config = kb.to_dict()
        kb_path: str = str(os.path.join(self.kb_store_folder, kb.name))
        os.makedirs(kb_path, exist_ok=True)
        config_path = os.path.join(kb_path, "config.json")
        temp_config_path = os.path.join(kb_path, "config.json.temp")
        with open(temp_config_path, "w") as fh:
            json.dump(config, fh)
        shutil.move(temp_config_path, config_path)
        return True

    def get(self, name: str) -> Optional[KnowledgeBase]:
        for kb in self.kb_list:
            if kb is not None:
                if kb.name == name:
                    return kb
        return None

    def list(self):
        return self.kb_list

    def upsert(self, kb: KnowledgeBase):
        self.kb_list.append(kb)


class MockDocSource(DocSource):
    def __init__(self, source_type: str, name: str):
        super().__init__(source_type, name)
        self.root_path = 'documents'
    def _list(self, pattern: str) -> List[Dict[str, Union[str, bool]]]:
        _pattern = to_posix_path(pattern)
        if pattern.startswith(self.name):
            _pattern = _pattern[len(self.name):].lstrip(os.sep)
        paths = []
        dir_to_crawl = self.root_path if _pattern == "" else os.path.join(self.root_path, _pattern)
        if not DocSource._is_glob_pattern(_pattern):
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
    def get(self, path: str) -> Optional[DocumentFile]:
        pass


class MockKBService(KnowledgeBaseService):
    def __init__(self, kb_store: KBStore, doc_source: DocSource, llm_runner: LLMRunner):
        super().__init__(kb_store, doc_source, llm_runner)

    def start(self):
        pass
    def stop(self):
        pass

    def service_status(self):
        return {"status": "test"}

class MockCollection:
    def __init__(self, docs):
        self.docs = docs

    def count(self):
        return len(self.docs)

class MockEmbedding(Embeddings):
    def __init__(self, model: str, temperature: str, seed: int):
        self.model = model
        self.temperature = temperature
        self.seed = seed

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        pass

    def embed_query(self, text: str) -> list[float]:
        pass

class MockChroma(VectorStore):
    _collection = MockCollection([])
    force_do = False
    def __init__(self, persist_directory, embedding_function):
        self.persist_directory = persist_directory
        self.embedding_function = embedding_function

    def get(self, **kwargs):
        if kwargs.get("where") is not None:
            if MockChroma.force_do:
                return {"metadatas": [], "documents": [], "ids": []}
            if kwargs["where"].get("document_hash") is not None or kwargs["where"].get("output_hash"):
                document_hash = "f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97"
                output_hash = "bad877b2f1bfd0d8e37ba5a2d3e6107320946d713b0ca19326bf690995d61145"
                if kwargs["where"].get("document_hash") == document_hash or kwargs["where"].get("output_hash") == output_hash:
                    result = {"metadatas": [], "documents": [], "ids": []}
                    output_file_path = "mock_data/existing_document/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97"
                    with open(os.path.join(output_file_path, "metadata.json"), "r") as fh:
                        metadata = json.load(fh)
                    for convertor in metadata["conversions"]:
                        convertor_output_path = os.path.join(output_file_path, convertor["output_folder"])
                        if not os.path.exists(os.path.join(convertor_output_path)):
                            continue
                        files = os.listdir(convertor_output_path)
                        for file_number, file in enumerate(files, 1):
                            with open(os.path.join(convertor_output_path, file), "r") as fh:
                                page_content = "\n".join(fh.readlines())
                            document = page_content
                            doc_metadata = {
                                "source": file,
                                "type": metadata["type"],
                                "document_hash": kwargs["where"].get("document_hash"),
                                "output_hash": convertor["hash"],
                                "conversion": convertor["conversion"],
                                "file_location": metadata["file_location"],
                                "model": "" if convertor["model"] is None else convertor["model"],
                                "document_number": file_number,
                                "document_count": len(files),
                                "chunk_number": 1,
                                "chunk_count": 1,
                            }
                            result["documents"].append(document)
                            result["metadatas"].append(doc_metadata)
                            result["ids"].append(file_number)
                    return result
        return {"metadatas": [], "documents": [], "ids": []}

    def update_document(self, chroma_id: int, chroma_document: Document):
        os.makedirs("temp", exist_ok=True)
        with open("temp/updated_document.json", "w") as fh:
            json.dump(self._document_to_dict(chroma_id, chroma_document), fh)


    def similarity_search_with_score(self, query, k) -> List[Tuple[Document, float]]:
        return [(Document(f"doc_{x}"), 1/x) for x in range(1, k + 1)]

    def similarity_search(self, query: str, k: int = 4, **kwargs: Any) -> list[Document]:
        pass

    @classmethod
    def from_documents(
        cls,
        documents: list[Document],
        embedding: Embeddings,
        **kwargs: Any,
    ) -> Self:
        cls._collection = MockCollection(documents)
        os.makedirs("temp", exist_ok=True)
        with open("temp/mock_chroma_db.json", "w") as fh:
            json.dump([MockChroma._document_to_dict(doc_id, doc) for doc_id, doc in enumerate(documents, 1)], fh)
        return cls

    @classmethod
    def from_texts(cls: type[VST], texts: list[str], embedding: Embeddings, metadatas: Optional[list[dict]] = None, *,
                   ids: Optional[list[str]] = None, **kwargs: Any) -> VST:
        pass

    @staticmethod
    def _document_to_dict(doc_id: int, doc: Document):
        output = {
            "metadata": doc.metadata,
            "page_content": doc.page_content,
            "id": doc_id
        }
        return output

def mock_embeddings_source(embedding_config):
    return MockEmbedding(**embedding_config)