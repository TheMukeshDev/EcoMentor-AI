"""Weekly Sustainability Report service.

Generates a comprehensive weekly carbon report comparing the user's
performance against their previous week and the global average.
Triggered by Cloud Scheduler or on-demand via GET endpoint.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.schemas.ai_schemas import WeeklyReportResponse

logger = logging.getLogger(__name__)

GLOBAL_AVG_WEEKLY_KG = 90.4

SYSTEM_INSTRUCTION = (
    "You are EcoMentor, a carbon reduction expert. Ground every response in "
    "verified IPCC emission factors. Always include at least one specific "
    "kg CO2e figure. Never invent statistics — if uncertain, say so and give "
    "a conservative estimate with source."
)


class ReportService:
    """Generates weekly sustainability reports with AI insights.

    Args:
        ai_service: The shared AIService for Gemini calls.
        carbon_history_repo: Repository for carbon history data.
        user_repo: Repository for user profile data.
        cache_service: Shared cache service instance.
    """

    def __init__(
        self,
        ai_service: Any,
        carbon_history_repo: Any,
        user_repo: Any,
        cache_service: Any,
    ) -> None:
        self._ai = ai_service
        self._carbon_history_repo = carbon_history_repo
        self._user_repo = user_repo
        self._cache = cache_service

    def generate_report(self, user_id: str) -> dict[str, Any]:
        """Generate a weekly sustainability report for a user.

        Args:
            user_id: The authenticated user's ID.

        Returns:
            Validated weekly report dict.
        """
        cached = self._cache.get(user_id, "weekly_sustainability_report")
        if cached:
            return cached

        context = self._build_context(user_id)
        prompt = self._build_prompt(context)
        result = self._ai._call_gemini(prompt, deterministic=True)

        validated = self._validate_response(result)
        if validated:
            self._cache.set(user_id, "weekly_sustainability_report", validated)
            return validated

        return self._fallback_report(context)

    def _build_context(self, user_id: str) -> dict[str, Any]:
        """Gather weekly context for report generation.

        Args:
            user_id: The user's ID.

        Returns:
            Dict with current/previous week data and user profile.
        """
        user = self._user_repo.get(user_id) or {}
        today = datetime.now(timezone.utc)

        current_start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        current_end = today.strftime("%Y-%m-%d")
        previous_start = (today - timedelta(days=14)).strftime("%Y-%m-%d")
        previous_end = (today - timedelta(days=8)).strftime("%Y-%m-%d")

        current = self._carbon_history_repo.find_by_user_and_date_range(
            user_id, current_start, current_end
        )
        previous = self._carbon_history_repo.find_by_user_and_date_range(
            user_id, previous_start, previous_end
        )

        current_total = sum(e.get("carbon_score", 0) for e in current)
        previous_total = sum(e.get("carbon_score", 0) for e in previous)

        return {
            "user_level": user.get("level", "Beginner"),
            "streak_days": user.get("streak", 0),
            "period_start": current_start,
            "period_end": current_end,
            "current_total_kg": round(current_total, 2),
            "previous_total_kg": round(previous_total, 2),
            "current_entries": current,
            "categories": self._category_totals(current),
        }

    def _category_totals(
        self, entries: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Sum each emission category across entries.

        Args:
            entries: List of carbon history entry dicts.

        Returns:
            Dict mapping category name to total kg.
        """
        totals: dict[str, float] = {}
        for entry in entries:
            for cat in ("transport", "electricity", "food", "waste"):
                totals[cat] = totals.get(cat, 0) + entry.get(cat, 0)
        return {k: round(v, 2) for k, v in totals.items()}

    def _compute_pct_change(
        self, current: float, previous: float
    ) -> float:
        """Calculate percentage change between two values.

        Args:
            current: Current period value.
            previous: Previous period value.

        Returns:
            Percentage change (negative means improvement).
        """
        if previous == 0:
            return 0.0
        return round(((current - previous) / previous) * 100, 1)

    def _build_prompt(self, context: dict[str, Any]) -> str:
        """Construct the Gemini prompt for weekly report.

        Args:
            context: User context data dict.

        Returns:
            Formatted prompt string for Gemini.
        """
        vs_last = self._compute_pct_change(
            context["current_total_kg"], context["previous_total_kg"]
        )
        vs_global = self._compute_pct_change(
            context["current_total_kg"], GLOBAL_AVG_WEEKLY_KG
        )

        return f"""{SYSTEM_INSTRUCTION}

Generate a weekly sustainability report for this user.

Period: {context['period_start']} to {context['period_end']}
Total CO2e this week: {context['current_total_kg']} kg
Total CO2e last week: {context['previous_total_kg']} kg
Change vs last week: {vs_last}%
Global average: {GLOBAL_AVG_WEEKLY_KG} kg/week
Change vs global: {vs_global}%
User level: {context['user_level']}
Streak: {context['streak_days']} days
Category breakdown: {context['categories']}

Return ONLY valid JSON:
{{
  "period": {{"start": "{context['period_start']}", "end": "{context['period_end']}"}},
  "total_co2e_kg": {context['current_total_kg']},
  "vs_last_week_pct": {vs_last},
  "vs_global_avg_pct": {vs_global},
  "biggest_win": "description of best achievement with kg CO2e saved",
  "top_opportunity": {{"action": "specific action", "saving_kg": 0.0}},
  "challenge": {{"title": "challenge name", "description": "details", "target_saving_kg": 0.0}},
  "streak_days": {context['streak_days']}
}}

Rules:
- Reference specific kg CO2e figures
- Be encouraging but data-driven
- Challenge should be achievable in one week"""

    def _validate_response(
        self, result: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Validate Gemini response against WeeklyReportResponse schema.

        Args:
            result: Raw parsed Gemini response dict.

        Returns:
            Validated dict or None if validation fails.
        """
        if not result or not isinstance(result, dict):
            return None
        try:
            validated = WeeklyReportResponse(**result)
            return validated.model_dump()
        except Exception as exc:
            logger.warning("Report validation failed: %s", exc)
            return None

    def _fallback_report(self, context: dict[str, Any]) -> dict[str, Any]:
        """Generate a rule-based fallback weekly report.

        Args:
            context: User context data dict.

        Returns:
            Fallback weekly report dict.
        """
        current = context["current_total_kg"]
        previous = context["previous_total_kg"]
        vs_last = self._compute_pct_change(current, previous)
        vs_global = self._compute_pct_change(current, GLOBAL_AVG_WEEKLY_KG)

        categories = context.get("categories", {})
        best_cat = min(categories, key=lambda k: categories[k]) if categories else "food"

        return {
            "period": {
                "start": context["period_start"],
                "end": context["period_end"],
            },
            "total_co2e_kg": current,
            "vs_last_week_pct": vs_last,
            "vs_global_avg_pct": vs_global,
            "biggest_win": f"Lowest emissions in {best_cat} category",
            "top_opportunity": {
                "action": "Walk or cycle for short trips under 3 km",
                "saving_kg": 2.5,
            },
            "challenge": {
                "title": "Green Commute Week",
                "description": "Use public transport or walk for all commutes this week",
                "target_saving_kg": 5.0,
            },
            "streak_days": context.get("streak_days", 0),
        }
