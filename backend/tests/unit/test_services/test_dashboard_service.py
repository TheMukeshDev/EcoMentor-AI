import pytest


class TestDashboardService:
    def test_instantiation(self, dashboard_service):
        assert dashboard_service is not None

    def test_has_expected_methods(self, dashboard_service):
        methods = ["get_summary", "get_history", "get_stats"]
        for name in methods:
            assert hasattr(dashboard_service, name)

    def test_get_summary_returns_none(self, dashboard_service):
        result = dashboard_service.get_summary("user-123")
        assert result is None

    def test_get_history_returns_none(self, dashboard_service):
        result = dashboard_service.get_history("user-123", "monthly")
        assert result is None

    def test_get_stats_returns_none(self, dashboard_service):
        result = dashboard_service.get_stats("user-123")
        assert result is None
