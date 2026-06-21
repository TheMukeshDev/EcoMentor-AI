"""Report dataclass representing a weekly sustainability report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Report:
    """A weekly sustainability report."""

    id: str
    uid: str
    period: str
    total_carbon: float
    transport_avg: float
    electricity_avg: float
    food_avg: float
    waste_avg: float
    generated_at: Optional[str] = None


__all__ = ["Report"]
