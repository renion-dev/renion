import asyncio
import logging
from src.infrastructure.storage import Storage
from src.infrastructure.event_bus import EventBus
from src.infrastructure.llm.ollama_client import OllamaClient
from src.application.opportunity_hunter import OpportunityHunter
from src.application.handlers import log_opportunity, generate_landing_for_hypothesis
from src.application.analyzer import OpportunityAnalyzer
from src.application.landing_generator import LandingGenerator
from src.config import RSS_SOURCES

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
    
    ollama = OllamaClient()
    available = await ollama.is_available()
    if not available:
        logger.warning("⚠️ Ollama not available. Please start Ollama and install model llama3:latest")
    else:
        logger.info("✅ Ollama available")
    
    analyzer = OpportunityAnalyzer(ollama)
    generator = LandingGenerator(ollama)
    
    async def landing_handler(event):
        await generate_landing_for_hypothesis(event, generator)
    
    event_bus.subscribe("hypothesis_generated", landing_handler)
    
    asyncio.create_task(event_bus.run())
    
    hunter = OpportunityHunter(storage, event_bus, RSS_SOURCES, analyzer)
    await hunter.scan()
    
    # Чекаємо завершення обробки всіх подій (включно з генерацією лендингів)
    await event_bus.queue.join()
    
    print("✅ Scan and analysis complete. Objects saved in aion.db")
    await storage.close()

if __name__ == "__main__":
    asyncio.run(main())
