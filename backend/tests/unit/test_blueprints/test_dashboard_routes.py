"""Tests for dashboard blueprint."""

import pytest

def get_headers():
    return {"Authorization": "Bearer test-token"}

@pytest.fixture(autouse=True)
def mock_auth(mocker):
    mocker.patch("firebase_admin.auth.verify_id_token", return_value={"uid": "user-1"})

def test_get_dashboard_success(client, mocker):
    mocker.patch("app.blueprints.dashboard.routes._service.get_summary", return_value={"score": 100})
    resp = client.get("/api/dashboard/summary", headers=get_headers())
    assert resp.status_code == 200
    assert resp.get_json()["data"]["score"] == 100

def test_get_dashboard_error(client, mocker):
    from app.utils.errors import AppError
    mocker.patch("app.blueprints.dashboard.routes._service.get_summary", side_effect=AppError("Fail", 400))
    resp = client.get("/api/dashboard/summary", headers=get_headers())
    assert resp.status_code == 400

def test_get_history_success(client, mocker):
    mocker.patch("app.blueprints.dashboard.routes._service.get_history", return_value=[{"score": 100}])
    resp = client.get("/api/dashboard/history?period=last_7", headers=get_headers())
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) == 1

def test_get_history_error(client, mocker):
    from app.utils.errors import AppError
    mocker.patch("app.blueprints.dashboard.routes._service.get_history", side_effect=AppError("Fail", 400))
    resp = client.get("/api/dashboard/history", headers=get_headers())
    assert resp.status_code == 400
