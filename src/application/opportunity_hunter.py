import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any
from src.domain.object import AionObject
from src.domain.event import Event
from src.infrastructure.external.rss_reader import read_rss
from src.infrastructure.external.github_issues import fetch_issues
from src.infrastructure.external.jobs_reader import read_jobs
from src.application.analyzer import OpportunityAnalyzer
from src.application.clustering import HypothesisClusterer
from src.application.market_estimator import MarketEstimator
from src.domain.payment import Invoice

logger = logging.getLogger(__name__)

class OpportunityHunter:
    """
    Агент для пошуку ринкових можливостей.
    """
    
    def __init__(self, storage, event_bus, rss_urls: List[str], github_repos: List[str], job_urls: List[str], 
                 analyzer: OpportunityAnalyzer, clusterer: HypothesisClusterer, market_estimator: MarketEstimator):
        self.storage = storage
        self.event_bus = event_bus
        self.rss_urls = rss_urls
        self.github_repos = github_repos
        self.job_urls = job_urls
        self.analyzer = analyzer
        self.clusterer = clusterer
        self.market_estimator = market_estimator

    async def scan(self):
        all_articles = []
        generated_hypotheses = []
        
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
        
        # 2. GitHub Issues
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
        
        # 3. Вакансії
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
        
        # 4. Аналіз
        if all_articles:
            logger.info(f"Analyzing {len(all_articles)} articles with LLM...")
            analysis_result = await self.analyzer.analyze(all_articles)
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
                    generated_hypotheses.append({
                        "id": obj.id,
                        "metadata": obj.metadata
                    })
                    invoice = Invoice(
                        object_id=obj.id,
                        amount=1.69,
                        currency="USD",
                        description=f"Validation payment for hypothesis: {problem.get('landing_headline', 'Untitled')}",
                        status="draft"
                    )
                    await self.storage.save_invoice(invoice)
                    logger.info(f"💰 Invoice created for hypothesis {obj.id}: ${invoice.amount}")
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
        
        # 5. Кластеризація та оцінка ринку
        if generated_hypotheses:
            logger.info(f"🔍 Clustering {len(generated_hypotheses)} hypotheses...")
            cluster_result = await self.clusterer.cluster_hypotheses(generated_hypotheses)
            if "clusters" in cluster_result:
                for cluster in cluster_result["clusters"]:
                    logger.info(f"📊 Cluster {cluster['id']}: {cluster['size']} hypotheses")
                    cluster_obj = AionObject(
                        type="Cluster",
                        metadata={
                            "cluster_id": cluster["id"],
                            "size": cluster["size"],
                            "center": cluster.get("center", ""),
                            "keywords": cluster.get("keywords", [])
                        }
                    )
                    await self.storage.save_object(cluster_obj)
                    
                    for hyp in cluster["hypotheses"]:
                        hyp_obj = await self.storage.get_object(hyp["id"])
                        if hyp_obj:
                            metadata = hyp_obj.get("metadata", {})
                            metadata["cluster_id"] = cluster["id"]
                            # Конвертуємо дати
                            created_at = datetime.fromisoformat(hyp_obj["created_at"]) if isinstance(hyp_obj.get("created_at"), str) else hyp_obj.get("created_at")
                            updated_at = datetime.fromisoformat(hyp_obj["updated_at"]) if isinstance(hyp_obj.get("updated_at"), str) else hyp_obj.get("updated_at")
                            temp_obj = AionObject(
                                id=hyp["id"],
                                type="Hypothesis",
                                metadata=metadata,
                                owner=hyp_obj.get("owner"),
                                created_at=created_at,
                                updated_at=updated_at,
                                permissions=hyp_obj.get("permissions", []),
                                lifecycle=hyp_obj.get("lifecycle", "active"),
                                history=hyp_obj.get("history", []),
                                telemetry=hyp_obj.get("telemetry", {})
                            )
                            await self.storage.save_object(temp_obj)
            
            logger.info("📈 Estimating market potential for hypotheses...")
            for hyp in generated_hypotheses:
                try:
                    estimation = await self.market_estimator.estimate(hyp["metadata"])
                    hyp_obj = await self.storage.get_object(hyp["id"])
                    if hyp_obj:
                        metadata = hyp_obj.get("metadata", {})
                        metadata["market_tam"] = estimation.get("tam", "unknown")
                        metadata["market_sam"] = estimation.get("sam", "unknown")
                        metadata["market_som"] = estimation.get("som", "unknown")
                        metadata["market_confidence"] = estimation.get("confidence", 0.0)
                        created_at = datetime.fromisoformat(hyp_obj["created_at"]) if isinstance(hyp_obj.get("created_at"), str) else hyp_obj.get("created_at")
                        updated_at = datetime.fromisoformat(hyp_obj["updated_at"]) if isinstance(hyp_obj.get("updated_at"), str) else hyp_obj.get("updated_at")
                        temp_obj = AionObject(
                            id=hyp["id"],
                            type="Hypothesis",
                            metadata=metadata,
                            owner=hyp_obj.get("owner"),
                            created_at=created_at,
                            updated_at=updated_at,
                            permissions=hyp_obj.get("permissions", []),
                            lifecycle=hyp_obj.get("lifecycle", "active"),
                            history=hyp_obj.get("history", []),
                            telemetry=hyp_obj.get("telemetry", {})
                        )
                        await self.storage.save_object(temp_obj)
                        logger.info(f"📈 Market estimation for {hyp['id']}: TAM={estimation.get('tam')}")
                except Exception as e:
                    logger.error(f"Failed to estimate market for {hyp['id']}: {e}")
        else:
            logger.info("No hypotheses generated, skipping clustering and market estimation")
