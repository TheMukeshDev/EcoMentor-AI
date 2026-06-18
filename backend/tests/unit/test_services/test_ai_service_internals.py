"""Tests for AIService internals: _call_gemini, _parse_response, edge cases."""

import json
import pytest
from unittest.mock import MagicMock, patch


class TestParseResponse:
    """Tests for AIService._parse_response."""

    def test_parse_valid_json_response(self, ai_service):
        """Should parse valid JSON from Gemini response."""
        data = {
            "candidates": [{
                "content": {"parts": [{"text": '{"tips": ["Tip 1"]}'}]},
            }]
        }
        result = ai_service._parse_response(data)
        assert result["tips"] == ["Tip 1"]

    def test_parse_code_fenced_response(self, ai_service):
        """Should strip code fences from JSON."""
        data = {
            "candidates": [{
                "content": {"parts": [{"text": "```json\n{\"key\": \"value\"}\n```"}]},
            }]
        }
        result = ai_service._parse_response(data)
        assert result["key"] == "value"

    def test_parse_empty_candidates(self, ai_service):
        """Should return None for empty candidates."""
        result = ai_service._parse_response({"candidates": []})
        assert result is None

    def test_parse_no_parts(self, ai_service):
        """Should return None for candidates with no parts."""
        data = {
            "candidates": [{
                "content": {"parts": []},
            }]
        }
        result = ai_service._parse_response(data)
        assert result is None

    def test_parse_safety_blocked(self, ai_service):
        """Should return safety response for SAFETY blocked."""
        data = {
            "candidates": [{
                "finishReason": "SAFETY",
                "content": {"parts": [{"text": "blocked"}]},
            }]
        }
        result = ai_service._parse_response(data)
        assert result["error"] == "SAFETY_BLOCKED"

    def test_parse_plain_text_fallback(self, ai_service):
        """Should fall back to plain text response for invalid JSON."""
        data = {
            "candidates": [{
                "content": {"parts": [{"text": "Just a plain text response"}]},
            }]
        }
        result = ai_service._parse_response(data)
        assert result["response"] == "Just a plain text response"

    def test_parse_completely_missing_structure(self, ai_service):
        """Should return None for completely malformed response."""
        result = ai_service._parse_response({})
        assert result is None


class TestCallGemini:
    """Tests for AIService._call_gemini."""

    def test_call_gemini_no_api_key(self):
        """Should return None when API key is not set."""
        from app.services.ai_service import AIService
        service = AIService(api_key=None)
        service._api_key = None
        result = service._call_gemini("test prompt")
        assert result is None

    def test_call_gemini_success(self, ai_service, mocker):
        """Should make HTTP POST and parse response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{
                "content": {"parts": [{"text": '{"result": "ok"}'}]},
            }]
        }
        mocker.patch("app.services.ai_service.requests.post", return_value=mock_resp)
        result = ai_service._call_gemini("prompt text")
        assert result["result"] == "ok"

    def test_call_gemini_non_200_error(self, ai_service, mocker):
        """Should return None on non-200 response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "Bad Request"
        mocker.patch("app.services.ai_service.requests.post", return_value=mock_resp)
        result = ai_service._call_gemini("prompt text")
        assert result is None

    def test_call_gemini_network_error(self, ai_service, mocker):
        """Should return None on network error after retries."""
        import requests as req
        mocker.patch(
            "app.services.ai_service.requests.post",
            side_effect=req.RequestException("timeout")
        )
        mocker.patch("app.services.ai_service.time.sleep")
        result = ai_service._call_gemini("prompt text")
        assert result is None

    def test_call_gemini_429_retries(self, ai_service, mocker):
        """Should retry on 429 and eventually succeed."""
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.text = "Rate limited"

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = {
            "candidates": [{
                "content": {"parts": [{"text": '{"ok": true}'}]},
            }]
        }
        mocker.patch(
            "app.services.ai_service.requests.post",
            side_effect=[mock_429, mock_200]
        )
        mocker.patch("app.services.ai_service.time.sleep")
        result = ai_service._call_gemini("prompt")
        assert result["ok"] is True

    def test_call_gemini_deterministic_params(self, ai_service, mocker):
        """Should set temperature=0 and seed=42 for deterministic mode."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{
                "content": {"parts": [{"text": '{"v": 1}'}]},
            }]
        }
        mock_post = mocker.patch("app.services.ai_service.requests.post", return_value=mock_resp)
        ai_service._call_gemini("prompt", deterministic=True)
        call_args = mock_post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        assert payload["generationConfig"]["temperature"] == 0.0
        assert payload["generationConfig"]["seed"] == 42


class TestEdgeCases:
    """Edge cases for AIService methods."""

    def test_recommendations_zero_score_shortcut(self, ai_service):
        """Should return default tips when score=0 and weekly_avg=0."""
        result = ai_service.get_recommendations("user-1", {"score": 0, "weekly_avg": 0})
        assert "tips" in result
        assert result["projected_weekly_savings_kg"] == 0.0

    def test_weekly_report_no_activities_shortcut(self, ai_service):
        """Should return default report when activity_count=0."""
        result = ai_service.get_weekly_report("user-1", {"activity_count": 0})
        assert "biggest_contributor" in result
        assert result["biggest_contributor"] == "None"

    def test_eco_personality_fallback(self, ai_service, mocker):
        """Should return default personality on Gemini failure."""
        mocker.patch.object(ai_service, "_call_gemini", return_value=None)
        result = ai_service.get_eco_personality("user-1", {})
        assert result["personality"] == "Eco Novice"

    def test_daily_mission_fallback(self, ai_service, mocker):
        """Should return default mission on Gemini failure."""
        mocker.patch.object(ai_service, "_call_gemini", return_value=None)
        result = ai_service.get_daily_mission("user-1", {})
        assert result["reward"] == 50

    def test_whats_if_fallback(self, ai_service, mocker):
        """Should return fallback analysis when Gemini fails."""
        mocker.patch.object(ai_service, "_call_gemini", return_value=None)
        result = ai_service.whats_if(
            "user-1",
            {"transport": "car", "distance": 10},
            {"description": "switch to bus"},
            {"level": "Beginner"},
        )
        assert "carbon_saved" in result
        assert "savings_forecast_30_days" in result

    def test_submit_feedback_fallback(self, ai_service, mocker):
        """Should return default acknowledgment on Gemini failure."""
        mocker.patch.object(ai_service, "_call_gemini", return_value=None)
        result = ai_service.submit_feedback("user-1", "like", "Great!", {})
        assert result["acknowledgment"] == "Thanks for your feedback!"

    def test_chat_greeting_shortcut(self, ai_service):
        """Should return instant greeting for hello messages."""
        result = ai_service.chat("user-1", "Hello", {})
        assert "EcoMentor" in result["response"]

    def test_chat_unsafe_input_blocked(self, ai_service, mocker):
        """Should block unsafe input."""
        mocker.patch(
            "app.services.ai_service.check_input_safety",
            return_value={"safe": False, "issues": ["violence"]}
        )
        result = ai_service.chat("user-1", "some unsafe text", {})
        assert "sustainability" in result["response"].lower() or "eco-friendly" in result["response"].lower()
