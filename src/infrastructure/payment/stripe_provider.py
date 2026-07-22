import os
import stripe
import logging
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class StripeProvider:
    def __init__(self):
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not self.api_key:
            logger.warning("STRIPE_SECRET_KEY not set")
        stripe.api_key = self.api_key
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")

    async def create_checkout_session(self, hypothesis_id: str, amount: float, currency: str = "usd") -> Dict[str, Any]:
        """Створює Stripe Checkout Session."""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {"name": f"Hypothesis {hypothesis_id[:8]}"},
                        "unit_amount": int(amount * 100),
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=f"{self.base_url}/hypotheses?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{self.base_url}/hypotheses",
                metadata={"hypothesis_id": hypothesis_id}
            )
            logger.info(f"✅ Checkout session created: {session.id}")
            return {"url": session.url, "session_id": session.id}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise

    async def get_payment_status(self, session_id: str) -> str:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return "completed" if session.payment_status == "paid" else "pending"
        except stripe.error.StripeError:
            return "unknown"
