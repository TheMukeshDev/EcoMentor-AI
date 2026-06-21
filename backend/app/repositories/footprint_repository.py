"""Footprint document repository for Firestore footprints collection."""

from __future__ import annotations

from datetime import datetime, timezone

from app.repositories.base_repository import BaseRepository


class FootprintRepository(BaseRepository):
    def __init__(self, db: object) -> None:
        super().__init__(db, "footprints")

    def find_by_user_id(self, user_id: str, limit: int | None = None) -> list[dict[str, object]]:
        """Find footprint records by user ID.

        Args:
            user_id: The user's UID.
            limit: Maximum number of results to return.

        Returns:
            List of matching footprint documents sorted by created_at descending.
        """
        results = self.query(
            filters=[("uid", "==", user_id)],
        )
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        if limit is not None:
            results = results[:limit]
        return results

    def find_latest_by_user(self, user_id: str) -> dict[str, object] | None:
        """Find the most recent footprint record for a user.

        Args:
            user_id: The user's UID.

        Returns:
            The latest footprint document, or None if none exist.
        """
        results = self.find_by_user_id(user_id, limit=1)
        return results[0] if results else None

    def upsert_daily_footprint(
        self, user_id: str, date_str: str, carbon_score: float, breakdown: dict
    ) -> None:
        existing = self.query(
            filters=[
                ("uid", "==", user_id),
                ("date", "==", date_str),
            ],
        )
        if existing:
            doc_id = existing[0].get("id", existing[0].get("doc_id"))
            if doc_id:
                self.update(
                    doc_id,
                    {
                        "carbon_score": carbon_score,
                        "breakdown": breakdown,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
                return
        doc = {
            "uid": user_id,
            "date": date_str,
            "carbon_score": carbon_score,
            "breakdown": breakdown,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.set(f"{user_id}_{date_str}", doc)


__all__ = ["FootprintRepository"]
