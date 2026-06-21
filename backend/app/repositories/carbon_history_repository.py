"""Carbon history document repository for Firestore carbon_history collection.

Supports date range queries and single-day lookups per user.
"""

from __future__ import annotations

from app.repositories.base_repository import BaseRepository


class CarbonHistoryRepository(BaseRepository):
    def __init__(self, db: object) -> None:
        super().__init__(db, "carbon_history")

    def find_by_user_id(self, user_id: str, limit: int | None = None) -> list[dict[str, object]]:
        """Find carbon history entries by user ID.

        Args:
            user_id: The user's UID.
            limit: Maximum number of results to return.

        Returns:
            List of matching carbon history documents sorted by date.
        """
        results = self.query(
            filters=[("uid", "==", user_id)],
        )
        results.sort(key=lambda x: x.get("date", ""), reverse=False)
        if limit is not None:
            results = results[:limit]
        return results

    def find_by_user_and_date_range(
        self, user_id: str, start: str, end: str
    ) -> list[dict[str, object]]:
        """Find carbon history entries by user ID within a date range.

        Args:
            user_id: The user's UID.
            start: Start date string (inclusive).
            end: End date string (inclusive).

        Returns:
            List of matching carbon history documents.
        """
        results = self.query(
            filters=[("uid", "==", user_id)],
        )
        filtered = [r for r in results if r.get("date", "") >= start and r.get("date", "") <= end]
        filtered.sort(key=lambda x: x.get("date", ""), reverse=False)
        return filtered

    def find_by_user_and_date(self, user_id: str, date: str) -> dict[str, object] | None:
        """Find a single carbon history entry by user ID and date.

        Args:
            user_id: The user's UID.
            date: The date string.

        Returns:
            The matching document with 'id' field, or None if not found.
        """
        results = self.query(
            filters=[
                ("uid", "==", user_id),
                ("date", "==", date),
            ],
        )
        return results[0] if results else None


__all__ = ["CarbonHistoryRepository"]
