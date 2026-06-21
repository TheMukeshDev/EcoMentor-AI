"""Activity document repository for Firestore activities collection.

Provides user-specific activity queries with date range filtering and pagination.
"""

from __future__ import annotations

from app.repositories.base_repository import BaseRepository


class ActivityRepository(BaseRepository):
    def __init__(self, db: object) -> None:
        super().__init__(db, "activities")

    def find_by_user_id(
        self, user_id: str, limit: int | None = None, cursor: str | None = None
    ) -> list[dict[str, object]]:
        """Find activities by user ID with optional pagination.

        Args:
            user_id: The user's UID.
            limit: Maximum number of results to return.
            cursor: Document ID to start after.

        Returns:
            List of matching activity documents sorted by date descending.
        """
        results = self.query(
            filters=[("uid", "==", user_id)],
        )
        results.sort(key=lambda x: x.get("date", ""), reverse=True)
        if cursor:
            try:
                idx = next(i for i, r in enumerate(results) if r.get("id") == cursor)
                results = results[idx + 1 :]
            except StopIteration:
                pass
        if limit is not None:
            results = results[:limit]
        return results

    def find_by_user_and_date_range(
        self, user_id: str, start: str, end: str
    ) -> list[dict[str, object]]:
        """Find activities by user ID within a date range.

        Args:
            user_id: The user's UID.
            start: Start date string (inclusive).
            end: End date string (inclusive).

        Returns:
            List of matching activity documents sorted by date.
        """
        results = self.query(
            filters=[("uid", "==", user_id)],
        )
        filtered = [r for r in results if r.get("date", "") >= start and r.get("date", "") <= end]
        filtered.sort(key=lambda x: x.get("date", ""), reverse=False)
        return filtered


__all__ = ["ActivityRepository"]
