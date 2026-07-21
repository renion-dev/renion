from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

@dataclass
class SocialPost:
    """Пост у соціальній мережі."""
    hypothesis_id: str
    platform: str  # twitter, reddit, linkedin, hackernews, email
    content: str
    status: str = "draft"  # draft, published, failed
    url: Optional[str] = None
    error: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0

    def publish(self, url: str):
        self.status = "published"
        self.url = url
        self.published_at = datetime.utcnow()

    def fail(self, error: str):
        self.status = "failed"
        self.error = error
        self.retry_count += 1

    def retry(self):
        self.status = "draft"
        self.error = None
