from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    uid: str
    email: str
    name: str
    points: int = 0
    streak: int = 0
    level: str = "Beginner"
    badge: str = "Seedling"
    created_at: Optional[str] = None
