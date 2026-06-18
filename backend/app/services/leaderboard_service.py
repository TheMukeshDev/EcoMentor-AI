from typing import Optional

from google.cloud import firestore

from app.repositories.user_repository import UserRepository
from app.repositories.footprint_repository import FootprintRepository


class LeaderboardService:
    def __init__(
        self,
        user_repository: UserRepository,
        footprint_repository: FootprintRepository,
    ) -> None:
        self._user_repo = user_repository
        self._footprint_repo = footprint_repository

    def get_global_leaderboard(self, limit: int = 20) -> list[dict]:
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

    def get_friends_leaderboard(self, user_id: str) -> list[dict]:
        # TODO(#12): implement with friends/relationships collection
        # Requires a friends subcollection or a separate relationships
        # collection to determine which users are friends of user_id
        return []
