import pytest


class TestUserRepository:
    def test_find_by_email_builds_correct_query(self, mock_db):
        from app.repositories.user_repository import UserRepository

        repo = UserRepository(mock_db)
        repo.find_by_email("test@example.com")

        mock_db.collection.assert_called_once_with("users")

    def test_repository_uses_users_collection(self, mock_db):
        from app.repositories.user_repository import UserRepository

        repo = UserRepository(mock_db)

        repo.get("user-123")

        mock_db.collection.assert_called_with("users")

    def test_get_batch_empty_list(self, mocker):
        from app.repositories.user_repository import UserRepository

        mock_db = mocker.MagicMock()
        repo = UserRepository(mock_db)
        result = repo.get_batch([])
        assert result == []

    def test_get_batch_returns_documents(self, mocker):
        from app.repositories.user_repository import UserRepository

        mock_db = mocker.MagicMock()
        repo = UserRepository(mock_db)

        mock_snap1 = mocker.MagicMock()
        mock_snap1.id = "user-1"
        mock_snap1.exists = True
        mock_snap1.to_dict.return_value = {"name": "Alice"}

        mock_db.get_all.return_value = [mock_snap1]
        result = repo.get_batch(["user-1"])
        assert len(result) == 1
        assert result[0]["name"] == "Alice"
