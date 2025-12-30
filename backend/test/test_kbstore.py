import glob
import os.path
import shutil
import unittest

from kb.knowledge_base import SuperKBStore
from kb.chroma import ChromaKnowledgeBase, ChromaKBStore


# Note: initializing SuperKBStore calls
class KBStoreTest(unittest.TestCase):
    def setUp(self):
        self.cleanup()

    def tearDown(self):
        self.cleanup()

    @staticmethod
    def cleanup():
        new_kb_path = "knowledge_bases/chroma/new_kb*"
        if os.path.basename(os.path.normpath(os.getcwd())) == "test":
            for path in glob.glob(new_kb_path):
                shutil.rmtree(path)

    def test_SuperKBStore_kb_list(self):
        kb_list = SuperKBStore([ChromaKBStore("chroma_store", "knowledge_bases/chroma")]).list()
        self.assertEqual(4, (len(kb_list)))
        names = [x.name for x in kb_list if x is not None]
        self.assertIn("default", names)
        self.assertIn("test_chroma_kb", names)
        self.assertIn("name with spaces", names)
        self.assertIn("1234567890" * 100, names)
        full_names = [x.full_name for x in kb_list if x is not None]
        self.assertIn("chroma_store/default", full_names)
        self.assertIn("chroma_store/test_chroma_kb", full_names)
        self.assertIn("chroma_store/name with spaces", full_names)
        self.assertIn("chroma_store/" + ("1234567890" * 100), full_names)

    def test_SuperKBStore_get_existing(self):
        kb = SuperKBStore([ChromaKBStore("chroma_store", "knowledge_bases/chroma")]).get("test_chroma_kb")
        self.assertIsInstance(kb.kb, ChromaKnowledgeBase)
        self.assertEqual(kb.name, "test_chroma_kb")

    def test_SuperKBStore_get_existing_full_name(self):
        kb = SuperKBStore([ChromaKBStore("chroma_store", "knowledge_bases/chroma")]).get("chroma_store/test_chroma_kb")
        self.assertIsInstance(kb.kb, ChromaKnowledgeBase)
        self.assertEqual(kb.name, "test_chroma_kb")

    def test_SuperKBStore_get_none(self):
        kb = SuperKBStore([ChromaKBStore("chroma_store", "knowledge_bases/chroma")]).get("does_not_exist_kb")
        self.assertIsNone(kb)
        kb = SuperKBStore([ChromaKBStore("chroma_store", "knowledge_bases/chroma")]).get("chroma_store/does_not_exist_kb")
        self.assertIsNone(kb)

    def test_SuperKBStore_upsert(self):
        new_kb_config = {
            "name": "new_kb",
            "selection": [],
            "convertors": [{"model": "test_convertor"}],
            "embedding": {"model": "test_embedding"}
        }
        with_full_name = {**new_kb_config, "full_name": "chroma_store/new_kb"}

        kb_store = SuperKBStore([ChromaKBStore("chroma_store", "knowledge_bases/chroma")])
        kb_store.upsert(new_kb_config)
        new_kb = kb_store.get("new_kb")
        # noinspection PyTypeChecker
        inner: ChromaKnowledgeBase = new_kb.kb
        self.assertEqual(with_full_name, new_kb.to_dict())
        self.assertEqual(with_full_name, kb_store.get("chroma_store/new_kb").to_dict())
        self.assertIn(with_full_name, [kb.to_dict() for kb in kb_store.list()])
        self.assertIn("config.json", os.listdir(inner.base_path))

if __name__ == '__main__':
    unittest.main()