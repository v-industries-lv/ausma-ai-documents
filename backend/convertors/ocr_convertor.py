from convertors.document_image_convertor import DocumentImageConvertor
import os

from convertors.llm_contexts import DocumentContext


class OcrConvertor(DocumentImageConvertor):

    def __init__(self):
        conversion_type = 'ocr'
        super().__init__(conversion_type, None)
        
    def image_to_text(self, input_data: str, context: DocumentContext) -> str:
        return DocumentImageConvertor.tesseract_convert(
            tesseract_path=os.environ.get("TESSERACT_PATH", "tesseract"),
            image_path=input_data,
            character_sets=context.character_sets
        )

