"""Recommendation dataclass representing an AI-generated sustainability tip."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Recommendation:
    """An AI-generated sustainability tip."""

    id: str
    user_id: str
    category: str
    title: str
    description: str
    potential_saving_kg: float
    difficulty: str
    created_at: Optional[str] = None


__all__ = ["Recommendation"]
