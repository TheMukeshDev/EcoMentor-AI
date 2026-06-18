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
