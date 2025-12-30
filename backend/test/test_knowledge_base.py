import json
import shutil
import unittest

from chromadb import PersistentClient
from langchain_core.documents import Document
import os
import sys

from convertors.convertor_result import ConvertorResult
from convertors.document_file import DocumentFile
from kb.knowledge_base import KnowledgeBase
from kb.chroma import ChromaKnowledgeBase
from llm_runners.ollama_runner import OllamaRunner
from settings import RAGSettings
from test.mock_classes import MockChroma, mock_embeddings_source


class KnowledgeBaseTest(unittest.TestCase):
    chroma = None
    real_chroma = None
    LLM_RUNNER = OllamaRunner.from_dict({"type": "ollama"})

    @classmethod
    def setUpClass(cls):
        module = sys.modules['kb.chroma']
        cls.real_chroma = module.Chroma
        cls.chroma = module.Chroma = MockChroma

    @classmethod
    def tearDownClass(cls):
        module = sys.modules['kb.chroma']
        module.Chroma = cls.real_chroma

    def setUp(self):
        self.chroma_client = PersistentClient("chroma")
        self.cleanup()

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        if os.path.basename(os.path.normpath(os.getcwd())) == "test":
            temp_path = "temp"
            if os.path.exists(temp_path):
                shutil.rmtree(temp_path)
            if os.path.exists("kb_check_cache"):
                shutil.rmtree("kb_check_cache")
        MockChroma.force_do = False
        collections = self.chroma_client.list_collections()
        for collection in collections:
            self.chroma_client.delete_collection(collection.name)

    def test_create_embedding(self):
        kb, _ = self._makeChroma()
        embedding = kb._create_embedding(mock_embeddings_source)
        self.assertEqual(embedding.model, "bge-m3:latest")
        self.assertEqual(embedding.temperature, 0.7)
        self.assertEqual(embedding.seed, 42)

    def test_knowledgebase_validate_document_source_exists(self):
        convertor_result = ConvertorResult(
            pages=[],
            document_metadata={},
            conversion_type="raw",
            model=None,
            output_folder_name='',
            output_path="mock_data/existing_document/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97/raw",
            result_hash="bad877b2f1bfd0d8e37ba5a2d3e6107320946d713b0ca19326bf690995d61145",
            document_path="mock_data/existing_document/ducks.pdf",
        )

        self.assertTrue(KnowledgeBase.validate_document_source(convertor_result))

    def test_knowledgebase_validate_document_source_with_model_exists(self):
        convertor_result = ConvertorResult(
            pages=[],
            document_metadata={},
            conversion_type="ocr_llm",
            model="qwen2.5",
            output_folder_name='',
            output_path="mock_data/existing_document/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97/ocr_llm_qwen2.5",
            result_hash="11daa02a0e65c9f05ccccc85f41a297e0d7b3aa3ca9844c960f240520db78858",
            document_path="mock_data/existing_document/ducks.pdf",
        )

        self.assertTrue(KnowledgeBase.validate_document_source(convertor_result))

    def test_knowledgebase_validate_document_source_altered(self):
        convertor_result = ConvertorResult(
            pages=[],
            document_metadata={},
            conversion_type="raw",
            model=None,
            output_folder_name='',
            output_path="mock_data/existing_document/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97/raw",
            result_hash="hashofaltereddocumentfolder",
            document_path="mock_data/existing_document/ducks.pdf",
        )

        self.assertFalse(KnowledgeBase.validate_document_source(convertor_result))

    # Chroma kb tests
    def test_chroma_to_dict(self):
        kb, kb_dict = self._makeChroma()
        self.assertEqual(kb_dict, kb.to_dict())

    def test_chroma_rag_lookup(self):
        kb, _ = self._makeChroma()
        relevant_documents = kb.rag_lookup(mock_embeddings_source, "lookup some rag", 5)
        self.assertEqual(len(relevant_documents), 5)

    def test_chroma_rag_lookup_name_with_spaces(self):
        kb, _ = self._makeChroma("name_with_spaces")
        relevant_documents = kb.rag_lookup(mock_embeddings_source, "lookup some rag", 5)
        self.assertEqual(len(relevant_documents), 5)

    def test_chroma_add_metadata_document(self):
        document_list = [Document(f"doc_{x}") for x in range(1, 5 + 1)]
        for page_number, document in enumerate(document_list, 1):
            document.metadata["source"] = f"document/path/{page_number}.pdf"
        kb, _ = self._makeChroma()
        document_metadata = {
            "type": "document",
            "hash": "somedocumenthash",
            "file_location": "path/to/file/directory",
            "filename": "filename.pdf"
        }
        convertor_result = ConvertorResult(
            pages=[],
            document_metadata={},
            conversion_type="raw",
            model=None,
            output_folder_name='',
            output_path="convertor/result/path/raw",
            result_hash="someconvertorhash",
            document_path="convertor/result/path/raw",
        )

        kb._add_metadata(document_list, document_metadata, convertor_result)
        for document in document_list:
            self.assertTrue(document.metadata["type"] == "document")
            self.assertTrue(document.metadata["conversion"] == "raw")

    def test_chroma_add_chunk_metadata(self):
        chunk_list = [Document(f"doc_{x}") for x in range(1, 5 + 1)]
        kb, _ = self._makeChroma()
        kb._add_chunk_metadata(chunk_list)
        for chunk in chunk_list:
            self.assertTrue(chunk.metadata["chunk_number"] <= len(chunk_list))
            self.assertTrue(chunk.metadata["chunk_number"] > 0)
            self.assertEqual(chunk.metadata["chunk_count"], len(chunk_list))

    def _makeChroma(self, kb_name = "test"):
        config_path = f"knowledge_bases/chroma/{kb_name}/config.json"
        with open(config_path, "r") as fh:
            kb_dict = json.load(fh)
        kb = ChromaKnowledgeBase(kb_dict, config_path, self.chroma_client)
        return kb, kb_dict

    def test_chroma_store_convertor_result(self):
        MockChroma.force_do = True
        with open(
                "mock_data/existing_document/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97/metadata.json",
                "r") as fh:
            document_metadata = json.load(fh)
        kb, _ = self._makeChroma()
        output_path = "mock_data/existing_document/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97/raw"
        convertor_result = ConvertorResult(
            pages=os.listdir(output_path),
            document_metadata=document_metadata,
            conversion_type="raw",
            model=None,
            output_folder_name='',
            output_path=output_path,
            result_hash="bad877b2f1bfd0d8e37ba5a2d3e6107320946d713b0ca19326bf690995d61145",
            document_path="mock_data/existing_document/ducks.pdf",
        )
        rag_settings = RAGSettings(
            {
                "rag_document_count": 20,
                "rag_char_chunk_size": 1000,
                "rag_char_overlap": 200,
                "rag_similarity_score_threshold": 0.8,
                "rag_score_margin": 0.2,
                "rag_cosine_distance_irrelevance_threshold": 1.0
            }
        )
        kb.store_convertor_result(mock_embeddings_source, convertor_result, rag_settings=rag_settings)
        with open("temp/mock_chroma_db.json", "r") as fh:
            stored_document_contents = json.load(fh)
        self.assertEqual(len(stored_document_contents), 3)

    def test_chroma_has_full_document(self):
        kb, _ = self._makeChroma()
        document = DocumentFile.create("doc_source_name", os.path.join(os.getcwd(), "documents"), "documents/ducks.pdf")
        self.assertTrue(kb.has_full_document(mock_embeddings_source, document))

    def test_chroma_has_full_convertor_result(self):
        with open(
                "mock_data/existing_document/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97/metadata.json",
                "r") as fh:
            document_metadata = json.load(fh)
        kb, _ = self._makeChroma()
        output_path = "mock_data/existing_document/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97/raw"
        convertor_result = ConvertorResult(
            pages=os.listdir(output_path),
            document_metadata=document_metadata,
            conversion_type="raw",
            model=None,
            output_folder_name='',
            output_path=output_path,
            result_hash="bad877b2f1bfd0d8e37ba5a2d3e6107320946d713b0ca19326bf690995d61145",
            document_path="mock_data/existing_document/ducks.pdf",
        )
        self.assertTrue(kb.has_full_convertor_result(mock_embeddings_source, convertor_result))

    def test_chroma_add_doc_path(self):
        kb, _ = self._makeChroma()
        same_document = DocumentFile.create("doc_source_name", os.path.join(os.getcwd(), "documents"),
                                            "documents/same_ducks.pdf")
        kb.add_doc_path(mock_embeddings_source, same_document, same_document.file_path)
        with open("temp/updated_document.json", "r") as fh:
            updated_document = json.load(fh)
            paths = updated_document["metadata"]["document_path"]
            self.assertEqual(paths, "documents/ducks.pdf;doc_source_name/documents/same_ducks.pdf")


if __name__ == '__main__':
    unittest.main()
