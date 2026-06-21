"""AIReport dataclass representing cached AI-generated report content."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AIReport:
    """Cached AI-generated report content."""

    uid: str
    type: str
    content: dict
    generated_at: str
    expires_at: str
    id: Optional[str] = None


__all__ = ["AIReport"]
