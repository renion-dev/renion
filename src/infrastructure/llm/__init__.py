import os
from dotenv import load_dotenv
from src.infrastructure.llm.ollama_provider import OllamaProvider
from src.infrastructure.llm.groq_provider import GroqProvider

load_dotenv()

def get_llm_provider():
    provider = os.getenv("LLM_PROVIDER", "ollama")
    if provider == "groq":
        return GroqProvider()
    else:
        return OllamaProvider()
