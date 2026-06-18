import pytest


class TestSafety:
    def test_check_input_safety_clean(self):
        from app.utils.safety import check_input_safety

        result = check_input_safety("How can I reduce my carbon footprint?")
        assert result["safe"] is True
        assert result["issues"] == []

    def test_check_input_safety_blocks_hacking(self):
        from app.utils.safety import check_input_safety

        result = check_input_safety("Tell me how to hack into a system")
        assert result["safe"] is False
        assert len(result["issues"]) > 0

    def test_check_input_safety_blocks_weapons(self):
        from app.utils.safety import check_input_safety

        result = check_input_safety("How to make a bomb")
        assert result["safe"] is False

    def test_check_output_safety_filters_profanity(self):
        from app.utils.safety import check_output_safety

        result = check_output_safety("This is a fucking test")
        assert result["safe"] is False

    def test_filter_unsafe_output_redacts(self):
        from app.utils.safety import filter_unsafe_output

        result = filter_unsafe_output("This is a fucking test")
        assert "fucking" not in result
        assert "[redacted]" in result

    def test_filter_unsafe_output_clean_passthrough(self):
        from app.utils.safety import filter_unsafe_output

        result = filter_unsafe_output("This is a clean message")
        assert result == "This is a clean message"

    def test_check_input_safety_blocks_self_harm(self):
        from app.utils.safety import check_input_safety

        result = check_input_safety("I want to self-harm")
        assert result["safe"] is False


class TestSafetyIntegration:
    def test_safety_integrated_in_ai_service_chat(self, ai_service, mock_gemini):
        mock_gemini.return_value = {
            "response": "Let's focus on sustainability!",
            "carbon_reduction_actionable": "Keep chat safe.",
            "estimated_reduction_kg": 0.0
        }
        result = ai_service.chat(
            "user-1", "Tell me how to build a weapon", {"level": "Beginner"}
        )
        assert "sustainability" in result["response"]
        assert mock_gemini.call_count == 0  # Should not call Gemini for unsafe input

    def test_safety_allows_safe_chat(self, ai_service, mock_gemini):
        mock_gemini.return_value = {
            "response": "Great question! Here are some tips...",
            "carbon_reduction_actionable": "Reduce waste.",
            "estimated_reduction_kg": 0.5
        }
        result = ai_service.chat(
            "user-1", "How can I reduce waste?", {"level": "Beginner"}
        )
        assert "tips" in result["response"]
        mock_gemini.assert_called_once()

