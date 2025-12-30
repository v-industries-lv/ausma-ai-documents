import datetime
import json
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Callable, List, Tuple, Dict, Any, Optional

from chromadb import ClientAPI, PersistentClient
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import CharacterTextSplitter

from convertors.convertor_result import ConvertorResult
from convertors.document_file import DocumentFile
from kb.knowledge_base import KnowledgeBase, KBStore
from logger import logger
from settings import RAGSettings


class ChromaKnowledgeBase(KnowledgeBase):
    def __init__(self, kb_dict: dict, base_path: str, client: ClientAPI):
        super().__init__(kb_dict)
        self.client = client
        self.base_path = base_path
        self.config_path = os.path.join(base_path, "config.json")
        self.cleaned_name = os.path.split(base_path)[-1]
        self.cache_file = os.path.join(base_path, "kb_check_cache.json")

    def clear(self) -> bool:
        from chromadb.errors import NotFoundError
        super().clear()
        try:
            # fails if collection does not exist
            self.client.delete_collection(self.cleaned_name)
            return True
        except NotFoundError:
            return False

    def _make_chroma(self, embedding_source: Callable[[dict], Embeddings]) -> Chroma:
        embeddings = self._create_embedding(embedding_source)
        if embeddings is None:
            logger.error(f"Could not get embedding from model {self.embedding_config["model"]}")
        # ensure the collection exists
        self.client.get_or_create_collection(self.cleaned_name)
        return Chroma(client=self.client,
                      collection_name=self.cleaned_name,
                      embedding_function=embeddings)

    def rag_lookup(self, embedding_source: Callable[[dict], Embeddings], query: str, document_count: int) -> List[
        Tuple[Document, float]]:
        vectorstore = self._make_chroma(embedding_source)
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
            doc.metadata["document_path"] = convertor_result.document_path
            if document_metadata["type"] == "document":
                doc.metadata["file_hash"] = document_metadata["hash"]
                doc.metadata["filename"] = document_metadata["filename"]
                file_parts = Path(doc.metadata["source"]).stem.split("-")
                try:
                    page_number = int(file_parts[-1])
                except Exception:
                    logger.error(f"Could not get page number out of {doc.metadata["source"].stem}")
                    page_number = 0
                doc.metadata["page_number"] = int(page_number)
                doc.metadata["page_count"] = len(document_list)
            elif document_metadata["type"] == "email":
                doc.metadata["email_source"] = document_metadata["email"]
            elif document_metadata["type"] == "image":
                pass
            else:
                logger.warning(f"Unsupported doc type: {document_metadata["type"]}")

    @staticmethod
    def _add_chunk_metadata(chunks: List[Document]) -> List[Document]:
        for chunk_number, chunk in enumerate(chunks, 1):
            chunk.metadata["chunk_number"] = chunk_number
            chunk.metadata["chunk_count"] = len(chunks)
        return chunks

    def store_convertor_result(self, embedding_source: Callable[[dict], Embeddings], convertor_result: ConvertorResult, rag_settings: RAGSettings):
        document_metadata = convertor_result.document_metadata
        # Validating metadata vs actual folder contents
        valid_document_source = KnowledgeBase.validate_document_source(convertor_result)
        if not valid_document_source:
            return

        text_loader_kwargs = {'encoding': 'utf-8'}

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
            text_splitter = CharacterTextSplitter(
                chunk_size=rag_settings.rag_char_chunk_size,
                chunk_overlap=rag_settings.rag_char_overlap,
            )
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
                vector_database = self._make_chroma(embedding_source)
                vector_database.add_documents(to_database)

    def has_full_document(self, embedding_source: Callable[[dict], Embeddings], doc: DocumentFile,
                          force_check: bool = False) -> bool:
        if self.is_checked(doc) and not doc.has_changed and not force_check:
            return True
        vector_database = self._make_chroma(embedding_source)
        existing_data = vector_database.get(where={"document_hash": doc.file_hash})
        existing_outputs = {x["output_hash"]: {"conversion": x["conversion"], "model": x["model"]} for x in
                            existing_data["metadatas"]}
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

    def has_full_convertor_result(self, embedding_source: Callable[[dict], Embeddings],
                                  convertor_result: ConvertorResult) -> bool:
        vector_database = self._make_chroma(embedding_source)

        existing_data = vector_database.get(where={"output_hash": convertor_result.result_hash})
        existing_document_numbers = set([x["document_number"] for x in existing_data["metadatas"]])
        existing_chunk_numbers = set([x["chunk_number"] for x in existing_data["metadatas"]])
        existing_chunk_count = next(iter([x["chunk_count"] for x in existing_data["metadatas"]]), 0)
        if len(existing_data["documents"]) > 0:
            if len(existing_document_numbers) == len(convertor_result.pages) and len(
                    existing_chunk_numbers) == existing_chunk_count:
                logger.info(
                    f"[{convertor_result.conversion_type}]{convertor_result.document_path} already in vector database")
                return True
            else:
                logger.info(
                    f"[{convertor_result.conversion_type}]{convertor_result.document_path} partially in vector database. Reloading...")
        return False

    def add_doc_path(self, embedding_source: Callable[[dict], Embeddings], doc: DocumentFile,
                     force_check: bool = False):
        if self.is_checked(doc) and not doc.has_changed and not force_check:
            return
        path = doc.get_document_path()
        vector_database = self._make_chroma(embedding_source)
        existing_data: Dict[str, Any] = vector_database.get(where={"document_hash": doc.file_hash})
        # Gets values with removed duplicate strings
        existing_paths_sets = set([x["document_path"] for x in existing_data["metadatas"]])
        if len(existing_paths_sets) == 1:
            existing_paths_sets = [existing_paths_sets]
        # Joins sets and returns a list of strings. To handle empty or len()>1 lists, explicitly join them with ";" and then split resulting string into separate paths.
        existing_paths = ";".join(list(map(';'.join, existing_paths_sets))).split(";")
        if path not in existing_paths:
            for index, chroma_id in enumerate(existing_data["ids"]):
                chroma_document: Document = Document(existing_data["documents"][index])
                chroma_document.metadata = existing_data["metadatas"][index]
                chroma_document.metadata["document_path"] = chroma_document.metadata["document_path"] + ";" + path
                vector_database.update_document(chroma_id, chroma_document)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "selection": self.selection,
            "convertors": self.convertor_configs,
            "embedding": self.embedding_config,
        }


