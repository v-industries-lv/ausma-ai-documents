import platform
import shutil
import unittest
from pathlib import Path

import pdf2image.pdf2image

from pdf_to_png import poppler_convert, xpdf_convert, get_xpdf_path, get_poppler_path, make_absolute_path
import os


class PDFToPNGTest(unittest.TestCase):
    OS_DICT = {
        'Linux': "linux",
        'Darwin': "macos",
        'Windows': "windows",
    }

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
        xpdf_convert(pdf_path=os.path.join("encrypted-pdf", "encrypted-no-password.pdf"), output="temp")
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

    def test_get_xpdf_path(self):
        os.environ.pop("XPDF_PATH")
        self.assertIsNone(os.environ.get("XPDF_PATH"))
        current_os = PDFToPNGTest.OS_DICT.get(platform.system())
        extension = ".exe" if current_os == "windows" else ""
        expected = Path(f"backend/bin/{current_os}/pdftopng{extension}")
        returned = Path(get_xpdf_path())
        self.assertEqual(returned.parts[-len(expected.parts):], expected.parts)
        os.environ["XPDF_PATH"] = os.path.join("mock_data")
        expected = Path(f"mock_data")
        returned = Path(get_xpdf_path())
        self.assertEqual(returned.parts[-len(expected.parts):], expected.parts)

    def test_get_poppler_path(self):
        if PDFToPNGTest.OS_DICT.get(platform.system()) != "linux":
            print("Poppler not on linux. Skipping test_get_poppler_path()...")
            return
        os.environ.pop("POPPLER_PATH")
        expected = Path(f"/usr/bin")
        returned = Path(get_poppler_path())
        self.assertTrue(returned.parts[-len(expected.parts):] == expected.parts)
        os.environ["POPPLER_PATH"] = "mock_data"
        self.assertEqual(make_absolute_path("mock_data"), get_poppler_path())

if __name__ == '__main__':
    unittest.main()