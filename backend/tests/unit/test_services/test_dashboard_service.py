from datetime import datetime, timezone, timedelta
import pytest


today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
yesterday_str = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
seven_days_ago_str = (datetime.now(timezone.utc) - timedelta(days=7)).strftime(
    "%Y-%m-%d"
)


class TestDashboardService:
    def test_instantiation(self, dashboard_service):
        assert dashboard_service is not None

    def test_has_expected_methods(self, dashboard_service):
        methods = ["get_summary", "get_history", "get_trends"]
        for name in methods:
            assert hasattr(dashboard_service, name)

    def test_get_summary_returns_correct_structure(self, dashboard_service, mocker):
        mocker.patch.object(
            dashboard_service._user_repo,
            "get",
            return_value={"streak": 3},
        )
        mocker.patch.object(
            dashboard_service._carbon_history_repo,
            "find_by_user_and_date",
            return_value={"carbon_score": 15.5},
        )
        mocker.patch.object(
            dashboard_service._carbon_history_repo,
            "find_by_user_and_date_range",
            return_value=[
                {"carbon_score": 10},
                {"carbon_score": 20},
            ],
        )
        mocker.patch.object(
            dashboard_service._activity_repo,
            "find_by_user_id",
            return_value=[{"id": "a1"}, {"id": "a2"}, {"id": "a3"}],
        )
        result = dashboard_service.get_summary("user-123")
        assert result["current_score"] == 15.5
        assert result["weekly_average"] == 15.0
        assert result["streak"] == 3
        assert result["activities_logged"] == 3

    def test_get_summary_handles_missing_user(self, dashboard_service, mocker):
        mocker.patch.object(dashboard_service._user_repo, "get", return_value=None)
        mocker.patch.object(
            dashboard_service._carbon_history_repo,
            "find_by_user_and_date",
            return_value=None,
        )
        mocker.patch.object(
            dashboard_service._carbon_history_repo,
            "find_by_user_and_date_range",
            return_value=[],
        )
        mocker.patch.object(
            dashboard_service._activity_repo,
            "find_by_user_id",
            return_value=[],
        )
        result = dashboard_service.get_summary("user-123")
        assert result["current_score"] == 0
        assert result["weekly_average"] == 0
        assert result["streak"] == 0
        assert result["activities_logged"] == 0

    def test_get_history_last_7(self, dashboard_service, mocker):
        entries = [
            {
                "date": d,
                "carbon_score": 10.0,
                "transport": 5.0,
                "electricity": 2.0,
                "food": 2.0,
                "waste": 1.0,
            }
            for d in [seven_days_ago_str, today_str]
        ]
        mocker.patch.object(
            dashboard_service._carbon_history_repo,
            "find_by_user_and_date_range",
            return_value=entries,
        )
        result = dashboard_service.get_history("user-123", "last_7")
        assert len(result) == 2
        assert result[0]["date"] == seven_days_ago_str
        assert result[1]["carbon_score"] == 10.0

    def test_get_history_last_30(self, dashboard_service, mocker):
        mocker.patch.object(
            dashboard_service._carbon_history_repo,
            "find_by_user_and_date_range",
            return_value=[{"date": today_str, "carbon_score": 5.0}],
        )
        result = dashboard_service.get_history("user-123", "last_30")
        assert len(result) == 1
        assert result[0]["carbon_score"] == 5.0

    def test_get_history_defaults_to_last_7_for_invalid_period(
        self, dashboard_service, mocker
    ):
        mock_find = mocker.patch.object(
            dashboard_service._carbon_history_repo,
            "find_by_user_and_date_range",
            return_value=[],
        )
        dashboard_service.get_history("user-123", "invalid_period")
        args = mock_find.call_args[0]
        diff = (
            datetime.strptime(args[2], "%Y-%m-%d")
            - datetime.strptime(args[1], "%Y-%m-%d")
        ).days
        assert diff == 7

    def test_get_history_empty_entries(self, dashboard_service, mocker):
        mocker.patch.object(
            dashboard_service._carbon_history_repo,
            "find_by_user_and_date_range",
            return_value=[],
        )
        result = dashboard_service.get_history("user-123", "last_7")
        assert result == []

    def test_get_trends_returns_structure(self, dashboard_service, mocker):
        mocker.patch.object(
            dashboard_service._carbon_history_repo,
            "find_by_user_and_date_range",
            side_effect=[
                [{"carbon_score": 10}, {"carbon_score": 20}],
                [{"carbon_score": 15}, {"carbon_score": 25}],
            ],
        )
        result = dashboard_service.get_trends("user-123")
        assert "current_week_avg" in result
        assert "previous_week_avg" in result
        assert "change" in result
        assert "direction" in result

    def test_get_trends_direction_down(self, dashboard_service, mocker):
        mocker.patch.object(
            dashboard_service._carbon_history_repo,
            "find_by_user_and_date_range",
            side_effect=[
                [{"carbon_score": 5}, {"carbon_score": 5}],
                [{"carbon_score": 15}, {"carbon_score": 15}],
            ],
        )
        result = dashboard_service.get_trends("user-123")
        assert result["direction"] == "down"
        assert result["change"] == 10.0

    def test_get_trends_direction_up(self, dashboard_service, mocker):
        mocker.patch.object(
            dashboard_service._carbon_history_repo,
            "find_by_user_and_date_range",
            side_effect=[
                [{"carbon_score": 15}, {"carbon_score": 15}],
                [{"carbon_score": 5}, {"carbon_score": 5}],
            ],
        )
        result = dashboard_service.get_trends("user-123")
        assert result["direction"] == "up"
        assert result["change"] == 10.0

    def test_get_trends_direction_stable(self, dashboard_service, mocker):
        mocker.patch.object(
            dashboard_service._carbon_history_repo,
            "find_by_user_and_date_range",
            side_effect=[
                [{"carbon_score": 10}, {"carbon_score": 10}],
                [{"carbon_score": 10}, {"carbon_score": 10}],
            ],
        )
        result = dashboard_service.get_trends("user-123")
        assert result["direction"] == "stable"
        assert result["change"] == 0

    def test_get_insights_returns_structure_without_ai(self, dashboard_service, mocker):
        mocker.patch.object(
            dashboard_service._user_repo,
            "get",
            return_value={"streak": 3},
        )
        mocker.patch.object(
            dashboard_service._carbon_history_repo,
            "find_by_user_and_date",
            return_value={"carbon_score": 15.5},
        )
        mocker.patch.object(
            dashboard_service._carbon_history_repo,
            "find_by_user_and_date_range",
            return_value=[
                {"carbon_score": 10},
                {"carbon_score": 20},
            ],
        )
        mocker.patch.object(
            dashboard_service._activity_repo,
            "find_by_user_id",
            return_value=[{"id": "a1"}, {"id": "a2"}, {"id": "a3"}],
        )
        result = dashboard_service.get_insights("user-123")
        assert "summary" in result
        assert "trends" in result
        assert result["ai_insight"] is None
        assert result["ai_tip"] is None

    def test_get_insights_with_ai_returns_tip(self, dashboard_service_with_ai, mocker):
        mocker.patch.object(
            dashboard_service_with_ai._user_repo,
            "get",
            return_value={"streak": 1},
        )
        mocker.patch.object(
            dashboard_service_with_ai._carbon_history_repo,
            "find_by_user_and_date",
            return_value={"carbon_score": 10},
        )
        mocker.patch.object(
            dashboard_service_with_ai._carbon_history_repo,
            "find_by_user_and_date_range",
            return_value=[
                {"carbon_score": 10},
                {"carbon_score": 12},
            ],
        )
        mocker.patch.object(
            dashboard_service_with_ai._activity_repo,
            "find_by_user_id",
            return_value=[{"id": "a1"}],
        )
        dashboard_service_with_ai._ai_service.get_recommendations.return_value = {
            "tips": ["Use public transport"]
        }
        result = dashboard_service_with_ai.get_insights("user-123")
        assert result["ai_tip"] == "Use public transport"
        assert result["ai_insight"] is not None

    def test_get_insights_with_ai_fallback_on_failure(
        self, dashboard_service_with_ai, mocker
    ):
        mocker.patch.object(
            dashboard_service_with_ai._user_repo,
            "get",
            return_value={"streak": 0},
        )
        mocker.patch.object(
            dashboard_service_with_ai._carbon_history_repo,
            "find_by_user_and_date",
            return_value={"carbon_score": 0},
        )
        mocker.patch.object(
            dashboard_service_with_ai._carbon_history_repo,
            "find_by_user_and_date_range",
            return_value=[],
        )
        mocker.patch.object(
            dashboard_service_with_ai._activity_repo,
            "find_by_user_id",
            return_value=[],
        )
        dashboard_service_with_ai._ai_service.get_recommendations.side_effect = (
            Exception("AI down")
        )
        result = dashboard_service_with_ai.get_insights("user-123")
        assert result["ai_tip"] is None
        assert result["ai_insight"] is None
        assert "summary" in result

    def test_get_insights_has_expected_method(self, dashboard_service):
        assert hasattr(dashboard_service, "get_insights")

    def test_get_trends_handles_empty_entries(self, dashboard_service, mocker):
        mocker.patch.object(
            dashboard_service._carbon_history_repo,
            "find_by_user_and_date_range",
            return_value=[],
        )
        result = dashboard_service.get_trends("user-123")
        assert result["current_week_avg"] == 0
        assert result["previous_week_avg"] == 0
