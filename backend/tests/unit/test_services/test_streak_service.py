import pytest
from app.services.streak_service import StreakService


class TestStreakService:
    def setup_method(self):
        self.mock_repo = pytest.importorskip("unittest.mock").MagicMock()
        self.service = StreakService(self.mock_repo)

    def test_get_streak_returns_zero_for_missing_user(self):
        self.mock_repo.get.return_value = None
        assert self.service.get_streak("user-123") == 0

    def test_get_streak_returns_user_streak(self):
        self.mock_repo.get.return_value = {"streak": 5}
        assert self.service.get_streak("user-123") == 5

    def test_update_streak_sets_one_for_new_user(self):
        self.mock_repo.get.return_value = None
        result = self.service.update_streak("user-123", "2026-06-18")
        assert result == 1
        self.mock_repo.set.assert_called_once_with(
            "user-123", {"streak": 1, "last_activity_date": "2026-06-18"}
        )

    def test_update_streak_same_day_returns_current(self):
        self.mock_repo.get.return_value = {
            "streak": 3,
            "last_activity_date": "2026-06-18",
        }
        result = self.service.update_streak("user-123", "2026-06-18")
        assert result == 3
        self.mock_repo.update.assert_not_called()

    def test_update_streak_increments_on_consecutive_day(self):
        self.mock_repo.get.return_value = {
            "streak": 3,
            "last_activity_date": "2026-06-17",
        }
        result = self.service.update_streak("user-123", "2026-06-18")
        assert result == 4
        self.mock_repo.update.assert_called_once_with(
            "user-123",
            {"streak": 4, "last_activity_date": "2026-06-18"},
        )

    def test_update_streak_resets_on_skipped_day(self):
        self.mock_repo.get.return_value = {
            "streak": 5,
            "last_activity_date": "2026-06-10",
        }
        result = self.service.update_streak("user-123", "2026-06-18")
        assert result == 0
        self.mock_repo.update.assert_called_once_with(
            "user-123",
            {"streak": 0, "last_activity_date": "2026-06-18"},
        )

    def test_update_streak_handles_invalid_date(self):
        self.mock_repo.get.return_value = {
            "streak": 3,
            "last_activity_date": "2026-06-17",
        }
        result = self.service.update_streak("user-123", "not-a-date")
        assert result == 0
        self.mock_repo.update.assert_called_once()

    def test_update_streak_without_last_date_returns_one(self):
        self.mock_repo.get.return_value = {"streak": 0}
        result = self.service.update_streak("user-123", "2026-06-18")
        assert result == 1
