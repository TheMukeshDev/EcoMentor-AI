from flask import Blueprint, request

from app.middleware.auth_middleware import require_auth
from app.utils.responses import success_response, error_response
from app.extensions import db
from app.repositories.carbon_history_repository import CarbonHistoryRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.user_repository import UserRepository
from app.services.dashboard_service import DashboardService

dashboard_bp = Blueprint("dashboard", __name__)

_carbon_history_repo = CarbonHistoryRepository(db)
_activity_repo = ActivityRepository(db)
_user_repo = UserRepository(db)
_service = DashboardService(_carbon_history_repo, _activity_repo, _user_repo)


@dashboard_bp.route("/summary", methods=["GET"])
@require_auth
def get_summary():
    from flask import g

    try:
        data = _service.get_summary(g.user_id)
        return success_response(data)
    except Exception as e:
        return error_response(str(e), 400)


@dashboard_bp.route("/history", methods=["GET"])
@require_auth
def get_history():
    from flask import g

    period = request.args.get("period", "last_7")
    try:
        data = _service.get_history(g.user_id, period)
        return success_response(data)
    except Exception as e:
        return error_response(str(e), 400)


@dashboard_bp.route("/trends", methods=["GET"])
@require_auth
def get_trends():
    from flask import g

    try:
        data = _service.get_trends(g.user_id)
        return success_response(data)
    except Exception as e:
        return error_response(str(e), 400)
