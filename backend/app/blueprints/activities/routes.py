import logging

from flask import Blueprint, request

from app.middleware.auth_middleware import require_auth
from app.middleware.csrf import csrf_protect
from app.utils.responses import success_response, error_response
from app.utils.validators import validate_body
from app.blueprints.activities.schemas import LogActivityRequest
from app.extensions import db
from app.repositories.activity_repository import ActivityRepository
from app.repositories.carbon_history_repository import CarbonHistoryRepository
from app.repositories.user_repository import UserRepository
from app.services.activity_service import ActivityService
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

activities_bp = Blueprint("activities", __name__)

_activity_repo = ActivityRepository(db)
_carbon_history_repo = CarbonHistoryRepository(db)
_user_repo = UserRepository(db)
_ai_service = AIService()
_service = ActivityService(
    _activity_repo, _carbon_history_repo, _user_repo, ai_service=_ai_service
)


@activities_bp.route("", methods=["GET"])
@require_auth
def list_activities():
    from flask import g

    limit = request.args.get("limit", None, type=int)
    cursor = request.args.get("cursor", None, type=str)
    activities = _service.list_activities(g.user_id, limit=limit, cursor=cursor)
    return success_response(activities)


@activities_bp.route("", methods=["POST"])
@require_auth
@csrf_protect
@validate_body(LogActivityRequest)
def log_activity():
    from flask import g

    data = request.validated_body
    try:
        activity = _service.log_activity(g.user_id, data)
        return success_response(activity, 201)
    except Exception as e:
        logger.error("Failed to log activity: %s", e)
        return error_response("Failed to log activity", 400)


@activities_bp.route("/<activity_id>", methods=["GET"])
@require_auth
def get_activity(activity_id):
    activity = _service.get_activity(activity_id)
    if not activity:
        return error_response("Activity not found", 404)
    return success_response(activity)


@activities_bp.route("/<activity_id>", methods=["DELETE"])
@require_auth
@csrf_protect
def delete_activity(activity_id):
    _service.delete_activity(activity_id)
    return success_response({"message": "Activity deleted"})
