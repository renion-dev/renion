from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from src.domain.social_post import SocialPost

class SocialPoster(ABC):
    """Інтерфейс для публікації у соціальних мережах."""
    
    @abstractmethod
    async def post(self, content: str, hypothesis_id: str, metadata: Optional[Dict[str, Any]] = None) -> SocialPost:
        """
        Публікує пост у соціальній мережі.
        Повертає об'єкт SocialPost з оновленим статусом та ID.
        """
        pass
    
    @abstractmethod
    async def get_post_status(self, post_id: str) -> str:
        """Отримує статус поста за його ID у зовнішній системі."""
        pass
