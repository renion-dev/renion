import logging
from src.domain.event import Event
from src.application.landing_generator import LandingGenerator

logger = logging.getLogger(__name__)

async def log_opportunity(event: Event):
    """Обробник подій: логує нову можливість або гіпотезу."""
    if event.type == "hypothesis_generated":
        title = event.payload.get("description") or event.payload.get("landing_headline") or "Untitled Hypothesis"
    else:
        obj_data = event.payload.get("object", {})
        title = obj_data.get("title", "Untitled Opportunity")
    print(f"🔍 New opportunity found: {title}")

async def generate_landing_for_hypothesis(event: Event, generator: LandingGenerator):
    print(f"🔥 LANDING HANDLER TRIGGERED for {event.object_id}")
    """Генерує лендинг для нової гіпотези."""
    if event.type != "hypothesis_generated":
        logger.info(f"Ignoring event type: {event.type}")
        return
    
    logger.info(f"📝 Generating landing for hypothesis {event.object_id}")
    hypothesis_id = event.object_id
    hypothesis_data = event.payload
    
    try:
        filepath = await generator.generate(hypothesis_id, hypothesis_data)
        print(f"🌐 Landing page generated: {filepath}")
        logger.info(f"✅ Landing generated: {filepath}")
    except Exception as e:
        logger.error(f"❌ Failed to generate landing page: {e}")
        print(f"❌ Failed to generate landing page: {e}")
