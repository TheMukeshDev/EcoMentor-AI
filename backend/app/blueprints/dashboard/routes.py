import logging

from flask import Blueprint, request

from app.middleware.auth_middleware import require_auth
from app.utils.responses import success_response, error_response
from app.extensions import db
from app.repositories.carbon_history_repository import CarbonHistoryRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.user_repository import UserRepository
from app.services.dashboard_service import DashboardService
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__)

_carbon_history_repo = CarbonHistoryRepository(db)
_activity_repo = ActivityRepository(db)
_user_repo = UserRepository(db)
_ai_service = AIService()
_service = DashboardService(
    _carbon_history_repo, _activity_repo, _user_repo, ai_service=_ai_service
)


@dashboard_bp.route("/summary", methods=["GET"])
@require_auth
def get_summary():
    from flask import g

    try:
        data = _service.get_summary(g.user_id)
        return success_response(data)
    except Exception as e:
        logger.error("Failed to get summary: %s", e)
        return error_response("Failed to get dashboard summary", 400)


@dashboard_bp.route("/history", methods=["GET"])
@require_auth
def get_history():
    from flask import g

    period = request.args.get("period", "last_7")
    try:
        data = _service.get_history(g.user_id, period)
        return success_response(data)
    except Exception as e:
        logger.error("Failed to get history: %s", e)
        return error_response("Failed to get carbon history", 400)


@dashboard_bp.route("/insights", methods=["GET"])
@require_auth
def get_insights():
    from flask import g

    try:
        data = _service.get_insights(g.user_id)
        return success_response(data)
    except Exception as e:
        logger.error("Failed to get insights: %s", e)
        return error_response("Failed to get insights", 400)


@dashboard_bp.route("/trends", methods=["GET"])
@require_auth
def get_trends():
    from flask import g

    try:
        data = _service.get_trends(g.user_id)
        return success_response(data)
    except Exception as e:
        logger.error("Failed to get trends: %s", e)
        return error_response("Failed to get trends", 400)
