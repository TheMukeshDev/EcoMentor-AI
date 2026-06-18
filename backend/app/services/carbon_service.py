import logging
from typing import Any

logger = logging.getLogger(__name__)

# Emission factors (kg CO₂ per unit)
TRANSPORT: dict[str, float] = {
    "walking": 0,
    "bicycle": 0,
    "metro": 2,
    "bus": 4,
    "bike": 8,
    "car": 10,
    "plane": 20,
}

FOOD: dict[str, float] = {
    "vegan": 1,
    "vegetarian": 2,
    "non_vegetarian": 6,
}

AC_HOURS: dict[str, float] = {
    "none": 0,
    "1-2": 1.5,
    "3-5": 4,
    "6+": 8,
}

# Gemini emission factors (kg CO₂ per unit) — aligned with CarbonService
GEMINI_TRANSPORT: dict[str, float] = {
    "walking": 0,
    "bicycle": 0,
    "bus": 0.089,
    "metro": 0.041,
    "car": 0.171,
    "plane": 0.255,
}

GEMINI_FOOD: dict[str, float] = {
    "vegan": 1.5,
    "vegetarian": 1.7,
    "non_vegetarian": 2.5,
}

GEMINI_AC: dict[str, float] = {
    "none": 0,
    "1-2": 0.5,
    "3-5": 1.2,
    "6+": 2.0,
}

ELECTRICITY_PER_HOUR: float = 0.5
PLASTIC_PER_KG: float = 2.0
DISTANCE_FACTOR: float = 0.1

REGIONAL_FACTORS: dict[str, dict[str, Any]] = {
    "us": {"grid_intensity": 0.85, "label": "United States"},
    "eu": {"grid_intensity": 0.65, "label": "Europe"},
    "india": {"grid_intensity": 1.2, "label": "India"},
    "china": {"grid_intensity": 1.3, "label": "China"},
    "global": {"grid_intensity": 1.0, "label": "Global Average"},
}


def estimate_gemini_carbon(data: dict[str, Any]) -> float:
    transport = data.get("transport", "walking")
    distance = float(data.get("distance", 0))
    food_type = data.get("food_type", "vegetarian")
    ac_usage = data.get("ac_usage", "none")
    plastic_waste = float(data.get("plastic_waste", 0))

    transport_factor = GEMINI_TRANSPORT.get(transport, 0.089)
    food_factor = GEMINI_FOOD.get(food_type, 1.7)
    ac_factor = GEMINI_AC.get(ac_usage, 0)

    return round(
        transport_factor * distance + food_factor + ac_factor + plastic_waste * 0.5, 2
    )


class CarbonService:
    def __init__(self, region: str = "global") -> None:
        self.region = region if region in REGIONAL_FACTORS else "global"
        self._grid_factor = REGIONAL_FACTORS[self.region]["grid_intensity"]

    def set_region(self, region: str) -> None:
        if region in REGIONAL_FACTORS:
            self.region = region
            self._grid_factor = REGIONAL_FACTORS[region]["grid_intensity"]

    def _compute_scores(
        self,
        transport: str,
        distance: float,
        ac_usage: str,
        food_type: str,
        plastic_waste: float,
    ) -> dict[str, float]:
        transport_score = TRANSPORT.get(transport, 0) * distance * DISTANCE_FACTOR
        ac_hours = AC_HOURS.get(ac_usage, 0)
        ac_score = ac_hours * ELECTRICITY_PER_HOUR * self._grid_factor
        food_score = FOOD.get(food_type, 2) * 0.5
        waste_score = plastic_waste * PLASTIC_PER_KG
        return {
            "transport": round(transport_score, 2),
            "electricity": round(ac_score, 2),
            "food": round(food_score, 2),
            "waste": round(waste_score, 2),
        }

    def calculate(
        self,
        transport: str,
        distance: float,
        ac_usage: str,
        food_type: str,
        plastic_waste: float,
    ) -> float:
        scores = self._compute_scores(
            transport, distance, ac_usage, food_type, plastic_waste
        )
        return round(sum(scores.values()), 2)

    def get_breakdown(
        self,
        transport: str,
        distance: float,
        ac_usage: str,
        food_type: str,
        plastic_waste: float,
    ) -> dict[str, float]:
        scores = self._compute_scores(
            transport, distance, ac_usage, food_type, plastic_waste
        )
        return {
            "total": round(sum(scores.values()), 2),
            **scores,
        }

    @staticmethod
    def get_regions() -> dict[str, str]:
        return {k: v["label"] for k, v in REGIONAL_FACTORS.items()}
