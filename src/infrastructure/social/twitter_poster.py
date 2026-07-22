import os
import logging
import tweepy
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from src.domain.social_post import SocialPost
from src.domain.interfaces.social_poster import SocialPoster

load_dotenv()  # Завантажуємо .env при імпорті

logger = logging.getLogger(__name__)

class TwitterPoster(SocialPoster):
    """Реалізація публікації у Twitter через API v2."""
    
    def __init__(self):
        # Перечитуємо змінні середовища (на випадок, якщо .env змінився)
        load_dotenv()
        
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = os.getenv("TWITTER_ACCESS_SECRET")
        
        self._client = None
        self._available = False
        
        logger.info(f"Twitter keys: API_KEY={self.api_key[:5] if self.api_key else 'None'}..., ACCESS_TOKEN={self.access_token[:5] if self.access_token else 'None'}...")
        
        if all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            try:
                self._client = tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_secret
                )
                self._available = True
                logger.info("✅ Twitter API client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Twitter client: {e}")
                self._available = False
        else:
            logger.warning("⚠️ Twitter API credentials not set. Running in dry-run mode.")

    async def post(self, content: str, hypothesis_id: str, metadata: Optional[Dict[str, Any]] = None) -> SocialPost:
        post = SocialPost(
            platform="twitter",
            content=content,
            hypothesis_id=hypothesis_id,
            metadata=metadata or {}
        )
        
        if not self._available:
            logger.info(f"📝 [DRY-RUN] Twitter post would be:\n{content[:200]}...")
            post.mark_failed("Twitter client not available (dry-run)")
            return post
        
        try:
            if len(content) > 280:
                content = content[:277] + "..."
            
            response = self._client.create_tweet(text=content)
            if response.data and "id" in response.data:
                tweet_id = str(response.data["id"])
                tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"
                post.mark_published(tweet_id, tweet_url)
                logger.info(f"🐦 Tweet published: {tweet_url}")
            else:
                post.mark_failed("No tweet ID returned")
        except tweepy.TweepyException as e:
            logger.error(f"Twitter API error: {e}")
            post.mark_failed(str(e))
        
        return post

    async def get_post_status(self, post_id: str) -> str:
        if not self._available:
            return "unknown"
        try:
            tweet = self._client.get_tweet(post_id)
            if tweet.data:
                return "published"
            return "not_found"
        except tweepy.TweepyException:
            return "unknown"
