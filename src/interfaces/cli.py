import asyncio
import logging
from src.infrastructure.storage import Storage
from src.infrastructure.event_bus import EventBus
from src.application.opportunity_hunter import OpportunityHunter
from src.application.handlers import log_opportunity
from src.config import RSS_SOURCES

# Налаштовуємо логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    # Ініціалізація сховища
    storage = Storage("aion.db")
    await storage.init()
    
    # Ініціалізація шини подій
    event_bus = EventBus(storage)
    
    # Підписка на події
    event_bus.subscribe("opportunity_created", log_opportunity)
    
    # Запускаємо обробку подій у фоні
    asyncio.create_task(event_bus.run())
    
    # Створюємо агента з реальними джерелами
    hunter = OpportunityHunter(storage, event_bus, RSS_SOURCES)
    await hunter.scan()
    
    print("✅ Scan complete. Objects saved in aion.db")
    
    await asyncio.sleep(0.5)
    await storage.close()

if __name__ == "__main__":
    asyncio.run(main())
