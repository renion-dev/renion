import logging
from typing import Optional
from src.domain.payment import Payment, Invoice
from src.domain.interfaces.payment_provider import PaymentProvider
from src.infrastructure.storage import Storage

logger = logging.getLogger(__name__)

class PaymentProcessor:
    """Use case для обробки платежів."""
    
    def __init__(self, storage: Storage, provider: PaymentProvider):
        self.storage = storage
        self.provider = provider
    
    async def process_invoice(self, invoice: Invoice) -> Optional[Payment]:
        """
        Оплачує рахунок через платіжного провайдера.
        Створює платіж, зберігає його, оновлює статус інвойсу.
        """
        if invoice.status == "paid":
            logger.warning(f"Invoice {invoice.id} already paid")
            return None
        
        payment = await self.provider.create_payment(
            amount=invoice.amount,
            currency=invoice.currency,
            metadata={"invoice_id": invoice.id, "object_id": invoice.object_id}
        )
        
        # Зберігаємо платіж
        await self._save_payment(payment)
        
        # Оновлюємо інвойс
        if payment.status == "completed":
            invoice.mark_paid(payment.id)
        else:
            # Якщо платіж ще не завершено (наприклад, очікується підтвердження)
            invoice.status = "sent"  # проміжний статус
        await self._save_invoice(invoice)
        
        return payment
    
    async def get_invoice_by_object(self, object_id: str) -> Optional[Invoice]:
        """Отримує інвойс за ID об'єкта (наприклад, гіпотези)."""
        # Тут треба зробити запит до БД (метод get_object_by_metadata)
        # Поки що повертаємо None — реалізуємо в наступному кроці
        return None
    
    async def _save_payment(self, payment: Payment):
        """Зберігає платіж у БД."""
        # Треба додати метод у Storage
        pass
    
    async def _save_invoice(self, invoice: Invoice):
        """Зберігає інвойс у БД."""
        # Треба додати метод у Storage
        pass
