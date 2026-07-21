import asyncio
import logging
from src.infrastructure.storage import Storage
from src.infrastructure.event_bus import EventBus
from src.infrastructure.llm.ollama_client import OllamaClient
from src.application.opportunity_hunter import OpportunityHunter
from src.application.handlers import log_opportunity
from src.application.analyzer import OpportunityAnalyzer
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
    
    asyncio.create_task(event_bus.run())
    
    # Підключення до Ollama
    ollama = OllamaClient()
    connected = await ollama.check_connection()
    if not connected:
        logger.warning("Ollama not connected. Please start Ollama and install model llama3:latest")
    
    # СТВОРЮЄМО АНАЛІЗАТОР
    analyzer = OpportunityAnalyzer(ollama)
    
    # ПЕРЕДАЄМО АНАЛІЗАТОР, а не ollama
    hunter = OpportunityHunter(storage, event_bus, RSS_SOURCES, analyzer)
    await hunter.scan()
    
    print("✅ Scan and analysis complete. Objects saved in aion.db")
    
    await asyncio.sleep(1)
    await storage.close()

if __name__ == "__main__":
    asyncio.run(main())
