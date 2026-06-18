"""Habit Engine service.

Rule-based habit suggestion layer that fires BEFORE Gemini to reduce
API costs. Only escalates to Gemini for personalization of the
rule-based suggestion.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.schemas.ai_schemas import HabitCard, HabitResponse

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "You are EcoMentor, a carbon reduction expert. Ground every response in "
    "verified IPCC emission factors. Always include at least one specific "
    "kg CO2e figure. Never invent statistics — if uncertain, say so and give "
    "a conservative estimate with source."
)

# ── Rule-based habit triggers ─────────────────────────────────────

_DEFAULT_HABITS: list[dict[str, Any]] = [
    {
        "title": "Switch to Plant-Based Meals",
        "description": "Replace 3 beef meals per week with plant-based alternatives to save ~9 kg CO2e/week.",
        "category": "food",
        "impact_kg_per_month": 36.0,
        "difficulty": 3,
        "days_to_form": 21,
        "tracking_metric": "plant-based meals per week",
    },
    {
        "title": "Active Commute Challenge",
        "description": "Walk or cycle for trips under 3 km instead of driving. Saves ~1.0 kg CO2e per trip.",
        "category": "transport",
        "impact_kg_per_month": 20.0,
        "difficulty": 2,
        "days_to_form": 14,
        "tracking_metric": "active commute trips per week",
    },
    {
        "title": "Energy Audit at Home",
        "description": "Reduce electricity usage by 10% through LED bulbs and unplugging standby devices.",
        "category": "electricity",
        "impact_kg_per_month": 15.0,
        "difficulty": 2,
        "days_to_form": 30,
        "tracking_metric": "kWh saved per week",
    },
]


class HabitService:
    """Generates habit suggestions using rules first, Gemini second.

    Args:
        ai_service: The shared AIService for Gemini calls.
        activity_repo: Repository for user activity data.
        carbon_history_repo: Repository for carbon history data.
        user_repo: Repository for user profile data.
        cache_service: Shared cache service instance.
    """

    def __init__(
        self,
        ai_service: Any,
        activity_repo: Any,
        carbon_history_repo: Any,
        user_repo: Any,
        cache_service: Any,
    ) -> None:
        self._ai = ai_service
        self._activity_repo = activity_repo
        self._carbon_history_repo = carbon_history_repo
        self._user_repo = user_repo
        self._cache = cache_service

    def get_habits(self, user_id: str) -> dict[str, Any]:
        """Generate personalized habit suggestions for a user.

        Args:
            user_id: The authenticated user's ID.

        Returns:
            Dict with a list of habit cards.
        """
        cached = self._cache.get(user_id, "habits")
        if cached:
            return cached

        context = self._build_context(user_id)
        rule_habits = self._apply_rules(context)

        if rule_habits:
            personalized = self._personalize_with_ai(rule_habits, context)
            result = personalized or {"habits": rule_habits}
        else:
            result = {"habits": _DEFAULT_HABITS}

        self._cache.set(user_id, "habits", result)
        return result

    def _build_context(self, user_id: str) -> dict[str, Any]:
        """Gather user behavior data for rule evaluation.

        Args:
            user_id: The user's ID.

        Returns:
            Dict with weekly behavior metrics.
        """
        user = self._user_repo.get(user_id) or {}
        today = datetime.now(timezone.utc)
        start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")

        activities = self._activity_repo.find_by_user_and_date_range(
            user_id, start, end
        ) if hasattr(self._activity_repo, "find_by_user_and_date_range") else []

        history = self._carbon_history_repo.find_by_user_and_date_range(
            user_id, start, end
        )

        car_trips = self._count_transport(activities, "car")
        beef_meals = self._count_food(activities, "non_vegetarian")
        electricity_kwh = self._sum_electricity(history)

        return {
            "user_level": user.get("level", "Beginner"),
            "streak_days": user.get("streak", 0),
            "car_trips_per_week": car_trips,
            "beef_meals_per_week": beef_meals,
            "electricity_kwh_per_month": electricity_kwh * 4,
            "weekly_co2e_kg": self._weekly_avg(history),
        }

    def _count_transport(
        self, activities: list[dict[str, Any]], transport_type: str
    ) -> int:
        """Count activities using a specific transport type.

        Args:
            activities: List of activity dicts.
            transport_type: Transport mode to count.

        Returns:
            Number of matching activities.
        """
        return sum(
            1 for a in activities if a.get("transport") == transport_type
        )

    def _count_food(
        self, activities: list[dict[str, Any]], food_type: str
    ) -> int:
        """Count activities with a specific food type.

        Args:
            activities: List of activity dicts.
            food_type: Food type to count.

        Returns:
            Number of matching activities.
        """
        return sum(
            1 for a in activities if a.get("food_type") == food_type
        )

    def _sum_electricity(
        self, history: list[dict[str, Any]]
    ) -> float:
        """Sum weekly electricity emissions from history.

        Args:
            history: List of carbon history entries.

        Returns:
            Total electricity emissions for the period.
        """
        return sum(e.get("electricity", 0) for e in history)

    def _weekly_avg(self, history: list[dict[str, Any]]) -> float:
        """Calculate average weekly emissions.

        Args:
            history: List of carbon history entries.

        Returns:
            Average weekly CO2e in kg.
        """
        if not history:
            return 0.0
        total = sum(e.get("carbon_score", 0) for e in history)
        return round(total, 2)

    def _apply_rules(
        self, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Apply rule-based triggers to generate habit suggestions.

        Args:
            context: User behavior context dict.

        Returns:
            List of habit card dicts triggered by rules.
        """
        habits: list[dict[str, Any]] = []

        if context["car_trips_per_week"] > 5:
            habits.append({
                "title": "Switch to Public Transit or EV",
                "description": (
                    f"You made {context['car_trips_per_week']} car trips this week. "
                    "Each km by car emits ~0.171 kg CO2e. Try bus (0.089 kg/km) "
                    "or metro (0.041 kg/km) instead."
                ),
                "category": "transport",
                "impact_kg_per_month": round(
                    context["car_trips_per_week"] * 5 * 0.1 * 4, 1
                ),
                "difficulty": 3,
                "days_to_form": 21,
                "tracking_metric": "public transit trips per week",
            })

        if context["beef_meals_per_week"] > 3:
            habits.append({
                "title": "Plant-Based Meal Swap",
                "description": (
                    f"You had {context['beef_meals_per_week']} non-vegetarian meals. "
                    "Beef produces ~27 kg CO2e/kg (IPCC). Try swapping 2 meals "
                    "with plant-based alternatives to save ~6 kg CO2e/week."
                ),
                "category": "food",
                "impact_kg_per_month": 24.0,
                "difficulty": 2,
                "days_to_form": 14,
                "tracking_metric": "plant-based meals per week",
            })

        if context["electricity_kwh_per_month"] > 300:
            habits.append({
                "title": "Home Energy Audit",
                "description": (
                    "Your electricity usage is above 300 kWh/month. "
                    "Schedule an energy audit, switch to LED bulbs (~75% less "
                    "energy), and unplug standby devices to save ~0.5 kg CO2e/kWh."
                ),
                "category": "electricity",
                "impact_kg_per_month": 30.0,
                "difficulty": 2,
                "days_to_form": 30,
                "tracking_metric": "kWh reduced per month",
            })

        return habits

    def _personalize_with_ai(
        self,
        rule_habits: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Enhance rule-based habits with Gemini personalization.

        Args:
            rule_habits: List of rule-triggered habit dicts.
            context: User behavior context dict.

        Returns:
            Validated habit response dict, or None on failure.
        """
        habits_text = "\n".join(
            f"- {h['title']}: {h['description']}" for h in rule_habits
        )

        prompt = f"""{SYSTEM_INSTRUCTION}

Personalize these habit suggestions for the user.

Rule-triggered habits:
{habits_text}

User context:
- Level: {context['user_level']}
- Streak: {context['streak_days']} days
- Weekly CO2e: {context['weekly_co2e_kg']} kg

Return ONLY valid JSON:
{{
  "habits": [
    {{
      "title": "habit title",
      "description": "personalized description with kg CO2e figures",
      "category": "transport|food|electricity|waste",
      "impact_kg_per_month": 0.0,
      "difficulty": 3,
      "days_to_form": 21,
      "tracking_metric": "metric to track"
    }}
  ]
}}

Rules:
- Keep the core suggestions but personalize language
- Always include specific kg CO2e figures
- Each habit must be actionable and measurable"""

        result = self._ai._call_gemini(prompt, deterministic=True)
        return self._validate_response(result)

    def _validate_response(
        self, result: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Validate Gemini response against HabitResponse schema.

        Args:
            result: Raw parsed Gemini response dict.

        Returns:
            Validated dict or None if validation fails.
        """
        if not result or not isinstance(result, dict):
            return None
        try:
            validated = HabitResponse(**result)
            return validated.model_dump()
        except Exception as exc:
            logger.warning("Habit response validation failed: %s", exc)
            return None
