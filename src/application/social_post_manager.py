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
        results = []
        
        # Генеруємо різний контент для різних платформ
        for poster in self.posters:
            try:
                content = self._generate_content(poster.__class__.__name__, hypothesis_data)
                post = await poster.post(
                    content=content,
                    hypothesis_id=hypothesis_id,
                    metadata={"hypothesis": hypothesis_data}
                )
                await self._save_post(post)
                results.append(post)
                logger.info(f"📤 Posted to {post.platform}: {post.status}")
            except Exception as e:
                logger.error(f"Failed to post to {poster.__class__.__name__}: {e}")
        
        return results

    def _generate_content(self, platform: str, hypothesis_data: dict, language: str = "en") -> str:
        """Генерує текст для різних платформ."""
        headline = hypothesis_data.get("landing_headline", "New Solution")
        problem = hypothesis_data.get("description", "A problem needs solving")
        cta = hypothesis_data.get("cta", "Learn more")
        landing_url = hypothesis_data.get("landing_url", "")
        
        if "Reddit" in platform:
            return f"""
🚀 {headline}

**The Problem:**
{problem}

**The Solution:**
{hypothesis_data.get('mvp', 'MVP')}

**Learn More:** {landing_url}
"""
        elif "HackerNews" in platform:
            return f"Show HN: {headline}\n\n{problem[:200]}...\n\nMVP: {hypothesis_data.get('mvp', 'MVP')}\n\n→ {landing_url}"
        elif "Medium" in platform:
            return f"""
# {headline}

## The Problem
{problem}

## The Solution
{hypothesis_data.get('mvp', 'MVP')}

## Hypothesis
{hypothesis_data.get('hypothesis', '')}

## Get Involved
{cta} → {landing_url}
"""
        else:
            return f"🚀 {headline}\n\n{problem[:120]}...\n\n{cta} → {landing_url}"

    async def _save_post(self, post: SocialPost):
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
