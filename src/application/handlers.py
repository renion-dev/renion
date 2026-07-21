from src.domain.event import Event

async def log_opportunity(event: Event):
    """Обробник подій: логує нову можливість або гіпотезу."""
    if event.type == "hypothesis_generated":
        # Для гіпотези дані лежать напряму в payload
        title = event.payload.get("description") or event.payload.get("landing_headline") or "Untitled Hypothesis"
    else:
        # Для звичайних можливостей дані вкладено в object
        obj_data = event.payload.get("object", {})
        title = obj_data.get("title", "Untitled Opportunity")
    
    print(f"🔍 New opportunity found: {title}")
