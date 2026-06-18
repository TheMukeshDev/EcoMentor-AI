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


class CarbonService:
    def calculate(self, transport, distance, ac_usage, food_type, plastic_waste):
        transport_score = TRANSPORT.get(transport, 0) * distance * DISTANCE_FACTOR
        ac_hours = AC_HOURS.get(ac_usage, 0)
        ac_score = ac_hours * ELECTRICITY_PER_HOUR
        food_score = FOOD.get(food_type, 2) * 0.5
        waste_score = plastic_waste * PLASTIC_PER_KG
        return round(transport_score + ac_score + food_score + waste_score, 2)

    def get_breakdown(self, transport, distance, ac_usage, food_type, plastic_waste):
        transport_score = TRANSPORT.get(transport, 0) * distance * DISTANCE_FACTOR
        ac_hours = AC_HOURS.get(ac_usage, 0)
        ac_score = ac_hours * ELECTRICITY_PER_HOUR
        food_score = FOOD.get(food_type, 2) * 0.5
        waste_score = plastic_waste * PLASTIC_PER_KG
        total = round(transport_score + ac_score + food_score + waste_score, 2)
        return {
            "total": total,
            "transport": round(transport_score, 2),
            "electricity": round(ac_score, 2),
            "food": round(food_score, 2),
            "waste": round(waste_score, 2),
        }
