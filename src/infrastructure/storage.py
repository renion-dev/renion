import aiosqlite
import json
from typing import Optional, Dict, Any
from src.domain.object import AionObject
from src.domain.event import Event

class Storage:
    """Сховище об'єктів та подій на основі SQLite."""
    
    def __init__(self, db_path: str = "aion.db"):
        self.db_path = db_path
        self.conn = None

    async def init(self):
        """Ініціалізує базу даних: створює таблиці, якщо їх немає."""
        if self.conn is None:
            self.conn = await aiosqlite.connect(self.db_path)
        
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS objects (
                id TEXT PRIMARY KEY,
                type TEXT,
                owner TEXT,
                created_at TEXT,
                updated_at TEXT,
                metadata TEXT,
                permissions TEXT,
                lifecycle TEXT,
                history TEXT,
                telemetry TEXT
            )
        """)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                object_id TEXT,
                type TEXT,
                payload TEXT,
                timestamp TEXT,
                source TEXT
            )
        """)
        await self.conn.commit()

    async def save_object(self, obj: AionObject):
        """Зберігає або оновлює об'єкт у базі."""
        if self.conn is None:
            raise RuntimeError("Storage not initialized. Call init() first.")
        
        await self.conn.execute(
            """INSERT OR REPLACE INTO objects
               (id, type, owner, created_at, updated_at, metadata, permissions,
                lifecycle, history, telemetry)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                obj.id, obj.type, obj.owner,
                obj.created_at.isoformat(), obj.updated_at.isoformat(),
                json.dumps(obj.metadata),
                json.dumps(obj.permissions),
                obj.lifecycle,
                json.dumps(obj.history),
                json.dumps(obj.telemetry)
            )
        )
        await self.conn.commit()

    async def get_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        """Отримує об'єкт за ID у вигляді словника."""
        if self.conn is None:
            raise RuntimeError("Storage not initialized. Call init() first.")
        
        async with self.conn.execute("SELECT * FROM objects WHERE id=?", (object_id,)) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return {
                "id": row[0],
                "type": row[1],
                "owner": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "metadata": json.loads(row[5]),
                "permissions": json.loads(row[6]),
                "lifecycle": row[7],
                "history": json.loads(row[8]),
                "telemetry": json.loads(row[9])
            }

    async def save_event(self, event: Event):
        """Зберігає подію в базі."""
        if self.conn is None:
            raise RuntimeError("Storage not initialized. Call init() first.")
        
        await self.conn.execute(
            """INSERT INTO events (id, object_id, type, payload, timestamp, source)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                event.id, event.object_id, event.type,
                json.dumps(event.payload),
                event.timestamp.isoformat(),
                event.source
            )
        )
        await self.conn.commit()

    async def close(self):
        """Закриває з'єднання з базою даних."""
        if self.conn:
            await self.conn.close()
            self.conn = None
