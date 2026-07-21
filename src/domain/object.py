import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass
class AionObject:
    """Універсальний об'єкт AION."""
    
    # Обов'язкове поле — тип об'єкта
    type: str
    
    # Генерується автоматично
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Власник (опціонально)
    owner: Optional[str] = None
    
    # Час створення та оновлення
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Метадані (довільний словник)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Права доступу (список рядків)
    permissions: List[str] = field(default_factory=list)
    
    # Життєвий цикл: active, archived, deleted
    lifecycle: str = "active"
    
    # Історія подій (список ID подій)
    history: List[str] = field(default_factory=list)
    
    # Телеметрія (метрики використання)
    telemetry: Dict[str, Any] = field(default_factory=dict)
