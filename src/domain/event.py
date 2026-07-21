from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

@dataclass
class Event:
    """Подія AION — фіксує будь-яку зміну стану."""
    
    # Унікальний ідентифікатор події
    id: str
    
    # ID об'єкта, до якого належить подія
    object_id: str
    
    # Тип події (наприклад, created, updated, deleted, opportunity_created)
    type: str
    
    # Дані події (довільний словник)
    payload: Dict[str, Any]
    
    # Час створення події
    timestamp: datetime = datetime.utcnow()
    
    # Джерело події (компонент, який її згенерував)
    source: Optional[str] = None
