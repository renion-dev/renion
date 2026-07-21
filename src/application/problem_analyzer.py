import logging
import json
from typing import List, Dict, Any
from src.infrastructure.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class ProblemAnalyzer:
    """Аналізує тексти з джерел, виявляє проблеми та болі користувачів."""
    
    def __init__(self, llm_client: OllamaClient):
        self.llm = llm_client

    async def analyze_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Аналізує список записів (з RSS) та повертає структуровані проблеми.
        Кожен запис — це словник з title, summary, link, source.
        """
        if not entries:
            return []
        
        # Формуємо промпт для аналізу
        prompt = self._build_analysis_prompt(entries)
        system_prompt = """Ти — аналітик ринку. Твоє завдання — виявити проблеми, про які пишуть люди.
        З кожного тексту виділи:
        1. Проблему (одним реченням)
        2. Біль (наскільки це важливо для людей)
        3. Цільову аудиторію
        
        Відповідай у форматі JSON: список об'єктів з полями problem, pain_level (1-10), audience.
        """
        
        response = await self.llm.generate(prompt, system_prompt)
        
        # Парсимо відповідь (очікуємо JSON)
        try:
            problems = json.loads(response)
            if isinstance(problems, list):
                return problems
            else:
                logger.warning("LLM відповів не списком")
                return []
        except json.JSONDecodeError:
            # Якщо не вдалося розпарсити, логуємо і повертаємо порожній список
            logger.warning(f"Не вдалося розпарсити JSON з LLM: {response[:200]}...")
            return []

    def _build_analysis_prompt(self, entries: List[Dict]) -> str:
        """Формує промпт з записів."""
        texts = []
        for i, entry in enumerate(entries[:20], 1):  # обмежуємо до 20 записів на аналіз
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            texts.append(f"{i}. Title: {title}\n   Summary: {summary}")
        
        return f"Проаналізуй наступні тексти та вияви проблеми:\n\n" + "\n".join(texts)
