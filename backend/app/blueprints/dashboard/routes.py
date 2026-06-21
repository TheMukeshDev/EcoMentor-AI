import logging

from flask import Blueprint, request, g

from app.middleware.auth_middleware import require_auth
from app.utils.responses import success_response, error_response
from app.repositories.carbon_history_repository import CarbonHistoryRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.user_repository import UserRepository
from app.services.dashboard_service import DashboardService
from app.services.ai_service import AIService

"""Dashboard blueprint routes for carbon footprint analytics.

Aggregates summary statistics, historical trends, and AI-powered
insights for the user's dashboard view.
"""

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__)


VALID_PERIODS = {"last_7", "last_30", "last_90", "all"}


def _get_db():
    from flask import current_app

    return current_app.extensions["firestore"]


def _get_service():
    db = _get_db()

    return DashboardService(
        CarbonHistoryRepository(db),
        ActivityRepository(db),
        UserRepository(db),
        ai_service=AIService(),
    )


@dashboard_bp.route("/summary", methods=["GET"])
@require_auth
def get_summary():
    try:
        data = _get_service().get_summary(g.user_id)
        return success_response(data)
    except Exception as e:
        logger.error("Failed to get summary: %s", e)
        return error_response("Failed to get dashboard summary", 400)


@dashboard_bp.route("/history", methods=["GET"])
@require_auth
def get_history():
    period = request.args.get("period", "last_7")
    if period not in VALID_PERIODS:
        return error_response("Invalid period", 422)
    try:
        data = _get_service().get_history(g.user_id, period)
        return success_response(data)
    except Exception as e:
        logger.error("Failed to get history: %s", e)
        return error_response("Failed to get carbon history", 400)


@dashboard_bp.route("/insights", methods=["GET"])
@require_auth
def get_insights():
    try:
        data = _get_service().get_insights(g.user_id)
        return success_response(data)
    except Exception as e:
        logger.error("Failed to get insights: %s", e)
        return error_response("Failed to get insights", 400)


@dashboard_bp.route("/trends", methods=["GET"])
@require_auth
def get_trends():
    try:
        data = _get_service().get_trends(g.user_id)
        return success_response(data)
    except Exception as e:
        logger.error("Failed to get trends: %s", e)
        return error_response("Failed to get trends", 400)
