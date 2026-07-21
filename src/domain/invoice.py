from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

class InvoiceStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

@dataclass
class Invoice:
    """Рахунок — вимога до оплати."""
    
    id: str
    object_id: str                           # ID об'єкта, за який виставляється рахунок (наприклад, Hypothesis)
    amount: float
    currency: str
    status: InvoiceStatus = InvoiceStatus.DRAFT
    
    # Опис товару/послуги
    description: str = ""
    line_items: List[Dict[str, Any]] = field(default_factory=list)  # [{description, amount, quantity}]
    
    # Реквізити
    due_date: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    
    # Зовнішній ідентифікатор
    provider_invoice_id: Optional[str] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def send(self) -> None:
        """Відправляє рахунок."""
        if self.status == InvoiceStatus.DRAFT:
            self.status = InvoiceStatus.SENT
            self.sent_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def mark_paid(self, provider_id: Optional[str] = None) -> None:
        """Позначає рахунок як оплачений."""
        self.status = InvoiceStatus.PAID
        self.paid_at = datetime.utcnow()
        self.provider_invoice_id = provider_id
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """Скасовує рахунок."""
        self.status = InvoiceStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def add_line_item(self, description: str, amount: float, quantity: int = 1) -> None:
        """Додає позицію в рахунок."""
        self.line_items.append({
            "description": description,
            "amount": amount,
            "quantity": quantity,
            "total": amount * quantity
        })
