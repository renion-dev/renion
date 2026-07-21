from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

@dataclass
class ScanJob:
    """Об'єкт, що представляє стан сканування."""
    status: str = "idle"  # idle, running, completed, failed
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    hypotheses_count: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def start(self):
        self.status = "running"
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete(self, hypotheses_count: int = 0):
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.hypotheses_count = hypotheses_count
        self.updated_at = datetime.utcnow()

    def fail(self, error: str):
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error = error
        self.updated_at = datetime.utcnow()
