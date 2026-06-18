from google.cloud import firestore


class LeaderboardService:
    def __init__(self, user_repository, footprint_repository):
        self._user_repo = user_repository
        self._footprint_repo = footprint_repository

    def get_global_leaderboard(self, limit=20):
        users = self._user_repo.query(
            order_by=("points", firestore.Query.DESCENDING),
            limit=limit,
        )
        return [
            {
                "uid": u.get("id", u.get("uid", "")),
                "name": u.get("name", "Anonymous"),
                "level": u.get("level", "Beginner"),
                "points": u.get("points", 0),
            }
            for u in users
        ]

    def get_friends_leaderboard(self, user_id):
        return []
