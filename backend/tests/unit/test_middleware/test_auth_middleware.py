import pytest


class TestAuthMiddleware:
    def test_require_auth_missing_header(self, client):
        response = client.get("/api/auth/profile")
        assert response.status_code == 401

    def test_require_auth_invalid_token(self, client):
        response = client.get(
            "/api/auth/profile",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_auth_header_missing_bearer_prefix(self, client):
        response = client.get(
            "/api/auth/profile",
            headers={"Authorization": "Token abc123"},
        )
        assert response.status_code == 401
