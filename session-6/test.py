from langchain_ollama import ChatOllama
import os
from dotenv import load_dotenv

load_dotenv()

base_url = os.getenv("BASE_URL_OLLAMA")
print("Base URL:", base_url)

llm = ChatOllama(
    model="kimi-k2.5:cloud",
    base_url=base_url
)

# This will now successfully call the Ollama server
response = llm.invoke("Hello! Can you tell me one interesting fact about GIT?")
print("Model response:", response.content)
