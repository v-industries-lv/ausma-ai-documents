import os
import shutil
import unittest
from convertors.convertor_result import ConvertorResult
from convertors.convertor import Convertor
from convertors.raw_convertor import RawConvertor
from convertors.ocr_convertor import OcrConvertor
from convertors.ocr_with_llm_convertor import OcrLlmConvertor
from convertors.llm_convertor import LlmConvertor
from convertors.convertor import DocumentFile
import json

from llm_runners.ollama_runner import OllamaRunner


class ConvertorTest(unittest.TestCase):
    LLM_RUNNER = OllamaRunner.from_settings({"type": "ollama", "host": "http://localhost:11434"})
    def setUp(self):
        if os.path.exists("processed"):
            shutil.rmtree("processed")

    def tearDown(self):
        if os.path.exists("processed"):
            shutil.rmtree("processed")

    def test_factory(self):
        config_path = 'convertor_configs'
        convertor_types = {'raw': RawConvertor, 'ocr': OcrConvertor, 'ocr_llm': OcrLlmConvertor, 'llm': LlmConvertor}
        for convertor_type in convertor_types.keys():
            print(convertor_type)
            with open(os.path.join(config_path, convertor_type+".json")) as fh:
                convertor = Convertor.from_config(json.load(fh), ConvertorTest.LLM_RUNNER)
                check_convertor_class = convertor_types[convertor_type]
                self.assertTrue(isinstance(convertor, check_convertor_class))

    def test_convert(self):
        config_path = 'convertor_configs'
        convertor_types = {
            'raw': RawConvertor,
            'ocr': OcrConvertor,
            'ocr_llm': OcrLlmConvertor,
            'llm': LlmConvertor
        }

        document = DocumentFile.from_path("doc_source_name", os.path.join(os.getcwd(), "documents"), "documents/ducks.pdf")

        for convertor_type in convertor_types.keys():
            print(convertor_type)
            with open(os.path.join(config_path, convertor_type + ".json")) as fh:
                convertor = Convertor.from_config(json.load(fh), ConvertorTest.LLM_RUNNER)
                result = convertor.convert(document)
                self.assertTrue(isinstance(result, ConvertorResult))
                self.assertEqual(len(result.pages), 3)

    def test_get_or_init_conversion_no_cache(self):
        config_path = 'convertor_configs'
        document = DocumentFile.from_path("doc_source_name", os.path.join(os.getcwd(), "documents"), "documents/ducks.pdf")
        with open(os.path.join(config_path, "raw.json")) as fh:
            convertor = Convertor.from_config(json.load(fh), ConvertorTest.LLM_RUNNER)
        converter_result = convertor.get_or_init_conversion(document)
        self.assertEqual(len(converter_result.pages), 0)

    def test_get_or_init_conversion_deleted_cache_files(self):
        shutil.copytree(
            "mock_data/existing_document/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97",
            "processed/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97"
        )
        config_path = 'convertor_configs'
        document = DocumentFile.from_path("doc_source_name", os.path.join(os.getcwd(), "documents"), "documents/ducks.pdf")
        with open(os.path.join(config_path, "ocr.json")) as fh:
            convertor = Convertor.from_config(json.load(fh), ConvertorTest.LLM_RUNNER)
        converter_result = convertor.get_or_init_conversion(document)
        self.assertEqual(len(converter_result.pages), 0)

    def test_get_or_init_conversion_existing_cache(self):
        shutil.copytree(
            "mock_data/existing_document/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97",
            "processed/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97"
        )
        config_path = 'convertor_configs'
        document = DocumentFile.from_path("doc_source_name", os.path.join(os.getcwd(), "documents"), "documents/ducks.pdf")
        with open(os.path.join(config_path, "raw.json")) as fh:
            convertor = Convertor.from_config(json.load(fh), ConvertorTest.LLM_RUNNER)
        converter_result = convertor.get_or_init_conversion(document)
        self.assertEqual(len(converter_result.pages), 3)

if __name__ == '__main__':
    unittest.main()
