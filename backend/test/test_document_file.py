import os.path
import shutil
import unittest
from convertors.document_file import DocumentFile, PDFDocumentFile, TextDocumentFile

class DocumentFileTest(unittest.TestCase):
    def setUp(self):
        path = "processed"
        if os.path.exists(path) and os.path.basename(os.path.normpath(os.getcwd())) == "test":
            shutil.rmtree(path)
        path = "temp_images"
        if os.path.exists(path) and os.path.basename(os.path.normpath(os.getcwd())) == "test":
            shutil.rmtree(path)

    def tearDown(self):
        path = "processed"
        if os.path.exists(path) and os.path.basename(os.path.normpath(os.getcwd())) == "test":
            shutil.rmtree(path)
        path = "temp_images"
        if os.path.exists(path) and os.path.basename(os.path.normpath(os.getcwd())) == "test":
            shutil.rmtree(path)

    def test_calculate_hash(self):
        document = DocumentFile.create('test_doc_source_name', 'documents', 'documents/ducks.pdf')
        document.calculate_hash()
        self.assertEqual(document.file_hash, 'f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97')

    def test_get_output_path(self):
        document = DocumentFile.create('test_doc_source_name', 'documents', 'documents/ducks.pdf')
        self.assertEqual(document.get_output_path(), 'ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97')

    def test_ensure_output_folder(self):
        document = DocumentFile.create('test_doc_source_name', 'documents', 'documents/ducks.pdf')
        document._ensure_output_exists()
        self.assertTrue(os.path.exists("processed/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97"))
        document.cleanup_output()
        self.assertFalse(os.path.exists("processed/ducks.pdf_f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97"))

    def test_new_and_existing_metadata(self):
        document = DocumentFile.create('test_doc_source_name', 'documents', 'documents/ducks.pdf')
        document.cleanup_output()
        # Test getting fresh metadata
        metadata = document.get_or_init_metadata()
        test_metadata = {'type': 'document', 'filename': 'ducks.pdf', 'file_location': 'documents/ducks.pdf', 'hash': 'f06b0e20587b9f30a7274843eded4de2ae437a1de1dd44b8d0646831f8acee97', 'conversions': []}
        self.assertEqual(metadata, test_metadata)
        # Test getting existing metadata
        test_metadata["filename"] = "modified"
        document.write_metadata(test_metadata)
        metadata = document.get_or_init_metadata()
        self.assertEqual(metadata, test_metadata)

    def test_from_path(self):
        document = DocumentFile.create('test_doc_source_name', 'documents', 'documents/frogs.md')
        self.assertIsInstance(document, TextDocumentFile)
        document = DocumentFile.create('test_doc_source_name', 'documents', 'documents/ducks.pdf')
        self.assertIsInstance(document, PDFDocumentFile)

    # TextDocumentFIle tests
    def test_raw_dump_text(self):
        document = TextDocumentFile('test_doc_source_name', 'documents', 'documents/frogs.md')
        document.raw_dump()
        self.assertEqual(len(os.listdir(os.path.join(document.processed_path, "raw"))), 1)

    # PDFDocumentFile tests
    def test_raw_dump_pdf(self):
        document = PDFDocumentFile('test_doc_source_name', 'documents', 'documents/ducks.pdf')
        document.raw_dump()
        self.assertEqual(len(os.listdir(os.path.join(document.processed_path, "raw"))), 3)

    def test_convert_document_to_images(self):
        document = PDFDocumentFile('test_doc_source_name', 'documents', 'documents/ducks.pdf')
        document.convert_document_to_images()
        self.assertEqual(len(os.listdir(document.temp_image_path)), 3)

        os.environ["XPDF_PATH"] = "__disabled__"
        document = PDFDocumentFile('test_doc_source_name', 'documents', 'documents/ducks.pdf')
        document.convert_document_to_images()
        self.assertEqual(len(os.listdir(document.temp_image_path)), 3)

        os.environ["POPPLER_PATH"] = "__disabled__"
        document = PDFDocumentFile('test_doc_source_name', 'documents', 'documents/ducks.pdf')
        document.convert_document_to_images()
        self.assertEqual(len(os.listdir(document.temp_image_path)), 0)
if __name__ == '__main__':
    unittest.main()