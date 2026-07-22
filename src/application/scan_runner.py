import asyncio
import logging
from src.infrastructure.storage import Storage
from src.infrastructure.event_bus import EventBus
from src.infrastructure.llm.ollama_client import OllamaClient
from src.application.opportunity_hunter import OpportunityHunter
from src.application.handlers import log_opportunity, generate_landing_for_hypothesis
from src.application.analyzer import OpportunityAnalyzer
from src.application.landing_generator import LandingGenerator
from src.application.advertising import AdvertisingManager
from src.application.social_post_manager import SocialPostManager
from src.application.clustering import HypothesisClusterer
from src.application.market_estimator import MarketEstimator
from src.infrastructure.social.twitter_poster import TwitterPoster
from src.infrastructure.social.mastodon_poster import MastodonPoster
from src.infrastructure.social.reddit_poster import RedditPoster
from src.infrastructure.social.hackernews_poster import HackerNewsPoster
from src.infrastructure.social.medium_poster import MediumPoster
from src.config import RSS_SOURCES, GITHUB_REPOS, JOB_RSS_SOURCES

logger = logging.getLogger(__name__)

async def run_scan(storage: Storage):
    """Запускає сканування з повним набором обробників (для CLI та веб)."""
    event_bus = EventBus(storage)
    event_bus.subscribe("opportunity_created", log_opportunity)
    event_bus.subscribe("hypothesis_generated", log_opportunity)
    
    ollama = OllamaClient()
    await ollama.is_available()
    
    analyzer = OpportunityAnalyzer(ollama)
    generator = LandingGenerator(ollama)
    advertiser = AdvertisingManager(storage, event_bus)
    clusterer = HypothesisClusterer()
    market_estimator = MarketEstimator(ollama)
    
    twitter_poster = TwitterPoster()
    mastodon_poster = MastodonPoster()
    reddit_poster = RedditPoster()
    hackernews_poster = HackerNewsPoster()
    medium_poster = MediumPoster()
    social_manager = SocialPostManager(storage, [
        twitter_poster,
        mastodon_poster,
        reddit_poster,
        hackernews_poster,
        medium_poster
    ])
    
    async def landing_handler(event):
        await generate_landing_for_hypothesis(event, generator)
    
    async def ad_handler(event):
        if event.type == "hypothesis_generated":
            hypothesis_id = event.object_id
            hypothesis_data = event.payload
            hypothesis_data["landing_url"] = f"/landings/{hypothesis_id}.html"
            await advertiser.launch_campaign(hypothesis_id, hypothesis_data)
    
    async def social_handler(event):
        if event.type == "hypothesis_generated":
            hypothesis_id = event.object_id
            hypothesis_data = event.payload
            hypothesis_data["landing_url"] = f"/landings/{hypothesis_id}.html"
            await social_manager.post_hypothesis(hypothesis_id, hypothesis_data)
    
    event_bus.subscribe("hypothesis_generated", landing_handler)
    event_bus.subscribe("hypothesis_generated", ad_handler)
    event_bus.subscribe("hypothesis_generated", social_handler)
    
    asyncio.create_task(event_bus.run())
    
    hunter = OpportunityHunter(
        storage, event_bus, RSS_SOURCES, GITHUB_REPOS, JOB_RSS_SOURCES,
        analyzer, clusterer, market_estimator
    )
    await hunter.scan()
    
    await event_bus.queue.join()
    logger.info("✅ Scan completed")
