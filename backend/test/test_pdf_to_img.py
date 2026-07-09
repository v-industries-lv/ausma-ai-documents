import shutil
import unittest
from pathlib import Path

import pdf2image.pdf2image

from pdf_to_png import poppler_convert, xpdf_convert
import os


class PDFToPNGTest(unittest.TestCase):

    def setUp(self):
        if os.path.exists("temp") and os.path.basename(os.path.normpath(os.getcwd())) == "test":
            shutil.rmtree("temp")
        os.environ["XPDF_PATH"] = os.path.join(Path.cwd().parent, "bin", "linux", "pdftopng")
        os.environ["POPPLER_PATH"] = "/usr/bin"

    def tearDown(self):
        if os.path.exists("temp") and os.path.basename(os.path.normpath(os.getcwd())) == "test":
            shutil.rmtree("temp")

    @staticmethod
    def is_poppler_working() -> bool:
        try:
            os.makedirs("temp", exist_ok=True)
            poppler_convert(pdf_path=os.path.join("encrypted-pdf","not-encrypted-ducks.pdf"), output="temp")
            shutil.rmtree("temp")
            return True
        except Exception as e:
            print(e)
            return False

    @staticmethod
    def is_xpdf_working() -> bool:
        try:
            os.makedirs("temp", exist_ok=True)
            xpdf_convert(pdf_path=os.path.join("encrypted-pdf","not-encrypted-ducks.pdf"), output="temp")
            shutil.rmtree("temp")
            return True
        except Exception as e:
            print(e)
            return False

    def test_poppler_encrypted_no_password(self):
        if not PDFToPNGTest.is_poppler_working():
            print("Failed to use poppler. If using XPDF, then ignore.")
            return
        os.makedirs("temp", exist_ok=True)
        poppler_convert(pdf_path=os.path.join("encrypted-pdf", "encrypted-no-password.pdf"), output="temp")
        self.assertEqual(1, len(os.listdir("temp")))

    def test_xpdf_encrypted_no_password(self):
        if not PDFToPNGTest.is_xpdf_working():
            print("Failed to use XPDF. If using poppler, then ignore.")
            return
        os.makedirs("temp", exist_ok=True)
        poppler_convert(pdf_path=os.path.join("encrypted-pdf", "encrypted-no-password.pdf"), output="temp")
        self.assertEqual(1, len(os.listdir("temp")))

    def test_poppler_encrypted_password(self):
        if not PDFToPNGTest.is_poppler_working():
            print("Failed to use poppler. If using XPDF, then ignore.")
            return
        os.makedirs("temp", exist_ok=True)
        try:
            poppler_convert(pdf_path=os.path.join("encrypted-pdf", "test-with-password.pdf"), output="temp")
        except Exception as e:
            self.assertIsInstance(e, pdf2image.pdf2image.PDFPageCountError)
            return
        # We expect code above to throw error on encrypted file with password. Otherwise, something is not right.
        self.assertTrue(False)


    def test_xpdf_encrypted_password(self):
        if not PDFToPNGTest.is_xpdf_working():
            print("Failed to use XPDF. If using poppler, then ignore.")
            return
        os.makedirs("temp", exist_ok=True)
        try:
            xpdf_convert(pdf_path=os.path.join("encrypted-pdf", "test-with-password.pdf"), output="temp")
        except Exception as e:
            self.assertIsInstance(e, ValueError)
            return
        # We expect code above to throw error on encrypted file with password. Otherwise, something is not right.
        self.assertTrue(False)

if __name__ == '__main__':
    unittest.main()