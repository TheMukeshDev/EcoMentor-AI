from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)


class DashboardService:
    def __init__(
        self,
        carbon_history_repository,
        activity_repository,
        user_repository,
        ai_service=None,
    ):
        self._carbon_history_repo = carbon_history_repository
        self._activity_repo = activity_repository
        self._user_repo = user_repository
        self._ai_service = ai_service

    def get_summary(self, user_id):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime(
            "%Y-%m-%d"
        )

        user = self._user_repo.get(user_id)
        streak = user.get("streak", 0) if user else 0

        today_entry = self._carbon_history_repo.find_by_user_and_date(user_id, today)
        current_score = today_entry.get("carbon_score", 0) if today_entry else 0

        week_entries = self._carbon_history_repo.find_by_user_and_date_range(
            user_id, seven_days_ago, today
        )
        scores = [e.get("carbon_score", 0) for e in week_entries]
        weekly_average = round(sum(scores) / len(scores), 2) if scores else 0

        activities = self._activity_repo.find_by_user_id(user_id)
        activities_logged = len(activities)

        return {
            "current_score": current_score,
            "weekly_average": weekly_average,
            "streak": streak,
            "activities_logged": activities_logged,
        }

    def get_history(self, user_id, period):
        today = datetime.now(timezone.utc)
        if period == "last_7":
            start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        elif period == "last_30":
            start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        else:
            start = (today - timedelta(days=7)).strftime("%Y-%m-%d")

        end = today.strftime("%Y-%m-%d")
        entries = self._carbon_history_repo.find_by_user_and_date_range(
            user_id, start, end
        )
        return [
            {
                "date": e.get("date"),
                "carbon_score": e.get("carbon_score", 0),
                "transport": e.get("transport", 0),
                "electricity": e.get("electricity", 0),
                "food": e.get("food", 0),
                "waste": e.get("waste", 0),
            }
            for e in entries
        ]

    def get_trends(self, user_id):
        today = datetime.now(timezone.utc)
        current_start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        previous_start = (today - timedelta(days=14)).strftime("%Y-%m-%d")
        previous_end = (today - timedelta(days=8)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")

        current_entries = self._carbon_history_repo.find_by_user_and_date_range(
            user_id, current_start, end
        )
        previous_entries = self._carbon_history_repo.find_by_user_and_date_range(
            user_id, previous_start, previous_end
        )

        current_avg = (
            round(
                sum(e.get("carbon_score", 0) for e in current_entries)
                / len(current_entries),
                2,
            )
            if current_entries
            else 0
        )
        previous_avg = (
            round(
                sum(e.get("carbon_score", 0) for e in previous_entries)
                / len(previous_entries),
                2,
            )
            if previous_entries
            else 0
        )

        change = round(current_avg - previous_avg, 2)
        direction = "up" if change > 0 else "down" if change < 0 else "stable"

        return {
            "current_week_avg": current_avg,
            "previous_week_avg": previous_avg,
            "change": abs(change),
            "direction": direction,
        }

    def get_insights(self, user_id):
        summary = self.get_summary(user_id)
        history = self.get_history(user_id, "last_7")
        trends = self.get_trends(user_id)

        if not self._ai_service:
            return {
                "summary": summary,
                "trends": trends,
                "ai_insight": None,
                "ai_tip": None,
            }

        try:
            scores = {
                "score": summary.get("current_score", 0),
                "transport": "walking",
                "food": "vegetarian",
                "ac_usage": "none",
            }
            recs = self._ai_service.get_recommendations(user_id, scores)
            tip = (
                recs.get("tips", [None])[0]
                if recs and isinstance(recs.get("tips"), list)
                else None
            )
            direction = trends.get("direction", "stable")
            if direction == "down":
                insight = f"Your carbon score dropped by {trends.get('change', 0)} points this week. Keep it up!"
            elif direction == "up":
                insight = f"Your carbon score rose by {trends.get('change', 0)} points. Try the tips below to reverse the trend."
            else:
                insight = "Your carbon footprint is stable. Small changes can make a big difference!"
            return {
                "summary": summary,
                "trends": trends,
                "ai_insight": insight,
                "ai_tip": tip,
            }
        except Exception as e:
            logger.warning("Failed to generate AI insights: %s", e)
            return {
                "summary": summary,
                "trends": trends,
                "ai_insight": None,
                "ai_tip": None,
            }
