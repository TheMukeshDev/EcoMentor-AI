"""Leaderboard entry repository for Firestore leaderboard collection."""

from __future__ import annotations

from app.repositories.base_repository import BaseRepository


class LeaderboardRepository(BaseRepository):
    def __init__(self, db: object) -> None:
        super().__init__(db, "leaderboard")

    def get_top(self, limit: int = 50) -> list[dict[str, object]]:
        """Get the top-ranked leaderboard entries.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of top leaderboard entries sorted by points.
        """
        return self.query(order_by="points", limit=limit)


__all__ = ["LeaderboardRepository"]
