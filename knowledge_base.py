import json
import os
import glob
import shutil

from logger import logger
from typing import List, Optional, Tuple, Callable
from abc import ABC, abstractmethod
from convertors.convertor_result import ConvertorResult
from convertors.document_file import DocumentFile
import datetime

from utils import compute_folder_hash
from pathlib import Path
from langchain.text_splitter import CharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents.base import Document
from langchain_core.embeddings import Embeddings


class DocSource(ABC):
    def __init__(self, source_type: str, name: str):
        self.type: str = source_type
        self.name: str = name
    @abstractmethod
    def list(self, pattern: str) -> List[str]:
        pass

    @abstractmethod
    def get(self, path: str) -> Optional[DocumentFile]:
        pass

    def to_dict(self):
        return {
            "type": self.type,
            "name": self.name
        }


def to_posix_path(path):
    if os.sep != "/":
        return path.replace(os.sep, "/")
    return path

def from_posix_path(path):
    if os.sep != "/":
        return path.replace("/", os.sep)
    return path

class LocalFileSystemSource(DocSource):
    def __init__(self, name: str, root_path: str):
        super().__init__("local_fs", name)
        self.root_path: str = root_path

    def list(self, pattern: str) -> List[str]:
        return [to_posix_path(self.name + '/' + os.path.relpath(x, self.root_path)) for x in glob.glob(os.path.join(self.root_path, pattern),
                                                                                     recursive=True) if os.path.isfile(x)]
    def get(self, path: str) -> DocumentFile:
        _, split_path = path.split("/", maxsplit=1)
        new_path = os.path.join(self.root_path, from_posix_path(split_path))
        return DocumentFile.from_path(self.name, self.root_path, new_path)

    def to_dict(self) -> dict:
        output_dict = super().to_dict()
        output_dict["root_path"] = self.root_path
        return output_dict

class SuperDocSource(DocSource):
    def __init__(self, name: Optional[str]="", doc_sources: Optional[List[DocSource]] = None):
        super().__init__("super_type", "" if name is None else name)
        self.doc_sources = [] if doc_sources is None else doc_sources

    def list(self, pattern: str) -> List[str]:
        paths = []
        for doc_source in self.doc_sources:
            paths+= [self.name + os.sep + x if len(self.name) > 0 else x for x in doc_source.list(pattern)]
        return paths

    def get(self, path: str) -> Optional[DocumentFile]:
        doc_path = path.split("/", maxsplit=1)[1] if len(self.name) > 0 else path
        for doc_source in self.doc_sources:
            return doc_source.get(doc_path)
        return None

    def to_dict(self) -> List[dict]:
        return [x.to_dict() for x in self.doc_sources]


class KnowledgeBase(ABC):
    def __init__(self, store: str, kb_dict: dict):
        self.store: str = store
        self.name: str = kb_dict["name"]
        self.selection: List[str] = kb_dict["selection"]
        self.convertor_configs: List[dict] = kb_dict["convertors"]
        self.embedding_config: dict = kb_dict["embedding"]
        self.kb_store_folder = kb_dict.get("kb_store_folder", os.path.join("knowledge_bases", "chroma"))

    def _create_embedding(self, embedding_source: Callable[[dict], Embeddings]):
        return embedding_source(self.embedding_config)

    @abstractmethod
    def rag_lookup(self, embedding_source: Callable[[dict], Embeddings], query: str, document_count: int):
        pass

    @abstractmethod
    def store_convertor_result(self, embedding_source: Callable[[dict], Embeddings], convertor_result: ConvertorResult):
        pass

    @abstractmethod
    def has_full_document(self, embedding_source: Callable[[dict], Embeddings], doc: DocumentFile) -> bool:
        pass

    @abstractmethod
    def has_full_convertor_result(self, embedding_source: Callable[[dict], Embeddings], convertor_result: ConvertorResult) -> bool:
        pass

    @abstractmethod
    def add_doc_path(self, embedding_source: Callable[[dict], Embeddings], doc: DocumentFile, path: str):
        pass

    @staticmethod
    def from_dict(kb_dict: dict):
        try:
            if kb_dict["store"] == "chroma":
                return ChromaKnowledgeBase(kb_dict)
        except Exception as e:
            logger.error(f"Failed to create knowledge base from dict {kb_dict} . Error: {e}")
            return None
        return None

    @abstractmethod
    def to_dict(self) -> dict:
        pass

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


