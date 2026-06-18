import pytest


class TestBlueprintRegistration:
    def test_auth_blueprint_has_expected_routes(self, app):
        rules = [rule.rule for rule in app.url_map.iter_rules()]

        assert "/api/auth/register" in rules
        assert "/api/auth/login" in rules
        assert "/api/auth/profile" in rules

    def test_dashboard_blueprint_has_expected_routes(self, app):
        rules = [rule.rule for rule in app.url_map.iter_rules()]

        assert "/api/dashboard/summary" in rules
        assert "/api/dashboard/history" in rules
        assert "/api/dashboard/trends" in rules

    def test_activities_blueprint_has_expected_routes(self, app):
        rules = [rule.rule for rule in app.url_map.iter_rules()]

        assert "/api/activities" in rules
        assert "/api/activities/<activity_id>" in rules

    def test_ai_blueprint_has_expected_routes(self, app):
        rules = [rule.rule for rule in app.url_map.iter_rules()]

        assert "/api/ai/recommendations" in rules
        assert "/api/ai/weekly-report" in rules
        assert "/api/ai/eco-personality" in rules
        assert "/api/ai/daily-mission" in rules

    def test_leaderboard_blueprint_has_expected_routes(self, app):
        rules = [rule.rule for rule in app.url_map.iter_rules()]

        assert "/api/leaderboard/global" in rules
        assert "/api/leaderboard/friends" in rules

    def test_all_routes_have_unique_endpoint_names(self, app):
        rules = list(app.url_map.iter_rules())

        names = [rule.endpoint for rule in rules]
        assert len(names) == len(set(names))

    def test_unknown_route_returns_404(self, client):
        response = client.get("/api/nonexistent")

        assert response.status_code == 404
