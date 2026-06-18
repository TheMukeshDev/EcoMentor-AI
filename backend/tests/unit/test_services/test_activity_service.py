import pytest


class TestActivityService:
    def test_instantiation(self, activity_service):
        assert activity_service is not None

    def test_has_expected_methods(self, activity_service):
        methods = [
            "list_activities",
            "log_activity",
            "get_activity",
            "delete_activity",
        ]
        for name in methods:
            assert hasattr(activity_service, name)

    def test_log_activity_returns_activity_with_carbon_score(
        self, activity_service, mocker
    ):
        mocker.patch.object(
            activity_service._carbon_history_repo,
            "find_by_user_and_date",
            return_value=None,
        )
        mocker.patch.object(
            activity_service._streak_service._user_repo,
            "get",
            return_value={"streak": 0, "points": 0},
        )
        mocker.patch.object(
            activity_service._points_service._user_repo,
            "get",
            return_value={"streak": 0, "points": 0},
        )
        mocker.patch.object(
            activity_service._points_service,
            "add_points",
            return_value={"points": 10, "level": "Beginner", "badge": "Seedling"},
        )
        activity_service._activity_repo.set.return_value = None
        result = activity_service.log_activity(
            "user-123",
            {
                "transport": "car",
                "distance": 10,
                "ac_usage": "1-2",
                "food_type": "vegetarian",
                "plastic_waste": 0.5,
            },
        )
        assert result is not None
        assert result["uid"] == "user-123"
        assert result["transport"] == "car"
        assert isinstance(result["carbon_score"], float)
        assert result["carbon_score"] > 0
        assert "id" in result
        assert "created_at" in result

    def test_log_activity_invalidates_ai_cache(self, activity_service, mocker):
        mocker.patch.object(
            activity_service._carbon_history_repo,
            "find_by_user_and_date",
            return_value=None,
        )
        mocker.patch.object(
            activity_service._streak_service._user_repo,
            "get",
            return_value={"streak": 0, "points": 0},
        )
        mocker.patch.object(
            activity_service._points_service._user_repo,
            "get",
            return_value={"streak": 0, "points": 0},
        )
        mocker.patch.object(
            activity_service._points_service,
            "add_points",
            return_value={"points": 10, "level": "Beginner", "badge": "Seedling"},
        )
        activity_service.log_activity(
            "user-123",
            {
                "transport": "bicycle",
                "distance": 5,
                "ac_usage": "none",
                "food_type": "vegan",
                "plastic_waste": 0,
            },
        )
        activity_service._ai_service.invalidate_cache.assert_called_once()

    def test_log_activity_stores_in_repo(self, activity_service, mocker):
        mock_set = mocker.patch.object(activity_service._activity_repo, "set")
        mocker.patch.object(
            activity_service._carbon_history_repo,
            "find_by_user_and_date",
            return_value=None,
        )
        mocker.patch.object(
            activity_service._streak_service._user_repo,
            "get",
            return_value={"streak": 0, "points": 0},
        )
        mocker.patch.object(
            activity_service._points_service._user_repo,
            "get",
            return_value={"streak": 0, "points": 0},
        )
        mocker.patch.object(
            activity_service._points_service,
            "add_points",
            return_value={"points": 10, "level": "Beginner", "badge": "Seedling"},
        )
        activity_service.log_activity(
            "user-123",
            {
                "transport": "bicycle",
                "distance": 5,
                "ac_usage": "none",
                "food_type": "vegan",
                "plastic_waste": 0,
            },
        )
        mock_set.assert_called_once()
        args = mock_set.call_args[0]
        assert args[1]["carbon_score"] == 0.5

    def test_list_activities_delegates_to_repo(self, activity_service, mocker):
        mock_find = mocker.patch.object(
            activity_service._activity_repo, "find_by_user_id", return_value=[]
        )
        result = activity_service.list_activities("user-123")
        mock_find.assert_called_once_with("user-123", limit=None, cursor=None)
        assert result == []

    def test_list_activities_with_limit_and_cursor(self, activity_service, mocker):
        mock_find = mocker.patch.object(
            activity_service._activity_repo, "find_by_user_id", return_value=[]
        )
        result = activity_service.list_activities(
            "user-123", limit=10, cursor="last-id"
        )
        mock_find.assert_called_once_with("user-123", limit=10, cursor="last-id")
        assert result == []

    def test_get_activity_delegates_to_repo(self, activity_service, mocker):
        mock_get = mocker.patch.object(
            activity_service._activity_repo,
            "get",
            return_value={"id": "act-1", "uid": "user-123"},
        )
        result = activity_service.get_activity("act-1")
        mock_get.assert_called_once_with("act-1")
        assert result["id"] == "act-1"

    def test_get_activity_unauthorized_raises_error(self, activity_service, mocker):
        mocker.patch.object(
            activity_service._activity_repo,
            "get",
            return_value={"id": "act-1", "uid": "user-123"},
        )
        from app.utils.errors import AuthorizationError
        with pytest.raises(AuthorizationError):
            activity_service.get_activity("act-1", user_id="other-user")

    def test_delete_activity_delegates_to_repo(self, activity_service, mocker):
        mocker.patch.object(
            activity_service._activity_repo,
            "get",
            return_value={"id": "act-1", "uid": "user-123"},
        )
        mock_delete = mocker.patch.object(activity_service._activity_repo, "delete")
        activity_service.delete_activity("act-1")
        mock_delete.assert_called_once_with("act-1")

    def test_delete_activity_unauthorized_raises_error(self, activity_service, mocker):
        mocker.patch.object(
            activity_service._activity_repo,
            "get",
            return_value={"id": "act-1", "uid": "user-123"},
        )
        from app.utils.errors import AuthorizationError
        with pytest.raises(AuthorizationError):
            activity_service.delete_activity("act-1", user_id="other-user")

    def test_delete_activity_not_found_raises_error(self, activity_service, mocker):
        mocker.patch.object(
            activity_service._activity_repo,
            "get",
            return_value=None,
        )
        from app.utils.errors import NotFoundError
        with pytest.raises(NotFoundError):
            activity_service.delete_activity("act-1")
