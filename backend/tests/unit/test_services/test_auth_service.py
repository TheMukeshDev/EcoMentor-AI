import pytest
from unittest.mock import MagicMock, patch


class TestAuthService:
    def test_instantiation(self, auth_service):
        assert auth_service is not None

    def test_has_expected_methods(self, auth_service):
        methods = [
            "register_user",
            "authenticate_user",
            "get_user_profile",
            "update_user_profile",
        ]
        for name in methods:
            assert hasattr(auth_service, name)

    def test_get_user_profile_raises_for_missing_user(self, auth_service, mocker):
        mocker.patch.object(auth_service._user_repo, "get", return_value=None)
        with pytest.raises(Exception, match="User not found"):
            auth_service.get_user_profile("nonexistent")

    def test_update_user_profile_accepts_updates(self, auth_service, mocker):
        mock_get = mocker.patch.object(
            auth_service._user_repo,
            "get",
            return_value={"uid": "user-123", "name": "Old"},
        )
        mock_update = mocker.patch.object(auth_service._user_repo, "update")
        result = auth_service.update_user_profile("user-123", {"name": "New Name"})
        mock_get.assert_called()
        mock_update.assert_called_once_with("user-123", {"name": "New Name"})

    def test_update_user_profile_raises_for_missing_user(self, auth_service, mocker):
        mocker.patch.object(auth_service._user_repo, "get", return_value=None)
        with pytest.raises(Exception):
            auth_service.update_user_profile("nonexistent", {"name": "Test"})

    def test_update_user_profile_only_allows_name(self, auth_service, mocker):
        mocker.patch.object(
            auth_service._user_repo,
            "get",
            return_value={"uid": "user-123", "name": "Old", "points": 10},
        )
        mock_update = mocker.patch.object(auth_service._user_repo, "update")
        auth_service.update_user_profile("user-123", {"name": "New", "points": 100})
        mock_update.assert_called_once_with("user-123", {"name": "New"})

    def test_register_user_raises_without_email(self, auth_service):
        with pytest.raises(Exception):
            auth_service.register_user({"password": "test123"})

    def test_get_user_profile_delegates_to_repo(self, auth_service, mocker):
        mock_get = mocker.patch.object(
            auth_service._user_repo,
            "get",
            return_value={"uid": "user-123", "name": "Test"},
        )
        result = auth_service.get_user_profile("user-123")
        mock_get.assert_called_once_with("user-123")
        assert result["uid"] == "user-123"

    def test_update_profile_no_valid_fields_returns_existing(self, auth_service, mocker):
        existing = {"uid": "user-1", "name": "Alice"}
        mocker.patch.object(auth_service._user_repo, "get", return_value=existing)
        result = auth_service.update_user_profile("user-1", {"email": "x@y.com"})
        assert result == existing

    def test_register_user_success(self, auth_service, mocker):
        from firebase_admin import auth as firebase_auth

        mock_record = MagicMock()
        mock_record.uid = "firebase-uid-123"
        mocker.patch.object(firebase_auth, "create_user", return_value=mock_record)
        mocker.patch.object(auth_service, "_sign_in_with_password", return_value="id-token-abc")
        mocker.patch.object(auth_service._user_repo, "set")

        result = auth_service.register_user({
            "email": "test@example.com",
            "password": "securepass123",
            "name": "Test User",
        })
        assert result["id_token"] == "id-token-abc"
        assert result["profile"]["uid"] == "firebase-uid-123"
        assert result["profile"]["name"] == "Test User"
        auth_service._user_repo.set.assert_called_once()

    def test_register_user_email_exists(self, auth_service, mocker):
        from firebase_admin import auth as firebase_auth
        from app.utils.errors import AuthenticationError

        mocker.patch.object(
            firebase_auth, "create_user",
            side_effect=firebase_auth.EmailAlreadyExistsError("exists", "exists", 400)
        )
        with pytest.raises(AuthenticationError, match="Email already registered"):
            auth_service.register_user({
                "email": "dup@example.com",
                "password": "pass123",
            })

    def test_register_user_firebase_error(self, auth_service, mocker):
        from firebase_admin import auth as firebase_auth
        from app.utils.errors import AuthenticationError

        mocker.patch.object(
            firebase_auth, "create_user",
            side_effect=Exception("Firebase down")
        )
        with pytest.raises(AuthenticationError, match="Registration failed"):
            auth_service.register_user({
                "email": "new@example.com",
                "password": "pass123",
            })

    def test_login_user_success(self, auth_service, mocker):
        from firebase_admin import auth as firebase_auth

        mock_user = MagicMock()
        mock_user.uid = "uid-456"
        mocker.patch.object(firebase_auth, "get_user_by_email", return_value=mock_user)
        mocker.patch.object(auth_service, "_sign_in_with_password", return_value="tok-xyz")
        mocker.patch.object(
            auth_service._user_repo, "get",
            return_value={"uid": "uid-456", "name": "Alice"}
        )

        result = auth_service.login_user("alice@example.com", "pass123")
        assert result["uid"] == "uid-456"
        assert result["id_token"] == "tok-xyz"

    def test_login_user_not_found(self, auth_service, mocker):
        from firebase_admin import auth as firebase_auth
        from app.utils.errors import AuthenticationError

        mocker.patch.object(
            firebase_auth, "get_user_by_email",
            side_effect=firebase_auth.UserNotFoundError("not found")
        )
        with pytest.raises(AuthenticationError, match="Invalid email"):
            auth_service.login_user("ghost@example.com", "pass")

    def test_login_user_firebase_error(self, auth_service, mocker):
        from firebase_admin import auth as firebase_auth
        from app.utils.errors import AuthenticationError

        mocker.patch.object(
            firebase_auth, "get_user_by_email",
            side_effect=Exception("Firebase error")
        )
        with pytest.raises(AuthenticationError, match="Login failed"):
            auth_service.login_user("err@example.com", "pass")

    def test_authenticate_user_success(self, auth_service, mocker):
        from firebase_admin import auth as firebase_auth

        mocker.patch.object(
            firebase_auth, "verify_id_token",
            return_value={"uid": "verified-uid"}
        )
        uid = auth_service.authenticate_user("valid-token")
        assert uid == "verified-uid"

    def test_authenticate_user_invalid_token(self, auth_service, mocker):
        from firebase_admin import auth as firebase_auth
        from app.utils.errors import AuthenticationError

        mocker.patch.object(
            firebase_auth, "verify_id_token",
            side_effect=Exception("token expired")
        )
        with pytest.raises(AuthenticationError, match="Invalid token"):
            auth_service.authenticate_user("bad-token")

    def test_google_auth_new_user(self, auth_service, mocker):
        from firebase_admin import auth as firebase_auth

        mocker.patch.object(
            firebase_auth, "verify_id_token",
            return_value={"uid": "g-uid", "email": "g@test.com", "name": "Google User", "picture": "url"}
        )
        mocker.patch.object(auth_service._user_repo, "get", return_value=None)
        mocker.patch.object(auth_service._user_repo, "set")

        result = auth_service.google_auth("google-token")
        assert result["profile"]["email"] == "g@test.com"
        auth_service._user_repo.set.assert_called_once()

    def test_google_auth_existing_user(self, auth_service, mocker):
        from firebase_admin import auth as firebase_auth

        mocker.patch.object(
            firebase_auth, "verify_id_token",
            return_value={"uid": "g-uid", "email": "g@test.com", "name": "Updated", "picture": "pic"}
        )
        existing = {"uid": "g-uid", "name": "Old", "email": "g@test.com", "photoURL": ""}
        mocker.patch.object(auth_service._user_repo, "get", return_value=existing)
        mocker.patch.object(auth_service._user_repo, "update")

        result = auth_service.google_auth("google-token")
        auth_service._user_repo.update.assert_called_once()

    def test_google_auth_invalid_token(self, auth_service, mocker):
        from firebase_admin import auth as firebase_auth
        from app.utils.errors import AuthenticationError

        mocker.patch.object(
            firebase_auth, "verify_id_token",
            side_effect=Exception("bad token")
        )
        with pytest.raises(AuthenticationError, match="Invalid token"):
            auth_service.google_auth("bad-google-token")

    def test_sign_in_with_password_success(self, auth_service, mocker):
        from flask import Flask

        app = Flask(__name__)
        app.config["FIREBASE_API_KEY"] = "test-api-key"

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"idToken": "fresh-token"}
        mocker.patch("app.services.auth_service.requests.post", return_value=mock_resp)

        with app.app_context():
            token = auth_service._sign_in_with_password("test@test.com", "pass123")
            assert token == "fresh-token"

    def test_sign_in_with_password_no_api_key(self, auth_service, mocker):
        from flask import Flask
        from app.utils.errors import AuthenticationError

        app = Flask(__name__)
        app.config["FIREBASE_API_KEY"] = ""

        with app.app_context():
            with pytest.raises(AuthenticationError, match="API key"):
                auth_service._sign_in_with_password("test@test.com", "pass")

    def test_sign_in_with_password_api_error(self, auth_service, mocker):
        from flask import Flask
        from app.utils.errors import AuthenticationError

        app = Flask(__name__)
        app.config["FIREBASE_API_KEY"] = "key"

        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.json.return_value = {"error": {"message": "INVALID_PASSWORD"}}
        mocker.patch("app.services.auth_service.requests.post", return_value=mock_resp)

        with app.app_context():
            with pytest.raises(AuthenticationError, match="INVALID_PASSWORD"):
                auth_service._sign_in_with_password("test@test.com", "wrong")

    def test_sign_in_with_password_network_error(self, auth_service, mocker):
        from flask import Flask
        from app.utils.errors import AuthenticationError
        import requests as req

        app = Flask(__name__)
        app.config["FIREBASE_API_KEY"] = "key"

        mocker.patch(
            "app.services.auth_service.requests.post",
            side_effect=req.RequestException("timeout")
        )

        with app.app_context():
            with pytest.raises(AuthenticationError, match="service unavailable"):
                auth_service._sign_in_with_password("test@test.com", "pass")

