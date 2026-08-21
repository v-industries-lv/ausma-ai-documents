import os

from langchain_ollama import OllamaEmbeddings

from llm_runners.ollama_runner import OllamaRunner

ollama_host = os.environ.get('TEST_OLLAMA_HOST', "http://localhost:11434")
def get_llm_runner():
    return OllamaRunner.from_dict({"type": "ollama", "host": ollama_host})

def get_embeddings(model):
    return OllamaEmbeddings(model=model, base_url=ollama_host)