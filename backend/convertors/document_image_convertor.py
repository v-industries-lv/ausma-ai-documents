import pathlib
import subprocess

from convertors.convertor_result import ConvertorResult
from convertors.convertor import Convertor
from abc import abstractmethod
from typing import Optional, List, Union

from convertors.llm_contexts import DocumentContext
from logger import logger
from utils import compute_folder_hash
from convertors.document_file import PDFDocumentFile, ImageDocumentFile
import os


class DocumentImageConvertor(Convertor):
    def __init__(self, conversion_type, model):
        super().__init__(conversion_type, model)
        self.images = None

    @abstractmethod
    def image_to_text(self, input_data, context: DocumentContext):
        pass

    def convert(self, doc: Union[PDFDocumentFile, ImageDocumentFile], context: DocumentContext) -> Optional[ConvertorResult]:
        # TODO: add check if zero pages is intended as in complete
        conversion_result = self.get_or_init_conversion(doc)
        if len(conversion_result.pages) == 0:
            return self.convert_image_document(doc, conversion_result.document_metadata, context)
        else:
            return conversion_result

    def convert_image_document(self, document: Union[PDFDocumentFile, ImageDocumentFile], metadata: dict, context: DocumentContext) -> Optional[ConvertorResult]:
        try:
            if document.image_based:
                # Check if you need to generate temp images for image conversion
                try:
                    self.images = document.convert_document_to_images()
                    if self.images is None:
                        logger.error(f"Image conversion failed. File: {document.file_name}")
                        return None
                    logger.info(f"Doing {self.conversion_type}")
                    output_path = self.get_output_path(document)
                    os.makedirs(output_path, exist_ok=True)

                    for image_path in self.images:
                        logger.info(f"{self.conversion_type} - {image_path}")
                        image_filename = pathlib.Path(image_path).stem
                        with open(os.path.join(output_path, image_filename + ".txt"),
                                  "w") as fh:
                            converted_text = self.image_to_text(image_path, context)
                            if converted_text is None:
                                return None
                            fh.write(converted_text)
                    extra_string_list = []
                    if self.conversion_type in ["ocr_llm", "llm"]:
                        extra_string_list = [self.model]
                    result_hash = compute_folder_hash(
                        os.path.join(document.processed_path, self.output_folder_name),
                        extra_string_list=extra_string_list)
                    metadata["conversions"].append(self.conversion_metadata(result_hash))
                    document.write_metadata(metadata)
                finally:
                    document.cleanup_temp_files()
                return ConvertorResult(
                    pages=[x.path for x in os.scandir(os.path.abspath(output_path))],
                    document_metadata=metadata,
                    conversion_type=self.conversion_type,
                    model=self.model,
                    output_folder_name=self.output_folder_name,
                    output_path=output_path,
                    result_hash=result_hash,
                    document_path=document.get_document_path(),
                )
            else:
                logger.info(
                    f"[{self.conversion_type}]Document {document.file_path} does not support image conversion.")
                return None
        except Exception as e:
            logger.error(f"[{self.conversion_type}] failed!")
            logger.error(e)
            return None

    @staticmethod
    def tesseract_convert(tesseract_path: str, image_path: str, character_sets: List[str] = None) -> Optional[str]:
        if character_sets is None or len(character_sets) == 0:
            character_sets = ["eng"]

        args = ["-l", "+".join(character_sets)]
        process = subprocess.run(
            [tesseract_path] + args + [image_path, "stdout"],
            text=True,
            capture_output=True,
        )
        if process.returncode != 0:
            logger.error(f"Error converting {image_path} with tesseract ocr. Error: {process.stderr}")
            return None
        return process.stdout

    @staticmethod
    def get_tesseract_langs() -> Optional[List[str]]:
        process = subprocess.run(
            [os.environ.get("TESSERACT_PATH", "tesseract"), "--list-langs"],
            text=True,
            capture_output=True,
        )
        if process.returncode != 0:
            logger.error(process.stderr)
            return None
        return [x for x in process.stdout.split("\n") if
                not x.startswith("List of available languages") and x not in ["osd", ""]]