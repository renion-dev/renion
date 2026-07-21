import logging
import json
import re
from typing import List, Dict, Any, Optional
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

        # Обмежуємо кількість статей до 10 найновіших
        def get_sort_key(article):
            published = article.get("published", "")
            if published is None:
                return ""
            return str(published)

        sorted_articles = sorted(articles, key=get_sort_key, reverse=True)
        limited_articles = sorted_articles[:10]

        # Підготовка даних: об'єднуємо заголовки та скорочені описи
        texts = []
        for a in limited_articles:
            title = a.get("title", "")
            summary = a.get("summary", "")[:300]
            if not summary:
                summary = title
            texts.append(f"Title: {title}\nSummary: {summary}")
        
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
        
        # Перша спроба
        response = await self.ollama.generate(prompt, system_prompt)
        result = self._try_parse_response(response)
        
        # Якщо не вдалося — спроба з іншим промптом
        if "error" in result or "raw" in result:
            logger.info("Retrying with more specific JSON prompt...")
            retry_prompt = f"""
            Based on the following articles, return ONLY a valid JSON object with the structure:
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
            
            Articles:
            {combined_text}
            """
            response = await self.ollama.generate(retry_prompt, "Return only valid JSON.")
            result = self._try_parse_response(response)
        
        return result

    def _try_parse_response(self, text: str) -> Dict[str, Any]:
        """Спроба розпарсити відповідь з підтримкою різних форматів."""
        if not text:
            return {"error": "Empty response from LLM"}
        
        # Спроба 1: прямий JSON
        try:
            data = json.loads(text)
            if "problems" in data:
                logger.info("✅ JSON parsed successfully")
                return data
        except json.JSONDecodeError:
            pass
        
        # Спроба 2: пошук JSON-блоку
        json_match = re.search(r'\{.*\n?\s*"problems".*\}', text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                logger.info("✅ JSON extracted from text")
                return data
            except json.JSONDecodeError:
                pass
        
        # Спроба 3: резервний парсинг
        logger.info("Falling back to regex parsing")
        parsed = self._fallback_parse(text)
        if parsed:
            return parsed
        
        # Якщо нічого не спрацювало
        logger.warning("Could not parse LLM response")
        return {"raw": text, "error": "Parsing failed"}

    def _fallback_parse(self, text: str) -> Optional[Dict[str, Any]]:
        """Резервний парсинг через регулярні вирази."""
        problems = []
        # Шукаємо блоки, які починаються з "Problem:" або "1.", "2." тощо
        # Спрощений підхід: шукаємо ключові слова
        problem_blocks = re.split(r'(?:\d+\.\s*|Problem:?\s*)', text)
        for block in problem_blocks:
            if not block.strip():
                continue
            # Шукаємо поля
            desc_match = re.search(r'(?:description|problem|issue)[\s:]+(.+?)(?=\s*(?:mvp|hypothesis|landing|cta|$))', block, re.IGNORECASE)
            mvp_match = re.search(r'(?:mvp|solution)[\s:]+(.+?)(?=\s*(?:hypothesis|landing|cta|$))', block, re.IGNORECASE)
            hypo_match = re.search(r'(?:hypothesis|test)[\s:]+(.+?)(?=\s*(?:landing|cta|$))', block, re.IGNORECASE)
            head_match = re.search(r'(?:landing headline|headline)[\s:]+(.+?)(?=\s*(?:cta|$))', block, re.IGNORECASE)
            cta_match = re.search(r'(?:cta|call to action)[\s:]+(.+?)(?=\s*$)', block, re.IGNORECASE)
            
            if desc_match or mvp_match or hypo_match:
                problems.append({
                    "description": desc_match.group(1).strip() if desc_match else "Not found",
                    "mvp": mvp_match.group(1).strip() if mvp_match else "Not found",
                    "hypothesis": hypo_match.group(1).strip() if hypo_match else "Not found",
                    "landing_headline": head_match.group(1).strip() if head_match else "Not found",
                    "cta": cta_match.group(1).strip() if cta_match else "Not found"
                })
        
        if problems:
            logger.info(f"✅ Fallback parsing found {len(problems)} problems")
            return {"problems": problems}
        return None
