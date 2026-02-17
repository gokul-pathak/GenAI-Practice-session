from langchain_ollama import OllamaEmbeddings
import os

base_url = os.getenv("BASE_URL_OLLAMA", "http://localhost:11434")

embeddings = OllamaEmbeddings(
    model="qwen3-embedding:0.6b",
    base_url=base_url
)
