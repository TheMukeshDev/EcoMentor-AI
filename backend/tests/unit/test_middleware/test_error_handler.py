"""Tests for centralized error handler middleware."""

import pytest
from flask import Flask


class TestErrorHandler:
    """Tests for error handler responses."""

    def test_404_returns_json(self, client):
        """Should return JSON for unknown routes."""
        response = client.get("/api/nonexistent")
        data = response.get_json()

        assert response.status_code == 404
        assert data["status"] == "error"
        assert "request_id" in data

    def test_405_returns_json(self, client):
        """Should return JSON for wrong HTTP method."""
        response = client.delete("/health")
        data = response.get_json()

        assert response.status_code == 405
        assert data["status"] == "error"

    def test_error_responses_never_leak_stack(self, client):
        """Error responses should never contain stack traces."""
        response = client.get("/api/nonexistent")
        text = response.get_data(as_text=True)

        assert "Traceback" not in text
        assert "File " not in text
        assert ".py" not in text
        assert "line " not in text

    def test_health_endpoint_ok(self, client):
        """Health check should always return 200."""
        response = client.get("/health")
        data = response.get_json()

        assert response.status_code == 200
        assert data["status"] == "healthy"

    def test_security_headers_present(self, client):
        """Every response should include security headers."""
        response = client.get("/health")

        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers


class TestAppError:
    """Tests for AppError handling."""

    def test_app_error_returns_correct_status(self):
        """Should return the custom status code from AppError."""
        from app.utils.errors import AppError
        from app.middleware.errors import register_error_handlers

        app = Flask(__name__)
        register_error_handlers(app)

        @app.route("/trigger-error")
        def trigger():
            raise AppError("Custom error", 422)

        with app.test_client() as client:
            resp = client.get("/trigger-error")
            assert resp.status_code == 422
            data = resp.get_json()
            assert data["message"] == "Custom error"

    def test_unhandled_exception_returns_500(self):
        """Should catch unhandled exceptions and return 500."""
        from app.middleware.errors import register_error_handlers

        app = Flask(__name__)
        register_error_handlers(app)

        @app.route("/crash")
        def crash():
            raise RuntimeError("Unexpected failure")

        with app.test_client() as client:
            resp = client.get("/crash")
            assert resp.status_code == 500
            data = resp.get_json()
            assert data["status"] == "error"
            assert "request_id" in data
            assert "Unexpected" not in data.get("message", "")

    def test_bad_request_returns_400(self):
        """Should handle 400 errors."""
        from app.middleware.errors import register_error_handlers
        from werkzeug.exceptions import BadRequest

        app = Flask(__name__)
        register_error_handlers(app)

        @app.route("/bad")
        def bad():
            raise BadRequest("malformed")

        with app.test_client() as client:
            resp = client.get("/bad")
            assert resp.status_code == 400
            data = resp.get_json()
            assert data["status"] == "error"

