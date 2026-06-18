import pytest


class TestAIServiceAdvanced:
    def test_chat_returns_response(self, ai_service, mock_gemini):
        mock_gemini.return_value = {"response": "Hello! I'm your EcoMentor coach."}
        result = ai_service.chat("user-1", "Hello", {"level": "Beginner"})
        assert result == "Hello! I'm your EcoMentor coach."

    def test_chat_maintains_history(self, ai_service, mock_gemini):
        mock_gemini.return_value = {"response": "Acknowledged."}
        ai_service.chat("user-1", "First message", {"level": "Beginner"})
        ai_service.chat("user-1", "Second message", {"level": "Beginner"})
        history = ai_service.get_conversation_history("user-1")
        assert len(history) == 4
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "First message"
        assert history[2]["content"] == "Second message"

    def test_chat_clear(self, ai_service, mock_gemini):
        mock_gemini.return_value = {"response": "OK"}
        ai_service.chat("user-1", "Message", {"level": "Beginner"})
        ai_service.clear_conversation("user-1")
        assert ai_service.get_conversation_history("user-1") == []

    def test_chat_returns_fallback_on_failure(self, ai_service, mocker):
        mocker.patch.object(ai_service, "_call_gemini", return_value=None)
        result = ai_service.chat("user-1", "Hello", {"level": "Beginner"})
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_what_if_returns_analysis(self, ai_service, mock_gemini):
        mock_gemini.return_value = {
            "estimated_impact": "positive",
            "carbon_saved": 2.5,
            "comparison": "30% reduction",
            "tip": "Try it!",
        }
        result = ai_service.whats_if(
            "user-1",
            {
                "transport": "car",
                "distance": 10,
                "food_type": "non_vegetarian",
                "ac_usage": "3-5",
                "plastic_waste": 0.5,
            },
            {"description": "Switch to bicycle for daily commute"},
            {"level": "Beginner"},
        )
        assert result["estimated_impact"] == "positive"
        assert result["carbon_saved"] == 2.5

    def test_submit_feedback_invalidates_cache(self, ai_service, mock_gemini, mocker):
        mock_gemini.return_value = {
            "acknowledgment": "Thanks!",
            "adjusted_tip": "Try walking",
            "follow_up": "How does that sound?",
        }
        invalidate_spy = mocker.spy(ai_service._cache, "invalidate")
        result = ai_service.submit_feedback(
            "user-1", "like", "Great tips!", {"level": "Beginner"}
        )
        assert result is not None
        invalidate_spy.assert_called_once_with("user-1", "recommendations")

    def test_invalidate_cache(self, ai_service):
        ai_service._cache.set("user-1", "recommendations", {"tip": "test"})
        ai_service.invalidate_cache("user-1")
        assert ai_service._cache.get("user-1", "recommendations") is None
