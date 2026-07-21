import logging
from typing import Optional, Dict, Any
from src.domain.social_post import SocialPost
from src.domain.interfaces.social_poster import SocialPoster

logger = logging.getLogger(__name__)

class HackerNewsPoster(SocialPoster):
    """Dry-run реалізація публікації у Hacker News (Show HN)."""
    
    async def post(self, content: str, hypothesis_id: str, metadata: Optional[Dict[str, Any]] = None) -> SocialPost:
        post = SocialPost(
            platform="hackernews",
            content=content,
            hypothesis_id=hypothesis_id,
            metadata=metadata or {}
        )
        
        # Для Show HN: заголовок має починатися з "Show HN:"
        if not content.startswith("Show HN:"):
            content = f"Show HN: {content}"
        
        if len(content) > 300:
            content = content[:297] + "..."
        
        logger.info(f"📝 [DRY-RUN] Hacker News post would be:\n{content[:200]}...")
        post.mark_failed("Hacker News dry-run (no API keys configured)")
        return post

    async def get_post_status(self, post_id: str) -> str:
        return "unknown"
