"""Dashboard service for aggregating carbon footprint analytics.

Provides summary, history, trends, and AI-powered insight
generation for the user's dashboard view.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HistoryPeriod(str, Enum):
    """Supported time periods for carbon history queries."""

    LAST_7 = "last_7"
    LAST_30 = "last_30"


_PERIOD_DAYS: dict[str, int] = {
    HistoryPeriod.LAST_7: 7,
    HistoryPeriod.LAST_30: 30,
}


class DefaultActivityProfile(str, Enum):
    """Default lifestyle values used when building AI recommendation context."""

    TRANSPORT = "walking"
    FOOD = "vegetarian"
    AC_USAGE = "none"


class DashboardService:
    """Aggregates carbon data into dashboard-ready summaries and insights."""

    def __init__(
        self,
        carbon_history_repository: Any,
        activity_repository: Any,
        user_repository: Any,
        ai_service: Any | None = None,
    ) -> None:
        self._carbon_history_repo = carbon_history_repository
        self._activity_repo = activity_repository
        self._user_repo = user_repository
        self._ai_service = ai_service

    def get_summary(self, user_id: str) -> dict[str, Any]:
        """Get high-level dashboard summary for a user.

        Args:
            user_id: The authenticated user's unique identifier.

        Returns:
            Dictionary containing current score, weekly average,
            streak count, and total activities logged.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

        user = self._user_repo.get(user_id)
        streak = user.get("streak", 0) if user else 0

        today_entry = self._carbon_history_repo.find_by_user_and_date(user_id, today)
        current_score = today_entry.get("carbon_score", 0) if today_entry else 0

        week_entries = self._carbon_history_repo.find_by_user_and_date_range(
            user_id, seven_days_ago, today
        )
        weekly_average = _compute_average(week_entries, "carbon_score")

        activities = self._activity_repo.find_by_user_id(user_id)
        activities_logged = len(activities)

        return {
            "current_score": current_score,
            "weekly_average": weekly_average,
            "streak": streak,
            "activities_logged": activities_logged,
        }

    def get_history(self, user_id: str, period: str) -> list[dict[str, Any]]:
        """Get carbon history over a specified period.

        Args:
            user_id: The authenticated user's unique identifier.
            period: One of 'last_7' or 'last_30'.

        Returns:
            List of daily carbon score entries with category breakdowns.
        """
        days = _PERIOD_DAYS.get(period, 7)
        today = datetime.now(timezone.utc)
        start = (today - timedelta(days=days)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")

        entries = self._carbon_history_repo.find_by_user_and_date_range(user_id, start, end)
        return [
            {
                "date": entry.get("date"),
                "carbon_score": entry.get("carbon_score", 0),
                "transport": entry.get("transport", 0),
                "electricity": entry.get("electricity", 0),
                "food": entry.get("food", 0),
                "waste": entry.get("waste", 0),
            }
            for entry in entries
        ]

    def get_trends(self, user_id: str) -> dict[str, Any]:
        """Calculate week-over-week carbon emission trends.

        Args:
            user_id: The authenticated user's unique identifier.

        Returns:
            Dictionary with current/previous week averages,
            absolute change, and direction indicator.
        """
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

        current_avg = _compute_average(current_entries, "carbon_score")
        previous_avg = _compute_average(previous_entries, "carbon_score")

        change = round(current_avg - previous_avg, 2)
        direction = _determine_trend_direction(change)

        return {
            "current_week_avg": current_avg,
            "previous_week_avg": previous_avg,
            "change": abs(change),
            "direction": direction,
        }

    def get_insights(self, user_id: str) -> dict[str, Any]:
        """Generate AI-powered insights based on user carbon footprint.

        Combines the user's summary and trend data, then optionally
        queries the AI service for a personalised tip.

        Args:
            user_id: The authenticated user's unique identifier.

        Returns:
            Dictionary with summary, trends, AI insight message,
            and AI tip (or None if AI is unavailable).
        """
        summary = self.get_summary(user_id)
        trends = self.get_trends(user_id)

        if not self._ai_service:
            return _build_insight_response(summary, trends)

        try:
            recommendation_context = {
                "score": summary.get("current_score", 0),
                "transport": DefaultActivityProfile.TRANSPORT.value,
                "food": DefaultActivityProfile.FOOD.value,
                "ac_usage": DefaultActivityProfile.AC_USAGE.value,
            }
            recommendations = self._ai_service.get_recommendations(user_id, recommendation_context)
            tip = _extract_first_tip(recommendations)
            insight = _generate_insight_message(trends)

            return _build_insight_response(summary, trends, ai_insight=insight, ai_tip=tip)
        except Exception as exc:
            logger.warning("Failed to generate AI insights: %s", exc)
            return _build_insight_response(summary, trends)

    @staticmethod
    def _avg_field(entries, field):
        vals = [e.get(field, 0) for e in entries]
        return round(sum(vals) / len(vals), 2) if vals else 0

    @staticmethod
    def _compute_trend(scores):
        if len(scores) < 2:
            return "stable"
        window = scores[-3:] if len(scores) >= 3 else scores
        if window[-1] < window[0]:
            return "improving"
        if window[-1] > window[0]:
            return "declining"
        return "stable"

    @staticmethod
    def _best_worst_category(week_entries):
        totals = {}
        counts = {}
        for e in week_entries:
            for cat in ("transport", "electricity", "food", "waste"):
                val = e.get(cat, 0)
                if val:
                    totals[cat] = totals.get(cat, 0) + val
                    counts[cat] = counts.get(cat, 0) + 1
        avgs = {c: (totals[c] / counts[c] if counts.get(c) else 0) for c in totals}
        if not avgs:
            return "transport", "transport"
        worst = max(avgs, key=avgs.get)
        best = min(avgs, key=avgs.get)
        return best, worst

    def build_user_context(self, user_id):
        user = self._user_repo.get(user_id) or {}
        today = datetime.now(timezone.utc)
        seven_days_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        week_entries = self._carbon_history_repo.find_by_user_and_date_range(
            user_id, seven_days_ago, today.strftime("%Y-%m-%d")
        )
        scores = [e.get("carbon_score", 0) for e in week_entries]
        weekly_avg = round(sum(scores) / len(scores), 2) if scores else 0
        activities = self._activity_repo.find_by_user_id(user_id)
        best_cat, worst_cat = DashboardService._best_worst_category(week_entries)

        return {
            "level": user.get("level", "Beginner"),
            "streak": user.get("streak", 0),
            "weekly_avg": weekly_avg,
            "current_score": scores[-1] if scores else 0,
            "activity_count": len(activities),
            "score_trend": DashboardService._compute_trend(scores),
            "best_category": best_cat,
            "worst_category": worst_cat,
            "score_history": scores[-7:] if scores else [],
            "weekly_data": {
                "transport_avg": DashboardService._avg_field(week_entries, "transport"),
                "electricity_avg": DashboardService._avg_field(week_entries, "electricity"),
                "food_avg": DashboardService._avg_field(week_entries, "food"),
                "waste_avg": DashboardService._avg_field(week_entries, "waste"),
            },
        }


# ---------------------------------------------------------------------------
# Private helper functions
# ---------------------------------------------------------------------------


def _compute_average(entries: list[dict[str, Any]], field: str) -> float:
    """Compute the average value of a numeric field across entries.

    Args:
        entries: List of dictionary records.
        field: The key whose values to average.

    Returns:
        Rounded average, or 0 if entries is empty.
    """
    if not entries:
        return 0
    scores = [entry.get(field, 0) for entry in entries]
    return round(sum(scores) / len(scores), 2)


def _determine_trend_direction(change: float) -> str:
    """Classify a numeric change into a trend direction.

    Args:
        change: The signed difference between current and previous values.

    Returns:
        One of 'up', 'down', or 'stable'.
    """
    if change > 0:
        return "up"
    if change < 0:
        return "down"
    return "stable"


def _extract_first_tip(
    recommendations: dict[str, Any] | None,
) -> str | None:
    """Safely extract the first tip from AI recommendations.

    Args:
        recommendations: The AI service response dictionary.

    Returns:
        The first tip string, or None.
    """
    if not recommendations:
        return None
    tips = recommendations.get("tips")
    if isinstance(tips, list) and tips:
        return tips[0]
    return None


def _generate_insight_message(trends: dict[str, Any]) -> str:
    """Build a human-readable insight message from trend data.

    Args:
        trends: Dictionary with 'direction' and 'change' keys.

    Returns:
        A motivational insight string.
    """
    direction = trends.get("direction", "stable")
    change = trends.get("change", 0)

    if direction == "down":
        return f"Your carbon score dropped by {change} points this week. Keep it up!"
    if direction == "up":
        return (
            f"Your carbon score rose by {change} points. Try the tips below to reverse the trend."
        )
    return "Your carbon footprint is stable. Small changes can make a big difference!"


def _build_insight_response(
    summary: dict[str, Any],
    trends: dict[str, Any],
    ai_insight: str | None = None,
    ai_tip: str | None = None,
) -> dict[str, Any]:
    """Construct the standard insights response payload.

    Args:
        summary: The dashboard summary dictionary.
        trends: The trend analysis dictionary.
        ai_insight: Optional AI-generated insight message.
        ai_tip: Optional AI-generated tip.

    Returns:
        Standardised insights response dictionary.
    """
    return {
        "summary": summary,
        "trends": trends,
        "ai_insight": ai_insight,
        "ai_tip": ai_tip,
    }
