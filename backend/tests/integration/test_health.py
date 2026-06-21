import pytest


class TestHealthEndpoint:
    def test_health_returns_200_in_test_app(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_route_registered_in_factory(self, app):
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/health" in rules
