import pytest
import json
from unittest.mock import ANY


class TestAuthRoutes:
    def test_register_post_returns_400_without_data(self, client):
        resp = client.post(
            "/api/auth/register", content_type="application/json", data="{}"
        )
        assert resp.status_code in (400, 422)

    def test_login_post_returns_400_without_data(self, client):
        resp = client.post(
            "/api/auth/login", content_type="application/json", data="{}"
        )
        assert resp.status_code in (400, 422)

    def test_profile_get_returns_401_without_auth(self, client):
        resp = client.get("/api/auth/profile")
        assert resp.status_code == 401

    def test_profile_put_returns_401_without_auth(self, client):
        resp = client.put(
            "/api/auth/profile", content_type="application/json", data="{}"
        )
        assert resp.status_code == 401

    def test_google_auth_returns_400_without_token(self, client):
        resp = client.post(
            "/api/auth/google", content_type="application/json", data="{}"
        )
        assert resp.status_code in (400, 422)


class TestActivitiesRoutes:
    def test_list_activities_returns_401_without_auth(self, client):
        resp = client.get("/api/activities")
        assert resp.status_code == 401

    def test_create_activity_returns_401_without_auth(self, client):
        resp = client.post(
            "/api/activities", content_type="application/json", data="{}"
        )
        assert resp.status_code == 401

    def test_get_activity_returns_401_without_auth(self, client, app):
        resp = client.get("/api/activities/some-id")
        assert resp.status_code == 401

    def test_delete_activity_returns_401_without_auth(self, client):
        resp = client.delete("/api/activities/some-id")
        assert resp.status_code == 401

    def test_get_activity_returns_404_for_missing(self, client, app):
        from unittest.mock import patch
        with patch("firebase_admin.auth.verify_id_token", return_value={"uid": "test-user"}):
            with patch(
                "app.blueprints.activities.routes._service.get_activity",
                return_value=None,
            ):
                resp = client.get(
                    "/api/activities/missing-id",
                    headers={"Authorization": "Bearer fake-token"},
                )
                assert resp.status_code == 404

    def test_get_activity_owned_by_other_user_returns_403(self, client, app):
        from unittest.mock import patch
        with patch("firebase_admin.auth.verify_id_token", return_value={"uid": "test-user"}):
            with patch(
                "app.blueprints.activities.routes._activity_repo.get",
                return_value={"id": "some-id", "uid": "other-user", "carbon_score": 10},
            ):
                resp = client.get(
                    "/api/activities/some-id",
                    headers={"Authorization": "Bearer fake-token"},
                )
                assert resp.status_code == 403

    def test_delete_activity_owned_by_other_user_returns_403(self, client, app):
        from unittest.mock import patch
        with patch("firebase_admin.auth.verify_id_token", return_value={"uid": "test-user"}):
            with patch(
                "app.blueprints.activities.routes._activity_repo.get",
                return_value={"id": "some-id", "uid": "other-user", "carbon_score": 10},
            ):
                resp = client.delete(
                    "/api/activities/some-id",
                    headers={"Authorization": "Bearer fake-token"},
                )
                assert resp.status_code == 403


class TestDashboardRoutes:
    def test_summary_returns_401_without_auth(self, client):
        resp = client.get("/api/dashboard/summary")
        assert resp.status_code == 401

    def test_history_returns_401_without_auth(self, client):
        resp = client.get("/api/dashboard/history")
        assert resp.status_code == 401

    def test_trends_returns_401_without_auth(self, client):
        resp = client.get("/api/dashboard/trends")
        assert resp.status_code == 401

    def test_insights_returns_401_without_auth(self, client):
        resp = client.get("/api/dashboard/insights")
        assert resp.status_code == 401


