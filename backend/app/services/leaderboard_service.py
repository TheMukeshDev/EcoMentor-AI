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
        user = self._user_repo.get(user_id)
        if not user:
            return []
        friend_uids = user.get("friend_uids", [])
        if not friend_uids:
            return []
        friends = self._user_repo.get_batch(friend_uids)
        friend_map = {f.get("uid", f.get("id", "")): f for f in friends if f}
        results = []
        for fid in friend_uids:
            friend = friend_map.get(fid)
            if not friend:
                continue
            latest = self._footprint_repo.find_latest_by_user(fid)
            results.append(
                {
                    "uid": fid,
                    "name": friend.get("name", "Anonymous"),
                    "level": friend.get("level", "Beginner"),
                    "points": friend.get("points", 0),
                    "latest_score": latest.get("carbon_score", 0) if latest else 0,
                }
            )
        results.sort(key=lambda r: r["points"], reverse=True)
        return results

    def add_friend(self, user_id: str, friend_id: str) -> bool:
        user = self._user_repo.get(user_id)
        if not user:
            return False
        friend_uids = set(user.get("friend_uids", []))
        if friend_id not in friend_uids:
            friend_uids.add(friend_id)
            self._user_repo.update(user_id, {"friend_uids": list(friend_uids)})
        return True

    def remove_friend(self, user_id: str, friend_id: str) -> bool:
        user = self._user_repo.get(user_id)
        if not user:
            return False
        friend_uids = set(user.get("friend_uids", []))
        friend_uids.discard(friend_id)
        self._user_repo.update(user_id, {"friend_uids": list(friend_uids)})
        return True
