from kb.knowledge_base import KnowledgeBase


class ChatContext:
    def __init__(self, llm_model: str, system_prompt: str, kb: KnowledgeBase):
        self.llm_model = llm_model
        self.system_prompt = system_prompt
        self.kb = kb

class DocumentContext:
    def __init__(self, kb: KnowledgeBase):
        self.character_sets = kb.languages