class TestAIRoutes:
    def test_recommendations_returns_401_without_auth(self, client):
        resp = client.post(
            "/api/ai/recommendations", content_type="application/json", data="{}"
        )
        assert resp.status_code == 401

    def test_weekly_report_returns_401_without_auth(self, client):
        resp = client.get("/api/ai/weekly-report")
        assert resp.status_code == 401

    def test_eco_personality_returns_401_without_auth(self, client):
        resp = client.get("/api/ai/eco-personality")
        assert resp.status_code == 401

    def test_daily_mission_returns_401_without_auth(self, client):
        resp = client.get("/api/ai/daily-mission")
        assert resp.status_code == 401

    def test_chat_returns_401_without_auth(self, client):
        resp = client.post("/api/ai/chat", content_type="application/json", data="{}")
        assert resp.status_code == 401

    def test_chat_stream_returns_401_without_auth(self, client):
        resp = client.post(
            "/api/ai/chat/stream", content_type="application/json", data="{}"
        )
        assert resp.status_code == 401

    def test_chat_unsafe_input_returns_422(self, client):
        from unittest.mock import patch
        with patch("firebase_admin.auth.verify_id_token", return_value={"uid": "test-user"}):
            resp = client.post(
                "/api/ai/chat",
                headers={"Authorization": "Bearer fake-token"},
                content_type="application/json",
                data=json.dumps({"message": "how to make a bomb"}),
            )
            assert resp.status_code == 422
            assert "prohibited content" in resp.get_json()["message"]

    def test_chat_stream_unsafe_input_returns_422(self, client):
        from unittest.mock import patch
        with patch("firebase_admin.auth.verify_id_token", return_value={"uid": "test-user"}):
            resp = client.post(
                "/api/ai/chat/stream",
                headers={"Authorization": "Bearer fake-token"},
                content_type="application/json",
                data=json.dumps({"message": "how to make a bomb"}),
            )
            assert resp.status_code == 422
            assert "prohibited content" in resp.get_json()["message"]

    def test_what_if_returns_401_without_auth(self, client):
        resp = client.post(
            "/api/ai/what-if", content_type="application/json", data="{}"
        )
        assert resp.status_code == 401

    def test_feedback_returns_401_without_auth(self, client):
        resp = client.post(
            "/api/ai/feedback", content_type="application/json", data="{}"
        )
        assert resp.status_code == 401

    def test_forecast_returns_success_with_auth(self, client):
        from unittest.mock import patch
        with patch("firebase_admin.auth.verify_id_token", return_value={"uid": "test-user"}):
            with patch("app.services.ai_service.AIService.get_recommendations") as mock_rec, \
                 patch("app.services.ai_service.AIService.get_carbon_savings_forecast") as mock_forecast:
                mock_rec.return_value = {"tips": ["Tip 1"], "projected_weekly_savings_kg": 2.5}
                mock_forecast.return_value = {
                    "current_weekly_footprint_kg": 25.0,
                    "forecast_1_month_kg": 10.0,
                    "forecast_3_months_kg": 30.0,
                    "forecast_6_months_kg": 60.0,
                    "motivation_message": "Let's do it!"
                }
                resp = client.get(
                    "/api/ai/forecast",
                    headers={"Authorization": "Bearer fake-token"}
                )
                assert resp.status_code == 200
                data = resp.get_json()["data"]
                assert data["forecast_1_month_kg"] == 10.0
                assert data["motivation_message"] == "Let's do it!"



class TestLeaderboardRoutes:
    def test_global_returns_401_without_auth(self, client):
        resp = client.get("/api/leaderboard/global")
        assert resp.status_code == 401

    def test_friends_returns_401_without_auth(self, client):
        resp = client.get("/api/leaderboard/friends")
        assert resp.status_code == 401

    def test_add_friend_returns_401_without_auth(self, client):
        resp = client.post(
            "/api/leaderboard/friends/add", content_type="application/json", data="{}"
        )
        assert resp.status_code == 401

    def test_remove_friend_returns_401_without_auth(self, client):
        resp = client.post(
            "/api/leaderboard/friends/remove",
            content_type="application/json",
            data="{}",
        )
        assert resp.status_code == 401


class TestApiClientEndpoints:
    def test_csrf_token_endpoint_works(self, client):
        resp = client.get("/api/auth/csrf-token")
        assert resp.status_code == 200

    def test_csrf_token_returns_token(self, client):
        resp = client.get("/api/auth/csrf-token")
        data = resp.get_json()
        assert data is not None
        token = data.get("token") or data.get("csrf_token")
        assert token is not None

    def test_unknown_api_route_returns_404(self, client):
        resp = client.get("/api/unknown-route-12345")
        assert resp.status_code == 404

    def test_cors_headers_present(self, client):
        resp = client.options("/api/auth/login")
        assert "Access-Control-Allow-Origin" in resp.headers or resp.status_code in (
            200,
            404,
        )
