import logging
from typing import Optional, Dict, Any
from src.domain.social_post import SocialPost
from src.domain.interfaces.social_poster import SocialPoster

logger = logging.getLogger(__name__)

class RedditPoster(SocialPoster):
    """Dry-run реалізація публікації у Reddit."""
    
    async def post(self, content: str, hypothesis_id: str, metadata: Optional[Dict[str, Any]] = None) -> SocialPost:
        post = SocialPost(
            platform="reddit",
            content=content,
            hypothesis_id=hypothesis_id,
            metadata=metadata or {}
        )
        
        # Обмеження довжини для Reddit (пост до 40000 символів, але для безпеки 1000)
        if len(content) > 1000:
            content = content[:997] + "..."
        
        logger.info(f"📝 [DRY-RUN] Reddit post would be:\n{content[:200]}...")
        post.mark_failed("Reddit dry-run (no API keys configured)")
        return post

    async def get_post_status(self, post_id: str) -> str:
        return "unknown"
