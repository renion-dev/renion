import logging
import json
import re
from typing import List, Dict, Any, Optional
from src.domain.interfaces.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

class OpportunityAnalyzer:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def analyze(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not articles:
            return {"error": "No articles to analyze"}

        def get_sort_key(article):
            published = article.get("published", "")
            if published is None:
                return ""
            return str(published)

        sorted_articles = sorted(articles, key=get_sort_key, reverse=True)
        limited_articles = sorted_articles[:10]

        texts = []
        for a in limited_articles:
            title = a.get("title", "")
            summary = a.get("summary", "")[:300]
            if not summary:
                summary = title
            texts.append(f"Title: {title}\nSummary: {summary}")
        
        combined_text = "\n---\n".join(texts)
        
        system_prompt = (
            "You are an expert business analyst and startup founder. "
            "Your task is to find recurring problems and unmet needs from user discussions."
        )
        
        prompt = f"""
        Analyze the following articles and forum posts. They contain people's problems, complaints, and requests.
        
        {combined_text}
        
        Please:
        1. Identify the top 3 most common problems or unmet needs mentioned.
        2. For each problem, suggest a minimal viable product (MVP) as a short, clear paragraph (1-2 sentences).
        3. For each, propose a hypothesis to test: "If we build X, then Y people will pay Z price."
        4. Suggest a simple landing page headline and call-to-action.
        
        Output in JSON format:
        {{
          "problems": [
            {{
              "description": "Problem description",
              "frequency": "How often mentioned",
              "mvp": "A short description of the MVP",
              "hypothesis": "Hypothesis statement",
              "landing_headline": "Headline for landing page",
              "cta": "Call to action"
            }}
          ]
        }}
        """
        
        response = await self.llm.generate(prompt, system_prompt)
        result = self._try_parse_response(response)
        
        if "error" in result or "raw" in result:
            logger.info("Retrying with more specific JSON prompt...")
            retry_prompt = f"""
            Based on the following articles, return ONLY a valid JSON object with the structure:
            {{
              "problems": [
                {{
                  "description": "Problem description",
                  "frequency": "How often mentioned",
                  "mvp": "A short description of the MVP",
                  "hypothesis": "Hypothesis statement",
                  "landing_headline": "Headline for landing page",
                  "cta": "Call to action"
                }}
              ]
            }}
            
            Articles:
            {combined_text}
            """
            response = await self.llm.generate(retry_prompt, "Return only valid JSON.")
            result = self._try_parse_response(response)
        
        return result

    def _try_parse_response(self, text: str) -> Dict[str, Any]:
        if not text:
            return {"error": "Empty response from LLM"}
        
        try:
            data = json.loads(text)
            if "problems" in data:
                logger.info("✅ JSON parsed successfully")
                return data
        except json.JSONDecodeError:
            pass
        
        json_match = re.search(r'\{.*\n?\s*"problems".*\}', text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                logger.info("✅ JSON extracted from text")
                return data
            except json.JSONDecodeError:
                pass
        
        logger.warning("Could not parse LLM response")
        return {"raw": text, "error": "Parsing failed"}
