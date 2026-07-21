import asyncio
import feedparser
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

async def read_rss(url: str, timeout: int = 10) -> List[Dict[str, Any]]:
    """
    Асинхронно читає RSS/Atom стрічку та повертає список записів.
    Кожен запис містить: title, link, summary, published, source.
    """
    try:
        # feedparser робить синхронний запит, обгортаємо в asyncio.to_thread
        feed_data = await asyncio.to_thread(feedparser.parse, url)
        
        if feed_data.bozo:  # якщо є помилка парсингу
            logger.warning(f"Feed parse warning for {url}: {feed_data.bozo_exception}")
            return []
        
        entries = []
        for entry in feed_data.entries[:10]:  # обмежуємо до 10 записів на стрічку
            entries.append({
                "title": entry.get("title", "No title"),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", entry.get("description", "No summary")),
                "published": entry.get("published", entry.get("updated", "")),
                "source": url,
            })
        return entries
    except Exception as e:
        logger.error(f"Error reading feed {url}: {e}")
        return []
