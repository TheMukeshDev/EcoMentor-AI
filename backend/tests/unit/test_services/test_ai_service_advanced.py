import pytest


class TestAIServiceAdvanced:
    def test_chat_returns_response(self, ai_service, mock_gemini):
        mock_gemini.return_value = {
            "response": "Hello! I'm your EcoMentor coach.",
            "carbon_reduction_actionable": "Turn off unused appliances.",
            "estimated_reduction_kg": 0.5
        }
        result = ai_service.chat("user-1", "How do I recycle paper?", {"level": "Beginner"})
        assert result["response"] == "Hello! I'm your EcoMentor coach."

    def test_chat_maintains_history(self, ai_service, mock_gemini):
        mock_gemini.return_value = {
            "response": "Acknowledged.",
            "carbon_reduction_actionable": "Keep track of daily habits.",
            "estimated_reduction_kg": 0.2
        }
        ai_service.chat("user-1", "First message", {"level": "Beginner"})
        ai_service.chat("user-1", "Second message", {"level": "Beginner"})
        history = ai_service.get_conversation_history("user-1")
        assert len(history) == 4
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "First message"
        assert history[2]["content"] == "Second message"

    def test_chat_clear(self, ai_service, mock_gemini):
        mock_gemini.return_value = {
            "response": "OK",
            "carbon_reduction_actionable": "Keep track of daily habits.",
            "estimated_reduction_kg": 0.1
        }
        ai_service.chat("user-1", "Message", {"level": "Beginner"})
        ai_service.clear_conversation("user-1")
        assert ai_service.get_conversation_history("user-1") == []

    def test_chat_returns_fallback_on_failure(self, ai_service, mocker):
        mocker.patch.object(ai_service, "_call_gemini", return_value=None)
        result = ai_service.chat("user-1", "Hello", {"level": "Beginner"})
        assert result is not None
        assert isinstance(result, dict)
        assert "response" in result

    def test_what_if_returns_analysis(self, ai_service, mock_gemini):
        mock_gemini.return_value = {
            "estimated_impact": "positive",
            "carbon_saved": 2.5,
            "comparison": "30% reduction",
            "tip": "Try it!",
            "savings_forecast_30_days": 75.0,
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

    def test_summarize_compact_below_threshold(self, ai_service):
        for i in range(20):
            ai_service._conversations["user-1"] = ai_service._conversations.get(
                "user-1", []
            ) + [
                {
                    "role": "user",
                    "content": f"msg {i}",
                    "timestamp": "2026-01-01T00:00:00",
                },
                {
                    "role": "assistant",
                    "content": f"reply {i}",
                    "timestamp": "2026-01-01T00:00:00",
                },
            ]
        before = len(ai_service._conversations["user-1"])
        ai_service._summarize_and_compact("user-1")
        assert len(ai_service._conversations["user-1"]) == before

    def test_summarize_compact_success(self, ai_service, mocker):
        for i in range(25):
            ai_service._conversations["user-1"] = ai_service._conversations.get(
                "user-1", []
            ) + [
                {
                    "role": "user",
                    "content": f"msg {i}",
                    "timestamp": "2026-01-01T00:00:00",
                },
                {
                    "role": "assistant",
                    "content": f"reply {i}",
                    "timestamp": "2026-01-01T00:00:00",
                },
            ]
        mocker.patch.object(
            ai_service,
            "_call_gemini",
            return_value={"summary": "User discussed transportation options"},
        )
        ai_service._summarize_and_compact("user-1")
        history = ai_service._conversations["user-1"]
        assert history[0]["role"] == "system"
        assert "summary" in history[0]["content"].lower()
        assert len(history) <= 21

    def test_summarize_compact_fallback_on_failure(self, ai_service, mock_gemini):
        for i in range(25):
            ai_service._conversations["user-1"] = ai_service._conversations.get(
                "user-1", []
            ) + [
                {
                    "role": "user",
                    "content": f"msg {i}",
                    "timestamp": "2026-01-01T00:00:00",
                },
                {
                    "role": "assistant",
                    "content": f"reply {i}",
                    "timestamp": "2026-01-01T00:00:00",
                },
            ]
        ai_service._summarize_and_compact("user-1")
        history = ai_service._conversations["user-1"]
        assert len(history) <= 40

    def test_chat_triggers_summarization_at_threshold(self, ai_service, mocker):
        summarizer = mocker.patch.object(ai_service, "_summarize_and_compact")
        mocker.patch.object(ai_service, "_call_gemini", return_value={
            "response": "OK",
            "carbon_reduction_actionable": "Keep tracking.",
            "estimated_reduction_kg": 0.1
        })
        for i in range(20):
            ai_service._conversations["user-1"] = ai_service._conversations.get(
                "user-1", []
            ) + [
                {
                    "role": "user",
                    "content": f"msg {i}",
                    "timestamp": "2026-01-01T00:00:00",
                },
                {
                    "role": "assistant",
                    "content": f"reply {i}",
                    "timestamp": "2026-01-01T00:00:00",
                },
            ]
        ai_service.chat("user-1", "new message", {"level": "Beginner"})
        summarizer.assert_called_once_with("user-1")

    def test_prompt_formats_system_role(self, ai_service, mock_gemini):
        ai_service._conversations["user-1"] = [
            {
                "role": "system",
                "content": "Previous conversation summary: User talked about recycling",
                "timestamp": "2026-01-01T00:00:00",
            },
            {"role": "user", "content": "Hello", "timestamp": "2026-01-01T00:00:00"},
        ]
        mock_gemini.return_value = {
            "response": "Hi there!",
            "carbon_reduction_actionable": "Keep tracking.",
            "estimated_reduction_kg": 0.1
        }
        result = ai_service.chat("user-1", "How do I recycle paper?", {"level": "Beginner"})
        assert result["response"] == "Hi there!"

