"""User dataclass representing a Firestore user profile document."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """A Firestore user profile document."""

    uid: str
    email: str
    name: str
    points: int = 0
    streak: int = 0
    level: str = "Beginner"
    badge: str = "Seedling"
    created_at: Optional[str] = None


__all__ = ["User"]
