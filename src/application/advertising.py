import logging
import uuid
from typing import Dict, Any
from src.domain.object import AionObject
from src.domain.event import Event

logger = logging.getLogger(__name__)

class AdvertisingManager:
    """Менеджер запуску рекламних кампаній (заглушка)."""
    
    def __init__(self, storage, event_bus):
        self.storage = storage
        self.event_bus = event_bus

    async def launch_campaign(self, hypothesis_id: str, hypothesis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Запускає рекламну кампанію для гіпотези (заглушка).
        Логує дію, створює об'єкт AdCampaign у БД, публікує подію.
        """
        logger.info(f"🚀 Launching ad campaign for hypothesis {hypothesis_id}")
        
        # Дані кампанії
        campaign_data = {
            "hypothesis_id": hypothesis_id,
            "problem": hypothesis_data.get("description", "Unknown"),
            "landing_headline": hypothesis_data.get("landing_headline", "No headline"),
            "landing_url": f"/landings/{hypothesis_id}.html",
            "platform": "simulated",
            "budget": 100,  # фіксований бюджет для тесту
            "status": "simulated",
            "simulated_campaign_id": f"sim_{uuid.uuid4().hex[:8]}"
        }
        
        # Створюємо об'єкт AdCampaign
        campaign_obj = AionObject(
            type="AdCampaign",
            metadata=campaign_data
        )
        await self.storage.save_object(campaign_obj)
        
        # Публікуємо подію про запуск кампанії
        event = Event(
            id=str(uuid.uuid4()),
            object_id=campaign_obj.id,
            type="ad_campaign_launched",
            payload=campaign_data,
            source="AdvertisingManager"
        )
        await self.event_bus.publish(event)
        
        logger.info(f"✅ Ad campaign simulated for hypothesis {hypothesis_id}, campaign ID: {campaign_obj.id}")
        return {
            "status": "simulated",
            "campaign_id": campaign_obj.id,
            "message": "Campaign launched successfully (simulated)"
        }
