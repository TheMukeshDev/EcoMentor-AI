"""Personalized Carbon Coach service.

Analyzes the user's last 30 days of activity history and generates
a reduction plan via Gemini, validated against Pydantic schemas.
Caches results for 24 hours per user.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.schemas.ai_schemas import CoachResponse
from app.services.carbon_service import CarbonService

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "You are EcoMentor, a carbon reduction expert. Ground every response in "
    "verified IPCC emission factors. Always include at least one specific "
    "kg CO2e figure. Never invent statistics — if uncertain, say so and give "
    "a conservative estimate with source."
)

_CACHE_TTL_SECONDS = 86400  # 24 hours


class CoachService:
    """Generates personalized carbon reduction plans from user history.

    Args:
        ai_service: The shared AIService for Gemini calls.
        carbon_history_repo: Repository for carbon history data.
        activity_repo: Repository for user activity data.
        user_repo: Repository for user profile data.
        cache_service: Shared cache service instance.
    """

    def __init__(
        self,
        ai_service: Any,
        carbon_history_repo: Any,
        activity_repo: Any,
        user_repo: Any,
        cache_service: Any,
    ) -> None:
        self._ai = ai_service
        self._carbon_history_repo = carbon_history_repo
        self._activity_repo = activity_repo
        self._user_repo = user_repo
        self._cache = cache_service
        self._carbon = CarbonService()

    def get_coaching_plan(self, user_id: str) -> dict[str, Any]:
        """Generate a personalized carbon coaching plan.

        Args:
            user_id: The authenticated user's ID.

        Returns:
            Validated coaching plan with top categories and reduction plan.
        """
        cached = self._cache.get(user_id, "coach")
        if cached:
            return cached

        context = self._build_context(user_id)
        prompt = self._build_prompt(context)
        result = self._ai._call_gemini(prompt, deterministic=True)

        validated = self._validate_response(result)
        if validated:
            self._cache.set(user_id, "coach", validated)
            return validated

        return self._fallback_plan(context)

    def _build_context(self, user_id: str) -> dict[str, Any]:
        """Gather user context from last 30 days of data.

        Args:
            user_id: The user's ID.

        Returns:
            Dict with user profile, history stats, and category breakdowns.
        """
        user = self._user_repo.get(user_id) or {}
        today = datetime.now(timezone.utc)
        start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")

        history = self._carbon_history_repo.find_by_user_and_date_range(
            user_id, start, end
        )
        categories = self._aggregate_categories(history)

        return {
            "user_level": user.get("level", "Beginner"),
            "streak_days": user.get("streak", 0),
            "weekly_co2e_kg": self._weekly_avg(history),
            "top_emission_category": categories.get("worst", "transport"),
            "category_averages": categories.get("averages", {}),
            "activity_count": len(history),
        }

    def _aggregate_categories(
        self, history: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Compute per-category averages and identify worst/best.

        Args:
            history: List of carbon history entries.

        Returns:
            Dict with averages, worst, and best category names.
        """
        totals: dict[str, float] = {}
        count = len(history) or 1

        for entry in history:
            for cat in ("transport", "electricity", "food", "waste"):
                totals[cat] = totals.get(cat, 0) + entry.get(cat, 0)

        averages = {k: round(v / count, 2) for k, v in totals.items()}
        if not averages:
            return {"averages": {}, "worst": "transport", "best": "food"}

        worst = max(averages, key=lambda k: averages[k])
        best = min(averages, key=lambda k: averages[k])
        return {"averages": averages, "worst": worst, "best": best}

    def _weekly_avg(self, history: list[dict[str, Any]]) -> float:
        """Calculate average weekly CO2e from history entries.

        Args:
            history: List of carbon history entries.

        Returns:
            Average weekly CO2e in kg, rounded to 2 decimals.
        """
        if not history:
            return 0.0
        total = sum(e.get("carbon_score", 0) for e in history)
        weeks = max(len(history) / 7, 1)
        return round(total / weeks, 2)

    def _build_prompt(self, context: dict[str, Any]) -> str:
        """Construct the Gemini prompt for coaching plan generation.

        Args:
            context: User context data dict.

        Returns:
            Formatted prompt string for Gemini.
        """
        return f"""{SYSTEM_INSTRUCTION}

Analyze this user's carbon footprint and create a personalized reduction plan.

User context:
- Level: {context['user_level']}
- Streak: {context['streak_days']} days
- Weekly CO2e: {context['weekly_co2e_kg']} kg
- Top emission category: {context['top_emission_category']}
- Category averages (kg/day): {context['category_averages']}
- Activities logged (30 days): {context['activity_count']}
- Global average: 90.4 kg CO2e/week

Return ONLY valid JSON:
{{
  "top_3_categories": ["category1", "category2", "category3"],
  "reduction_plan": [
    {{
      "week": 1,
      "goal_kg": 5.0,
      "actions": ["specific action with kg CO2e saving"]
    }}
  ]
}}

Rules:
- Include 3-4 weeks in the plan
- Each action must mention a specific kg CO2e saving
- Be realistic based on user level and current emissions
- Focus on the top emission category first"""

    def _validate_response(
        self, result: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Validate Gemini response against the CoachResponse schema.

        Args:
            result: Raw parsed Gemini response dict.

        Returns:
            Validated dict or None if validation fails.
        """
        if not result or not isinstance(result, dict):
            return None
        try:
            validated = CoachResponse(**result)
            return validated.model_dump()
        except Exception as exc:
            logger.warning("Coach response validation failed: %s", exc)
            return None

    def _fallback_plan(self, context: dict[str, Any]) -> dict[str, Any]:
        """Generate a rule-based fallback coaching plan.

        Args:
            context: User context data dict.

        Returns:
            Fallback coaching plan dict.
        """
        worst = context.get("top_emission_category", "transport")
        weekly = context.get("weekly_co2e_kg", 90.4)
        target = round(weekly * 0.1, 2)

        return {
            "top_3_categories": [worst, "electricity", "food"],
            "reduction_plan": [
                {
                    "week": 1,
                    "goal_kg": target,
                    "actions": [
                        f"Reduce {worst} by choosing lower-emission alternatives (save ~{target} kg CO2e)",
                        "Switch to LED bulbs to save ~0.5 kg CO2e/week",
                    ],
                },
                {
                    "week": 2,
                    "goal_kg": round(target * 1.5, 2),
                    "actions": [
                        "Walk or cycle for trips under 3 km (save ~1.0 kg CO2e/trip)",
                        "Reduce meat consumption by 1 meal/week (save ~3.0 kg CO2e)",
                    ],
                },
                {
                    "week": 3,
                    "goal_kg": round(target * 2, 2),
                    "actions": [
                        "Batch errands to reduce car trips (save ~2.0 kg CO2e/week)",
                        "Turn off AC 1 hour earlier daily (save ~0.5 kg CO2e/day)",
                    ],
                },
            ],
        }
