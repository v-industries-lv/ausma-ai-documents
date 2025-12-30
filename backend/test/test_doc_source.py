import json
import os.path
import shutil
import unittest
from doc_sources.doc_source import SuperDocSource
from doc_sources.local_file_system import LocalFileSystemSource


class DocSourceTest(unittest.TestCase):
    def setUp(self):
        if os.path.exists(".cache") and os.path.basename(os.path.normpath(os.getcwd())) == "test":
            shutil.rmtree(".cache")
    def tearDown(self):
        if os.path.exists(".cache") and os.path.basename(os.path.normpath(os.getcwd())) == "test":
            shutil.rmtree(".cache")

    def test_local_doc_source(self):
        doc_source = LocalFileSystemSource("test_name", "documents", cache_hashes=False)
        doc_list = doc_source.list_files("**/*.pdf")
        self.assertTrue(len(doc_list) > 0)
        expected_list = ['test_name/geese.pdf', 'test_name/storks.pdf', 'test_name/same_ducks.pdf', 'test_name/water_birds.pdf', 'test_name/ducks.pdf']
        for doc in doc_list:
            self.assertTrue(doc in expected_list)

        document = doc_source.get('test_name/geese.pdf')
        self.assertTrue(document.file_name == 'geese.pdf')

    def test_local_doc_source_cached(self):
        cache_dir = os.path.join(".cache", "doc_hash_cache")
        doc_source = LocalFileSystemSource("test_name", "documents", cache_hashes=True, cache_dir=cache_dir)
        doc_list = doc_source.list_files("**/*.pdf")
        self.assertTrue(len(doc_list) > 0)
        expected_list = ['test_name/geese.pdf', 'test_name/storks.pdf', 'test_name/same_ducks.pdf', 'test_name/water_birds.pdf', 'test_name/ducks.pdf']
        for doc in doc_list:
            self.assertTrue(doc in expected_list)

        document = doc_source.get('test_name/geese.pdf')
        self.assertTrue(document.file_name == 'geese.pdf')
        doc_source.update_cache(document)
        with open(os.path.join(cache_dir, "test_name.json")) as fh:
            hash_cache = json.load(fh)
            self.assertEqual(document.file_hash, hash_cache[document.get_document_path()]["hash"])

    def test_super_doc_source(self):
        super_doc_source = SuperDocSource(
            doc_sources = [
                LocalFileSystemSource("test_name", "documents"),
                LocalFileSystemSource("test_name_raw", "documents_raw")
             ]
        )

        doc_list = super_doc_source.list_files("**/*.pdf")
        self.assertTrue(len(doc_list)>0)
        expected_list = ['test_name/geese.pdf', 'test_name/storks.pdf', 'test_name/same_ducks.pdf', 'test_name/water_birds.pdf', 'test_name/ducks.pdf']
        for doc in doc_list:
            self.assertTrue(doc in expected_list)

        document = super_doc_source.get('test_name/geese.pdf')
        self.assertTrue(document.file_name == 'geese.pdf')

    def test_chained_super_doc_source(self):
        super_doc_source = SuperDocSource(
            "second_level_super",
            doc_sources = [
                LocalFileSystemSource("test_name", "documents"),
                LocalFileSystemSource("test_name_raw", "documents_raw")
            ]
        )
        chained_super_doc_source = SuperDocSource(
            "first_level_super",
            [
                super_doc_source
            ],
        )

        doc_list = chained_super_doc_source.list_files("**/*.pdf")
        self.assertTrue(len(doc_list) > 0)
        expected_list = ['first_level_super/second_level_super/test_name/geese.pdf',
                         'first_level_super/second_level_super/test_name/storks.pdf',
                         'first_level_super/second_level_super/test_name/same_ducks.pdf',
                         'first_level_super/second_level_super/test_name/water_birds.pdf',
                         'first_level_super/second_level_super/test_name/ducks.pdf']
        for doc in doc_list:
            self.assertTrue(doc in expected_list)

        document = chained_super_doc_source.get('first_level_super/second_level_super/test_name/geese.pdf')
        self.assertTrue(document.file_name == 'geese.pdf')

    def test_chained_super_doc_source_first_unnamed(self):
        super_doc_source = SuperDocSource(
            "second_level_super",
            doc_sources=[
                LocalFileSystemSource("test_name", "documents"),
                LocalFileSystemSource("test_name_raw", "documents_raw")
            ]
        )
        chained_super_doc_source = SuperDocSource(
            "",
            [
                super_doc_source
            ],
        )

        doc_list = chained_super_doc_source.list_files("**/*.pdf")
        self.assertTrue(len(doc_list) > 0)
        expected_list = ['second_level_super/test_name/geese.pdf', 'second_level_super/test_name/storks.pdf',
                         'second_level_super/test_name/same_ducks.pdf',
                         'second_level_super/test_name/water_birds.pdf', 'second_level_super/test_name/ducks.pdf']
        self.assertEqual(sorted(expected_list), sorted(doc_list))

        document = chained_super_doc_source.get('second_level_super/test_name/geese.pdf')
        self.assertTrue(document.file_name == 'geese.pdf')

    def test_super_doc_source_spec_cases(self):
        super_doc_source = SuperDocSource(
            doc_sources = [
                LocalFileSystemSource("test_name", "documents"),
                LocalFileSystemSource("test_name_raw", "documents_raw"),
                LocalFileSystemSource("test_name_nested", "documents_nested"),
             ]
        )
        self.assertEqual([], super_doc_source.list_files("first"))

        self.assertEqual(
            sorted(["test_name_nested/water_birds.pdf"]),
            sorted(super_doc_source.list_files("test_name_nested"))
        )

        self.assertEqual(
            sorted(['test_name_nested/first/same_ducks.pdf', 'test_name_nested/first/ducks.pdf']),
            sorted(super_doc_source.list_files("test_name_nested/first"))
        )

        self.assertEqual(
            sorted(['test_name/storks.pdf',
             'test_name/same_ducks.pdf',
             'test_name/ducks.pdf',
             'test_name/file.unsupported',
             'test_name/frogs.md',
             'test_name/water_birds.pdf',
             'test_name/geese.pdf',
             'test_name_raw/storks.odt',
             'test_name_raw/geese.odt',
             'test_name_raw/water_birds.odt',
             'test_name_raw/ducks.odt',
             'test_name_nested/first/same_ducks.pdf',
             'test_name_nested/first/ducks.pdf',
             'test_name_nested/first/second/storks.pdf',
             'test_name_nested/first/second/geese.pdf',
             'test_name_nested/water_birds.pdf']),
            sorted(super_doc_source.list_files("**"))
        )

        self.assertEqual(
            [],
            sorted(super_doc_source.list_files("test_name_nestedfirst/*"))
        )

        self.assertEqual(
            [],
            sorted(super_doc_source.list_files("**/test_name_nested/*"))
        )
if __name__ == '__main__':
    unittest.main()