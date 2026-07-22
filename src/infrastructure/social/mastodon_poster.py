import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from mastodon import Mastodon
from src.domain.social_post import SocialPost
from src.domain.interfaces.social_poster import SocialPoster

load_dotenv()
logger = logging.getLogger(__name__)

class MastodonPoster(SocialPoster):
    """Реалізація публікації у Mastodon (безкоштовно)."""
    
    def __init__(self):
        self.instance = os.getenv("MASTODON_INSTANCE", "mastodon.social")
        self.access_token = os.getenv("MASTODON_ACCESS_TOKEN")
        self.client_id = os.getenv("MASTODON_CLIENT_ID")
        self.client_secret = os.getenv("MASTODON_CLIENT_SECRET")
        
        self._client = None
        self._available = False
        
        if self.access_token:
            try:
                self._client = Mastodon(
                    access_token=self.access_token,
                    api_base_url=f"https://{self.instance}"
                )
                # Перевіряємо підключення
                self._client.account_verify_credentials()
                self._available = True
                logger.info(f"✅ Mastodon client initialized on {self.instance}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Mastodon client: {e}")
                self._available = False
        else:
            logger.warning("⚠️ Mastodon access token not set. Running in dry-run mode.")

    async def post(self, content: str, hypothesis_id: str, metadata: Optional[Dict[str, Any]] = None) -> SocialPost:
        post = SocialPost(
            platform="mastodon",
            content=content,
            hypothesis_id=hypothesis_id,
            metadata=metadata or {}
        )
        
        if not self._available:
            logger.info(f"📝 [DRY-RUN] Mastodon post would be:\n{content[:200]}...")
            post.mark_failed("Mastodon client not available (dry-run)")
            return post
        
        try:
            # Mastodon обмеження: 500 символів (залежить від інстансу)
            if len(content) > 500:
                content = content[:497] + "..."
            
            response = self._client.status_post(content, visibility="public")
            if response and response.id:
                post_url = f"https://{self.instance}/@{response.account.acct}/{response.id}"
                post.mark_published(str(response.id), post_url)
                logger.info(f"🐘 Mastodon post published: {post_url}")
            else:
                post.mark_failed("No post ID returned")
        except Exception as e:
            logger.error(f"Mastodon API error: {e}")
            post.mark_failed(str(e))
        
        return post

    async def get_post_status(self, post_id: str) -> str:
        if not self._available:
            return "unknown"
        try:
            status = self._client.status(post_id)
            return "published" if status else "not_found"
        except Exception:
            return "unknown"
