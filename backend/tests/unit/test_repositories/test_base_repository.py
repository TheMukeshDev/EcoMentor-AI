import pytest
from unittest.mock import MagicMock, patch
from app.repositories.base_repository import BaseRepository


class TestBaseRepository:
    def setup_method(self):
        self.mock_db = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_db.collection.return_value = self.mock_collection
        self.repo = BaseRepository(self.mock_db, "test_collection")

    def test_paginated_query_applies_offset_and_limit(self):
        mock_docs = [MagicMock(id=f"doc-{i}") for i in range(3)]
        for i, d in enumerate(mock_docs):
            d.to_dict.return_value = {"data": i}
        query_mock = MagicMock()
        self.mock_collection.where.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.stream.return_value = mock_docs
        result = self.repo.paginated_query(
            filters=[("uid", "==", "user-1")],
            order_by="date",
            page=2,
            page_size=10,
        )
        query_mock.offset.assert_called_once_with(10)
        query_mock.limit.assert_called_once_with(10)
        assert len(result) == 3

    def test_paginated_query_without_filters(self, mocker):
        result = self.repo.paginated_query(order_by="date", page=1, page_size=5)
        self.repo._collection.order_by.assert_called_once_with("date")
        self.repo._collection.order_by.return_value.offset.assert_called_once_with(0)
        self.repo._collection.order_by.return_value.offset.return_value.limit.assert_called_once_with(
            5
        )

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
