from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    uid: str
    email: str
    display_name: str
    photo_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
