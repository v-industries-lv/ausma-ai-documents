import pathlib

from convertors.convertor_result import ConvertorResult
from convertors.convertor import Convertor
from abc import abstractmethod
from typing import Optional
from logger import logger
from utils import compute_folder_hash
from convertors.document_file import PDFDocumentFile
import os


class DocumentImageConvertor(Convertor):
    def __init__(self, conversion_type, model):
        super().__init__(conversion_type, model)
        self.images = None

    @abstractmethod
    def image_to_text(self, input_data):
        pass

    def convert(self, doc: PDFDocumentFile) -> Optional[ConvertorResult]:
        # TODO: add check if zero pages is intended as in complete
        conversion_result = self.get_or_init_conversion(doc)
        if len(conversion_result.pages) == 0:
            return self.convert_image_document(doc, conversion_result.document_metadata)
        else:
            return conversion_result

    def convert_image_document(self, document: PDFDocumentFile, metadata: dict) -> Optional[ConvertorResult]:
        try:
            if document.needs_images:
                # Check if you need to generate temp images for image conversion
                try:
                    self.images = document.convert_document_to_images()
                    logger.info(f"Doing {self.conversion_type}")
                    output_path = self.get_output_path(document)
                    os.makedirs(output_path, exist_ok=True)
                    for image_path in self.images:
                        logger.info(f"{self.conversion_type} - {image_path}")
                        image_filename = pathlib.Path(image_path).name
                        with open(os.path.join(output_path, image_filename.split('-')[-1].replace(".png", ".txt")),
                                  "w") as fh:
                            fh.write(self.image_to_text(image_path))
                    extra_string_list = []
                    if self.conversion_type in ["ocr_llm", "llm"]:
                        extra_string_list = [self.model]
                    result_hash = compute_folder_hash(
                        os.path.join(document.processed_path, self.output_folder_name),
                        extra_string_list=extra_string_list)
                    metadata["conversions"].append(self.conversion_metadata(result_hash))
                    document.write_metadata(metadata)
                finally:
                    document.clear_images()
                return ConvertorResult(
                    pages=[x.path for x in os.scandir(os.path.abspath(output_path))],
                    document_metadata=metadata,
                    conversion_type=self.conversion_type,
                    model=self.model,
                    output_folder_name=self.output_folder_name,
                    output_path=output_path,
                    result_hash=result_hash,
                )
            else:
                logger.info(
                    f"[{self.conversion_type}]Document {document.file_path} does not support image conversion.")
                return None
        except Exception as e:
            logger.error(f"[{self.conversion_type}] failed!")
            logger.error(e)
            return None
