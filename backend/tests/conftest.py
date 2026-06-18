"""Test fixtures for the EcoMentor AI backend test suite.

Provides app, client, mock repositories, and pre-configured
service instances with all dependencies mocked.
"""

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


# ── Mock repositories ────────────────────────────────────────────


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
def mock_carbon_history_repo(mocker):
    return mocker.MagicMock(name="CarbonHistoryRepository")


@pytest.fixture
def mock_ai_report_repo(mocker):
    return mocker.MagicMock(name="AIReportRepository")


@pytest.fixture
def mock_ai_service(mocker):
    return mocker.MagicMock(name="AIService")


@pytest.fixture
def mock_cache_service(mocker):
    return mocker.MagicMock(name="CacheService")


# ── Service instances ────────────────────────────────────────────


@pytest.fixture
def auth_service(mock_user_repo):
    from app.services.auth_service import AuthService

    return AuthService(user_repository=mock_user_repo)


@pytest.fixture
def dashboard_service(mock_carbon_history_repo, mock_activity_repo, mock_user_repo):
    from app.services.dashboard_service import DashboardService

    return DashboardService(
        carbon_history_repository=mock_carbon_history_repo,
        activity_repository=mock_activity_repo,
        user_repository=mock_user_repo,
    )


@pytest.fixture
def dashboard_service_with_ai(
    mock_carbon_history_repo, mock_activity_repo, mock_user_repo, mock_ai_service
):
    from app.services.dashboard_service import DashboardService

    return DashboardService(
        carbon_history_repository=mock_carbon_history_repo,
        activity_repository=mock_activity_repo,
        user_repository=mock_user_repo,
        ai_service=mock_ai_service,
    )


@pytest.fixture
def activity_service(
    mock_activity_repo, mock_carbon_history_repo, mock_user_repo, mock_ai_service
):
    from app.services.activity_service import ActivityService

    return ActivityService(
        activity_repository=mock_activity_repo,
        carbon_history_repository=mock_carbon_history_repo,
        user_repository=mock_user_repo,
        ai_service=mock_ai_service,
    )


@pytest.fixture
def ai_service(mock_carbon_history_repo):
    from app.services.ai_service import AIService

    return AIService(
        api_key="test-key",
        ai_report_repository=None,
    )


@pytest.fixture
def mock_gemini(mocker):
    return mocker.patch(
        "app.services.ai_service.AIService._call_gemini",
        return_value={"test": "response"},
    )


@pytest.fixture
def leaderboard_service(mock_user_repo, mock_footprint_repo):
    from app.services.leaderboard_service import LeaderboardService

    return LeaderboardService(
        user_repository=mock_user_repo,
        footprint_repository=mock_footprint_repo,
    )


@pytest.fixture
def carbon_service():
    from app.services.carbon_service import CarbonService

    return CarbonService()


# ── New feature service fixtures ─────────────────────────────────


@pytest.fixture
def coach_service(
    mock_ai_service,
    mock_carbon_history_repo,
    mock_activity_repo,
    mock_user_repo,
    mock_cache_service,
):
    from app.services.coach_service import CoachService

    return CoachService(
        ai_service=mock_ai_service,
        carbon_history_repo=mock_carbon_history_repo,
        activity_repo=mock_activity_repo,
        user_repo=mock_user_repo,
        cache_service=mock_cache_service,
    )


@pytest.fixture
def report_service(
    mock_ai_service,
    mock_carbon_history_repo,
    mock_user_repo,
    mock_cache_service,
):
    from app.services.report_service import ReportService

    return ReportService(
        ai_service=mock_ai_service,
        carbon_history_repo=mock_carbon_history_repo,
        user_repo=mock_user_repo,
        cache_service=mock_cache_service,
    )


@pytest.fixture
def simulator_service(
    mock_ai_service,
    mock_carbon_history_repo,
    mock_user_repo,
):
    from app.services.simulator_service import SimulatorService

    return SimulatorService(
        ai_service=mock_ai_service,
        carbon_history_repo=mock_carbon_history_repo,
        user_repo=mock_user_repo,
    )


@pytest.fixture
def habit_service(
    mock_ai_service,
    mock_activity_repo,
    mock_carbon_history_repo,
    mock_user_repo,
    mock_cache_service,
):
    from app.services.habit_service import HabitService

    return HabitService(
        ai_service=mock_ai_service,
        activity_repo=mock_activity_repo,
        carbon_history_repo=mock_carbon_history_repo,
        user_repo=mock_user_repo,
        cache_service=mock_cache_service,
    )


@pytest.fixture
def forecast_service(
    mock_carbon_history_repo,
    mock_user_repo,
):
    from app.services.forecast_service import ForecastService

    return ForecastService(
        carbon_history_repo=mock_carbon_history_repo,
        user_repo=mock_user_repo,
    )
