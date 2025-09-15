import unittest
from knowledge_base import LocalFileSystemSource, SuperDocSource


class DocSourceTest(unittest.TestCase):
    def test_local_doc_source(self):
        doc_source = LocalFileSystemSource("test_name", "documents")
        doc_list = doc_source.list("**/*.pdf")
        self.assertTrue(len(doc_list) > 0)
        expected_list = ['test_name/geese.pdf', 'test_name/storks.pdf', 'test_name/same_ducks.pdf', 'test_name/water_birds.pdf', 'test_name/ducks.pdf']
        for doc in doc_list:
            self.assertTrue(doc in expected_list)

        document = doc_source.get('test_name/geese.pdf')
        self.assertTrue(document.file_name == 'geese.pdf')

    def test_super_doc_source(self):
        super_doc_source = SuperDocSource(
            doc_sources = [
                LocalFileSystemSource("test_name", "documents"),
                LocalFileSystemSource("test_name_raw", "documents_raw")
             ]
        )

        doc_list = super_doc_source.list("**/*.pdf")
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

        doc_list = chained_super_doc_source.list("**/*.pdf")
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

        doc_list = chained_super_doc_source.list("**/*.pdf")
        self.assertTrue(len(doc_list) > 0)
        expected_list = ['second_level_super/test_name/geese.pdf', 'second_level_super/test_name/storks.pdf',
                         'second_level_super/test_name/same_ducks.pdf',
                         'second_level_super/test_name/water_birds.pdf', 'second_level_super/test_name/ducks.pdf']
        for doc in doc_list:
            self.assertTrue(doc in expected_list)

        document = chained_super_doc_source.get('second_level_super/test_name/geese.pdf')
        self.assertTrue(document.file_name == 'geese.pdf')

if __name__ == '__main__':
    unittest.main()