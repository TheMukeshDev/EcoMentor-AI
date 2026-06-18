from dataclasses import dataclass
from typing import Optional


@dataclass
class Report:
    id: str
    uid: str
    period: str
    total_carbon: float
    transport_avg: float
    electricity_avg: float
    food_avg: float
    waste_avg: float
    generated_at: Optional[str] = None
