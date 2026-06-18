"""What-If Simulator service.

Allows users to explore hypothetical lifestyle changes and see
their projected annual carbon savings, monthly projections, and
real-world equivalents.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.schemas.ai_schemas import SimulatorResponse

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "You are EcoMentor, a carbon reduction expert. Ground every response in "
    "verified IPCC emission factors. Always include at least one specific "
    "kg CO2e figure. Never invent statistics — if uncertain, say so and give "
    "a conservative estimate with source."
)

# Conversion factors for equivalents
KG_CO2_PER_TREE_PER_YEAR = 22.0
KG_CO2_PER_KM_DRIVEN = 0.171
KG_CO2_PER_SHORT_FLIGHT = 200.0


class SimulatorService:
    """Simulates the carbon impact of hypothetical lifestyle changes.

    Args:
        ai_service: The shared AIService for Gemini calls.
        carbon_history_repo: Repository for carbon history data.
        user_repo: Repository for user profile data.
    """

    def __init__(
        self,
        ai_service: Any,
        carbon_history_repo: Any,
        user_repo: Any,
    ) -> None:
        self._ai = ai_service
        self._carbon_history_repo = carbon_history_repo
        self._user_repo = user_repo

    def simulate(self, user_id: str, scenario: str) -> dict[str, Any]:
        """Run a what-if simulation for a given scenario.

        Args:
            user_id: The authenticated user's ID.
            scenario: Natural language description of the lifestyle change.

        Returns:
            Validated simulation result with projections and equivalents.
        """
        context = self._build_context(user_id)
        prompt = self._build_prompt(scenario, context)
        result = self._ai._call_gemini(prompt, deterministic=True)

        validated = self._validate_response(result)
        if validated:
            return validated

        logger.info("Simulator fallback triggered for user %s", user_id)
        return self._fallback_response(scenario, context)

    def _build_context(self, user_id: str) -> dict[str, Any]:
        """Gather user context for simulation accuracy.

        Args:
            user_id: The user's ID.

        Returns:
            Dict with user profile and recent emission data.
        """
        user = self._user_repo.get(user_id) or {}
        today = datetime.now(timezone.utc)
        start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")

        history = self._carbon_history_repo.find_by_user_and_date_range(
            user_id, start, end
        )
        weekly_avg = self._compute_weekly_avg(history)

        return {
            "user_level": user.get("level", "Beginner"),
            "weekly_co2e_kg": weekly_avg,
            "annual_co2e_kg": round(weekly_avg * 52, 2),
            "diet_type": user.get("diet_type", "mixed"),
            "primary_transport": user.get("primary_transport", "car"),
        }

    def _compute_weekly_avg(
        self, history: list[dict[str, Any]]
    ) -> float:
        """Calculate average weekly emissions from history.

        Args:
            history: List of carbon history entries.

        Returns:
            Weekly average CO2e in kg.
        """
        if not history:
            return 90.4  # Use global average as default
        total = sum(e.get("carbon_score", 0) for e in history)
        weeks = max(len(history) / 7, 1)
        return round(total / weeks, 2)

    def _build_prompt(
        self, scenario: str, context: dict[str, Any]
    ) -> str:
        """Build the Gemini prompt for what-if simulation.

        Args:
            scenario: User's scenario description.
            context: User context data dict.

        Returns:
            Formatted prompt string.
        """
        return f"""{SYSTEM_INSTRUCTION}

Simulate the carbon impact of this lifestyle change scenario.

Scenario: "{scenario}"

User context:
- Current weekly CO2e: {context['weekly_co2e_kg']} kg
- Estimated annual CO2e: {context['annual_co2e_kg']} kg
- User level: {context['user_level']}
- Diet: {context['diet_type']}
- Primary transport: {context['primary_transport']}

Return ONLY valid JSON:
{{
  "scenario_description": "clear description of what changes",
  "annual_saving_kg": 0.0,
  "monthly_projection": [
    {{"month": 1, "co2e_kg": 0.0}},
    {{"month": 2, "co2e_kg": 0.0}}
  ],
  "equivalents": {{
    "trees_planted": 0.0,
    "km_not_driven": 0.0,
    "flights_avoided": 0.0
  }},
  "steps": ["step 1", "step 2"],
  "difficulty": 5
}}

Rules:
- annual_saving_kg MUST be between 0 and 3000
- Include 12 months in monthly_projection
- Calculate equivalents: 1 tree absorbs ~22 kg CO2/year
- 1 km not driven saves ~0.171 kg CO2
- 1 short flight ≈ 200 kg CO2
- Be realistic and conservative
- difficulty 1-10 based on lifestyle disruption"""

    def _validate_response(
        self, result: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Validate and guard against hallucinated savings.

        Args:
            result: Raw parsed Gemini response dict.

        Returns:
            Validated dict or None if validation fails.
        """
        if not result or not isinstance(result, dict):
            return None
        try:
            annual = result.get("annual_saving_kg", 0)
            if annual < 0 or annual > 3000:
                logger.warning(
                    "Hallucination guard: annual_saving_kg=%s out of range",
                    annual,
                )
                result["annual_saving_kg"] = min(max(annual, 0), 3000)

            validated = SimulatorResponse(**result)
            return validated.model_dump()
        except Exception as exc:
            logger.warning("Simulator validation failed: %s", exc)
            return None

    def _compute_equivalents(
        self, annual_kg: float
    ) -> dict[str, float]:
        """Convert annual savings to real-world equivalents.

        Args:
            annual_kg: Annual CO2e savings in kg.

        Returns:
            Dict with trees_planted, km_not_driven, flights_avoided.
        """
        return {
            "trees_planted": round(annual_kg / KG_CO2_PER_TREE_PER_YEAR, 1),
            "km_not_driven": round(annual_kg / KG_CO2_PER_KM_DRIVEN, 0),
            "flights_avoided": round(annual_kg / KG_CO2_PER_SHORT_FLIGHT, 1),
        }

    def _fallback_response(
        self, scenario: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate a rule-based fallback simulation result.

        Args:
            scenario: User's scenario description.
            context: User context data dict.

        Returns:
            Fallback simulation result dict.
        """
        annual_saving = round(context["weekly_co2e_kg"] * 52 * 0.1, 2)
        annual_saving = min(annual_saving, 3000)
        monthly_saving = round(annual_saving / 12, 2)

        monthly_projection = []
        for month in range(1, 13):
            cumulative = round(monthly_saving * month, 2)
            monthly_projection.append({"month": month, "co2e_kg": cumulative})

        return {
            "scenario_description": scenario[:500],
            "annual_saving_kg": annual_saving,
            "monthly_projection": monthly_projection,
            "equivalents": self._compute_equivalents(annual_saving),
            "steps": [
                "Start with small daily changes this week",
                "Track your progress in the EcoMentor dashboard",
                "Gradually increase your commitment each month",
            ],
            "difficulty": 5,
        }
