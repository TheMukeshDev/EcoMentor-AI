import pytest
from unittest.mock import MagicMock, patch
from app.repositories.base_repository import BaseRepository


class TestBaseRepository:
    def setup_method(self):
        self.mock_db = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_db.collection.return_value = self.mock_collection
        self.repo = BaseRepository(self.mock_db, "test_collection")

    def test_count_returns_number_of_documents(self):
        mock_docs = [MagicMock(), MagicMock()]
        for d in mock_docs:
            d.to_dict.return_value = {}
        query_mock = MagicMock()
        self.mock_collection.where.return_value = query_mock
        query_mock.stream.return_value = mock_docs
        result = self.repo.count(filters=[("uid", "==", "user-1")])
        assert result == 2

    def test_count_without_filters(self):
        mock_docs = [MagicMock() for _ in range(5)]
        for d in mock_docs:
            d.to_dict.return_value = {}
        self.mock_collection.stream.return_value = mock_docs
        result = self.repo.count()
        assert result == 5
