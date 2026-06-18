import uuid
from datetime import datetime, timezone

from app.services.carbon_service import CarbonService


class ActivityService:
    def __init__(self, activity_repository):
        self._activity_repo = activity_repository
        self._carbon = CarbonService()

    def log_activity(self, user_id, data):
        carbon_score = self._carbon.calculate(
            transport=data.get("transport", "walking"),
            distance=data.get("distance", 0),
            ac_usage=data.get("ac_usage", "none"),
            food_type=data.get("food_type", "vegetarian"),
            plastic_waste=data.get("plastic_waste", 0),
        )
        now = datetime.now(timezone.utc).isoformat()
        activity = {
            "id": str(uuid.uuid4()),
            "uid": user_id,
            "date": data.get("date", now[:10]),
            "transport": data["transport"],
            "distance": data["distance"],
            "ac_usage": data["ac_usage"],
            "food_type": data["food_type"],
            "plastic_waste": data["plastic_waste"],
            "carbon_score": carbon_score,
            "created_at": now,
        }
        self._activity_repo.set(activity["id"], activity)
        return activity

    def list_activities(self, user_id):
        return self._activity_repo.find_by_user_id(user_id)

    def get_activity(self, activity_id):
        return self._activity_repo.get(activity_id)

    def delete_activity(self, activity_id):
        self._activity_repo.delete(activity_id)
