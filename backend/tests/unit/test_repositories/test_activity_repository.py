import pytest


class TestActivityRepository:
    def test_instantiation(self, mocker):
        from app.repositories.activity_repository import ActivityRepository

        mock_db = mocker.MagicMock()
        repo = ActivityRepository(mock_db)
        assert repo is not None

    def test_find_by_user_id(self, mocker):
        from app.repositories.activity_repository import ActivityRepository

        mock_db = mocker.MagicMock()
        repo = ActivityRepository(mock_db)
        mocker.patch.object(repo, "query", return_value=[{"id": "a1"}])
        result = repo.find_by_user_id("user-123")
        assert len(result) == 1

    def test_find_by_user_and_date_range(self, mocker):
        from app.repositories.activity_repository import ActivityRepository

        mock_db = mocker.MagicMock()
        repo = ActivityRepository(mock_db)
        mocker.patch.object(repo, "query", return_value=[{"id": "a1"}])
        result = repo.find_by_user_and_date_range(
            "user-123", "2026-01-01", "2026-01-07"
        )
        assert len(result) == 1

    def test_find_by_user_id_with_cursor(self, mocker):
        from app.repositories.activity_repository import ActivityRepository

        mock_db = mocker.MagicMock()
        repo = ActivityRepository(mock_db)
        mocker.patch.object(repo, "query", return_value=[])
        result = repo.find_by_user_id("user-123", limit=10, cursor="last-doc")
        assert result == []
