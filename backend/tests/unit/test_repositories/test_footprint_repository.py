import pytest


class TestFootprintRepository:
    def test_instantiation(self, mocker):
        from app.repositories.footprint_repository import FootprintRepository

        mock_db = mocker.MagicMock()
        repo = FootprintRepository(mock_db)
        assert repo is not None
        assert repo._collection is not None

    def test_find_by_user_id_calls_query(self, mocker):
        from app.repositories.footprint_repository import FootprintRepository

        mock_db = mocker.MagicMock()
        repo = FootprintRepository(mock_db)
        mocker.patch.object(repo, "query", return_value=[])
        result = repo.find_by_user_id("user-123")
        assert result == []

    def test_find_latest_by_user(self, mocker):
        from app.repositories.footprint_repository import FootprintRepository

        mock_db = mocker.MagicMock()
        repo = FootprintRepository(mock_db)
        mocker.patch.object(
            repo, "query", return_value=[{"id": "doc1", "carbon_score": 10}]
        )
        result = repo.find_latest_by_user("user-123")
        assert result is not None
        assert result["carbon_score"] == 10

    def test_find_latest_by_user_returns_none(self, mocker):
        from app.repositories.footprint_repository import FootprintRepository

        mock_db = mocker.MagicMock()
        repo = FootprintRepository(mock_db)
        mocker.patch.object(repo, "query", return_value=[])
        result = repo.find_latest_by_user("user-123")
        assert result is None
