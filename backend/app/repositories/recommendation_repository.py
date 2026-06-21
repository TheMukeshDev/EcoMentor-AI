"""Recommendation document repository for Firestore recommendations collection."""

from __future__ import annotations

from app.repositories.base_repository import BaseRepository


class RecommendationRepository(BaseRepository):
    def __init__(self, db: object) -> None:
        super().__init__(db, "recommendations")

    def find_by_user_id(self, user_id: str, limit: int | None = None) -> list[dict[str, object]]:
        """Find recommendations by user ID.

        Args:
            user_id: The user's UID.
            limit: Maximum number of results to return.

        Returns:
            List of recommendation documents sorted by created_at descending.
        """
        return self.query(
            filters=[("uid", "==", user_id)],
            order_by=("created_at", "DESCENDING"),
            limit=limit,
        )

    def find_by_category(self, category: str) -> list[dict[str, object]]:
        """Find recommendations by category.

        Args:
            category: The recommendation category.

        Returns:
            List of matching recommendation documents.
        """
        return self.query(
            filters=[("category", "==", category)],
            order_by="created_at",
        )

    def find_valid_by_user_and_type(
        self, user_id: str, report_type: str
    ) -> list[dict[str, object]]:
        """Find non-expired recommendations by user and type.

        Args:
            user_id: The user's UID.
            report_type: The report type identifier.

        Returns:
            List of valid recommendation documents.
        """
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        return self.query(
            filters=[
                ("uid", "==", user_id),
                ("type", "==", report_type),
                ("expires_at", ">=", now),
            ],
            order_by=("generated_at", "DESCENDING"),
        )


__all__ = ["RecommendationRepository"]
