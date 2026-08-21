import unittest
from assistants.assistant import AssistantRagModule
from langchain_ollama import OllamaEmbeddings

from test.llm_environment import get_embeddings

OLLAMA_EMBEDDINGS = get_embeddings("bge-m3")


class AssistantRagModuleTest(unittest.TestCase):
    def test_rag_module(self):
        # Original query "What does the duck do?"
        documents = [
            {"similarity_score": 0.44706198, "content": "The yellow duck paddled slowly across the quiet pond, leaving gentle ripples in the water that shimmered under the morning sun."},
            {"similarity_score": 0.4437142, "content": "The yellow duck paddled gently across the quiet pond, creating soft ripples in the water that glistened as the sunlight touched the surface."},
            {"similarity_score": 0.47103302, "content": "A group of ducks gathered near the tall reeds along the pond’s edge, quacking excitedly at the warm glow of the morning sun."},
            {"similarity_score": 0.50994284, "content": "The fluffy ducklings followed closely behind their mother in a neat line across the calm lake, occasionally dipping their heads to nibble at floating leaves."},
            {"similarity_score": 0.66728379, "content": "The wetlands were calm at dawn, filled with distant bird calls, soft ripples across the water, and the faint rustling of reeds in the cool morning breeze."},
        ]
        rag_module = AssistantRagModule.from_settings(
            {
                "rag_document_count": 20,
                "rag_similarity_score_threshold": 0.8,
                "rag_score_margin": 0.2,
                "rag_cosine_distance_irrelevance_threshold": 1.0
            }
        )
        result = rag_module.filter_relevant_documents(documents, embedding=OLLAMA_EMBEDDINGS)
        self.assertEqual(3, len(result))

    def test_rag_module_irrelevant_documents(self):
        documents = [
            {"similarity_score": 1.1, "content": "[Irrelevant piece of text]"},
            {"similarity_score": 1.1, "content": "[Irrelevant piece of text]"},
            {"similarity_score": 1.1, "content": "[Irrelevant piece of text]"},
            {"similarity_score": 1.1, "content": "[Irrelevant piece of text]"},
            {"similarity_score": 1.1, "content": "[Irrelevant piece of text]"},
        ]
        rag_module = AssistantRagModule.from_settings(
            {
                "rag_document_count": 20,
                "rag_similarity_score_threshold": 0.8,
                "rag_score_margin": 0.2,
                "rag_cosine_distance_irrelevance_threshold": 1.0
            }
        )
        result = rag_module.filter_relevant_documents(documents, embedding=OLLAMA_EMBEDDINGS)
        self.assertEqual(0, len(result))

    def test_rag_module_empty(self):
        documents = []
        rag_module = AssistantRagModule.from_settings(
            {
                "rag_document_count": 20,
                "rag_similarity_score_threshold": 0.8,
                "rag_score_margin": 0.2,
                "rag_cosine_distance_irrelevance_threshold": 1.0
            }
        )
        result = rag_module.filter_relevant_documents(documents, embedding=OLLAMA_EMBEDDINGS)
        self.assertEqual(0, len(result))
if __name__ == '__main__':
    unittest.main()
