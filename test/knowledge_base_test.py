import json
import shutil
import unittest
from langchain_core.documents import Document
import os
import sys


from convertors.convertor_result import ConvertorResult
from convertors.document_file import DocumentFile
from knowledge_base import ChromaKnowledgeBase, KnowledgeBase
from llm_runners.ollama_runner import OllamaRunner
from mock_classes import MockChroma, mock_embeddings_source


class KnowledgeBaseTest(unittest.TestCase):
    chroma = None
    real_chroma = None
    LLM_RUNNER = OllamaRunner.from_settings({"type": "ollama"})

    @classmethod
    def setUpClass(cls):
        module = sys.modules['knowledge_base']
        cls.real_chroma = module.Chroma
        cls.chroma = module.Chroma = MockChroma

    def setUp(self):
        temp_path = "temp"
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
        MockChroma.force_do = False

    def tearDown(self):
        temp_path = "temp"
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
        MockChroma.force_do = False

    def test_create_embedding(self):
        kb_name = "test"
        with open(f"knowledge_bases/chroma/{kb_name}/config.json", "r") as fh:
            kb_dict = json.load(fh)
        kb = ChromaKnowledgeBase(kb_dict)
        embedding = kb._create_embedding(mock_embeddings_source)
        self.assertEqual(embedding.model, "bge-m3:latest")
        self.assertEqual(embedding.temperature, 0.7)
        self.assertEqual(embedding.seed, 42)

    def test_knowledgebase_from_dict(self):
        kb_name = "test"
        with open(f"knowledge_bases/chroma/{kb_name}/config.json", "r") as fh:
            kb = KnowledgeBase.from_dict(json.load(fh))
        self.assertTrue(isinstance(kb, ChromaKnowledgeBase))

    def test_knowledgebase_validate_document_source_exists(self):
        convertor_result = ConvertorResult(
            pages=[],
            document_metadata={},
            conversion_type="raw",
            model=None,
            output_folder_name='',
            output_path="mock_data/existing_document/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97/raw",
            result_hash="bad877b2f1bfd0d8e37ba5a2d3e6107320946d713b0ca19326bf690995d61145",
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
            result_hash="11daa02a0e65c9f05ccccc85f41a297e0d7b3aa3ca9844c960f240520db78858"
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
        )

        self.assertFalse(KnowledgeBase.validate_document_source(convertor_result))

    # Chroma kb tests
    def test_chroma_to_dict(self):
        kb_name = "test"
        with open(f"knowledge_bases/chroma/{kb_name}/config.json", "r") as fh:
            kb_dict = json.load(fh)
        kb = ChromaKnowledgeBase(kb_dict)
        self.assertTrue(kb_dict==kb.to_dict())

    def test_chroma_rag_lookup(self):
        kb_name = "test"
        with open(f"knowledge_bases/chroma/{kb_name}/config.json", "r") as fh:
            kb_dict = json.load(fh)
        kb = ChromaKnowledgeBase(kb_dict)
        relevant_documents = kb.rag_lookup(mock_embeddings_source, "lookup some rag", 5)
        self.assertEqual(len(relevant_documents), 5)

    def test_chroma_add_metadata_document(self):
        document_list = [Document(f"doc_{x}") for x in range(1, 5 + 1)]
        for page_number, document in enumerate(document_list, 1):
            document.metadata["source"] = f"document/path/{page_number}.pdf"
        kb_name = "test"
        with open(f"knowledge_bases/chroma/{kb_name}/config.json", "r") as fh:
            kb_dict = json.load(fh)
        kb = ChromaKnowledgeBase(kb_dict)
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
        )

        kb._add_metadata(document_list, document_metadata, convertor_result)
        for document in document_list:
            self.assertTrue(document.metadata["type"] == "document")
            self.assertTrue(document.metadata["conversion"] == "raw")

    def test_chroma_add_chunk_metadata(self):
        chunk_list = [Document(f"doc_{x}") for x in range(1, 5 + 1)]
        kb_name = "test"
        with open(f"knowledge_bases/chroma/{kb_name}/config.json", "r") as fh:
            kb_dict = json.load(fh)
        kb = ChromaKnowledgeBase(kb_dict)
        kb._add_chunk_metadata(chunk_list)
        for chunk in chunk_list:
            self.assertTrue(chunk.metadata["chunk_number"] <= len(chunk_list))
            self.assertTrue(chunk.metadata["chunk_number"] > 0)
            self.assertEqual(chunk.metadata["chunk_count"], len(chunk_list))

    def test_chroma_store_convertor_result(self):
        MockChroma.force_do = True
        with open("mock_data/existing_document/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97/metadata.json", "r") as fh:
            document_metadata = json.load(fh)
        kb_name = "test"
        with open(f"knowledge_bases/chroma/{kb_name}/config.json", "r") as fh:
            kb_dict = json.load(fh)
        kb = ChromaKnowledgeBase(kb_dict)
        output_path = "mock_data/existing_document/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97/raw"
        convertor_result = ConvertorResult(
            pages=os.listdir(output_path),
            document_metadata=document_metadata,
            conversion_type="raw",
            model=None,
            output_folder_name='',
            output_path=output_path,
            result_hash="bad877b2f1bfd0d8e37ba5a2d3e6107320946d713b0ca19326bf690995d61145",
        )
        kb.store_convertor_result(mock_embeddings_source, convertor_result)
        with open("temp/mock_chroma_db.json", "r") as fh:
            stored_document_contents = json.load(fh)
        self.assertEqual(len(stored_document_contents), 3)

    def test_chroma_has_full_document(self):
        kb_name = "test"
        with open(f"knowledge_bases/chroma/{kb_name}/config.json", "r") as fh:
            kb_dict = json.load(fh)
        kb = ChromaKnowledgeBase(kb_dict)
        document = DocumentFile.from_path("doc_source_name", os.path.join(os.getcwd(), "documents"), "documents/ducks.pdf")
        self.assertTrue(kb.has_full_document(mock_embeddings_source, document))

    def test_chroma_has_full_convertor_result(self):
        with open(
                "mock_data/existing_document/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97/metadata.json",
                "r") as fh:
            document_metadata = json.load(fh)
        kb_name = "test"
        with open(f"knowledge_bases/chroma/{kb_name}/config.json", "r") as fh:
            kb_dict = json.load(fh)
        kb = ChromaKnowledgeBase(kb_dict)
        output_path = "mock_data/existing_document/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97/raw"
        convertor_result = ConvertorResult(
            pages=os.listdir(output_path),
            document_metadata=document_metadata,
            conversion_type="raw",
            model=None,
            output_folder_name='',
            output_path=output_path,
            result_hash="bad877b2f1bfd0d8e37ba5a2d3e6107320946d713b0ca19326bf690995d61145",
        )
        self.assertTrue(kb.has_full_convertor_result(mock_embeddings_source, convertor_result))

    def test_chroma_add_doc_path(self):
        kb_name = "test"
        with open(f"knowledge_bases/chroma/{kb_name}/config.json", "r") as fh:
            kb_dict = json.load(fh)
        kb = ChromaKnowledgeBase(kb_dict)
        same_document = DocumentFile.from_path("doc_source_name", os.path.join(os.getcwd(), "documents"),
                                          "documents/same_ducks.pdf")
        kb.add_doc_path(mock_embeddings_source, same_document, same_document.file_path)
        with open("temp/updated_document.json", "r") as fh:
            updated_document = json.load(fh)
            paths = updated_document["metadata"]["file_location"]
            self.assertEqual(paths, "documents/ducks.pdf;documents/same_ducks.pdf")

if __name__ == '__main__':
    unittest.main()
