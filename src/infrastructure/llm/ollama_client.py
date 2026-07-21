import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class OllamaClient:
    """Клієнт для роботи з локальним Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3", timeout: int = 300):
        self.base_url = base_url
        self.model = model
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Генерує відповідь на основі промпту."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(f"{self.base_url}/api/generate", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("response", "")
                    else:
                        error_text = await resp.text()
                        logger.error(f"Ollama API error: {resp.status} - {error_text}")
                        return ""
        except asyncio.TimeoutError:
            logger.error("Ollama API timeout")
            return ""
        except Exception as e:
            logger.error(f"Ollama API exception: {e}")
            return ""

    async def generate_with_context(self, prompt: str, context: str, system: Optional[str] = None) -> str:
        """Генерує відповідь з контекстом (передає його в промпт)."""
        full_prompt = f"Context: {context}\n\n{prompt}"
        return await self.generate(full_prompt, system)

    async def is_available(self) -> bool:
        """Перевіряє доступність Ollama API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    return resp.status == 200
        except:
            return False
