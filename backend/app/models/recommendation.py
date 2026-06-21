from dataclasses import dataclass
from typing import Optional


@dataclass
class Recommendation:
    id: str
    user_id: str
    category: str
    title: str
    description: str
    potential_saving_kg: float
    difficulty: str
    created_at: Optional[str] = None
