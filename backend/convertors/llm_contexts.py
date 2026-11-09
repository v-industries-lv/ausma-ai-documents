from kb.knowledge_base import KnowledgeBase
from typing import List


class ChatContext:
    def __init__(self, knowledge_bases: List[KnowledgeBase]):
        self.knowledge_bases = knowledge_bases

class DocumentContext:
    def __init__(self, kb: KnowledgeBase):
        self.character_sets = kb.languages
