from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

@dataclass
class Payment:
    """Платіж — грошова транзакція."""
    amount: float
    currency: str = "USD"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"  # pending, completed, failed, refunded
    method: Optional[str] = None  # stripe, paypal, simulated
    provider_reference: Optional[str] = None  # ID у зовнішній системі
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def complete(self):
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def fail(self):
        self.status = "failed"
        self.updated_at = datetime.utcnow()

    def refund(self):
        self.status = "refunded"
        self.updated_at = datetime.utcnow()

@dataclass
class Transaction:
    """Транзакція — запис про рух коштів."""
    payment_id: str
    amount: float
    currency: str = "USD"
    type: str = "charge"  # charge, refund, capture, etc.
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider_transaction_id: Optional[str] = None
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Invoice:
    """Рахунок — вимога до оплати."""
    object_id: str  # ID об'єкта, за який виставляється рахунок (наприклад, Hypothesis)
    amount: float
    currency: str = "USD"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "draft"  # draft, sent, paid, overdue, cancelled
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    payment_id: Optional[str] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_sent(self):
        self.status = "sent"
        self.updated_at = datetime.utcnow()

    def mark_paid(self, payment_id: str):
        self.status = "paid"
        self.paid_at = datetime.utcnow()
        self.payment_id = payment_id
        self.updated_at = datetime.utcnow()

    def mark_overdue(self):
        self.status = "overdue"
        self.updated_at = datetime.utcnow()

    def cancel(self):
        self.status = "cancelled"
        self.updated_at = datetime.utcnow()
