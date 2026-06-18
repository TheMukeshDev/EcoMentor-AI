import pytest
from unittest.mock import MagicMock
from app.repositories.carbon_history_repository import CarbonHistoryRepository


class TestCarbonHistoryRepository:
    def setup_method(self):
        self.mock_db = MagicMock()
        self.repo = CarbonHistoryRepository(self.mock_db)
        self.repo._collection = MagicMock()

    def test_find_by_user_id_calls_query(self, mocker):
        mock_query = mocker.patch.object(self.repo, "query", return_value=[])
        self.repo.find_by_user_id("user-123")
        mock_query.assert_called_once_with(
            filters=[("uid", "==", "user-123")],
            order_by="date",
            limit=None,
        )

    def test_find_by_user_id_with_limit(self, mocker):
        mock_query = mocker.patch.object(self.repo, "query", return_value=[])
        self.repo.find_by_user_id("user-123", limit=10)
        mock_query.assert_called_once_with(
            filters=[("uid", "==", "user-123")],
            order_by="date",
            limit=10,
        )

    def test_find_by_user_and_date_range_calls_query(self, mocker):
        mock_query = mocker.patch.object(self.repo, "query", return_value=[])
        self.repo.find_by_user_and_date_range("user-123", "2026-06-01", "2026-06-18")
        mock_query.assert_called_once_with(
            filters=[
                ("uid", "==", "user-123"),
                ("date", ">=", "2026-06-01"),
                ("date", "<=", "2026-06-18"),
            ],
            order_by="date",
        )

    def test_find_by_user_and_date_returns_first_result(self, mocker):
        expected = {"id": "doc-1", "uid": "user-123", "date": "2026-06-18"}
        mocker.patch.object(self.repo, "query", return_value=[expected])
        result = self.repo.find_by_user_and_date("user-123", "2026-06-18")
        assert result == expected

    def test_find_by_user_and_date_returns_none_when_empty(self, mocker):
        mocker.patch.object(self.repo, "query", return_value=[])
        result = self.repo.find_by_user_and_date("user-123", "2026-06-18")
        assert result is None

    def test_find_by_user_and_date_calls_query_with_correct_filters(self, mocker):
        mock_query = mocker.patch.object(self.repo, "query", return_value=[])
        self.repo.find_by_user_and_date("user-123", "2026-06-18")
        mock_query.assert_called_once_with(
            filters=[
                ("uid", "==", "user-123"),
                ("date", "==", "2026-06-18"),
            ],
        )
