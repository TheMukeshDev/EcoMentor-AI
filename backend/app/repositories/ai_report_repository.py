"""AI report document repository for Firestore ai_reports collection.

Handles TTL-based validity checks and type-scoped queries for cached AI content.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.repositories.base_repository import BaseRepository


class AIReportRepository(BaseRepository):
    def __init__(self, db: object) -> None:
        super().__init__(db, "ai_reports")

    def find_valid_by_user_and_type(
        self, user_id: str, report_type: str
    ) -> list[dict[str, object]]:
        """Find non-expired AI reports by user and type.

        Args:
            user_id: The user's UID.
            report_type: The report type identifier.

        Returns:
            List of valid (non-expired) AI report documents.
        """
        now = datetime.now(timezone.utc).isoformat()
        results = self.query(
            filters=[
                ("uid", "==", user_id),
                ("type", "==", report_type),
            ],
        )
        filtered = [r for r in results if r.get("expires_at", "") >= now]
        filtered.sort(key=lambda x: x.get("generated_at", ""), reverse=False)
        return filtered

    def find_by_user_and_type(self, user_id: str, report_type: str) -> list[dict[str, object]]:
        """Find all AI reports by user and type regardless of expiry.

        Args:
            user_id: The user's UID.
            report_type: The report type identifier.

        Returns:
            List of AI report documents sorted by generated_at.
        """
        results = self.query(
            filters=[
                ("uid", "==", user_id),
                ("type", "==", report_type),
            ],
        )
        results.sort(key=lambda x: x.get("generated_at", ""), reverse=False)
        return results


__all__ = ["AIReportRepository"]