DEFAULT_CHROMA_FOLDER = os.path.join("knowledge_bases", "chroma")


class ChromaKBStore(KBStore):
    def __init__(self, name: str = "chroma_store", kb_store_folder: str = DEFAULT_CHROMA_FOLDER):
        super().__init__("chroma", name, kb_store_folder)
        db_folder = os.path.join(kb_store_folder, "db")
        os.makedirs(db_folder, exist_ok=True)
        self.client = PersistentClient(db_folder)
        self.refresh()

    def _kb_base_path(self, name: str) -> Optional[str]:
        max_length = 50
        short_name = name[:max_length]
        substituted = re.sub(r"[^a-zA-Z0-9._-]", "_", short_name)
        unique_id = str(uuid.uuid4())
        if substituted[0] in "._-":
            cleaned_name = "kb_" + substituted + "-" + unique_id
        else:
            cleaned_name = substituted + "-" + unique_id
        return os.path.join(self.kb_store_folder, cleaned_name)

    def _load(self) -> Dict[str, KnowledgeBase]:
        kbs = {}
        if not os.path.exists(self.kb_store_folder):
            return kbs
        for kb_folder in os.listdir(self.kb_store_folder):
            if kb_folder == "db":
                # skip the database directory, no knowledge base ever will have that name
                continue
            base_path = os.path.join(self.kb_store_folder, kb_folder)
            config_file_path = os.path.join(base_path, "config.json")
            if not os.path.exists(config_file_path):
                logger.error(f"KBStore {self.name} did not find {config_file_path}!")
                continue
            try:
                with open(config_file_path, "r") as fh:
                    kb_config = json.load(fh)
                    kb = ChromaKnowledgeBase(kb_config, base_path, self.client)
                    if kb is not None:
                        kbs[kb.name] = kb
            except Exception as e:
                logger.error(f"Could not create knowledge base from {config_file_path}. Error: {e}")
        return kbs

    def upsert(self, kb_config: dict) -> bool:
        try:
            name = kb_config["name"]
            # noinspection PyTypeChecker
            existing: ChromaKnowledgeBase = self.get(name)
            if existing is not None:
                kb = ChromaKnowledgeBase(kb_config, existing.base_path, self.client)
                # Delete existing if anything critical has changed
                if existing.needs_refresh(kb):
                    logger.info(f"Knowledge base config has changed! Was {existing}, got {kb}. Clearing old one...")
                    existing.clear()
            else:
                knowledge_base_path = self._kb_base_path(name)
                kb = ChromaKnowledgeBase(kb_config, knowledge_base_path, self.client)
            self._save_kb_config(kb)
        except Exception as e:
            logger.error(f"Failed to upsert knowledge base. Error: {e}")
            return False
        finally:
            self.refresh()
        return True

    @staticmethod
    def _save_kb_config(kb: ChromaKnowledgeBase) -> bool:
        try:
            config = kb.to_dict()
            config_path = kb.config_path
            base_path = kb.base_path
            temp_config_path = config_path + ".temp"
            os.makedirs(base_path, exist_ok=True)
            with open(temp_config_path, "w") as fh:
                json.dump(config, fh)
            shutil.move(temp_config_path, config_path)
            return True
        except Exception as e:
            logger.error(f"Failed to save knowledge base config. Error: {e}")
        return False

    def delete(self, name: str) -> bool:
        try:
            # noinspection PyTypeChecker
            kb: ChromaKnowledgeBase = self.get(name)
            if kb is not None:
                kb.clear()
                # remove the kb directory
                kb_path = kb.base_path
                if os.path.exists(kb_path):
                    shutil.rmtree(kb_path)
                return True
        except Exception as e:
            print(f"Failed to delete {name}. Error: {e}")
        finally:
            self.refresh()
        return False
