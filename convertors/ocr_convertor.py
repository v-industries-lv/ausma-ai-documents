import os
import sys

import pytesseract

from convertors.base_convertor import Convertor


class OCR_convertor(Convertor):

    def __init__(self):
        pytesseract.tesseract_cmd = "/usr/bin/tesseract"
        sys.path.append("/usr/bin/tesseract")

        self.convertor_type = 'ocr'
    def image_to_text(self, input_data):
        return pytesseract.image_to_string(input_data)


if __name__ == "__main__":
    import shutil
    pytesseract.pytesseract.tesseract_cmd = None
    os.environ["PATH"] += os.pathsep + "/usr/bin/tesseract"
    # search for tesseract binary in path
    def find_tesseract_binary() -> str:
        print(os.environ['PATH'])
        print(sys.path)
        return shutil.which("tesseract")

    # set tesseract binary path
    pytesseract.pytesseract.tesseract_cmd = find_tesseract_binary()
    if not pytesseract.pytesseract.tesseract_cmd:
        print("Tesseract binary not found in PATH. Please install Tesseract.")
    else:
        print("Tesseract found!")
