import unittest
import rag_processor
import os
import shutil
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

LLM_MODEL = 'qwen2.5'
EMBEDDING_MODEL = 'bge-m3'

class FakeArgs:
    def __init__(self, llm_model, embedding_model, chroma_path, document_path, rework):
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.chroma_path = chroma_path
        self.document_path = document_path
        self.rework = rework

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        db_path = "test/chroma"
        if os.path.exists(db_path):
            shutil.rmtree(db_path)

    def test_process(self):
        chroma_path = "test/chroma"
        rag_processor.main(FakeArgs(LLM_MODEL, EMBEDDING_MODEL, chroma_path, 'test/text', rework=True))
        db_folder = os.path.join(chroma_path, EMBEDDING_MODEL)
        embeddings = OllamaEmbeddings(temperature=0.7, model=EMBEDDING_MODEL)
        vector_store = Chroma(persist_directory=db_folder, embedding_function=embeddings)

        results = vector_store.similarity_search_with_score(
            "What is a duck?", k=2,
        )
        print(len(results))
        for doc, score in results:
            print(doc, score)
            self.assertTrue("duck" in doc.page_content or "Duck" in doc.page_content)

if __name__ == '__main__':
    unittest.main()
