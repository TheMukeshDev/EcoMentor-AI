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
        ]
        for name in methods:
            assert hasattr(ai_service, name)

    def test_get_recommendations_returns_tips(self, ai_service, mock_gemini):
        data = {"score": 65, "transport": "car", "food": "mixed", "ac_usage": "high"}
        result = ai_service.get_recommendations("user-123", data)
        assert result == {"test": "response"}
        mock_gemini.assert_called_once()

    def test_get_recommendations_returns_cached_on_second_call(
        self, ai_service, mock_gemini
    ):
        data = {"score": 50, "transport": "bike", "food": "vegan", "ac_usage": "low"}
        result1 = ai_service.get_recommendations("user-123", data)
        result2 = ai_service.get_recommendations("user-123", data)
        assert result1 == result2
        assert mock_gemini.call_count == 1

    def test_get_weekly_report_returns_report(self, ai_service, mock_gemini):
        context = {
            "level": "Explorer",
            "streak": 5,
            "weekly_avg": 42,
            "current_score": 35,
            "activity_count": 10,
            "weekly_data": {},
        }
        result = ai_service.get_weekly_report("user-123", context)
        assert result == {"test": "response"}

    def test_get_eco_personality_returns_personality(self, ai_service, mock_gemini):
        context = {
            "level": "Eco Warrior",
            "streak": 14,
            "weekly_avg": 30,
            "weekly_data": {},
        }
        result = ai_service.get_eco_personality("user-123", context)
        assert result == {"test": "response"}

    def test_get_daily_mission_returns_mission(self, ai_service, mock_gemini):
        context = {"level": "Beginner"}
        result = ai_service.get_daily_mission("user-123", context)
        assert result == {"test": "response"}

    def test_returns_none_when_gemini_fails(self, ai_service, mocker):
        mocker.patch.object(ai_service, "_call_gemini", return_value=None)
        result = ai_service.get_recommendations("user-123", {"score": 50})
        assert result is None

    def test_returns_none_without_api_key(self):
        from app.services.ai_service import AIService

        service = AIService(api_key=None)
        result = service.get_recommendations("user-123", {"score": 50})
        assert result is None

    def test_cache_invalidation(self, ai_service, mock_gemini):
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
