import pytest


class TestHealthEndpoint:
    def test_health_returns_404_in_test_app(self, client):
        response = client.get("/health")

        assert response.status_code == 404

    def test_health_route_not_registered_in_factory(self, app):
        rules = [rule.rule for rule in app.url_map.iter_rules()]

        assert "/health" not in rules

    def test_health_route_registered_in_main(self, app):
        import main

        rules = [rule.rule for rule in main.app.url_map.iter_rules()]

        assert "/health" in rules
