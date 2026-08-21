from kb.knowledge_base import KnowledgeBase
from typing import Optional

class ChatContext:
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

class DocumentContext:
    def __init__(self, kb: KnowledgeBase):
        self.character_sets = kb.languages
