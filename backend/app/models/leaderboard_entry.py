"""LeaderboardEntry dataclass representing a user's leaderboard ranking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class LeaderboardEntry:
    """A user's leaderboard ranking."""

    uid: str
    name: str
    points: int
    streak: int
    level: str
    badge: str
    updated_at: Optional[str] = None


__all__ = ["LeaderboardEntry"]
