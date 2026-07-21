import uuid
import logging
from typing import List, Dict, Any
from src.domain.object import AionObject
from src.domain.event import Event
from src.infrastructure.external.rss_reader import read_rss
from src.application.analyzer import OpportunityAnalyzer

logger = logging.getLogger(__name__)

class OpportunityHunter:
    """
    Агент для пошуку ринкових можливостей.
    Сканує RSS-стрічки, накопичує статті, а потім аналізує через LLM.
    """
    
    def __init__(self, storage, event_bus, rss_urls: List[str], analyzer: OpportunityAnalyzer):
        self.storage = storage
        self.event_bus = event_bus
        self.rss_urls = rss_urls
        self.analyzer = analyzer

    async def scan(self):
        """Запускає сканування всіх RSS-джерел, збирає статті та аналізує."""
        all_articles = []
        
        for url in self.rss_urls:
            logger.info(f"Scanning {url}")
            items = await read_rss(url)
            logger.info(f"Found {len(items)} items from {url}")
            
            for item in items:
                # Перевіряємо дублікат за посиланням
                link = item.get("link")
                if link:
                    existing = await self.storage.get_object_by_metadata("link", link, "Article")
                    if existing:
                        logger.debug(f"Skipping duplicate article: {item.get('title')} ({link})")
                        continue
                
                # Додаємо джерело до метаданих
                item["source"] = url
                all_articles.append(item)
                
                # Створюємо об'єкт Article
                obj = AionObject(
                    type="Article",
                    metadata=item
                )
                await self.storage.save_object(obj)
                
                # Подія про нову статтю
                event = Event(
                    id=str(uuid.uuid4()),
                    object_id=obj.id,
                    type="article_fetched",
                    payload={"article": item},
                    source="OpportunityHunter"
                )
                await self.event_bus.publish(event)
        
        # Після збору всіх статей - аналізуємо
        if all_articles:
            logger.info(f"Analyzing {len(all_articles)} articles with LLM...")
            analysis_result = await self.analyzer.analyze(all_articles)
            
            # Створюємо об'єкт Opportunity (гіпотезу) на основі аналізу
            if "problems" in analysis_result:
                for problem in analysis_result["problems"]:
                    obj = AionObject(
                        type="Hypothesis",
                        metadata={
                            "problem": problem.get("description"),
                            "frequency": problem.get("frequency"),
                            "mvp": problem.get("mvp"),
                            "hypothesis": problem.get("hypothesis"),
                            "landing_headline": problem.get("landing_headline"),
                            "cta": problem.get("cta"),
                        }
                    )
                    await self.storage.save_object(obj)
                    
                    event = Event(
                        id=str(uuid.uuid4()),
                        object_id=obj.id,
                        type="hypothesis_generated",
                        payload=problem,
                        source="OpportunityHunter"
                    )
                    await self.event_bus.publish(event)
                    logger.info(f"✅ Hypothesis generated: {problem.get('description', '')[:100]}...")
            else:
                logger.warning("No problems found in analysis result")
        else:
            logger.info("No new articles collected, skipping analysis")
