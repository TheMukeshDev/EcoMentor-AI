"""Challenge dataclass representing a user's daily sustainability challenge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Challenge:
    """A user's daily sustainability challenge."""

    id: str
    uid: str
    title: str
    reward: int = 50
    completed: bool = False
    date: Optional[str] = None
    created_at: Optional[str] = None


__all__ = ["Challenge"]
