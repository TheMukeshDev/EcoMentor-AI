import pytest


class TestAuthRoutes:
    def test_register_returns_405_without_post(self, client):
        response = client.get("/api/auth/register")

        assert response.status_code == 405

    def test_login_returns_405_without_post(self, client):
        response = client.get("/api/auth/login")

        assert response.status_code == 405

    def test_profile_supports_get_and_put(self, client):
        get_rules = [
            r
            for r in client.application.url_map.iter_rules()
            if r.rule == "/api/auth/profile"
        ]

        methods = set()
        for rule in get_rules:
            methods.update(rule.methods)

        assert "GET" in methods
        assert "PUT" in methods

    def test_unknown_auth_route_returns_404(self, client):
        response = client.get("/api/auth/nonexistent")

        assert response.status_code == 404
