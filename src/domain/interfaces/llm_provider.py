from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class LLMProvider(ABC):
    """Абстракція для будь-якого LLM-провайдера (Ollama, Groq, OpenAI тощо)."""
    
    @abstractmethod
    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Генерує відповідь на основі промпту."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Перевіряє доступність провайдера."""
        pass
