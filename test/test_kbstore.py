import os.path
import shutil
import unittest
from knowledge_base import SuperKBStore, ChromaKBStore, ChromaKnowledgeBase, KnowledgeBase


# Note: initializing SuperKBStore calls
class KBStoreTest(unittest.TestCase):
    def setUp(self):
        new_kb_path = "knowledge_bases/chroma/new_kb"
        if os.path.exists(new_kb_path):
            shutil.rmtree(new_kb_path)

    def tearDown(self):
        new_kb_path = "knowledge_bases/chroma/new_kb"
        if os.path.exists(new_kb_path):
            shutil.rmtree(new_kb_path)

    def test_SuperKBStore_kb_list(self):
        kb_list = SuperKBStore([ChromaKBStore("chroma_store", "knowledge_bases/chroma")]).kb_list
        self.assertEqual(2, (len(kb_list)))
        self.assertIn("test_chroma_kb", [x.name for x in kb_list if x is not None])

    def test_SuperKBStore_get_existing(self):
        kb = SuperKBStore([ChromaKBStore("chroma_store", "knowledge_bases/chroma")]).get("test_chroma_kb")
        self.assertTrue(isinstance(kb, ChromaKnowledgeBase))
        self.assertEqual(kb.name, "test_chroma_kb")

    def test_SuperKBStore_get_none(self):
        kb = SuperKBStore([ChromaKBStore("chroma_store", "knowledge_bases/chroma")]).get("does_not_exist_kb")
        self.assertIsNone(kb)

    def test_SuperKBStore_upsert(self):
        new_kb = KnowledgeBase.from_dict(
            {
                "name": "new_kb",
                "store": "chroma",
                "selection": [],
                "convertors": [{"model": "test_convertor"}],
                "embedding": {"model": "test_embedding"}
            }
        )
        kb_store = SuperKBStore([ChromaKBStore("chroma_store", "knowledge_bases/chroma")])
        kb_store.upsert(new_kb)
        self.assertIn(new_kb, kb_store.kb_list)
        self.assertIn("config.json", os.listdir("knowledge_bases/chroma/new_kb"))

if __name__ == '__main__':
    unittest.main()