"""Activity dataclass representing a logged carbon-emitting activity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Activity:
    """A logged carbon-emitting activity entry."""

    id: str
    uid: str
    date: str
    transport: str
    distance: float
    ac_usage: str
    food_type: str
    plastic_waste: float
    carbon_score: float
    created_at: Optional[str] = None


__all__ = ["Activity"]
