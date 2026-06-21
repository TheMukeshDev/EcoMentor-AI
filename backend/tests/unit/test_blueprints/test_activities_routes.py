"""Tests for activities blueprint."""

import pytest
from unittest.mock import MagicMock


def get_headers():
    return {"Authorization": "Bearer test-token"}


@pytest.fixture(autouse=True)
def mock_auth(mocker):
    mocker.patch("firebase_admin.auth.verify_id_token", return_value={"uid": "user-1"})


def test_log_activity_success(client, mocker):
    mocker.patch(
        "app.services.activity_service.ActivityService.log_activity", return_value={"id": "act-1"}
    )
    resp = client.post(
        "/api/activities",
        json={
            "date": "2026-06-18",
            "transport": "car",
            "distance": 10.0,
            "food_type": "vegan",
            "ac_usage": "none",
            "plastic_waste": 1.0,
        },
        headers=get_headers(),
    )
    assert resp.status_code == 201
    assert resp.get_json()["data"]["id"] == "act-1"


def test_log_activity_error(client, mocker):
    from app.utils.errors import AppError

    mocker.patch(
        "app.services.activity_service.ActivityService.log_activity",
        side_effect=AppError("Failed", 400),
    )
    resp = client.post(
        "/api/activities",
        json={
            "date": "2026-06-18",
            "transport": "car",
            "distance": 10.0,
            "food_type": "vegan",
            "ac_usage": "none",
            "plastic_waste": 1.0,
        },
        headers=get_headers(),
    )
    assert resp.status_code == 400


def test_list_activities_success(client, mocker):
    mocker.patch(
        "app.services.activity_service.ActivityService.list_activities",
        return_value=[{"id": "act-1"}],
    )
    resp = client.get("/api/activities", headers=get_headers())
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) == 1


def test_get_activity_success(client, mocker):
    mocker.patch(
        "app.services.activity_service.ActivityService.get_activity", return_value={"id": "act-1"}
    )
    resp = client.get("/api/activities/act-1", headers=get_headers())
    assert resp.status_code == 200


def test_get_activity_not_found(client, mocker):
    mocker.patch("app.services.activity_service.ActivityService.get_activity", return_value=None)
    resp = client.get("/api/activities/act-1", headers=get_headers())
    assert resp.status_code == 404


def test_delete_activity_success(client, mocker):
    mocker.patch("app.services.activity_service.ActivityService.delete_activity", return_value=True)
    resp = client.delete("/api/activities/act-1", headers=get_headers())
    assert resp.status_code == 200
