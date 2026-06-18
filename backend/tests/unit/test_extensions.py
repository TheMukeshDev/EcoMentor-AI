"""Tests for Flask extensions."""

import pytest
from unittest.mock import MagicMock, patch
from flask import Flask


class TestExtensions:
    """Tests for init_firestore in extensions.py."""

    def test_init_firestore_emulator(self, mocker):
        """Should initialize with emulator when configured."""
        from app.extensions import init_firestore
        app = Flask(__name__)
        app.config["GCP_PROJECT_ID"] = "test-project"
        app.config["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
        
        mock_client = mocker.patch("app.extensions.firestore.Client")
        
        init_firestore(app)
        
        mock_client.assert_called_once_with(
            project="test-project",
            client_options={"api_endpoint": "http://localhost:8080"},
        )
        assert "firestore" in app.extensions

    def test_init_firestore_service_account(self, mocker):
        """Should initialize with service account when credentials provided."""
        from app.extensions import init_firestore
        app = Flask(__name__)
        app.config["GCP_PROJECT_ID"] = "test-project"
        app.config["FIREBASE_PRIVATE_KEY"] = "fake\\nkey"
        app.config["FIREBASE_CLIENT_EMAIL"] = "test@example.com"
        
        mock_creds_class = mocker.patch("app.extensions.service_account.Credentials")
        mock_creds = MagicMock()
        mock_creds_class.from_service_account_info.return_value = mock_creds
        
        mock_client = mocker.patch("app.extensions.firestore.Client")
        
        init_firestore(app)
        
        mock_creds_class.from_service_account_info.assert_called_once()
        args = mock_creds_class.from_service_account_info.call_args[0][0]
        assert args["private_key"] == "fake\nkey"
        assert args["client_email"] == "test@example.com"
        
        mock_client.assert_called_once_with(project="test-project", credentials=mock_creds)

    def test_init_firestore_default_credentials(self, mocker):
        """Should initialize with default credentials when no specific ones provided."""
        from app.extensions import init_firestore
        app = Flask(__name__)
        app.config["GCP_PROJECT_ID"] = "test-project"
        
        mock_client = mocker.patch("app.extensions.firestore.Client")
        
        init_firestore(app)
        
        mock_client.assert_called_once_with(project="test-project")
