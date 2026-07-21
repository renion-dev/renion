import asyncio
import os
import uuid
import logging
import stripe
from typing import Dict, Any, Optional
from datetime import datetime
from src.domain.payment import Payment
from src.domain.interfaces.payment_provider import PaymentProvider
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class StripeProvider(PaymentProvider):
    """Реалізація платіжного провайдера через Stripe."""
    
    def __init__(self):
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not self.api_key:
            logger.warning("STRIPE_SECRET_KEY not set. StripeProvider will not work.")
        stripe.api_key = self.api_key
        self._payments: Dict[str, Payment] = {}  # Кеш для швидкого доступу

    async def create_payment(
        self,
        amount: float,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Payment:
        """Створює платіж через Stripe PaymentIntent."""
        try:
            # Stripe працює з центами (для USD)
            amount_cents = int(amount * 100)
            
            # Створюємо PaymentIntent
            intent = await asyncio.to_thread(
                stripe.PaymentIntent.create,
                amount=amount_cents,
                currency=currency.lower(),
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True}
            )
            
            payment = Payment(
                amount=amount,
                currency=currency,
                method="stripe",
                provider_reference=intent.id,
                metadata={
                    "client_secret": intent.client_secret,
                    "status": intent.status,
                    **(metadata or {})
                },
                status=self._map_stripe_status(intent.status)
            )
            
            self._payments[payment.id] = payment
            logger.info(f"💰 Stripe PaymentIntent created: {intent.id} for ${amount}")
            return payment
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise

    async def confirm_payment(self, payment_id: str) -> bool:
        """Підтверджує платіж (для синхронних методів)."""
        payment = self._payments.get(payment_id)
        if not payment:
            logger.error(f"Payment {payment_id} not found")
            return False
        
        try:
            intent = await asyncio.to_thread(
                stripe.PaymentIntent.retrieve,
                payment.provider_reference
            )
            
            if intent.status == "succeeded":
                payment.complete()
                logger.info(f"✅ Payment {payment_id} confirmed")
                return True
            else:
                logger.warning(f"Payment {payment_id} status: {intent.status}")
                return False
                
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return False

    async def get_payment_status(self, payment_id: str) -> str:
        """Отримує статус платежу з Stripe."""
        payment = self._payments.get(payment_id)
        if not payment:
            return "unknown"
        
        try:
            intent = await asyncio.to_thread(
                stripe.PaymentIntent.retrieve,
                payment.provider_reference
            )
            return self._map_stripe_status(intent.status)
        except stripe.error.StripeError:
            return payment.status

    async def refund_payment(self, payment_id: str) -> bool:
        """Повертає кошти за платежем."""
        payment = self._payments.get(payment_id)
        if not payment:
            return False
        
        try:
            refund = await asyncio.to_thread(
                stripe.Refund.create,
                payment_intent=payment.provider_reference
            )
            if refund.status == "succeeded":
                payment.refund()
                logger.info(f"↩️ Refund succeeded for {payment_id}")
                return True
            return False
        except stripe.error.StripeError as e:
            logger.error(f"Refund error: {e}")
            return False

    def _map_stripe_status(self, stripe_status: str) -> str:
        """Мапить статус Stripe у внутрішній статус."""
        mapping = {
            "requires_payment_method": "pending",
            "requires_confirmation": "pending",
            "requires_action": "pending",
            "processing": "pending",
            "succeeded": "completed",
            "canceled": "failed",
        }
        return mapping.get(stripe_status, "pending")
