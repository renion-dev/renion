import logging
from typing import List, Optional
from src.domain.social_post import SocialPost
from src.domain.interfaces.social_poster import SocialPoster
from src.infrastructure.storage import Storage

logger = logging.getLogger(__name__)

class SocialPostManager:
    """Координує публікацію гіпотез у соціальних мережах."""
    
    def __init__(self, storage: Storage, posters: List[SocialPoster]):
        self.storage = storage
        self.posters = posters

    async def post_hypothesis(self, hypothesis_id: str, hypothesis_data: dict) -> List[SocialPost]:
        """
        Публікує гіпотезу на всіх підключених платформах.
        Повертає список створених SocialPost об'єктів.
        """
        results = []
        
        # Генеруємо контент для постів (можна через LLM, але поки використовуємо шаблон)
        content = self._generate_post_content(hypothesis_data)
        
        for poster in self.posters:
            try:
                post = await poster.post(
                    content=content,
                    hypothesis_id=hypothesis_id,
                    metadata={"hypothesis": hypothesis_data}
                )
                # Зберігаємо пост у БД
                await self._save_post(post)
                results.append(post)
                logger.info(f"📤 Posted to {post.platform}: {post.status}")
            except Exception as e:
                logger.error(f"Failed to post to {poster.__class__.__name__}: {e}")
        
        return results

    def _generate_post_content(self, hypothesis_data: dict) -> str:
        """Генерує текст поста на основі гіпотези."""
        headline = hypothesis_data.get("landing_headline", "New Solution")
        problem = hypothesis_data.get("description", "A problem needs solving")
        cta = hypothesis_data.get("cta", "Learn more")
        
        # Короткий варіант для соцмереж
        return f"🚀 {headline}\n\n{problem[:120]}...\n\n{cta} → {hypothesis_data.get('landing_url', '')}"

    async def _save_post(self, post: SocialPost):
        """Зберігає пост у БД (як об'єкт)."""
        # Тут потрібно додати метод у Storage для збереження SocialPost
        # Поки використовуємо загальний метод save_object
        from src.domain.object import AionObject
        obj = AionObject(
            type="SocialPost",
            metadata={
                "platform": post.platform,
                "content": post.content,
                "hypothesis_id": post.hypothesis_id,
                "status": post.status,
                "platform_post_id": post.platform_post_id,
                "url": post.url,
                "error": post.error,
                "created_at": post.created_at.isoformat(),
                "published_at": post.published_at.isoformat() if post.published_at else None
            }
        )
        await self.storage.save_object(obj)
        logger.info(f"💾 SocialPost saved: {obj.id}")
