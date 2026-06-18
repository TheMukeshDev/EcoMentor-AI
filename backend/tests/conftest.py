import pytest
from app import create_app


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def app_ctx(app):
    with app.app_context():
        yield


@pytest.fixture
def request_ctx(app):
    with app.test_request_context():
        yield


@pytest.fixture
def mock_db(mocker):
    from app.extensions import db

    _mock = mocker.MagicMock()
    mocker.patch.object(db, "collection", return_value=_mock)
    return _mock


@pytest.fixture
def mock_user_repo(mocker):
    return mocker.MagicMock(name="UserRepository")


@pytest.fixture
def mock_activity_repo(mocker):
    return mocker.MagicMock(name="ActivityRepository")


@pytest.fixture
def mock_footprint_repo(mocker):
    return mocker.MagicMock(name="FootprintRepository")


@pytest.fixture
def mock_recommendation_repo(mocker):
    return mocker.MagicMock(name="RecommendationRepository")


@pytest.fixture
def mock_challenge_repo(mocker):
    return mocker.MagicMock(name="ChallengeRepository")


@pytest.fixture
def auth_service(mock_user_repo):
    from app.services.auth_service import AuthService

    return AuthService(user_repository=mock_user_repo)


@pytest.fixture
def dashboard_service(mock_footprint_repo, mock_activity_repo):
    from app.services.dashboard_service import DashboardService

    return DashboardService(
        footprint_repository=mock_footprint_repo,
        activity_repository=mock_activity_repo,
    )


@pytest.fixture
def activity_service(mock_activity_repo):
    from app.services.activity_service import ActivityService

    return ActivityService(activity_repository=mock_activity_repo)


@pytest.fixture
def ai_service(mock_recommendation_repo):
    from app.services.ai_service import AIService

    return AIService(recommendation_repository=mock_recommendation_repo)


@pytest.fixture
def leaderboard_service(mock_user_repo, mock_footprint_repo):
    from app.services.leaderboard_service import LeaderboardService

    return LeaderboardService(
        user_repository=mock_user_repo,
        footprint_repository=mock_footprint_repo,
    )
