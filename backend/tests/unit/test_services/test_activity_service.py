import pytest


class TestActivityService:
    def test_instantiation(self, activity_service):
        assert activity_service is not None

    def test_has_expected_methods(self, activity_service):
        methods = [
            "list_activities",
            "log_activity",
            "get_activity",
            "delete_activity",
        ]
        for name in methods:
            assert hasattr(activity_service, name)

    def test_list_activities_returns_none(self, activity_service):
        result = activity_service.list_activities("user-123")

        assert result is None

    def test_log_activity_accepts_data(self, activity_service):
        result = activity_service.log_activity(
            "user-123",
            {"category": "transport", "carbon_kg": 5.0},
        )

        assert result is None

    def test_get_activity_returns_none(self, activity_service):
        result = activity_service.get_activity("act-1")

        assert result is None

    def test_delete_activity_accepts_id(self, activity_service):
        result = activity_service.delete_activity("act-1")

        assert result is None
