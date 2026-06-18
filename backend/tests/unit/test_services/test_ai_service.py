import pytest


class TestAIService:
    def test_instantiation(self, ai_service):
        assert ai_service is not None

    def test_has_expected_methods(self, ai_service):
        methods = [
            "get_recommendations",
            "get_weekly_report",
            "get_eco_personality",
            "get_daily_mission",
            "get_carbon_savings_forecast"
        ]
        for name in methods:
            assert hasattr(ai_service, name)

    def test_get_recommendations_returns_tips(self, ai_service, mock_gemini):
        mock_gemini.return_value = {
            "tips": ["Tip 1", "Tip 2", "Tip 3"],
            "projected_weekly_savings_kg": 4.5
        }
        data = {"score": 65, "transport": "car", "food": "mixed", "ac_usage": "high"}
        result = ai_service.get_recommendations("user-123", data)
        assert result["tips"] == ["Tip 1", "Tip 2", "Tip 3"]
        assert result["projected_weekly_savings_kg"] == 4.5
        mock_gemini.assert_called_once()

    def test_get_recommendations_returns_cached_on_second_call(
        self, ai_service, mock_gemini
    ):
        mock_gemini.return_value = {
            "tips": ["Tip 1", "Tip 2", "Tip 3"],
            "projected_weekly_savings_kg": 4.5
        }
        data = {"score": 50, "transport": "bike", "food": "vegan", "ac_usage": "low"}
        result1 = ai_service.get_recommendations("user-123", data)
        result2 = ai_service.get_recommendations("user-123", data)
        assert result1 == result2
        assert mock_gemini.call_count == 1

    def test_get_weekly_report_returns_report(self, ai_service, mock_gemini):
        mock_gemini.return_value = {
            "biggest_contributor": "transport",
            "best_improvement": "food",
            "next_week_goal": "Reduce AC",
            "summary": "You did well.",
            "carbon_reduction_target_kg": 5.0
        }
        context = {
            "level": "Explorer",
            "streak": 5,
            "weekly_avg": 42,
            "current_score": 35,
            "activity_count": 10,
            "weekly_data": {},
            "worst_category": "transport"
        }
        result = ai_service.get_weekly_report("user-123", context)
        assert result["biggest_contributor"] == "transport"
        assert result["carbon_reduction_target_kg"] == 5.0

    def test_get_eco_personality_returns_personality(self, ai_service, mock_gemini):
        mock_gemini.return_value = {
            "personality": "Eco Warrior",
            "strength": "low transport",
            "weakness": "ac usage",
            "next_goal": "unplug"
        }
        context = {
            "level": "Eco Warrior",
            "streak": 14,
            "weekly_avg": 30,
            "weekly_data": {},
        }
        result = ai_service.get_eco_personality("user-123", context)
        assert result["personality"] == "Eco Warrior"

    def test_get_daily_mission_returns_mission(self, ai_service, mock_gemini):
        mock_gemini.return_value = {
            "challenge": "Walk to class",
            "reward": 50
        }
        context = {"level": "Beginner"}
        result = ai_service.get_daily_mission("user-123", context)
        assert result["challenge"] == "Walk to class"

    def test_returns_fallback_when_gemini_fails(self, ai_service, mocker):
        mocker.patch.object(ai_service, "_call_gemini", return_value=None)
        result = ai_service.get_recommendations("user-123", {"score": 50, "worst_category": "transport"})
        assert result is not None
        assert isinstance(result, dict)
        assert "tips" in result
        assert len(result["tips"]) > 0

    def test_returns_fallback_without_api_key(self):
        from app.services.ai_service import AIService
        service = AIService(api_key=None)
        result = service.get_recommendations("user-123", {"score": 50, "worst_category": "transport"})
        assert result is not None
        assert isinstance(result, dict)
        assert "tips" in result
        assert len(result["tips"]) > 0

    def test_cache_invalidation(self, ai_service, mock_gemini):
        mock_gemini.return_value = {
            "tips": ["Tip 1", "Tip 2", "Tip 3"],
            "projected_weekly_savings_kg": 4.5
        }
        data = {
            "score": 50,
            "transport": "walking",
            "food": "vegan",
            "ac_usage": "none",
        }
        ai_service.get_recommendations("user-123", data)
        ai_service._cache.invalidate("user-123", "recommendations")
        ai_service.get_recommendations("user-123", data)
        assert mock_gemini.call_count == 2

    def test_get_carbon_savings_forecast_returns_values(self, ai_service, mock_gemini):
        mock_gemini.return_value = {
            "current_weekly_footprint_kg": 42.0,
            "forecast_1_month_kg": 15.0,
            "forecast_3_months_kg": 45.0,
            "forecast_6_months_kg": 90.0,
            "motivation_message": "Awesome forecasting!"
        }
        context = {"weekly_avg": 42.0, "level": "Explorer"}
        result = ai_service.get_carbon_savings_forecast("user-123", context, ["Tip 1"])
        assert result["forecast_1_month_kg"] == 15.0
        assert result["motivation_message"] == "Awesome forecasting!"

    def test_get_carbon_savings_forecast_fallback_on_failure(self, ai_service, mocker):
        mocker.patch.object(ai_service, "_call_gemini", return_value=None)
        context = {"weekly_avg": 10.0, "level": "Beginner"}
        result = ai_service.get_carbon_savings_forecast("user-123", context, ["Tip 1"])
        assert result["forecast_1_month_kg"] == 4.0  # 10 * 0.1 * 4
        assert "savings" in result["motivation_message"].lower()


