from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Challenge:
    id: str
    title: str
    description: str
    goal_kg: float
    duration_days: int
    difficulty: str
    participants: int
    created_at: Optional[str] = None
