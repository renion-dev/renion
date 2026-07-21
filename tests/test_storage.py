import pytest
from src.infrastructure.storage import Storage
from src.domain.object import AionObject
from src.domain.event import Event
import uuid

@pytest.mark.asyncio
async def test_save_and_get_object():
    """Тест: збереження та отримання об'єкта."""
    storage = Storage(":memory:")
    await storage.init()
    
    obj = AionObject(type="Test")
    await storage.save_object(obj)
    
    fetched = await storage.get_object(obj.id)
    assert fetched is not None
    assert fetched["id"] == obj.id
    assert fetched["type"] == "Test"
    assert fetched["lifecycle"] == "active"
    
    await storage.close()

@pytest.mark.asyncio
async def test_save_event():
    """Тест: збереження події."""
    storage = Storage(":memory:")
    await storage.init()
    
    obj = AionObject(type="Test")
    await storage.save_object(obj)
    
    event = Event(
        id=str(uuid.uuid4()),
        object_id=obj.id,
        type="test_event",
        payload={"key": "value"}
    )
    await storage.save_event(event)
    
    # Перевіряємо, чи подія збереглася (зробимо прямий запит)
    async with storage.conn.execute("SELECT * FROM events WHERE id=?", (event.id,)) as cursor:
        row = await cursor.fetchone()
        assert row is not None
        assert row[1] == obj.id  # object_id
        assert row[2] == "test_event"
    
    await storage.close()
