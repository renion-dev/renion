from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.domain.payment import Payment

class PaymentProvider(ABC):
    """Абстракція платіжного провайдера."""
    
    @abstractmethod
    async def create_payment(
        self,
        amount: float,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Payment:
        """Створює платіж і повертає об'єкт Payment."""
        pass
    
    @abstractmethod
    async def confirm_payment(self, payment_id: str) -> bool:
        """Підтверджує платіж (для асинхронних методів)."""
        pass
    
    @abstractmethod
    async def get_payment_status(self, payment_id: str) -> str:
        """Отримує статус платежу."""
        pass
    
    @abstractmethod
    async def refund_payment(self, payment_id: str) -> bool:
        """Повертає кошти за платежем."""
        pass
