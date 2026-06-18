from datetime import datetime, timezone, timedelta


class StreakService:
    def __init__(self, user_repository):
        self._user_repo = user_repository

    def get_streak(self, user_id):
        user = self._user_repo.get(user_id)
        if not user:
            return 0
        return user.get("streak", 0)

    def update_streak(self, user_id, activity_date_str):
        user = self._user_repo.get(user_id)
        if not user:
            self._user_repo.set(
                user_id, {"streak": 1, "last_activity_date": activity_date_str}
            )
            return 1

        current_streak = user.get("streak", 0)
        last_date_str = user.get("last_activity_date")

        if last_date_str == activity_date_str:
            return current_streak

        try:
            activity_date = datetime.strptime(activity_date_str, "%Y-%m-%d").date()
            if last_date_str:
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
                expected = last_date + timedelta(days=1)
                if activity_date == expected:
                    current_streak += 1
                elif activity_date > expected:
                    current_streak = 0
            else:
                current_streak = 1
        except ValueError:
            current_streak = 0

        self._user_repo.update(
            user_id,
            {
                "streak": current_streak,
                "last_activity_date": activity_date_str,
            },
        )
        return current_streak
