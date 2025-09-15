import pytesseract
from convertors.document_image_convertor import DocumentImageConvertor

class OcrConvertor(DocumentImageConvertor):

    def __init__(self):
        conversion_type = 'ocr'
        super().__init__(conversion_type, None)
        
    def image_to_text(self, input_data: str) -> str:
        return pytesseract.image_to_string(input_data)

