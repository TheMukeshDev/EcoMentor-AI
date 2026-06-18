import logging

logger = logging.getLogger(__name__)

TRANSPORT = {
    "walking": 0,
    "bicycle": 0,
    "metro": 2,
    "bus": 4,
    "bike": 8,
    "car": 10,
    "plane": 20,
}

FOOD = {
    "vegan": 1,
    "vegetarian": 2,
    "non_vegetarian": 6,
}

AC_HOURS = {
    "none": 0,
    "1-2": 1.5,
    "3-5": 4,
    "6+": 8,
}

ELECTRICITY_PER_HOUR = 0.5
PLASTIC_PER_KG = 2.0
DISTANCE_FACTOR = 0.1

REGIONAL_FACTORS = {
    "us": {"grid_intensity": 0.85, "label": "United States"},
    "eu": {"grid_intensity": 0.65, "label": "Europe"},
    "india": {"grid_intensity": 1.2, "label": "India"},
    "china": {"grid_intensity": 1.3, "label": "China"},
    "global": {"grid_intensity": 1.0, "label": "Global Average"},
}


class CarbonService:
    def __init__(self, region="global"):
        self.region = region if region in REGIONAL_FACTORS else "global"
        self._grid_factor = REGIONAL_FACTORS[self.region]["grid_intensity"]

    def set_region(self, region):
        if region in REGIONAL_FACTORS:
            self.region = region
            self._grid_factor = REGIONAL_FACTORS[region]["grid_intensity"]

    def _compute_scores(self, transport, distance, ac_usage, food_type, plastic_waste):
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

    def calculate(self, transport, distance, ac_usage, food_type, plastic_waste):
        scores = self._compute_scores(
            transport, distance, ac_usage, food_type, plastic_waste
        )
        return round(sum(scores.values()), 2)

    def get_breakdown(self, transport, distance, ac_usage, food_type, plastic_waste):
        scores = self._compute_scores(
            transport, distance, ac_usage, food_type, plastic_waste
        )
        return {
            "total": round(sum(scores.values()), 2),
            **scores,
        }

    @staticmethod
    def get_regions():
        return {k: v["label"] for k, v in REGIONAL_FACTORS.items()}
