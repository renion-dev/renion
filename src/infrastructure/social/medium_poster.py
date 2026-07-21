import logging
from typing import Optional, Dict, Any
from src.domain.social_post import SocialPost
from src.domain.interfaces.social_poster import SocialPoster

logger = logging.getLogger(__name__)

class MediumPoster(SocialPoster):
    """Dry-run реалізація публікації статті на Medium/Dev.to."""
    
    async def post(self, content: str, hypothesis_id: str, metadata: Optional[Dict[str, Any]] = None) -> SocialPost:
        post = SocialPost(
            platform="medium",
            content=content,
            hypothesis_id=hypothesis_id,
            metadata=metadata or {}
        )
        
        # Для Medium стаття може бути довгою, але для dry-run обмежимо
        if len(content) > 2000:
            content = content[:1997] + "..."
        
        logger.info(f"📝 [DRY-RUN] Medium article would be:\n{content[:300]}...")
        post.mark_failed("Medium dry-run (no API keys configured)")
        return post

    async def get_post_status(self, post_id: str) -> str:
        return "unknown"
