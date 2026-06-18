from dataclasses import dataclass
from typing import Optional


@dataclass
class Challenge:
    id: str
    uid: str
    title: str
    reward: int = 50
    completed: bool = False
    date: Optional[str] = None
    created_at: Optional[str] = None
