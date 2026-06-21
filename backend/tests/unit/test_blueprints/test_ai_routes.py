"""Tests for AI blueprint."""

import pytest


def get_headers():
    return {"Authorization": "Bearer test-token"}


@pytest.fixture(autouse=True)
def mock_auth(mocker):
    mocker.patch("firebase_admin.auth.verify_id_token", return_value={"uid": "user-1"})


def test_get_recommendations_success(client, mocker):
    mocker.patch(
        "app.services.ai_service.AIService.get_recommendations", return_value={"tips": ["tip1"]}
    )
    resp = client.post(
        "/api/ai/recommendations",
        json={
            "score": 50,
            "transport": "car",
            "food": "mixed",
            "ac_usage": "high",
            "plastic_waste": 1.0,
        },
        headers=get_headers(),
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["tips"] == ["tip1"]


def test_get_weekly_report_success(client, mocker):
    mocker.patch(
        "app.services.ai_service.AIService.get_weekly_report",
        return_value={"biggest_contributor": "car"},
    )
    resp = client.get("/api/ai/weekly-report", headers=get_headers())
    assert resp.status_code == 200
    assert resp.get_json()["data"]["biggest_contributor"] == "car"


def test_get_eco_personality_success(client, mocker):
    mocker.patch(
        "app.services.ai_service.AIService.get_eco_personality",
        return_value={"personality": "Warrior"},
    )
    resp = client.get("/api/ai/eco-personality", headers=get_headers())
    assert resp.status_code == 200
    assert resp.get_json()["data"]["personality"] == "Warrior"


def test_get_daily_mission_success(client, mocker):
    mocker.patch(
        "app.services.ai_service.AIService.get_daily_mission", return_value={"challenge": "Walk"}
    )
    resp = client.get("/api/ai/daily-mission", headers=get_headers())
    assert resp.status_code == 200
    assert resp.get_json()["data"]["challenge"] == "Walk"


def test_get_forecast_success(client, mocker):
    mocker.patch(
        "app.services.ai_service.AIService.get_carbon_savings_forecast",
        return_value={"forecast_1_month_kg": 10.0},
    )
    mocker.patch(
        "app.services.ai_service.AIService.get_recommendations", return_value={"tips": ["tip1"]}
    )
    resp = client.get("/api/ai/forecast", headers=get_headers())
    assert resp.status_code == 200
    assert resp.get_json()["data"]["forecast_1_month_kg"] == 10.0


def test_chat_success(client, mocker):
    mocker.patch("app.services.ai_service.AIService.chat", return_value={"response": "hello"})
    resp = client.post("/api/ai/chat", json={"message": "hi"}, headers=get_headers())
    assert resp.status_code == 200
    assert resp.get_json()["data"]["response"] == "hello"


def test_chat_history_success(client, mocker):
    mocker.patch(
        "app.services.ai_service.AIService.get_conversation_history",
        return_value=[{"role": "user"}],
    )
    resp = client.get("/api/ai/chat/history", headers=get_headers())
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) == 1


def test_chat_clear_success(client, mocker):
    mocker.patch("app.services.ai_service.AIService.clear_conversation")
    resp = client.post("/api/ai/chat/clear", headers=get_headers())
    assert resp.status_code == 200


def test_whats_if_success(client, mocker):
    mocker.patch("app.services.ai_service.AIService.whats_if", return_value={"carbon_saved": 5.0})
    resp = client.post(
        "/api/ai/what-if",
        json={
            "transport": "car",
            "distance": 10.0,
            "food_type": "vegan",
            "ac_usage": "low",
            "plastic_waste": 1.0,
            "scenario_description": "walk",
        },
        headers=get_headers(),
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["carbon_saved"] == 5.0


def test_feedback_success(client, mocker):
    mocker.patch(
        "app.services.ai_service.AIService.submit_feedback",
        return_value={"acknowledgment": "thanks"},
    )
    resp = client.post(
        "/api/ai/feedback", json={"feedback_type": "like", "message": "good"}, headers=get_headers()
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["acknowledgment"] == "thanks"


def test_coach_success(client, mocker):
    mocker.patch(
        "app.services.coach_service.CoachService.get_coaching_plan",
        return_value={"plan": "Do this"},
    )
    resp = client.get("/api/ai/coach", headers=get_headers())
    assert resp.status_code == 200


def test_sustainability_report_success(client, mocker):
    mocker.patch(
        "app.services.report_service.ReportService.generate_report",
        return_value={"report": "Good job"},
    )
    resp = client.get("/api/ai/sustainability-report", headers=get_headers())
    assert resp.status_code == 200


def test_habits_success(client, mocker):
    mocker.patch(
        "app.services.habit_service.HabitService.get_habits", return_value=[{"habit": "Recycle"}]
    )
    resp = client.get("/api/ai/habits", headers=get_headers())
    assert resp.status_code == 200


def test_carbon_forecast_success(client, mocker):
    mocker.patch(
        "app.services.forecast_service.ForecastService.get_forecast", return_value={"trend": "down"}
    )
    resp = client.get("/api/ai/carbon-forecast", headers=get_headers())
    assert resp.status_code == 200
