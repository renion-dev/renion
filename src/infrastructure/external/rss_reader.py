import asyncio
from typing import List, Dict

async def read_rss(url: str) -> List[Dict[str, str]]:
    """
    Заглушка для читання RSS.
    Повертає тестові дані для MVP.
    """
    await asyncio.sleep(0.1)  # Імітація мережевого запиту
    return [
        {
            "title": f"Opportunity from {url}",
            "link": "https://example.com/opportunity",
            "summary": "This is a test opportunity summary."
        }
    ]
