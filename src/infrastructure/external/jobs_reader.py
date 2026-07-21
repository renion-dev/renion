import asyncio
import feedparser
import logging
from typing import List, Dict, Any
import aiohttp

logger = logging.getLogger(__name__)

async def read_jobs(url: str, timeout: int = 15) -> List[Dict[str, Any]]:
    """
    Асинхронно читає RSS-стрічку вакансій з User-Agent та повертає список записів.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout, headers=headers) as resp:
                if resp.status != 200:
                    logger.warning(f"Job feed returned status {resp.status} for {url}")
                    return []
                
                content = await resp.text()
                # Обробляємо потенційно некоректний XML
                feed_data = feedparser.parse(content)
                
                if feed_data.bozo:
                    logger.warning(f"Job feed parse warning for {url}: {feed_data.bozo_exception}")
                    # Якщо парсинг невдалий, можна спробувати витягти хоча б частину даних
                    # Але поки повертаємо порожній список
                    return []
                
                entries = []
                for entry in feed_data.entries[:10]:
                    company = entry.get("author", "")
                    if not company and "description" in entry:
                        # Можна спробувати знайти компанію в описі, але поки пропускаємо
                        pass
                    
                    entries.append({
                        "title": entry.get("title", "No title"),
                        "description": entry.get("description", entry.get("summary", "No description")),
                        "company": company,
                        "link": entry.get("link", ""),
                        "published": entry.get("published", entry.get("updated", "")),
                        "source": url,
                        "type": "job"
                    })
                return entries
    except asyncio.TimeoutError:
        logger.error(f"Timeout reading job feed {url}")
        return []
    except Exception as e:
        logger.error(f"Error reading job feed {url}: {e}")
        return []
