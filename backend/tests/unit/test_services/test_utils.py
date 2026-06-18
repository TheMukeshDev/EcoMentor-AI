"""Tests for utility modules: responses, validators, secrets."""

import pytest
from unittest.mock import MagicMock, patch
from flask import Flask


class TestResponses:
    """Tests for response utility functions."""

    def test_success_response(self):
        """Should return JSON with status=success."""
        app = Flask(__name__)
        with app.app_context():
            from app.utils.responses import success_response
            resp, code = success_response({"key": "value"})
            data = resp.get_json()
            assert data["status"] == "success"
            assert data["data"]["key"] == "value"
            assert code == 200

    def test_success_response_custom_code(self):
        """Should accept custom status code."""
        app = Flask(__name__)
        with app.app_context():
            from app.utils.responses import success_response
            _, code = success_response({"ok": True}, 201)
            assert code == 201

    def test_error_response(self):
        """Should return JSON with status=error."""
        app = Flask(__name__)
        with app.app_context():
            from app.utils.responses import error_response
            resp, code = error_response("Something failed")
            data = resp.get_json()
            assert data["status"] == "error"
            assert data["message"] == "Something failed"
            assert code == 400

    def test_error_response_custom_code(self):
        """Should accept custom status code."""
        app = Flask(__name__)
        with app.app_context():
            from app.utils.responses import error_response
            _, code = error_response("Not found", 404)
            assert code == 404


class TestValidators:
    """Tests for validate_body decorator."""

    def test_validate_body_valid_data(self):
        """Should pass validation and set validated_body."""
        from pydantic import BaseModel, Field

        class TestSchema(BaseModel):
            name: str = Field(..., min_length=1)

        app = Flask(__name__)
        from app.utils.validators import validate_body

        @app.route("/test", methods=["POST"])
        @validate_body(TestSchema)
        def test_view():
            from flask import request, jsonify
            return jsonify(request.validated_body)

        with app.test_client() as client:
            resp = client.post("/test", json={"name": "Alice"})
            assert resp.status_code == 200
            assert resp.get_json()["name"] == "Alice"

    def test_validate_body_invalid_data(self):
        """Should return 422 for invalid data."""
        from pydantic import BaseModel, Field

        class TestSchema(BaseModel):
            name: str = Field(..., min_length=1)

        app = Flask(__name__)
        from app.utils.validators import validate_body

        @app.route("/test", methods=["POST"])
        @validate_body(TestSchema)
        def test_view():
            from flask import jsonify
            return jsonify({})

        with app.test_client() as client:
            resp = client.post("/test", json={})
            assert resp.status_code == 422
            data = resp.get_json()
            assert data["status"] == "error"
            assert "errors" in data

    def test_validate_body_no_json(self):
        """Should handle requests without JSON body."""
        from pydantic import BaseModel, Field

        class TestSchema(BaseModel):
            name: str = Field(..., min_length=1)

        app = Flask(__name__)
        from app.utils.validators import validate_body

        @app.route("/test", methods=["POST"])
        @validate_body(TestSchema)
        def test_view():
            from flask import jsonify
            return jsonify({})

        with app.test_client() as client:
            resp = client.post("/test", data="not json")
            assert resp.status_code == 422


class TestSecrets:
    """Tests for secrets utility."""

    def test_validate_required_secrets_passes(self):
        """Should not raise when SECRET_KEY is set."""
        from app.utils.secrets import validate_required_secrets
        app = MagicMock()
        app.config = {"SECRET_KEY": "test-key-12345"}
        validate_required_secrets(app)  # Should not raise

    def test_validate_required_secrets_raises(self):
        """Should raise RuntimeError when SECRET_KEY is missing."""
        from app.utils.secrets import validate_required_secrets
        app = MagicMock()
        app.config = {}
        with patch("app.utils.secrets.get_secret", return_value=None):
            with pytest.raises(RuntimeError, match="Missing required"):
                validate_required_secrets(app)

    def test_get_secret_returns_env_var(self):
        """Should return env var in non-production."""
        from app.utils.secrets import get_secret
        with patch.dict("os.environ", {"TEST_VAR": "hello", "APP_ENV": "development"}):
            result = get_secret("TEST_VAR")
            assert result == "hello"

    def test_get_secret_returns_default(self):
        """Should return default when env var not set."""
        from app.utils.secrets import get_secret
        with patch.dict("os.environ", {"APP_ENV": "development"}, clear=False):
            result = get_secret("NONEXISTENT_VAR_12345", "fallback")
            assert result == "fallback"
