import asyncio
from typing import Dict, List, Callable, Awaitable
from src.domain.event import Event

class EventBus:
    """Шина подій: публікація, підписка та асинхронна обробка."""
    
    def __init__(self, storage):
        self.storage = storage
        self.handlers: Dict[str, List[Callable[[Event], Awaitable[None]]]] = {}
        self.queue: asyncio.Queue[Event] = asyncio.Queue()

    def subscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]) -> None:
        """Підписує обробник на події вказаного типу."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    async def publish(self, event: Event) -> None:
        """Публікує подію: зберігає в БД і ставить у чергу."""
        await self.storage.save_event(event)
        await self.queue.put(event)

    async def run(self) -> None:
        """Запускає цикл обробки подій (повинен працювати фоном)."""
        while True:
            event = await self.queue.get()
            handlers = self.handlers.get(event.type, [])
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    # Тут можна додати логування
                    print(f"Event handler error for {event.id}: {e}")
