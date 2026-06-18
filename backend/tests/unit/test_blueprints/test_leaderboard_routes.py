"""Tests for leaderboard blueprint."""

import pytest

def get_headers():
    return {"Authorization": "Bearer test-token"}

@pytest.fixture(autouse=True)
def mock_auth(mocker):
    mocker.patch("firebase_admin.auth.verify_id_token", return_value={"uid": "user-1"})

def test_get_leaderboard_success(client, mocker):
    mocker.patch("app.blueprints.leaderboard.routes._service.get_global_leaderboard", return_value=[{"name": "Alice"}])
    resp = client.get("/api/leaderboard/global", headers=get_headers())
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) == 1

def test_get_leaderboard_error(client, mocker):
    from app.utils.errors import AppError
    mocker.patch("app.blueprints.leaderboard.routes._service.get_global_leaderboard", side_effect=AppError("Fail", 400))
    resp = client.get("/api/leaderboard/global", headers=get_headers())
    assert resp.status_code == 400

def test_get_friends_leaderboard_success(client, mocker):
    mocker.patch("app.blueprints.leaderboard.routes._service.get_friends_leaderboard", return_value=[])
    resp = client.get("/api/leaderboard/friends", headers=get_headers())
    assert resp.status_code == 200

def test_add_friend_success(client, mocker):
    mocker.patch("app.blueprints.leaderboard.routes._service.add_friend", return_value=True)
    resp = client.post("/api/leaderboard/friends/add", json={"friend_id": "user-2"}, headers=get_headers())
    assert resp.status_code == 200

def test_remove_friend_success(client, mocker):
    mocker.patch("app.blueprints.leaderboard.routes._service.remove_friend", return_value=True)
    resp = client.post("/api/leaderboard/friends/remove", json={"friend_id": "user-2"}, headers=get_headers())
    assert resp.status_code == 200