# TODO: ChromaDB as ChromaKnowledgeBase specific field. Lazy loading? Needs locks
class ChromaKnowledgeBase(KnowledgeBase):
    def __init__(self, kb_dict: dict):
        super().__init__("chroma", kb_dict)
        self.db_folder = os.path.join(self.kb_store_folder, self.name)

    def rag_lookup(self, embedding_source: Callable[[dict], Embeddings], query: str, document_count: int) -> List[Tuple[Document, float]]:
        embeddings = self._create_embedding(embedding_source)
        if embeddings is None:
            logger.error(f"Could not get embedding from model {self.embedding_config["model"]}")
            return []
        vectorstore = Chroma(persist_directory=self.db_folder,
                             embedding_function=embeddings)
        relevant_documents = vectorstore.similarity_search_with_score(
            query=query, k=document_count,
        )
        return relevant_documents

    @staticmethod
    def _add_metadata(document_list: List[Document], document_metadata: dict, convertor_result: ConvertorResult):
        for document_number, doc in enumerate(document_list, 1):
            doc.metadata["type"] = document_metadata["type"]
            doc.metadata["inserted"] = datetime.datetime.now(datetime.UTC).isoformat()
            doc.metadata["conversion"] = convertor_result.conversion_type
            doc.metadata["model"] = "" if convertor_result.model is None else convertor_result.model
            doc.metadata["document_hash"] = document_metadata["hash"]
            doc.metadata["output_hash"] = convertor_result.result_hash
            doc.metadata["document_number"] = document_number
            doc.metadata["document_count"] = len(document_list)
            if document_metadata["type"] == "document":
                doc.metadata["file_hash"] = document_metadata["hash"]
                doc.metadata["file_location"] = document_metadata["file_location"]
                doc.metadata["filename"] = document_metadata["filename"]
                doc.metadata["page_number"] = int(Path(doc.metadata["source"]).stem)
                doc.metadata["page_count"] = len(document_list)
            elif document_metadata["type"] == "email":
                doc.metadata["email_source"] = document_metadata["email"]
            else:
                logger.warning(f"Unsupported doc type: {document_metadata["type"]}")

    @staticmethod
    def _add_chunk_metadata(chunks: List[Document]) -> List[Document]:
        for chunk_number, chunk in enumerate(chunks, 1):
            chunk.metadata["chunk_number"] = chunk_number
            chunk.metadata["chunk_count"] = len(chunks)
        return chunks

    def store_convertor_result(self, embedding_source: Callable[[dict], Embeddings], convertor_result: ConvertorResult):
        document_metadata = convertor_result.document_metadata
        # Validating metadata vs actual folder contents
        valid_document_source = KnowledgeBase.validate_document_source(convertor_result)
        if not valid_document_source:
            return

        text_loader_kwargs = {'encoding': 'utf-8'}
        os.makedirs(self.db_folder, exist_ok=True)

        logger.info(f"Processing {convertor_result.output_path}...")
        logger.info(f"Checking data...")
        data_exists = self.has_full_convertor_result(embedding_source, convertor_result)
        if data_exists:
            return

        logger.info(f"[{convertor_result.conversion_type}]Preparing data from {convertor_result.output_folder_name}...")
        loader = DirectoryLoader(
            str(convertor_result.output_path),
            loader_cls=TextLoader, loader_kwargs=text_loader_kwargs, sample_seed=self.embedding_config.get("seed", 42)
        )
        folder_docs = loader.load()
        ChromaKnowledgeBase._add_metadata(folder_docs, document_metadata, convertor_result)

        if len(folder_docs) > 0:
            logger.info(f"[{convertor_result.conversion_type}]Preparing {len(folder_docs)} documents...")
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(folder_docs)
            ChromaKnowledgeBase._add_chunk_metadata(chunks)
            to_database = []
            empty_strings = []
            for chunk in chunks:
                if len(chunk.page_content) == 0:
                    empty_strings.append(chunk)
                else:
                    to_database.append(chunk)
            if len(empty_strings) > 0:
                logger.info(f"[{convertor_result.conversion_type}]Empty chunks: {empty_strings}")
            if len(to_database) > 0:
                vectorstore = Chroma.from_documents(documents=to_database,
                                                    embedding=embedding_source(self.embedding_config),
                                                    persist_directory=self.db_folder)
                logger.info(
                    f"[{convertor_result.conversion_type}]Vectorstore created with {vectorstore._collection.count()} documents")

    def has_full_document(self, embedding_source: Callable[[dict], Embeddings], doc: DocumentFile) -> bool:
        vector_database = Chroma(persist_directory=self.db_folder, embedding_function=self._create_embedding(embedding_source))
        existing_data = vector_database.get(where={"document_hash": doc.calculate_hash()})
        existing_outputs = {x["output_hash"]: {"conversion": x["conversion"], "model": x["model"]} for x in existing_data["metadatas"]}
        for output_hash, conversion_dict in existing_outputs.items():
            existing_selection = [x for x in existing_data["metadatas"] if
                                  x["output_hash"] == output_hash
                                  and x["conversion"] == conversion_dict["conversion"]
                                  and x["model"] == conversion_dict["model"]
                                  ]
            existing_document_numbers = set([x["document_number"] for x in existing_selection])
            existing_document_count = next(iter([x["document_count"] for x in existing_selection]), 0)
            existing_chunk_numbers = set([x["chunk_number"] for x in existing_selection])
            existing_chunk_count = next(iter([x["chunk_count"] for x in existing_selection]), 0)
            if len(existing_selection) > 0:
                if (len(existing_document_numbers) == existing_document_count and
                        len(existing_chunk_numbers) == existing_chunk_count):
                    return True
        return False


    def has_full_convertor_result(self, embedding_source: Callable[[dict], Embeddings], convertor_result: ConvertorResult) -> bool:
        vector_database = Chroma(persist_directory=self.db_folder, embedding_function=self._create_embedding(embedding_source))
        document_metadata = convertor_result.document_metadata

        existing_data = vector_database.get(where={"output_hash": convertor_result.result_hash})
        existing_document_numbers = set([x["document_number"] for x in existing_data["metadatas"]])
        existing_chunk_numbers = set([x["chunk_number"] for x in existing_data["metadatas"]])
        existing_chunk_count = next(iter([x["chunk_count"] for x in existing_data["metadatas"]]), 0)
        if len(existing_data["documents"]) > 0:
            if len(existing_document_numbers) == len(convertor_result.pages) and len(
                    existing_chunk_numbers) == existing_chunk_count:
                logger.info(
                    f"[{convertor_result.conversion_type}]{document_metadata["file_location"]} already in vector database")
                return True
            else:
                logger.info(
                    f"[{convertor_result.conversion_type}]{document_metadata["file_location"]} partially in vector database. Reloading...")
        return False

    def add_doc_path(self, embedding_source: Callable[[dict], Embeddings], doc: DocumentFile, path: str):
        vector_database = Chroma(persist_directory=self.db_folder, embedding_function=self._create_embedding(embedding_source))
        existing_data = vector_database.get(where={"document_hash": doc.calculate_hash()})
        existing_paths = set([x["file_location"] for x in existing_data["metadatas"]])
        if path not in existing_paths:
            for index, chroma_id in enumerate(existing_data["ids"]):
                chroma_document: Document = Document(existing_data["documents"][index])
                chroma_document.metadata = existing_data["metadatas"][index]

                if path not in chroma_document.metadata["file_location"].split(";") and chroma_document.metadata["type"] == "document":
                    chroma_document.metadata["file_location"] = chroma_document.metadata["file_location"]+ ";"+path
                vector_database.update_document(chroma_id, chroma_document)

    def to_dict(self) -> dict:
        return {
            "store": self.store,
            "name": self.name,
            "selection": self.selection,
            "convertors": self.convertor_configs,
            "embedding": self.embedding_config,
        }

