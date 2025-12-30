import os
from typing import Optional
from convertors.convertor_result import ConvertorResult
from convertors.convertor import Convertor
from convertors.document_file import DocumentFile
from convertors.llm_contexts import DocumentContext
from utils import compute_folder_hash
from logger import logger

class RawConvertor(Convertor):

    def __init__(self):
        conversion_type = 'raw'
        super().__init__(conversion_type, None)

    def convert(self, doc: DocumentFile, context: DocumentContext) -> Optional[ConvertorResult]:
        # Types where raw dumping is not supported
        if doc.document_type in ["image"]:
            logger.warn(f"Cannot [raw] convert an image file")
            return None
        conversion_result = self.get_or_init_conversion(doc)
        # TODO: add check if zero pages is intended as in complete
        if len(conversion_result.pages) == 0:
            return self.convert_raw_document(doc, conversion_result.document_metadata)
        else:
            return conversion_result

    def convert_raw_document(self, document: DocumentFile, metadata: dict) -> Optional[ConvertorResult]:
        try:
            document.raw_dump()
            output_path = self.get_output_path(document)
            result_hash = compute_folder_hash(output_path)
            metadata["conversions"].append(self.conversion_metadata(result_hash))
            document.write_metadata(metadata)
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
        except Exception as e:
            logger.error(f"[{self.conversion_type}] failed!")
            logger.error(e)
            return None
