import uuid
import os
from datetime import datetime, timezone
from collections import OrderedDict


CACHE_TTL = {
    "recommendations": int(os.getenv("CACHE_TTL_RECOMMENDATIONS", "3600")),
    "weekly_report": int(os.getenv("CACHE_TTL_WEEKLY_REPORT", "86400")),
    "eco_personality": int(os.getenv("CACHE_TTL_ECO_PERSONALITY", "86400")),
    "daily_mission": int(os.getenv("CACHE_TTL_DAILY_MISSION", "3600")),
}

MAX_LOCAL_ENTRIES = int(os.getenv("CACHE_MAX_LOCAL_ENTRIES", "1000"))


class CacheService:
    def __init__(self, ai_report_repository=None):
        self._repo = ai_report_repository
        self._local = OrderedDict()

    def _enforce_limit(self):
        while len(self._local) > MAX_LOCAL_ENTRIES:
            self._local.popitem(last=False)

    def get(self, user_id, report_type):
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

    def set(self, user_id, report_type, content):
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

    def invalidate(self, user_id, report_type=None):
        if report_type:
            key = f"{user_id}:{report_type}"
            self._local.pop(key, None)
        else:
            prefix = f"{user_id}:"
            keys = [k for k in self._local if k.startswith(prefix)]
            for k in keys:
                del self._local[k]

    def clear(self):
        self._local.clear()
