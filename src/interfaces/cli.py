import asyncio
import logging
from src.infrastructure.storage import Storage
from src.infrastructure.event_bus import EventBus
from src.infrastructure.llm import get_llm_provider
from src.application.opportunity_hunter import OpportunityHunter
from src.application.handlers import log_opportunity, generate_landing_for_hypothesis
from src.application.analyzer import OpportunityAnalyzer
from src.application.clustering import HypothesisClusterer
from src.application.market_estimator import MarketEstimator
from src.application.landing_generator import LandingGenerator
from src.application.advertising import AdvertisingManager
from src.application.social_post_manager import SocialPostManager
from src.infrastructure.social.twitter_poster import TwitterPoster
from src.infrastructure.social.mastodon_poster import MastodonPoster
from src.infrastructure.social.reddit_poster import RedditPoster
from src.infrastructure.social.hackernews_poster import HackerNewsPoster
from src.infrastructure.social.medium_poster import MediumPoster
from src.config import RSS_SOURCES, GITHUB_REPOS, JOB_RSS_SOURCES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    storage = Storage("aion.db")
    await storage.init()
    
    event_bus = EventBus(storage)
    event_bus.subscribe("opportunity_created", log_opportunity)
    event_bus.subscribe("hypothesis_generated", log_opportunity)
    
    ollama = get_llm_provider()
    available = await ollama.is_available()
    if not available:
        logger.warning("⚠️ Ollama not available. Please start Ollama and install model llama3:latest")
    else:
        logger.info("✅ Ollama available")
    
    analyzer = OpportunityAnalyzer(ollama)
    generator = LandingGenerator(ollama)
    advertiser = AdvertisingManager(storage, event_bus)
    clusterer = HypothesisClusterer()
    market_estimator = MarketEstimator(ollama)
    
    # Соціальні постери (всі dry-run)
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
    
    print("✅ Scan and analysis complete. Objects saved in aion.db")
    await storage.close()

if __name__ == "__main__":
    asyncio.run(main())
