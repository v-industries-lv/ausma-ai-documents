import os
import unittest
import prepare_documents
import shutil

class FakeArgs:
    def __init__(self, poppler_path, input_root, text_model, vision_model, conversions, dpi):
        self.poppler_path = poppler_path
        self.input_root = input_root
        self.text_model = text_model
        self.vision_model = vision_model
        self.conversions = conversions
        self.dpi = dpi

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        image_path = "test/images"
        if os.path.exists(image_path):
            shutil.rmtree(image_path)

        text_path = "test/text"
        if os.path.exists(text_path):
            shutil.rmtree(text_path)

    def test_raw_process(self):
        args = FakeArgs(
            poppler_path="/usr/bin/",
            input_root="test/",
            text_model=None,
            vision_model=None,
            conversions='raw',
            dpi=300
        )
        prepare_documents.main(args)
        self.assertEqual(len(os.listdir("test/text/raw/ducks.pdf")), 3)
        self.assertEqual(len(os.listdir("test/text/raw/geese.pdf")), 3)
        self.assertEqual(len(os.listdir("test/text/raw/storks.pdf")), 3)
        self.assertEqual(len(os.listdir("test/text/raw/water_birds.pdf")), 4)

    def test_ocr_process(self):
        args = FakeArgs(
            poppler_path="/usr/bin/",
            input_root="test/",
            text_model=None,
            vision_model=None,
            conversions='ocr',
            dpi=300
        )
        prepare_documents.main(args)
        self.assertEqual(len(os.listdir("test/text/ocr/ducks.pdf")), 3)
        self.assertEqual(len(os.listdir("test/text/ocr/geese.pdf")), 3)
        self.assertEqual(len(os.listdir("test/text/ocr/storks.pdf")), 3)
        self.assertEqual(len(os.listdir("test/text/ocr/water_birds.pdf")), 4)

    def test_ocr_llm_process(self):
        args = FakeArgs(
            poppler_path="/usr/bin/",
            input_root="test/",
            text_model="qwen2.5",
            vision_model=None,
            conversions='ocr_llm',
            dpi=300
        )
        prepare_documents.main(args)
        self.assertEqual(len(os.listdir("test/text/ocr_llm/ducks.pdf")), 3)
        self.assertEqual(len(os.listdir("test/text/ocr_llm/geese.pdf")), 3)
        self.assertEqual(len(os.listdir("test/text/ocr_llm/storks.pdf")), 3)
        self.assertEqual(len(os.listdir("test/text/ocr_llm/water_birds.pdf")), 4)

    def test_llm_process(self):
        args = FakeArgs(
            poppler_path="/usr/bin/",
            input_root="test/",
            text_model=None,
            vision_model="qwen2.5vl",
            conversions='llm',
            dpi=300
        )
        prepare_documents.main(args)
        self.assertEqual(len(os.listdir("test/text/llm/ducks.pdf")), 3)
        self.assertEqual(len(os.listdir("test/text/llm/geese.pdf")), 3)
        self.assertEqual(len(os.listdir("test/text/llm/storks.pdf")), 3)
        self.assertEqual(len(os.listdir("test/text/llm/water_birds.pdf")), 4)

if __name__ == '__main__':
    unittest.main()
