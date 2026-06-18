import pytest


class TestLeaderboardService:
    def test_get_global_leaderboard(self, leaderboard_service, mocker):
        mocker.patch.object(
            leaderboard_service._user_repo,
            "query",
            return_value=[
                {"id": "u1", "name": "Alice", "level": "Eco Warrior", "points": 500},
                {"id": "u2", "name": "Bob", "level": "Explorer", "points": 200},
            ],
        )
        result = leaderboard_service.get_global_leaderboard(limit=10)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"

    def test_get_global_leaderboard_empty(self, leaderboard_service, mocker):
        mocker.patch.object(leaderboard_service._user_repo, "query", return_value=[])
        result = leaderboard_service.get_global_leaderboard()
        assert result == []

    def test_get_friends_leaderboard_no_user(self, leaderboard_service, mocker):
        mocker.patch.object(leaderboard_service._user_repo, "get", return_value=None)
        result = leaderboard_service.get_friends_leaderboard("user-123")
        assert result == []

    def test_get_friends_leaderboard_no_friends(self, leaderboard_service, mocker):
        mocker.patch.object(
            leaderboard_service._user_repo,
            "get",
            return_value={"friend_uids": []},
        )
        result = leaderboard_service.get_friends_leaderboard("user-123")
        assert result == []

    def test_add_friend(self, leaderboard_service, mocker):
        mocker.patch.object(
            leaderboard_service._user_repo,
            "get",
            return_value={"friend_uids": ["friend-1"]},
        )
        mocker.patch.object(leaderboard_service._user_repo, "update")
        result = leaderboard_service.add_friend("user-123", "friend-2")
        assert result is True
        leaderboard_service._user_repo.update.assert_called_once()

    def test_remove_friend(self, leaderboard_service, mocker):
        mocker.patch.object(
            leaderboard_service._user_repo,
            "get",
            return_value={"friend_uids": ["friend-1", "friend-2"]},
        )
        mocker.patch.object(leaderboard_service._user_repo, "update")
        result = leaderboard_service.remove_friend("user-123", "friend-1")
        assert result is True
