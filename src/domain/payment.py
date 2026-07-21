from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class PaymentStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class PaymentMethod(Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CRYPTO = "crypto"
    SIMULATED = "simulated"
    UNKNOWN = "unknown"

@dataclass
class Payment:
    """Платіж — економічна операція."""
    
    # Основні поля
    id: str
    amount: float
    currency: str
    status: PaymentStatus = PaymentStatus.PENDING
    method: PaymentMethod = PaymentMethod.UNKNOWN
    
    # Прив'язка до об'єктів системи
    object_id: Optional[str] = None          # ID об'єкта, за який платять (наприклад, Hypothesis)
    invoice_id: Optional[str] = None         # ID рахунку (якщо є)
    
    # Ідентифікатор зовнішнього провайдера (Stripe Payment Intent ID тощо)
    provider_payment_id: Optional[str] = None
    
    # Додаткові дані
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None

    def mark_paid(self, provider_id: str) -> None:
        """Позначає платіж як сплачений."""
        self.status = PaymentStatus.PAID
        self.provider_payment_id = provider_id
        self.paid_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_failed(self) -> None:
        """Позначає платіж як невдалий."""
        self.status = PaymentStatus.FAILED
        self.updated_at = datetime.utcnow()

    def mark_refunded(self) -> None:
        """Позначає платіж як повернутий."""
        self.status = PaymentStatus.REFUNDED
        self.refunded_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """Скасовує платіж."""
        if self.status == PaymentStatus.PENDING:
            self.status = PaymentStatus.CANCELLED
            self.updated_at = datetime.utcnow()
