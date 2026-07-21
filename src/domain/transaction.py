from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class TransactionType(Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    FEE = "fee"

class TransactionStatus(Enum):
    INITIATED = "initiated"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Transaction:
    """Транзакція — запис про рух коштів між учасниками."""
    
    id: str
    payment_id: str
    amount: float
    currency: str
    type: TransactionType = TransactionType.PAYMENT
    status: TransactionStatus = TransactionStatus.INITIATED
    
    # Учасники (якщо потрібно)
    sender_id: Optional[str] = None           # ID об'єкта-відправника
    receiver_id: Optional[str] = None         # ID об'єкта-отримувача
    
    # Референс до зовнішньої системи (Stripe Transfer ID тощо)
    provider_transaction_id: Optional[str] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def mark_completed(self, provider_id: str) -> None:
        """Позначає транзакцію як завершену."""
        self.status = TransactionStatus.COMPLETED
        self.provider_transaction_id = provider_id
        self.completed_at = datetime.utcnow()

    def mark_failed(self) -> None:
        """Позначає транзакцію як невдалу."""
        self.status = TransactionStatus.FAILED
