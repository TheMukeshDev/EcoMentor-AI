from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Activity:
    id: str
    user_id: str
    category: str
    description: str
    carbon_kg: float
    date: str
    created_at: Optional[str] = None
