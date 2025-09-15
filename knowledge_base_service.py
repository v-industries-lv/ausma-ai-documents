from knowledge_base import KBStore, DocSource
from llm_runners.llm_runner import LLMRunner
from logger import logger
from convertors.convertor import Convertor
from convertors.document_image_convertor import DocumentImageConvertor
from convertors.convertor_result import ConvertorResult
import threading
from convertors.document_file import DocumentFile
from utils import utc_now
from typing import Optional, List, Dict, Any

class KnowledgeBaseService:
    def __init__(self, kb_store: KBStore, doc_source: DocSource, llm_runner: LLMRunner):
        self.kb_store: KBStore = kb_store
        self.doc_source: DocSource = doc_source
        self.llm_runner: LLMRunner = llm_runner
        self.active: bool = False
        self.lock = threading.Lock()
        self.status: dict = {"status": "done"}

    def start(self):
        with self.lock:
            if not self.active:
                self.active = True
                t = threading.Thread(target=self._run)
                t.start()

    def stop(self):
        with self.lock:
            self.active = False

    def service_status(self):
        return self.status

    def kb_status(self, name):
        kb = self.kb_store.get(name)
        documents = []
        for pattern in kb.selection:
            documents += self.doc_source.list(pattern)
        documents = list(set(documents))
        documents = sorted(documents)
        processed_documents = []
        not_processed_documents = []
        for document_path in documents:
            if kb.has_full_document(self.llm_runner.get_embedding, self.doc_source.get(document_path)):
                processed_documents.append(document_path)
            else:
                not_processed_documents.append(document_path)
        return {
            "processed_documents": processed_documents,
            "not_processed_documents": not_processed_documents,
        }

    def _status_update(self, **kwargs):
        self.status = kwargs

    def _run(self):
        def checkpoint():
            if not self.active:
                raise(InterruptedError())
        self._status_update(status="started")
        logger.info(f"Run started at: {utc_now()}")
        error_block: Dict[str, Any] = {"error": False}
        try:
            kb_list = self.kb_store.list()
            for kb_num, kb in enumerate(kb_list, 1):
                checkpoint()
                self._status_update(status="processing", kb_num=kb_num, kb_store=kb.store, kb_name=kb.name, kb_total=len(kb_list))
                documents: list = []
                for pattern in kb.selection:
                    checkpoint()
                    documents += self.doc_source.list(pattern)
                documents = list(set(documents))
                documents = sorted(documents)
                convertors: List[Convertor] = [Convertor.from_config(x, self.llm_runner) for x in kb.convertor_configs]
                convertors = [x for x in convertors if x is not None]
                for doc_num, document_path in enumerate(documents, 1):
                    checkpoint()
                    self._status_update(status="processing", kb_num=kb_num, kb_store=kb.store, kb_name=kb.name, kb_total=len(kb_list),
                                        doc_num=doc_num, doc_path=document_path, doc_total=len(documents))
                    # TODO: binary in DocumentFile
                    document: DocumentFile = self.doc_source.get(document_path)
                    if document is None:
                        logger.warning(f"Could not get document {document_path}")
                        error_block["error"] = True
                        continue
                    if kb.has_full_document(self.llm_runner.get_embedding, document):
                        kb.add_doc_path(self.llm_runner.get_embedding, document, document_path)
                        continue
                    convertor_result = None
                    for convertor in convertors:
                        checkpoint()
                        if isinstance(convertor, DocumentImageConvertor) and not document.needs_images:
                            continue
                        self._status_update(status="processing", kb_num=kb_num, kb_store=kb.store, kb_name=kb.name, kb_total=len(kb_list),
                                            doc_num=doc_num, doc_path=document_path, doc_total=len(documents),
                                            convertor=convertor.conversion_type)
                        # TODO: needs document_path
                        convertor_result: Optional[ConvertorResult] = convertor.convert(document)
                        if convertor_result is not None:
                            kb.store_convertor_result(self.llm_runner.get_embedding, convertor_result)
                            break
                    if convertor_result is None:
                        logger.error(f"Could not convert document {document.file_path}")
                        error_block["error"] = True
        except InterruptedError as e:
            logger.error(e)
            error_block["status"] = "cancelled"
        except Exception:
            error_block["error"] = True
        finally:
            with self.lock:
                self.active = False
            logger.info(f"Run complete at: {utc_now()}")
            final_status: Dict[str, Any] = {"status": "done"}
            final_status.update(error_block)
            self._status_update(**final_status)