class KBStore(ABC):
    def __init__(self, store_type: str, name: str, kb_store_folder: str):
        self.type = store_type
        self.name = name
        self.kb_store_folder = kb_store_folder
        self.kb_list = self.list()

    def list(self) -> List[KnowledgeBase]:
        kb_list = []
        if not os.path.exists(self.kb_store_folder):
            return kb_list
        for kb_folder in os.listdir(self.kb_store_folder):
            config_file_path = os.path.join(self.kb_store_folder, kb_folder, "config.json")
            if not os.path.exists(config_file_path):
                logger.error(f"KBStore {self.name} did not find {config_file_path}!")
                continue
            try:
                with open(config_file_path, "r") as fh:
                    kb_config = json.load(fh)
                    kb_config["kb_store_folder"] = self.kb_store_folder
                    kb = KnowledgeBase.from_dict(kb_config)
                    if kb is not None:
                        kb_list.append(kb)
            except Exception as e:
                logger.error(f"Could not create knowledge base from {config_file_path}. Error: {e}")
        return kb_list

    def upsert(self, kb: KnowledgeBase) -> bool:
        try:
            # Delete existing if anything critical has changed
            knowledge_base_path = os.path.join("knowledge_bases", kb.store, kb.name)
            config_path = os.path.join(knowledge_base_path, "config.json")
            if os.path.exists(config_path):
                try:
                    kb_config = kb.to_dict()
                    with open(config_path, "r") as fh:
                        existing_config = json.load(fh)
                        do_remove = False
                        for existing_selection in existing_config["selection"]:
                            if existing_selection not in kb_config["selection"]:
                                do_remove = True
                                break
                        critical_keys = ["store", "name", "convertors", "embedding"]
                        for critical_key in critical_keys:
                            if kb_config[critical_key] != existing_config[critical_key]:
                                do_remove = True
                                break
                        if do_remove:
                            logger.info(
                                f"Knowledge base config has changed! Was {existing_config}, got {kb_config}. Clearing old one...")
                            shutil.rmtree(knowledge_base_path)
                except Exception as e:
                    logger.error(f"Failed to load existing config! Error: {e}")
                    logger.info(f"Clearing old knowledge base...")
                    shutil.rmtree(knowledge_base_path)

            remove_kb = None
            for kb_existing in self.kb_list:
                if kb_existing.name == kb.name and kb_existing.store == kb.store:
                    remove_kb = kb_existing
            if remove_kb is not None:
                self.kb_list.remove(remove_kb)
            self._save_kb_config(kb)
        except Exception as e:
            logger.error(f"Failed to upsert knowledge base. Error: {e}")
            return False
        finally:
            self.kb_list = self.list()
        return True

    @abstractmethod
    def delete(self, kb: KnowledgeBase) -> bool:
        pass

    @abstractmethod
    def get(self, name: str) -> KnowledgeBase:
        pass

    @abstractmethod
    def _save_kb_config(self, kb: KnowledgeBase) -> bool:
        pass


