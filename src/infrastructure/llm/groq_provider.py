import os
import groq
import logging
from typing import Optional
from dotenv import load_dotenv
from src.domain.interfaces.llm_provider import LLMProvider

load_dotenv()
logger = logging.getLogger(__name__)

class GroqProvider(LLMProvider):
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = model
        self._available = False
        self._client = None
        if self.api_key:
            try:
                self._client = groq.Groq(api_key=self.api_key)
                self._available = True
                logger.info(f"✅ Groq client initialized (model: {self.model})")
            except Exception as e:
                logger.error(f"Groq init error: {e}")
        else:
            logger.warning("⚠️ GROQ_API_KEY not set")

    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        if not self._available:
            logger.error("Groq not available")
            return ""
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq generation error: {e}")
            return ""

    async def is_available(self) -> bool:
        return self._available
