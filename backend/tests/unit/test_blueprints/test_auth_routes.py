"""Tests for auth blueprint."""

import pytest

def get_headers():
    return {"Authorization": "Bearer test-token"}

@pytest.fixture(autouse=True)
def mock_auth(mocker):
    mocker.patch("firebase_admin.auth.verify_id_token", return_value={"uid": "user-1"})

def test_register_success(client, mocker):
    mocker.patch("app.blueprints.auth.routes._auth_service.register_user", return_value={"id_token": "token123"})
    resp = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User"
    })
    assert resp.status_code == 201

def test_register_error(client, mocker):
    from app.utils.errors import AuthenticationError
    mocker.patch("app.blueprints.auth.routes._auth_service.register_user", side_effect=AuthenticationError("Exists"))
    resp = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User"
    })
    assert resp.status_code == 401

def test_login_success(client, mocker):
    mocker.patch("app.blueprints.auth.routes._auth_service.login_user", return_value={"id_token": "token123"})
    resp = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert resp.status_code == 200

def test_login_error(client, mocker):
    from app.utils.errors import AuthenticationError
    mocker.patch("app.blueprints.auth.routes._auth_service.login_user", side_effect=AuthenticationError("Invalid"))
    resp = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert resp.status_code == 401

def test_get_profile_success(client, mocker):
    mocker.patch("app.blueprints.auth.routes._auth_service.get_user_profile", return_value={"name": "Alice"})
    resp = client.get("/api/auth/profile", headers=get_headers())
    assert resp.status_code == 200

def test_get_profile_error(client, mocker):
    from app.utils.errors import AppError
    mocker.patch("app.blueprints.auth.routes._auth_service.get_user_profile", side_effect=AppError("Not found", 404))
    resp = client.get("/api/auth/profile", headers=get_headers())
    assert resp.status_code == 404

def test_update_profile_success(client, mocker):
    mocker.patch("app.blueprints.auth.routes._auth_service.update_user_profile", return_value={"name": "Alice"})
    resp = client.put("/api/auth/profile", json={"name": "Alice"}, headers=get_headers())
    assert resp.status_code == 200

def test_update_profile_error(client, mocker):
    from app.utils.errors import AppError
    mocker.patch("app.blueprints.auth.routes._auth_service.update_user_profile", side_effect=AppError("Bad", 400))
    resp = client.put("/api/auth/profile", json={"name": "Alice"}, headers=get_headers())
    assert resp.status_code == 400

def test_google_auth_success(client, mocker):
    mocker.patch("app.blueprints.auth.routes._auth_service.google_auth", return_value={"id_token": "token"})
    resp = client.post("/api/auth/google", json={"id_token": "google123"})
    assert resp.status_code == 200

def test_google_auth_error(client, mocker):
    from app.utils.errors import AuthenticationError
    mocker.patch("app.blueprints.auth.routes._auth_service.google_auth", side_effect=AuthenticationError("Invalid"))
    resp = client.post("/api/auth/google", json={"id_token": "google123"})
    assert resp.status_code == 401
