import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from src.domain.payment import Payment
from src.domain.interfaces.payment_provider import PaymentProvider

logger = logging.getLogger(__name__)

class SimulatedProvider(PaymentProvider):
    """Заглушка платіжного провайдера для тестування."""
    
    def __init__(self):
        self._payments: Dict[str, Payment] = {}
        self._auto_confirm: bool = True  # Якщо True — автоматично підтверджуємо платіж
    
    async def create_payment(
        self,
        amount: float,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Payment:
        payment = Payment(
            amount=amount,
            currency=currency,
            method="simulated",
            provider_reference=f"sim_{uuid.uuid4().hex[:8]}",
            metadata=metadata or {}
        )
        self._payments[payment.id] = payment
        
        # Якщо авто-підтвердження ввімкнено, одразу завершуємо платіж
        if self._auto_confirm:
            await self.confirm_payment(payment.id)
        
        logger.info(f"💰 [Simulated] Payment created: {payment.id} - {amount} {currency}")
        return payment
    
    async def confirm_payment(self, payment_id: str) -> bool:
        payment = self._payments.get(payment_id)
        if not payment:
            logger.error(f"Payment {payment_id} not found")
            return False
        
        if payment.status == "pending":
            payment.complete()
            logger.info(f"✅ [Simulated] Payment confirmed: {payment_id}")
            return True
        else:
            logger.warning(f"Payment {payment_id} is already {payment.status}")
            return False
    
    async def get_payment_status(self, payment_id: str) -> str:
        payment = self._payments.get(payment_id)
        return payment.status if payment else "unknown"
    
    async def refund_payment(self, payment_id: str) -> bool:
        payment = self._payments.get(payment_id)
        if not payment:
            return False
        if payment.status == "completed":
            payment.refund()
            logger.info(f"↩️ [Simulated] Payment refunded: {payment_id}")
            return True
        return False
