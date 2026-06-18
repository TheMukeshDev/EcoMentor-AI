from flask import Blueprint, request

from app.middleware.auth_middleware import require_auth
from app.utils.responses import success_response, error_response
from app.utils.validators import validate_body
from app.blueprints.activities.schemas import LogActivityRequest
from app.extensions import db
from app.repositories.activity_repository import ActivityRepository
from app.services.activity_service import ActivityService

activities_bp = Blueprint("activities", __name__)

_activity_repo = ActivityRepository(db)

_service = ActivityService(_activity_repo)


@activities_bp.route("", methods=["GET"])
@require_auth
def list_activities():
    from flask import g

    activities = _service.list_activities(g.user_id)
    return success_response(activities)


@activities_bp.route("", methods=["POST"])
@require_auth
@validate_body(LogActivityRequest)
def log_activity():
    from flask import g

    data = request.validated_body
    try:
        activity = _service.log_activity(g.user_id, data)
        return success_response(activity, 201)
    except Exception as e:
        return error_response(str(e), 400)


@activities_bp.route("/<activity_id>", methods=["GET"])
@require_auth
def get_activity(activity_id):
    activity = _service.get_activity(activity_id)
    if not activity:
        return error_response("Activity not found", 404)
    return success_response(activity)


@activities_bp.route("/<activity_id>", methods=["DELETE"])
@require_auth
def delete_activity(activity_id):
    _service.delete_activity(activity_id)
    return success_response({"message": "Activity deleted"})
