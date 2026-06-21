"""Activity service for logging, retrieving, and managing user activities.

Orchestrates carbon score calculation, history persistence,
streak updates, and points awarding for each logged activity.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.services.carbon_service import CarbonService
from app.services.streak_service import StreakService
from app.services.points_service import PointsService, POINTS_ACTIVITY_LOG
from app.utils.errors import AuthorizationError, NotFoundError

_STREAK_BONUS_THRESHOLD = 7
_STREAK_BONUS_POINTS = 100


class ActivityService:
    """Manages the lifecycle of user carbon-tracking activities."""

    def __init__(
        self,
        activity_repository: Any,
        carbon_history_repository: Any,
        user_repository: Any,
        ai_service: Any | None = None,
    ) -> None:
        self._activity_repo = activity_repository
        self._carbon_history_repo = carbon_history_repository
        self._carbon = CarbonService()
        self._streak_service = StreakService(user_repository)
        self._points_service = PointsService(user_repository)
        self._ai_service = ai_service

    def set_ai_service(self, ai_service: Any) -> None:
        """Replace the AI service instance (for late-binding).

        Args:
            ai_service: The AI service instance.
        """
        self._ai_service = ai_service

    def log_activity(
        self, user_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Log a new carbon-emitting activity for a user.

        Calculates carbon breakdown, persists the activity,
        updates daily history, awards points, and updates streaks.

        Args:
            user_id: The authenticated user's unique identifier.
            data: Activity data including transport, distance, etc.

        Returns:
            The created activity record enriched with streak/points info.
        """
        now = datetime.now(timezone.utc)
        date_str = data.get("date", now.strftime("%Y-%m-%d"))

        breakdown = self._carbon.get_breakdown(
            transport=data.get("transport", "walking"),
            distance=data.get("distance", 0),
            ac_usage=data.get("ac_usage", "none"),
            food_type=data.get("food_type", "vegetarian"),
            plastic_waste=data.get("plastic_waste", 0),
        )
        carbon_score = breakdown["total"]

        activity = self._build_activity_record(
            user_id, date_str, data, carbon_score, now
        )
        self._activity_repo.set(activity["id"], activity)

        self._upsert_carbon_history(user_id, date_str, breakdown)
        streak = self._streak_service.update_streak(user_id, date_str)
        points_result = self._points_service.add_points(
            user_id, POINTS_ACTIVITY_LOG, reason="activity_logged"
        )

        if streak == _STREAK_BONUS_THRESHOLD:
            self._points_service.add_points(
                user_id, _STREAK_BONUS_POINTS, reason="7_day_streak"
            )

        if self._ai_service:
            self._ai_service.invalidate_cache(user_id)

        return self._enrich_response(activity, streak, points_result)

    def list_activities(
        self,
        user_id: str,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> list[dict[str, Any]]:
        """List activities for a user with optional pagination.

        Args:
            user_id: The authenticated user's unique identifier.
            limit: Maximum number of activities to return.
            cursor: Pagination cursor (activity ID to start after).

        Returns:
            List of activity records.
        """
        return self._activity_repo.find_by_user_id(
            user_id, limit=limit, cursor=cursor
        )

    def get_activity(
        self, activity_id: str, user_id: str | None = None
    ) -> dict[str, Any] | None:
        """Retrieve a single activity by ID.

        Args:
            activity_id: The activity's unique identifier.
            user_id: Optional owner check — raises if mismatch.

        Returns:
            The activity record, or None if not found.

        Raises:
            AuthorizationError: If user_id doesn't match the activity owner.
        """
        activity = self._activity_repo.get(activity_id)
        if not activity:
            return None
        if user_id and activity.get("uid") != user_id:
            raise AuthorizationError("Permission denied")
        return activity

    def delete_activity(
        self, activity_id: str, user_id: str | None = None
    ) -> None:
        """Delete an activity by ID.

        Args:
            activity_id: The activity's unique identifier.
            user_id: Optional owner check — raises if mismatch.

        Raises:
            NotFoundError: If the activity does not exist.
            AuthorizationError: If user_id doesn't match the activity owner.
        """
        activity = self._activity_repo.get(activity_id)
        if not activity:
            raise NotFoundError("Activity not found")
        if user_id and activity.get("uid") != user_id:
            raise AuthorizationError("Permission denied")
        self._activity_repo.delete(activity_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_activity_record(
        user_id: str,
        date_str: str,
        data: dict[str, Any],
        carbon_score: float,
        now: datetime,
    ) -> dict[str, Any]:
        """Construct an activity document for Firestore.

        Args:
            user_id: The user's UID.
            date_str: The activity date in YYYY-MM-DD format.
            data: Raw input data from the request.
            carbon_score: Calculated total carbon score.
            now: Current UTC datetime.

        Returns:
            A complete activity dictionary ready for persistence.
        """
        return {
            "id": str(uuid.uuid4()),
            "uid": user_id,
            "date": date_str,
            "transport": data["transport"],
            "distance": data["distance"],
            "ac_usage": data["ac_usage"],
            "food_type": data["food_type"],
            "plastic_waste": data["plastic_waste"],
            "carbon_score": carbon_score,
            "created_at": now.isoformat(),
        }

    def _upsert_carbon_history(
        self,
        user_id: str,
        date_str: str,
        breakdown: dict[str, float],
    ) -> None:
        """Create or update the daily carbon history entry.

        Args:
            user_id: The user's UID.
            date_str: The date in YYYY-MM-DD format.
            breakdown: Carbon score breakdown by category.
        """
        existing = self._carbon_history_repo.find_by_user_and_date(
            user_id, date_str
        )
        if existing:
            updated = {
                "carbon_score": existing["carbon_score"] + breakdown["total"],
                "transport": existing.get("transport", 0) + breakdown["transport"],
                "electricity": (
                    existing.get("electricity", 0) + breakdown["electricity"]
                ),
                "food": existing.get("food", 0) + breakdown["food"],
                "waste": existing.get("waste", 0) + breakdown["waste"],
                "activity_count": existing.get("activity_count", 0) + 1,
            }
            self._carbon_history_repo.update(existing["id"], updated)
        else:
            doc = {
                "uid": user_id,
                "date": date_str,
                "carbon_score": breakdown["total"],
                "transport": breakdown["transport"],
                "electricity": breakdown["electricity"],
                "food": breakdown["food"],
                "waste": breakdown["waste"],
                "activity_count": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._carbon_history_repo.set(f"{user_id}_{date_str}", doc)

    @staticmethod
    def _enrich_response(
        activity: dict[str, Any],
        streak: int,
        points_result: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Add streak and gamification data to the activity response.

        Args:
            activity: The base activity record.
            streak: Current streak count.
            points_result: Points service result or None.

        Returns:
            Enriched activity dictionary.
        """
        result = {**activity, "streak": streak}
        if points_result:
            result["points"] = points_result["points"]
            result["level"] = points_result["level"]
            result["badge"] = points_result["badge"]
        return result
