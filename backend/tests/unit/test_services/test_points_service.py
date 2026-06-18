import pytest
from app.services.points_service import PointsService, POINTS_ACTIVITY_LOG


class TestPointsService:
    def setup_method(self):
        self.mock_repo = pytest.importorskip("unittest.mock").MagicMock()
        self.service = PointsService(self.mock_repo)

    def test_add_points_returns_none_for_missing_user(self):
        self.mock_repo.get.return_value = None
        result = self.service.add_points("user-123", 10)
        assert result is None

    def test_add_points_updates_points_and_level(self):
        self.mock_repo.get.return_value = {"points": 0}
        self.mock_repo.update.return_value = {"points": 10}
        result = self.service.add_points("user-123", 10, reason="test")
        assert result["points"] == 10
        assert result["points_earned"] == 10
        assert result["reason"] == "test"
        assert result["level"] == "Beginner"
        self.mock_repo.update.assert_called_once_with(
            "user-123",
            {
                "points": 10,
                "level": "Beginner",
                "badge": "Seedling",
            },
        )

    def test_add_points_crosses_level_threshold(self):
        self.mock_repo.get.return_value = {"points": 95}
        result = self.service.add_points("user-123", 10)
        assert result["points"] == 105
        assert result["level"] == "Explorer"
        assert result["badge"] == "Sprout"

    def test_get_points_returns_zero_for_missing_user(self):
        self.mock_repo.get.return_value = None
        assert self.service.get_points("user-123") == 0

    def test_get_points_returns_user_points(self):
        self.mock_repo.get.return_value = {"points": 42}
        assert self.service.get_points("user-123") == 42

    def test_get_level_info_returns_default_for_missing_user(self):
        self.mock_repo.get.return_value = None
        info = self.service.get_level_info("user-123")
        assert info["name"] == "Beginner"
        assert info["badge"] == "Seedling"
        assert info["points"] == 0

    def test_get_level_info_beginner(self):
        self.mock_repo.get.return_value = {"points": 50}
        info = self.service.get_level_info("user-123")
        assert info["name"] == "Beginner"
        assert info["badge"] == "Seedling"
        assert info["points"] == 50
        assert info["next_level_points"] == 100
        assert 0 <= info["progress"] <= 100

    def test_get_level_info_explorer(self):
        self.mock_repo.get.return_value = {"points": 200}
        info = self.service.get_level_info("user-123")
        assert info["name"] == "Explorer"
        assert info["badge"] == "Sprout"

    def test_get_level_info_eco_warrior(self):
        self.mock_repo.get.return_value = {"points": 600}
        info = self.service.get_level_info("user-123")
        assert info["name"] == "Eco Warrior"
        assert info["badge"] == "Leaf"

    def test_get_level_info_planet_hero(self):
        self.mock_repo.get.return_value = {"points": 2000}
        info = self.service.get_level_info("user-123")
        assert info["name"] == "Planet Hero"
        assert info["badge"] == "Globe"
        assert info["next_level_points"] is None
        assert info["progress"] == 100

    def test_level_progress_is_correct_percentage(self):
        self.mock_repo.get.return_value = {"points": 250}
        info = self.service.get_level_info("user-123")
        assert info["name"] == "Explorer"
        assert info["progress"] == 37
