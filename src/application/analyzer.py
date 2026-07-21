import logging
from typing import List, Dict, Any
from src.infrastructure.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class OpportunityAnalyzer:
    """Аналізує зібрані статті, виявляє проблеми та генерує гіпотези."""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client

    async def analyze(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Аналізує список статей, виділяє повторювані проблеми,
        групує їх і генерує гіпотези для стартапів.
        """
        if not articles:
            return {"error": "No articles to analyze"}

        # Підготовка даних: об'єднуємо заголовки та описи
        texts = []
        for a in articles:
            title = a.get("title", "")
            summary = a.get("summary", "")
            texts.append(f"Title: {title}\nSummary: {summary[:200]}")
        
        combined_text = "\n---\n".join(texts)
        
        # Промпт для LLM
        system_prompt = (
            "You are an expert business analyst and startup founder. "
            "Your task is to find recurring problems and unmet needs from user discussions. "
            "For each problem, propose a simple MVP solution and a hypothesis for validation."
        )
        
        prompt = f"""
        Analyze the following articles and forum posts. They contain people's problems, complaints, and requests.
        
        {combined_text}
        
        Please:
        1. Identify the top 3 most common problems or unmet needs mentioned.
        2. For each problem, suggest a minimal viable product (MVP) that could solve it.
        3. For each, propose a hypothesis to test: "If we build X, then Y people will pay Z price."
        4. Suggest a simple landing page headline and call-to-action.
        
        Output in JSON format:
        {{
          "problems": [
            {{
              "description": "Problem description",
              "frequency": "How often mentioned",
              "mvp": "MVP idea",
              "hypothesis": "Hypothesis statement",
              "landing_headline": "Headline for landing page",
              "cta": "Call to action"
            }}
          ]
        }}
        """
        
        response = await self.ollama.generate(prompt, system_prompt)
        if response:
            try:
                import json
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                logger.warning("LLM response not valid JSON, returning raw text")
                return {"raw": response}
        return {"error": "No response from Ollama"}
