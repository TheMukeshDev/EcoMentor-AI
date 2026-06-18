LEVELS = [
    {"name": "Beginner", "badge": "Seedling", "min_points": 0},
    {"name": "Explorer", "badge": "Sprout", "min_points": 100},
    {"name": "Eco Warrior", "badge": "Leaf", "min_points": 500},
    {"name": "Planet Hero", "badge": "Globe", "min_points": 2000},
]

POINTS_ACTIVITY_LOG = 10
POINTS_CHALLENGE_COMPLETE = 50
POINTS_7_DAY_STREAK = 100


class PointsService:
    def __init__(self, user_repository):
        self._user_repo = user_repository

    def add_points(self, user_id, amount, reason=""):
        user = self._user_repo.get(user_id)
        if not user:
            return None

        current_points = user.get("points", 0)
        new_points = current_points + amount

        level_info = self._calculate_level(new_points)
        updates = {
            "points": new_points,
            "level": level_info["name"],
            "badge": level_info["badge"],
        }
        self._user_repo.update(user_id, updates)

        result = {**updates, "points_earned": amount, "reason": reason}
        return result

    def get_points(self, user_id):
        user = self._user_repo.get(user_id)
        if not user:
            return 0
        return user.get("points", 0)

    def get_level_info(self, user_id):
        user = self._user_repo.get(user_id)
        if not user:
            return {"name": "Beginner", "badge": "Seedling", "points": 0}
        points = user.get("points", 0)
        level = self._calculate_level(points)
        return {
            "name": level["name"],
            "badge": level["badge"],
            "points": points,
            "next_level_points": level.get("next_min", None),
            "progress": level.get("progress", 100),
        }

    def _calculate_level(self, points):
        current = LEVELS[0]
        for i, level in enumerate(LEVELS):
            if points >= level["min_points"]:
                current = level
            if i + 1 < len(LEVELS) and points < LEVELS[i + 1]["min_points"]:
                next_min = LEVELS[i + 1]["min_points"]
                current_min = level["min_points"]
                range_size = next_min - current_min
                progress = (
                    min(100, int((points - current_min) / range_size * 100))
                    if range_size > 0
                    else 100
                )
                return {**current, "next_min": next_min, "progress": progress}
        return {**current, "next_min": None, "progress": 100}
