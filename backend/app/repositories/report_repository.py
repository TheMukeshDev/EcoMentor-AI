"""Report document repository for Firestore reports collection."""

from __future__ import annotations

from app.repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository):
    def __init__(self, db: object) -> None:
        super().__init__(db, "reports")

    def find_by_user_id(self, user_id: str) -> list[dict[str, object]]:
        """Find reports by user ID.

        Args:
            user_id: The user's UID.

        Returns:
            List of report documents sorted by generated_at.
        """
        results = self.query(filters=[("uid", "==", user_id)])
        results.sort(key=lambda x: x.get("generated_at", ""), reverse=False)
        return results


__all__ = ["ReportRepository"]
