from dataclasses import dataclass
from typing import Optional


@dataclass
class LeaderboardEntry:
    uid: str
    name: str
    points: int
    streak: int
    level: str
    badge: str
    updated_at: Optional[str] = None
