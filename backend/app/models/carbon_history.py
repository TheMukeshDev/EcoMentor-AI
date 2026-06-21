"""CarbonHistory dataclass representing daily carbon score and breakdown."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class CarbonHistory:
    """Daily carbon score and breakdown."""

    uid: str
    date: str
    carbon_score: float
    transport: float = 0.0
    electricity: float = 0.0
    food: float = 0.0
    waste: float = 0.0
    activity_count: int = 0
    created_at: Optional[str] = None


__all__ = ["CarbonHistory"]
