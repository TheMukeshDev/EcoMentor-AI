"""Challenge document repository for Firestore challenges collection."""

from __future__ import annotations

from app.repositories.base_repository import BaseRepository


class ChallengeRepository(BaseRepository):
    def __init__(self, db: object) -> None:
        super().__init__(db, "challenges")

    def find_active(self) -> list[dict[str, object]]:
        """Find all incomplete (active) challenges.

        Returns:
            List of active challenge documents.
        """
        return self.query(filters=[("completed", "==", False)])

    def find_by_difficulty(self, difficulty: str) -> list[dict[str, object]]:
        """Find challenges by difficulty level.

        Args:
            difficulty: The difficulty level string.

        Returns:
            List of matching challenge documents.
        """
        return self.query(filters=[("difficulty", "==", difficulty)])


__all__ = ["ChallengeRepository"]
