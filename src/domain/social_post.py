from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

@dataclass
class SocialPost:
    """Об'єкт, що представляє пост у соціальній мережі."""
    platform: str  # twitter, reddit, linkedin, hackernews
    content: str
    hypothesis_id: str
    status: str = "pending"  # pending, published, failed
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    platform_post_id: Optional[str] = None  # ID поста у зовнішній системі
    url: Optional[str] = None  # URL опублікованого поста
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

    def mark_published(self, platform_post_id: str, url: str):
        self.status = "published"
        self.platform_post_id = platform_post_id
        self.url = url
        self.published_at = datetime.utcnow()

    def mark_failed(self, error: str):
        self.status = "failed"
        self.error = error
