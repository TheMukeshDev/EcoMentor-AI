import uuid
from datetime import datetime, timezone

from app.services.carbon_service import CarbonService
from app.services.streak_service import StreakService
from app.services.points_service import PointsService, POINTS_ACTIVITY_LOG


class ActivityService:
    def __init__(self, activity_repository, carbon_history_repository, user_repository):
        self._activity_repo = activity_repository
        self._carbon_history_repo = carbon_history_repository
        self._carbon = CarbonService()
        self._streak_service = StreakService(user_repository)
        self._points_service = PointsService(user_repository)

    def log_activity(self, user_id, data):
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

        activity = {
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
        self._activity_repo.set(activity["id"], activity)

        self._upsert_carbon_history(user_id, date_str, breakdown)
        streak = self._streak_service.update_streak(user_id, date_str)
        points_result = self._points_service.add_points(
            user_id, POINTS_ACTIVITY_LOG, reason="activity_logged"
        )

        if streak == 7:
            self._points_service.add_points(user_id, 100, reason="7_day_streak")

        result = {**activity, "streak": streak}
        if points_result:
            result["points"] = points_result["points"]
            result["level"] = points_result["level"]
            result["badge"] = points_result["badge"]
        return result

    def _upsert_carbon_history(self, user_id, date_str, breakdown):
        existing = self._carbon_history_repo.find_by_user_and_date(user_id, date_str)
        if existing:
            updated = {
                "carbon_score": existing["carbon_score"] + breakdown["total"],
                "transport": existing.get("transport", 0) + breakdown["transport"],
                "electricity": existing.get("electricity", 0)
                + breakdown["electricity"],
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

    def list_activities(self, user_id, limit=None):
        return self._activity_repo.find_by_user_id(user_id, limit=limit)

    def get_activity(self, activity_id):
        return self._activity_repo.get(activity_id)

    def delete_activity(self, activity_id):
        self._activity_repo.delete(activity_id)
