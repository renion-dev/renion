import uuid
import logging
from typing import List, Dict, Any
from src.domain.object import AionObject
from src.domain.event import Event
from src.infrastructure.external.rss_reader import read_rss
from src.infrastructure.external.github_issues import fetch_issues
from src.infrastructure.external.jobs_reader import read_jobs
from src.application.analyzer import OpportunityAnalyzer
from src.domain.payment import Invoice

logger = logging.getLogger(__name__)

class OpportunityHunter:
    """
    Агент для пошуку ринкових можливостей.
    Сканує RSS-стрічки, GitHub Issues та вакансії, накопичує статті, а потім аналізує через LLM.
    """
    
    def __init__(self, storage, event_bus, rss_urls: List[str], github_repos: List[str], job_urls: List[str], analyzer: OpportunityAnalyzer):
        self.storage = storage
        self.event_bus = event_bus
        self.rss_urls = rss_urls
        self.github_repos = github_repos
        self.job_urls = job_urls
        self.analyzer = analyzer

    async def scan(self):
        """Запускає сканування всіх джерел: RSS + GitHub Issues + Вакансії."""
        all_articles = []
        
        # 1. Скануємо RSS
        for url in self.rss_urls:
            logger.info(f"Scanning RSS: {url}")
            items = await read_rss(url)
            logger.info(f"Found {len(items)} items from {url}")
            
            for item in items:
                link = item.get("link")
                if link:
                    existing = await self.storage.get_object_by_metadata("link", link, "Article")
                    if existing:
                        logger.debug(f"Skipping duplicate article: {item.get('title')} ({link})")
                        continue
                
                item["source"] = url
                all_articles.append(item)
                
                obj = AionObject(type="Article", metadata=item)
                await self.storage.save_object(obj)
                
                event = Event(
                    id=str(uuid.uuid4()),
                    object_id=obj.id,
                    type="article_fetched",
                    payload={"article": item},
                    source="OpportunityHunter"
                )
                await self.event_bus.publish(event)
        
        # 2. Скануємо GitHub Issues
        for repo in self.github_repos:
            logger.info(f"Scanning GitHub Issues: {repo}")
            items = await fetch_issues(repo, limit=30)
            
            for item in items:
                link = item.get("html_url")
                if link:
                    existing = await self.storage.get_object_by_metadata("link", link, "Article")
                    if existing:
                        logger.debug(f"Skipping duplicate issue: {item.get('title')} ({link})")
                        continue
                
                body = item.get("body", "")[:300]
                comments = f"(Comments: {item.get('comments', 0)})"
                summary = f"{body} {comments}" if body else comments
                item["summary"] = summary
                
                all_articles.append(item)
                
                obj = AionObject(type="Article", metadata=item)
                await self.storage.save_object(obj)
                
                event = Event(
                    id=str(uuid.uuid4()),
                    object_id=obj.id,
                    type="article_fetched",
                    payload={"article": item},
                    source="OpportunityHunter"
                )
                await self.event_bus.publish(event)
        
        # 3. Скануємо вакансії
        for url in self.job_urls:
            logger.info(f"Scanning Jobs: {url}")
            items = await read_jobs(url, timeout=15)
            logger.info(f"Found {len(items)} jobs from {url}")
            
            for item in items:
                link = item.get("link")
                if link:
                    existing = await self.storage.get_object_by_metadata("link", link, "Article")
                    if existing:
                        logger.debug(f"Skipping duplicate job: {item.get('title')} ({link})")
                        continue
                
                # Формуємо текст для аналізу
                title = item.get("title", "")
                company = item.get("company", "")
                description = item.get("description", "")[:300]
                summary = f"Job: {title} at {company}. Description: {description}"
                item["summary"] = summary
                
                all_articles.append(item)
                
                obj = AionObject(type="Article", metadata=item)
                await self.storage.save_object(obj)
                
                event = Event(
                    id=str(uuid.uuid4()),
                    object_id=obj.id,
                    type="article_fetched",
                    payload={"article": item},
                    source="OpportunityHunter"
                )
                await self.event_bus.publish(event)
        
        # 4. Аналізуємо зібрані статті
        if all_articles:
            logger.info(f"Analyzing {len(all_articles)} articles with LLM...")
            analysis_result = await self.analyzer.analyze(all_articles)
            
            if "problems" in analysis_result:
                for problem in analysis_result["problems"]:
                    # Створюємо гіпотезу
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
                    
                    # Створюємо інвойс для гіпотези
                    invoice = Invoice(
                        object_id=obj.id,
                        amount=99.00,
                        currency="USD",
                        description=f"Validation payment for hypothesis: {problem.get('landing_headline', 'Untitled')}",
                        status="draft"
                    )
                    await self.storage.save_invoice(invoice)
                    logger.info(f"💰 Invoice created for hypothesis {obj.id}: ${invoice.amount}")
                    
                    # Публікуємо подію про гіпотезу
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
