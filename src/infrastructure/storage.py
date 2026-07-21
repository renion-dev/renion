import aiosqlite
import json
from typing import Optional, Dict, Any
from src.domain.object import AionObject
from src.domain.event import Event
from src.domain.payment import Payment, Invoice

class Storage:
    """Сховище об'єктів, подій, платежів та інвойсів на основі SQLite."""
    
    def __init__(self, db_path: str = "aion.db"):
        self.db_path = db_path
        self.conn = None

    async def init(self):
        """Ініціалізує базу даних: створює всі таблиці."""
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
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                amount REAL,
                currency TEXT,
                status TEXT,
                method TEXT,
                provider_reference TEXT,
                metadata TEXT,
                created_at TEXT,
                updated_at TEXT,
                completed_at TEXT
            )
        """)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY,
                object_id TEXT,
                amount REAL,
                currency TEXT,
                status TEXT,
                due_date TEXT,
                paid_at TEXT,
                payment_id TEXT,
                description TEXT,
                metadata TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        await self.conn.commit()

    async def save_object(self, obj: AionObject):
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

    async def get_object_by_metadata(self, key: str, value: str, object_type: str) -> Optional[Dict[str, Any]]:
        if self.conn is None:
            raise RuntimeError("Storage not initialized. Call init() first.")
        async with self.conn.execute(
            "SELECT * FROM objects WHERE type=? AND json_extract(metadata, '$.' || ?) = ?",
            (object_type, key, value)
        ) as cursor:
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

    async def save_payment(self, payment: Payment) -> None:
        if self.conn is None:
            raise RuntimeError("Storage not initialized. Call init() first.")
        await self.conn.execute(
            """INSERT OR REPLACE INTO payments
               (id, amount, currency, status, method, provider_reference, metadata, created_at, updated_at, completed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                payment.id, payment.amount, payment.currency, payment.status,
                payment.method, payment.provider_reference,
                json.dumps(payment.metadata),
                payment.created_at.isoformat(),
                payment.updated_at.isoformat(),
                payment.completed_at.isoformat() if payment.completed_at else None
            )
        )
        await self.conn.commit()

    async def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        if self.conn is None:
            raise RuntimeError("Storage not initialized. Call init() first.")
        async with self.conn.execute("SELECT * FROM payments WHERE id=?", (payment_id,)) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return {
                "id": row[0],
                "amount": row[1],
                "currency": row[2],
                "status": row[3],
                "method": row[4],
                "provider_reference": row[5],
                "metadata": json.loads(row[6]),
                "created_at": row[7],
                "updated_at": row[8],
                "completed_at": row[9]
            }

    async def save_invoice(self, invoice: Invoice) -> None:
        if self.conn is None:
            raise RuntimeError("Storage not initialized. Call init() first.")
        await self.conn.execute(
            """INSERT OR REPLACE INTO invoices
               (id, object_id, amount, currency, status, due_date, paid_at, payment_id, description, metadata, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                invoice.id, invoice.object_id, invoice.amount, invoice.currency,
                invoice.status,
                invoice.due_date.isoformat() if invoice.due_date else None,
                invoice.paid_at.isoformat() if invoice.paid_at else None,
                invoice.payment_id, invoice.description,
                json.dumps(invoice.metadata),
                invoice.created_at.isoformat(),
                invoice.updated_at.isoformat()
            )
        )
        await self.conn.commit()

    async def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        if self.conn is None:
            raise RuntimeError("Storage not initialized. Call init() first.")
        async with self.conn.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return {
                "id": row[0],
                "object_id": row[1],
                "amount": row[2],
                "currency": row[3],
                "status": row[4],
                "due_date": row[5],
                "paid_at": row[6],
                "payment_id": row[7],
                "description": row[8],
                "metadata": json.loads(row[9]),
                "created_at": row[10],
                "updated_at": row[11]
            }

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def get_payment_by_provider_reference(self, provider_reference: str) -> Optional[Dict[str, Any]]:
        """Отримує платіж за provider_reference (id Stripe PaymentIntent)."""
        if self.conn is None:
            raise RuntimeError("Storage not initialized")
        async with self.conn.execute("SELECT * FROM payments WHERE provider_reference=?", (provider_reference,)) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return {
                "id": row[0],
                "amount": row[1],
                "currency": row[2],
                "status": row[3],
                "method": row[4],
                "provider_reference": row[5],
                "metadata": json.loads(row[6]),
                "created_at": row[7],
                "updated_at": row[8],
                "completed_at": row[9]
            }

    async def update_payment_status(self, payment_id: str, status: str, completed_at: Optional[str] = None) -> None:
        """Оновлює статус платежу."""
        if self.conn is None:
            raise RuntimeError("Storage not initialized")
        await self.conn.execute(
            "UPDATE payments SET status=?, updated_at=?, completed_at=? WHERE id=?",
            (status, datetime.utcnow().isoformat(), completed_at, payment_id)
        )
        await self.conn.commit()

    async def update_invoice_status(self, invoice_id: str, status: str, payment_id: Optional[str] = None, paid_at: Optional[str] = None) -> None:
        """Оновлює статус інвойсу."""
        if self.conn is None:
            raise RuntimeError("Storage not initialized")
        await self.conn.execute(
            "UPDATE invoices SET status=?, updated_at=?, paid_at=?, payment_id=? WHERE id=?",
            (status, datetime.utcnow().isoformat(), paid_at, payment_id, invoice_id)
        )
        await self.conn.commit()
