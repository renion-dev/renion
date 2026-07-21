import asyncio
from src.infrastructure.storage import Storage
from src.infrastructure.event_bus import EventBus
from src.application.opportunity_hunter import OpportunityHunter
from src.application.handlers import log_opportunity

async def main():
    # Ініціалізація сховища
    storage = Storage("aion.db")
    await storage.init()
    
    # Ініціаліалізація шини подій
    event_bus = EventBus(storage)
    
    # Підписка на події (логіка)
    event_bus.subscribe("opportunity_created", log_opportunity)
    
    # Запускаємо обробку подій у фоні
    asyncio.create_task(event_bus.run())
    
    # Створюємо агента та запускаємо сканування
    hunter = OpportunityHunter(
        storage, 
        event_bus, 
        ["https://example.com/rss"]  # можна додати більше URL
    )
    await hunter.scan()
    
    print("✅ Scan complete. Objects saved in aion.db")
    
    # Чекаємо трохи, щоб обробники встигли виконатися
    await asyncio.sleep(0.5)
    
    # Закриваємо з'єднання
    await storage.close()

if __name__ == "__main__":
    asyncio.run(main())
