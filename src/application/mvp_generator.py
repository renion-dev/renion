import logging
from typing import Dict, Any
from src.infrastructure.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class MVPGenerator:
    """Генерує опис MVP та лендинг на основі виявленої проблеми."""
    
    def __init__(self, llm_client: OllamaClient):
        self.llm = llm_client

    async def generate_mvp_description(self, problem: str) -> str:
        """Генерує опис MVP для вирішення проблеми."""
        prompt = f"""
Проблема: {problem}

Завдання: Запропонуй мінімально життєздатний продукт (MVP), який вирішує цю проблему.
Опиши MVP у 3-5 реченнях. Які основні функції має мати MVP?
Відповідь має бути конкретною, без загальних фраз.
"""
        system_prompt = "Ти — продуктовий менеджер, що пропонує MVP для стартапів."
        return await self.llm.generate(prompt, system_prompt, temperature=0.8)

    async def generate_landing_page(self, problem: str, mvp_description: str) -> str:
        """Генерує HTML-код лендингу для MVP."""
        prompt = f"""
Проблема: {problem}
MVP: {mvp_description}

Створи простий лендинг у вигляді HTML/CSS коду, який:
- Має заголовок, що привертає увагу
- Описує проблему
- Пропонує рішення (MVP)
- Містить форму для збору email (заглушка)
- Стилізований сучасно (використовуй шрифти, кольори)

Поверни повний HTML код.
"""
        system_prompt = "Ти — веб-дизайнер, що створює лендинги для стартапів."
        return await self.llm.generate(prompt, system_prompt, temperature=0.9)
