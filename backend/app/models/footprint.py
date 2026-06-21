"""Footprint dataclass representing a carbon footprint record for a period."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Footprint:
    """A carbon footprint record for a period."""

    user_id: str
    period: str
    total_kg: float
    categories: dict
    recorded_at: Optional[str] = None


__all__ = ["Footprint"]
