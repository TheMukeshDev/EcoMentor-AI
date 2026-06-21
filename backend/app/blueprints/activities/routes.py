import logging

from flask import Blueprint, request, g

from app.middleware.auth_middleware import require_auth
from app.middleware.csrf import csrf_protect
from app.utils.responses import success_response, error_response
from app.utils.validators import validate_body
from app.blueprints.activities.schemas import LogActivityRequest
from app.repositories.activity_repository import ActivityRepository
from app.repositories.carbon_history_repository import CarbonHistoryRepository
from app.repositories.user_repository import UserRepository
from app.services.activity_service import ActivityService
from app.services.ai_service import AIService

"""Activity tracking blueprint routes for logging carbon-emitting actions.

Provides CRUD endpoints for user activities with input validation
and pagination via the activity service layer.
"""

logger = logging.getLogger(__name__)

activities_bp = Blueprint("activities", __name__)


def _get_db():
    from flask import current_app

    return current_app.extensions["firestore"]


def _get_service():
    db = _get_db()

    return ActivityService(
        ActivityRepository(db),
        CarbonHistoryRepository(db),
        UserRepository(db),
        ai_service=AIService(),
    )


@activities_bp.route("", methods=["GET"])
@require_auth
def list_activities():
    limit = min(request.args.get("limit", 50, type=int), 200)
    cursor = request.args.get("cursor", None, type=str)
    activities = _get_service().list_activities(g.user_id, limit=limit, cursor=cursor)
    return success_response(activities)


@activities_bp.route("", methods=["POST"])
@require_auth
@csrf_protect
@validate_body(LogActivityRequest)
def log_activity():
    data = request.validated_body
    try:
        activity = _get_service().log_activity(g.user_id, data)
        return success_response(activity, 201)
    except Exception as e:
        logger.error("Failed to log activity: %s", e)
        return error_response("Failed to log activity", 400)


@activities_bp.route("/<activity_id>", methods=["GET"])
@require_auth
def get_activity(activity_id):
    activity = _get_service().get_activity(activity_id, g.user_id)
    if not activity:
        return error_response("Activity not found", 404)
    return success_response(activity)


@activities_bp.route("/<activity_id>", methods=["DELETE"])
@require_auth
@csrf_protect
def delete_activity(activity_id):
    _get_service().delete_activity(activity_id, g.user_id)
    return success_response({"message": "Activity deleted"})
