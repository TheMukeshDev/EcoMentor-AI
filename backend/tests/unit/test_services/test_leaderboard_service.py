import pytest


class TestLeaderboardService:
    def test_instantiation(self, leaderboard_service):
        assert leaderboard_service is not None

    def test_has_expected_methods(self, leaderboard_service):
        methods = ["get_global_leaderboard", "get_friends_leaderboard"]
        for name in methods:
            assert hasattr(leaderboard_service, name)

    def test_get_global_leaderboard_returns_list(self, leaderboard_service):
        result = leaderboard_service.get_global_leaderboard()
        assert result == []

    def test_get_friends_leaderboard_returns_list(self, leaderboard_service):
        result = leaderboard_service.get_friends_leaderboard("user-123")
        assert result == []
