"""Structured audit event logging for security-relevant user actions."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

__all__ = ["log_event"]

audit_logger = logging.getLogger("audit")


def log_event(
    event: str,
    user_id: Optional[str] = None,
    ip: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    audit_logger.info(
        "EVENT=%s USER=%s IP=%s DETAILS=%s TIMESTAMP=%s",
        event,
        user_id or "anonymous",
        ip or "unknown",
        json.dumps(details or {}),
        datetime.now(timezone.utc).isoformat(),
    )
