from dataclasses import dataclass
from typing import Optional


@dataclass
class AIReport:
    uid: str
    type: str
    content: dict
    generated_at: str
    expires_at: str
    id: Optional[str] = None
