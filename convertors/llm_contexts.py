from knowledge_base import KnowledgeBase


class ChatContext:
    def __init__(self, llm_model: str, system_prompt: str, rag_document_count: int, kb: KnowledgeBase):
        self.llm_model = llm_model
        self.system_prompt = system_prompt
        self.rag_document_count = rag_document_count
        self.kb = kb

class DocumentContext:
    def __init__(self, kb: KnowledgeBase):
        self.character_sets = kb.languages
