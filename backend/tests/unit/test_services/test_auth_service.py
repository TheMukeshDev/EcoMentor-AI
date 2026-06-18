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