class ChromaKBStore(KBStore):
    def __init__(self, name: str = "chroma_store", kb_store_folder: str = "knowledge_bases/chroma"):
        super().__init__("chroma", name, kb_store_folder)

    def get(self, name: str) -> Optional[KnowledgeBase]:
        for kb in self.kb_list:
            if kb is None:
                continue
            if kb.name == name and kb.store == "chroma":
                return kb
        return None

    def delete(self, kb: KnowledgeBase) -> bool:
        kb_path = os.path.join(self.kb_store_folder, kb.name)
        try:
            if os.path.exists(kb_path):
                shutil.rmtree(kb_path)
                return True
        except Exception as e:
            print(f"Failed to delete {kb.name}. Error: {e}")
        finally:
            self.kb_list = self.list()
        return False

    def _save_kb_config(self, kb: ChromaKnowledgeBase) -> bool:
        if isinstance(kb, ChromaKnowledgeBase):
            try:
                config = kb.to_dict()
                os.makedirs(kb.db_folder, exist_ok=True)
                config_path = os.path.join(kb.db_folder, "config.json")
                temp_config_path = os.path.join(kb.db_folder, "config.json.temp")
                with open(temp_config_path, "w") as fh:
                    json.dump(config, fh)
                shutil.move(temp_config_path, config_path)
                return True
            except Exception as e:
                logger.error(f"Failed to save knowledge base config. Error: {e}")
        return False


class SuperKBStore(KBStore):
    def __init__(self, kb_stores: List[KBStore]):
        # Need to initialize first due to SuperKBStore overriding list() from KBStore
        self.kb_stores: List[KBStore] = kb_stores

        super().__init__("super", "super_store", "knowledge_bases")

    def list(self) -> List[KnowledgeBase]:
        kb_list = []
        for kb_store in self.kb_stores:
            kb_list += kb_store.list()
        return kb_list

    def get(self, name: str) -> Optional[KnowledgeBase]:
        for kb_store in self.kb_stores:
            kb = kb_store.get(name)
            if kb is not None:
                return kb
        return None

    def upsert(self, kb: KnowledgeBase) -> bool:
        try:
            for kb_store in self.kb_stores:
                if kb_store.upsert(kb):
                    return True
        except Exception as e:
            print(f"Failed to upsert {kb.name}. Error: {e}")
        finally:
            self.kb_list = self.list()
        return False

    def delete(self, kb: KnowledgeBase) -> bool:
        kb_store: Optional[KBStore] = None
        try:
            for kb_store in self.kb_stores:
                if kb_store.delete(kb):
                    return True
        except Exception as e:
            print(f"Failed to delete {kb.name} from {kb_store.name}. Error: {e}")
        finally:
            self.kb_list = self.list()
        return False

    def _save_kb_config(self, kb: KnowledgeBase) -> bool:
        for kb_store in self.kb_stores:
            if kb_store._save_kb_config(kb):
                return True
        return False

