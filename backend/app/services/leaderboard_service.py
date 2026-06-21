"""Leaderboard service for ranking users by points.

Supports global rankings, friend-based leaderboards, and
friend list management.
"""

from __future__ import annotations

from typing import Any

from google.cloud import firestore

from app.repositories.user_repository import UserRepository
from app.repositories.footprint_repository import FootprintRepository


class LeaderboardService:
    """Generates user rankings and manages friend connections."""

    def __init__(
        self,
        user_repository: UserRepository,
        footprint_repository: FootprintRepository,
    ) -> None:
        self._user_repo = user_repository
        self._footprint_repo = footprint_repository

    def get_global_leaderboard(self, limit: int = 20) -> list[dict[str, Any]]:
        """Retrieve the top users ranked by points.

        Args:
            limit: Maximum number of users to return.

        Returns:
            List of user summary dictionaries sorted by points descending.
        """
        users = self._user_repo.query(
            order_by=("points", firestore.Query.DESCENDING),
            limit=limit,
        )
        return [
            {
                "uid": user.get("id", user.get("uid", "")),
                "name": user.get("name", "Anonymous"),
                "level": user.get("level", "Beginner"),
                "points": user.get("points", 0),
            }
            for user in users
        ]

    def get_friends_leaderboard(
        self, user_id: str
    ) -> list[dict[str, Any]]:
        """Retrieve a leaderboard of the user's friends.

        Args:
            user_id: The authenticated user's unique identifier.

        Returns:
            List of friend summaries sorted by points descending.
        """
        user = self._user_repo.get(user_id)
        if not user:
            return []
        friend_uids = user.get("friend_uids", [])
        if not friend_uids:
            return []

        friends = self._user_repo.get_batch(friend_uids)
        friend_map = {
            friend.get("uid", friend.get("id", "")): friend
            for friend in friends
            if friend
        }

        results = []
        for friend_uid in friend_uids:
            friend = friend_map.get(friend_uid)
            if not friend:
                continue
            latest_footprint = self._footprint_repo.find_latest_by_user(
                friend_uid
            )
            results.append({
                "uid": friend_uid,
                "name": friend.get("name", "Anonymous"),
                "level": friend.get("level", "Beginner"),
                "points": friend.get("points", 0),
                "latest_score": (
                    latest_footprint.get("carbon_score", 0)
                    if latest_footprint
                    else 0
                ),
            })

        results.sort(key=lambda entry: entry["points"], reverse=True)
        return results

    def add_friend(self, user_id: str, friend_id: str) -> bool:
        """Add a friend connection for the user.

        Args:
            user_id: The user's unique identifier.
            friend_id: The friend's unique identifier.

        Returns:
            True if successful, False if the user was not found.
        """
        user = self._user_repo.get(user_id)
        if not user:
            return False
        friend_uids = set(user.get("friend_uids", []))
        if friend_id not in friend_uids:
            friend_uids.add(friend_id)
            self._user_repo.update(
                user_id, {"friend_uids": list(friend_uids)}
            )
        return True

    def remove_friend(self, user_id: str, friend_id: str) -> bool:
        """Remove a friend connection for the user.

        Args:
            user_id: The user's unique identifier.
            friend_id: The friend's unique identifier.

        Returns:
            True if successful, False if the user was not found.
        """
        user = self._user_repo.get(user_id)
        if not user:
            return False
        friend_uids = set(user.get("friend_uids", []))
        friend_uids.discard(friend_id)
        self._user_repo.update(
            user_id, {"friend_uids": list(friend_uids)}
        )
        return True
