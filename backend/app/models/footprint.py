from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Footprint:
    user_id: str
    period: str
    total_kg: float
    categories: dict
    recorded_at: Optional[str] = None
