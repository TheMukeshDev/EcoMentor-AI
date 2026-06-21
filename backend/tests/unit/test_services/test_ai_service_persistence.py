"""Tests for AIService persistence methods."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta


class TestAIServicePersistence:
    """Tests for AIService conversation persistence."""

    def test_conversation_collection_with_db(self, ai_service, mocker):
        """Should return collection if db is initialized."""
        mock_db = MagicMock()
        mocker.patch("app.services.ai_service.current_app.extensions", {"firestore": mock_db})

        col = ai_service._conversation_collection()
        mock_db.collection.assert_called_once_with("conversations")
        assert col == mock_db.collection.return_value

    def test_conversation_collection_without_db(self, ai_service, mocker):
        """Should return None if db is not initialized."""
        mocker.patch("app.services.ai_service.current_app.extensions", {})
        assert ai_service._conversation_collection() is None

    def test_load_conversation_success(self, ai_service, mocker):
        """Should load conversation and filter out old messages."""
        mock_db = MagicMock()
        mocker.patch("app.services.ai_service.db", mock_db)

        now = datetime.now(timezone.utc)
        recent = (now - timedelta(days=1)).isoformat()
        old = (now - timedelta(days=10)).isoformat()

        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "messages": [
                {"content": "old msg", "timestamp": old},
                {"content": "new msg", "timestamp": recent},
            ]
        }

        mock_col = MagicMock()
        mock_col.document.return_value.get.return_value = mock_doc
        mocker.patch.object(ai_service, "_conversation_collection", return_value=mock_col)

        result = ai_service._load_conversation_from_store("user-1")
        assert len(result) == 1
        assert result[0]["content"] == "new msg"

    def test_load_conversation_not_exists(self, ai_service, mocker):
        """Should return empty list if document does not exist."""
        mock_col = MagicMock()
        mock_col.document.return_value.get.return_value.exists = False
        mocker.patch.object(ai_service, "_conversation_collection", return_value=mock_col)

        result = ai_service._load_conversation_from_store("user-1")
        assert result == []

    def test_load_conversation_no_col(self, ai_service, mocker):
        """Should return empty list if collection is None."""
        mocker.patch.object(ai_service, "_conversation_collection", return_value=None)
        assert ai_service._load_conversation_from_store("user-1") == []

    def test_load_conversation_error(self, ai_service, mocker):
        """Should return empty list on db error."""
        mock_col = MagicMock()
        mock_col.document.return_value.get.side_effect = Exception("DB error")
        mocker.patch.object(ai_service, "_conversation_collection", return_value=mock_col)

        result = ai_service._load_conversation_from_store("user-1")
        assert result == []

    def test_persist_conversation_success(self, ai_service, mocker):
        """Should persist conversation."""
        mock_col = MagicMock()
        mocker.patch.object(ai_service, "_conversation_collection", return_value=mock_col)

        messages = [{"content": "hello"}]
        ai_service._persist_conversation("user-1", messages)

        mock_col.document.assert_called_with("user-1")
        mock_col.document.return_value.set.assert_called_once()
        args = mock_col.document.return_value.set.call_args[0][0]
        assert args["messages"] == messages
        assert "updated_at" in args

    def test_persist_conversation_no_col(self, ai_service, mocker):
        """Should not persist if collection is None."""
        mocker.patch.object(ai_service, "_conversation_collection", return_value=None)
        ai_service._persist_conversation("user-1", [])
        # No error should be raised

    def test_persist_conversation_error(self, ai_service, mocker):
        """Should handle persistence error gracefully."""
        mock_col = MagicMock()
        mock_col.document.return_value.set.side_effect = Exception("DB error")
        mocker.patch.object(ai_service, "_conversation_collection", return_value=mock_col)

        ai_service._persist_conversation("user-1", [])
        # No error should be raised

    def test_delete_conversation_success(self, ai_service, mocker):
        """Should delete conversation."""
        mock_col = MagicMock()
        mocker.patch.object(ai_service, "_conversation_collection", return_value=mock_col)

        ai_service._delete_conversation_from_store("user-1")
        mock_col.document.assert_called_with("user-1")
        mock_col.document.return_value.delete.assert_called_once()

    def test_delete_conversation_no_col(self, ai_service, mocker):
        """Should not delete if collection is None."""
        mocker.patch.object(ai_service, "_conversation_collection", return_value=None)
        ai_service._delete_conversation_from_store("user-1")
        # No error should be raised

    def test_delete_conversation_error(self, ai_service, mocker):
        """Should handle delete error gracefully."""
        mock_col = MagicMock()
        mock_col.document.return_value.delete.side_effect = Exception("DB error")
        mocker.patch.object(ai_service, "_conversation_collection", return_value=mock_col)

        ai_service._delete_conversation_from_store("user-1")
        # No error should be raised
