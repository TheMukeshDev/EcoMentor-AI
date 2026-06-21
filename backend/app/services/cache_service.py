"""Multi-tier caching service with local memory and Firestore persistence.

Implements TTL-based expiry, LRU-like ordering via OrderedDict, and
automatic cache limit enforcement for AI-generated content.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from collections import OrderedDict
from typing import Any

CACHE_TTL = {
    "recommendations": int(os.getenv("CACHE_TTL_RECOMMENDATIONS", "3600")),
    "weekly_report": int(os.getenv("CACHE_TTL_WEEKLY_REPORT", "86400")),
    "eco_personality": int(os.getenv("CACHE_TTL_ECO_PERSONALITY", "86400")),
    "daily_mission": int(os.getenv("CACHE_TTL_DAILY_MISSION", "3600")),
}

MAX_LOCAL_ENTRIES = int(os.getenv("CACHE_MAX_LOCAL_ENTRIES", "1000"))


class CacheService:
    def __init__(self, ai_report_repository=None) -> None:
        """Initialize the cache service with an optional report repository.

        Args:
            ai_report_repository: Optional repository for Firestore persistence.
        """
        self._repo = ai_report_repository
        self._local: OrderedDict = OrderedDict()

    def _enforce_limit(self) -> None:
        """Remove oldest entries when local cache exceeds the maximum limit."""
        while len(self._local) > MAX_LOCAL_ENTRIES:
            self._local.popitem(last=False)

    def get(self, user_id: str, report_type: str) -> Any | None:
        """Retrieve cached content for a user and report type.

        Checks local cache first, then falls back to the repository.

        Args:
            user_id: Unique identifier for the user.
            report_type: Type of cached report (e.g. 'recommendations').

        Returns:
            Cached content dictionary, or None if not found or expired.
        """
        key = f"{user_id}:{report_type}"
        cached = self._local.get(key)
        if cached:
            expires = cached.get("expires_at")
            if expires and expires >= datetime.now(timezone.utc).isoformat():
                self._local.move_to_end(key)
                return cached.get("content")
            del self._local[key]

        if self._repo:
            results = self._repo.find_valid_by_user_and_type(user_id, report_type)
            if results:
                report = results[0]
                self._local[key] = {
                    "content": report.get("content"),
                    "expires_at": report.get("expires_at"),
                }
                self._enforce_limit()
                return report.get("content")
        return None

    def set(self, user_id: str, report_type: str, content: dict) -> None:
        """Cache content for a user and report type with TTL-based expiry.

        Args:
            user_id: Unique identifier for the user.
            report_type: Type of report being cached.
            content: The content dictionary to cache.
        """
        ttl = CACHE_TTL.get(report_type, 3600)
        now = datetime.now(timezone.utc)
        expires_at = datetime.fromtimestamp(now.timestamp() + ttl, tz=timezone.utc)

        doc_id = f"{user_id}_{report_type}_{now.strftime('%Y%m%d%H%M%S')}"
        doc = {
            "uid": user_id,
            "type": report_type,
            "content": content,
            "generated_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        if self._repo:
            self._repo.set(doc_id, doc)

        self._local[f"{user_id}:{report_type}"] = {
            "content": content,
            "expires_at": expires_at.isoformat(),
        }
        self._enforce_limit()

    def invalidate(self, user_id: str, report_type: str | None = None) -> None:
        """Invalidate cached entries for a user, optionally by report type.

        Args:
            user_id: Unique identifier for the user.
            report_type: Specific report type to invalidate, or None for all.
        """
        if report_type:
            key = f"{user_id}:{report_type}"
            self._local.pop(key, None)
        else:
            prefix = f"{user_id}:"
            keys = [k for k in self._local if k.startswith(prefix)]
            for k in keys:
                del self._local[k]

    def clear(self) -> None:
        """Clear all entries from the local cache."""
        self._local.clear()


__all__ = ["CacheService"]
