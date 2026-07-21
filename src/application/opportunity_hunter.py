import uuid
from src.domain.object import AionObject
from src.domain.event import Event
from src.infrastructure.external.rss_reader import read_rss

class OpportunityHunter:
    """
    Агент для пошуку ринкових можливостей.
    Сканує RSS-стрічки, створює об'єкти Opportunity та публікує події.
    """
    
    def __init__(self, storage, event_bus, rss_urls):
        self.storage = storage
        self.event_bus = event_bus
        self.rss_urls = rss_urls

    async def scan(self):
        """Запускає сканування всіх RSS-джерел."""
        for url in self.rss_urls:
            items = await read_rss(url)
            for item in items:
                # Створюємо об'єкт Opportunity
                obj = AionObject(
                    type="Opportunity",
                    metadata={
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "summary": item.get("summary"),
                        "source": url,
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
