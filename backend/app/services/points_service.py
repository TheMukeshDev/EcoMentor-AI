"""Gamification points and level management service.

Calculates user points, determines level progression with badge
awards, and provides level info including progress to next level.
"""

from __future__ import annotations

from typing import Any

LEVELS = [
    {"name": "Beginner", "badge": "Seedling", "min_points": 0},
    {"name": "Explorer", "badge": "Sprout", "min_points": 100},
    {"name": "Eco Warrior", "badge": "Leaf", "min_points": 500},
    {"name": "Planet Hero", "badge": "Globe", "min_points": 2000},
]

POINTS_ACTIVITY_LOG = 10
POINTS_CHALLENGE_COMPLETE = 50
POINTS_7_DAY_STREAK = 100


class PointsService:
    def __init__(self, user_repository) -> None:
        """Initialize the points service with a user repository.

        Args:
            user_repository: Repository for user data persistence.
        """
        self._user_repo = user_repository

    def add_points(self, user_id: str, amount: int, reason: str = "") -> dict | None:
        """Add points to a user's account and update their level.

        Args:
            user_id: Unique identifier for the user.
            amount: Number of points to add.
            reason: Optional reason for the points award.

        Returns:
            Dictionary with updated points, level, badge, and reason,
            or None if the user was not found.
        """
        user = self._user_repo.get(user_id)
        if not user:
            return None

        current_points = user.get("points", 0)
        new_points = current_points + amount

        level_info = self._calculate_level(new_points)
        updates = {
            "points": new_points,
            "level": level_info["name"],
            "badge": level_info["badge"],
        }
        self._user_repo.update(user_id, updates)

        result = {**updates, "points_earned": amount, "reason": reason}
        return result

    def get_points(self, user_id: str) -> int:
        """Retrieve the current points for a user.

        Args:
            user_id: Unique identifier for the user.

        Returns:
            Current point total, or 0 if the user was not found.
        """
        user = self._user_repo.get(user_id)
        if not user:
            return 0
        return user.get("points", 0)

    def get_level_info(self, user_id: str) -> dict:
        """Retrieve the level information for a user.

        Args:
            user_id: Unique identifier for the user.

        Returns:
            Dictionary with name, badge, points, next_level_points, and progress.
        """
        user = self._user_repo.get(user_id)
        if not user:
            return {"name": "Beginner", "badge": "Seedling", "points": 0}
        points = user.get("points", 0)
        level = self._calculate_level(points)
        return {
            "name": level["name"],
            "badge": level["badge"],
            "points": points,
            "next_level_points": level.get("next_min", None),
            "progress": level.get("progress", 100),
        }

    def _calculate_level(self, points: int) -> dict:
        """Calculate the user's level and progress based on point total.

        Args:
            points: The user's current point total.

        Returns:
            Dictionary with name, badge, next_min, and progress percentage.
        """
        current = LEVELS[0]
        for i, level in enumerate(LEVELS):
            if points >= level["min_points"]:
                current = level
            if i + 1 < len(LEVELS) and points < LEVELS[i + 1]["min_points"]:
                next_min = LEVELS[i + 1]["min_points"]
                current_min = level["min_points"]
                range_size = next_min - current_min
                progress = (
                    min(100, int((points - current_min) / range_size * 100))
                    if range_size > 0
                    else 100
                )
                return {**current, "next_min": next_min, "progress": progress}
        return {**current, "next_min": None, "progress": 100}


__all__ = ["PointsService"]
