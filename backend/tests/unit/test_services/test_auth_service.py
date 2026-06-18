import pytest


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

    def test_register_user_accepts_data(self, auth_service):
        result = auth_service.register_user(
            {"uid": "user-123", "email": "test@example.com"}
        )

        assert result is None

    def test_get_user_profile_returns_none_for_missing_user(self, auth_service):
        result = auth_service.get_user_profile("nonexistent")

        assert result is None

    def test_authenticate_user_accepts_credentials(self, auth_service):
        result = auth_service.authenticate_user("test@example.com", "password123")

        assert result is None

    def test_update_user_profile_accepts_updates(self, auth_service):
        result = auth_service.update_user_profile(
            "user-123", {"display_name": "New Name"}
        )

        assert result is None
