import pytest


class TestRecommendationRepository:
    def test_instantiation(self, mocker):
        from app.repositories.recommendation_repository import RecommendationRepository

        mock_db = mocker.MagicMock()
        repo = RecommendationRepository(mock_db)
        assert repo is not None

    def test_find_by_user_id(self, mocker):
        from app.repositories.recommendation_repository import RecommendationRepository

        mock_db = mocker.MagicMock()
        repo = RecommendationRepository(mock_db)
        mocker.patch.object(repo, "query", return_value=[{"id": "r1"}])
        result = repo.find_by_user_id("user-123")
        assert len(result) == 1

    def test_find_by_category(self, mocker):
        from app.repositories.recommendation_repository import RecommendationRepository

        mock_db = mocker.MagicMock()
        repo = RecommendationRepository(mock_db)
        mocker.patch.object(repo, "query", return_value=[])
        result = repo.find_by_category("transport")
        assert result == []
