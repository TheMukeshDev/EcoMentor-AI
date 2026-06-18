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

    def test_get_friends_uses_batch_instead_of_n_plus_one(
        self, leaderboard_service, mocker
    ):
        mocker.patch.object(
            leaderboard_service._user_repo,
            "get",
            return_value={"uid": "user-1", "friend_uids": ["f1", "f2", "f3"]},
        )
        mock_batch = mocker.patch.object(
            leaderboard_service._user_repo,
            "get_batch",
            return_value=[
                {"id": "f1", "name": "A", "points": 10, "level": "Beginner"},
                {"id": "f2", "name": "B", "points": 20, "level": "Explorer"},
                {"id": "f3", "name": "C", "points": 30, "level": "Eco Warrior"},
            ],
        )
        mocker.patch.object(
            leaderboard_service._footprint_repo,
            "find_latest_by_user",
            return_value={"carbon_score": 15},
        )
        result = leaderboard_service.get_friends_leaderboard("user-1")
        mock_batch.assert_called_once_with(["f1", "f2", "f3"])
        assert len(result) == 3
        assert result[0]["points"] == 30  # Descending order
        assert result[2]["points"] == 10
