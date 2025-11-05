from abc import ABC, abstractmethod
from typing import Optional, List
import os
from convertors.document_file import DocumentFile
from convertors.llm_contexts import DocumentContext
from llm_runners.llm_runner import LLMRunner
from logger import logger
from utils import compute_folder_hash, clean_name

class ConvertorResult:
    def __init__(self, pages: List[str], document_metadata: dict, conversion_type: str, model: Optional[str], output_folder_name: str, output_path: str, result_hash: Optional[str]):
        self.pages = pages
        # Metadata contains specific document metadata.
        self.document_metadata = document_metadata
        self.output_folder_name = output_folder_name
        self.conversion_type = conversion_type
        self.model = model
        self.output_path = output_path
        self.result_hash = result_hash

class Convertor(ABC):

    def __init__(self, conversion_type, model):
        self.conversion_type = conversion_type
        self.model = model
        self.output_folder_name= self.conversion_type if self.model is None else "_".join([self.conversion_type, clean_name(model)])

    @staticmethod
    def from_config(config: dict, llm_runner: LLMRunner):
        from convertors import ocr_convertor, ocr_with_llm_convertor, llm_convertor, raw_convertor
        conversion = config.get("conversion")
        model = config.get("model")
        if conversion == "raw":
            return raw_convertor.RawConvertor()
        elif conversion == "ocr":
            return ocr_convertor.OcrConvertor()
        elif conversion == "ocr_llm":
            return ocr_with_llm_convertor.OcrLlmConvertor(llm_runner=llm_runner, model=model)
        elif conversion == "llm":
            return llm_convertor.LlmConvertor(llm_runner=llm_runner, model=model)
        return None

    @abstractmethod
    def convert(self, doc: DocumentFile, context: DocumentContext) -> Optional[ConvertorResult]:
        pass

    def get_or_init_conversion(self, document: DocumentFile) -> ConvertorResult:
        document_metadata = document.get_or_init_metadata()
        # Process document
        extra_string_list = []
        if self.model is not None:
            extra_string_list = [self.model]
        output_path = self.get_output_path(document)
        folder_hash = compute_folder_hash(output_path,
                                          extra_string_list=extra_string_list)
        for conversion_metadata in document_metadata["conversions"]:
            # Check if conversion is relevant to current convertor
            if self.conversion_type == conversion_metadata["conversion"] and self.model == conversion_metadata["model"]:
                if conversion_metadata["hash"] == folder_hash:
                    result_hash = conversion_metadata["hash"]
                    logger.info(
                        f"[{self.conversion_type}]Document {document.file_path} already complete. Getting cache...")
                    return ConvertorResult(
                        pages=[x.path for x in os.scandir(os.path.abspath(output_path))],
                        document_metadata=document_metadata,
                        conversion_type=self.conversion_type,
                        model=self.model,
                        output_folder_name=self.output_folder_name,
                        output_path=output_path,
                        result_hash=result_hash,
                    )
        return ConvertorResult(
            pages=[],
            document_metadata=document_metadata,
            conversion_type=self.conversion_type,
            model=self.model,
            output_folder_name=self.output_folder_name,
            output_path=output_path,
            result_hash=None,
        )

    def get_output_path(self, document) -> str:
        return str(os.path.join(document.processed_path, self.output_folder_name))

    def conversion_metadata(self, result_hash) -> dict:
        return {
            "conversion": self.conversion_type,
            "model": self.model,
            "output_folder": self.output_folder_name,
            "hash": result_hash
        }