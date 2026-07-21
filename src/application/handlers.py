from src.domain.event import Event

async def log_opportunity(event: Event):
    """Простий обробник, який виводить інформацію про нову можливість."""
    payload = event.payload.get("object", {})
    title = payload.get("title", "No title")
    print(f"🔍 New opportunity found: {title}")
