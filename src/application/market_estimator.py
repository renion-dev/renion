import logging
from typing import Dict, Any, Optional
from src.domain.interfaces.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

class MarketEstimator:
    """Оцінює TAM/SAM/SOM для гіпотези за допомогою LLM."""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def estimate(self, hypothesis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Оцінює потенціал ринку для гіпотези.
        Повертає: {"tam": "$X", "sam": "$Y", "som": "$Z", "confidence": 0.8}
        """
        problem = hypothesis_data.get("problem", "")
        mvp = hypothesis_data.get("mvp", "")
        frequency = hypothesis_data.get("frequency", "unknown")
        
        prompt = f"""
        Оціни ринковий потенціал для наступної гіпотези:
        
        Проблема: {problem}
        MVP: {mvp}
        Частота згадувань: {frequency}
        
        Поверни JSON з наступними полями:
        - tam (Total Addressable Market) — загальний обсяг ринку в доларах США
        - sam (Serviceable Addressable Market) — доступна частина ринку
        - som (Serviceable Obtainable Market) — реально досяжна частка
        - confidence — впевненість у оцінці (0-1)
        
        Відповідай лише JSON.
        """
        
        system_prompt = "Ти експерт з оцінки ринків та стартапів. Відповідай лише JSON без зайвих пояснень."
        
        response = await self.llm.generate(prompt, system_prompt)
        
        if not response:
            return {
                "tam": "unknown",
                "sam": "unknown",
                "som": "unknown",
                "confidence": 0.0,
                "error": "No response from LLM"
            }
        
        try:
            import json
            data = json.loads(response)
            return {
                "tam": data.get("tam", "unknown"),
                "sam": data.get("sam", "unknown"),
                "som": data.get("som", "unknown"),
                "confidence": data.get("confidence", 0.5)
            }
        except json.JSONDecodeError:
            logger.warning("Could not parse market estimation response")
            return {
                "tam": "unknown",
                "sam": "unknown",
                "som": "unknown",
                "confidence": 0.0,
                "raw_response": response[:200]
            }
