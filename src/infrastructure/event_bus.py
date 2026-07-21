import asyncio
import logging
from typing import Dict, List, Callable, Awaitable
from src.domain.event import Event

logger = logging.getLogger(__name__)

class EventBus:
    """Шина подій: публікація, підписка та асинхронна обробка."""
    
    def __init__(self, storage):
        self.storage = storage
        self.handlers: Dict[str, List[Callable[[Event], Awaitable[None]]]] = {}
        self.queue: asyncio.Queue[Event] = asyncio.Queue()

    def subscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]) -> None:
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.info(f"📌 Subscribed handler for event type: {event_type}")

    async def publish(self, event: Event) -> None:
        await self.storage.save_event(event)
        await self.queue.put(event)
        logger.debug(f"📤 Event published: {event.type} ({event.id})")

    async def run(self) -> None:
        logger.info("🔄 Event bus started")
        while True:
            event = await self.queue.get()
            logger.info(f"📨 Processing event: {event.type} ({event.id})")
            handlers = self.handlers.get(event.type, [])
            logger.info(f"📨 Found {len(handlers)} handlers for {event.type}")
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Event handler error for {event.id}: {e}")
            # Позначаємо завдання як виконане
            self.queue.task_done()
