import uuid
import logging
from typing import List
from src.domain.object import AionObject
from src.domain.event import Event
from src.infrastructure.external.rss_reader import read_rss

logger = logging.getLogger(__name__)

class OpportunityHunter:
    """
    Агент для пошуку ринкових можливостей.
    Сканує RSS-стрічки, створює об'єкти Opportunity та публікує події.
    """
    
    def __init__(self, storage, event_bus, rss_urls: List[str]):
        self.storage = storage
        self.event_bus = event_bus
        self.rss_urls = rss_urls

    async def scan(self):
        """Запускає сканування всіх RSS-джерел."""
        for url in self.rss_urls:
            logger.info(f"Scanning {url}")
            items = await read_rss(url)
            logger.info(f"Found {len(items)} items from {url}")
            
            for item in items:
                # Перевіряємо, чи вже є такий об'єкт (за посиланням)
                # Поки просто створюємо новий, у майбутньому додамо дедуплікацію
                obj = AionObject(
                    type="Opportunity",
                    metadata={
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "summary": item.get("summary"),
                        "published": item.get("published"),
                        "source": item.get("source"),
                    }
                )
                await self.storage.save_object(obj)
                
                # Публікуємо подію про створення
                event = Event(
                    id=str(uuid.uuid4()),
                    object_id=obj.id,
                    type="opportunity_created",
                    payload={"object": obj.metadata},
                    source="OpportunityHunter"
                )
                await self.event_bus.publish(event)
