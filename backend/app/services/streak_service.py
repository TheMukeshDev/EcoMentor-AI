"""User streak tracking service.

Manages daily activity streaks by comparing the current activity
date against the user's last recorded activity date.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


class StreakService:
    """Tracks consecutive daily activity streaks for users."""

    def __init__(self, user_repository: Any) -> None:
        self._user_repo = user_repository

    def get_streak(self, user_id: str) -> int:
        """Get the current streak count for a user.

        Args:
            user_id: The user's unique identifier.

        Returns:
            The current streak count, or 0 if user not found.
        """
        user = self._user_repo.get(user_id)
        if not user:
            return 0
        return user.get("streak", 0)

    def update_streak(self, user_id: str, activity_date_str: str) -> int:
        """Update the streak based on a new activity date.

        If the activity is on the day after the last activity, the
        streak increments. If it's the same day, no change. If a
        day was skipped, the streak resets to zero.

        Args:
            user_id: The user's unique identifier.
            activity_date_str: Activity date in YYYY-MM-DD format.

        Returns:
            The updated streak count.
        """
        user = self._user_repo.get(user_id)
        if not user:
            self._user_repo.set(
                user_id,
                {"streak": 1, "last_activity_date": activity_date_str},
            )
            return 1

        current_streak = user.get("streak", 0)
        last_date_str = user.get("last_activity_date")

        if last_date_str == activity_date_str:
            return current_streak

        current_streak = self._calculate_new_streak(
            current_streak, last_date_str, activity_date_str
        )

        self._user_repo.update(
            user_id,
            {
                "streak": current_streak,
                "last_activity_date": activity_date_str,
            },
        )
        return current_streak

    @staticmethod
    def _calculate_new_streak(
        current_streak: int,
        last_date_str: str | None,
        activity_date_str: str,
    ) -> int:
        """Determine the new streak value based on date continuity.

        Args:
            current_streak: The existing streak count.
            last_date_str: Last activity date string, or None.
            activity_date_str: New activity date string.

        Returns:
            Updated streak count.
        """
        try:
            activity_date = datetime.strptime(
                activity_date_str, "%Y-%m-%d"
            ).date()
            if last_date_str:
                last_date = datetime.strptime(
                    last_date_str, "%Y-%m-%d"
                ).date()
                expected_next = last_date + timedelta(days=1)
                if activity_date == expected_next:
                    return current_streak + 1
                if activity_date > expected_next:
                    return 0
            else:
                return 1
        except ValueError:
            return 0

        return current_streak
