import logging

from flask import Blueprint, request

from app.middleware.auth_middleware import require_auth
from app.middleware.csrf import csrf_protect
from app.utils.responses import success_response, error_response
from app.extensions import db
from app.repositories.user_repository import UserRepository
from app.repositories.footprint_repository import FootprintRepository
from app.services.leaderboard_service import LeaderboardService

logger = logging.getLogger(__name__)

leaderboard_bp = Blueprint("leaderboard", __name__)

_user_repo = UserRepository(db)
_footprint_repo = FootprintRepository(db)
_service = LeaderboardService(_user_repo, _footprint_repo)


@leaderboard_bp.route("/global", methods=["GET"])
@require_auth
def get_global_leaderboard():
    try:
        limit = request.args.get("limit", 20, type=int)
        data = _service.get_global_leaderboard(limit=limit)
        return success_response(data)
    except Exception as e:
        logger.error("Failed to get global leaderboard: %s", e)
        return error_response("Failed to get leaderboard", 400)


@leaderboard_bp.route("/friends", methods=["GET"])
@require_auth
def get_friends_leaderboard():
    from flask import g

    try:
        data = _service.get_friends_leaderboard(g.user_id)
        return success_response(data)
    except Exception as e:
        logger.error("Failed to get friends leaderboard: %s", e)
        return error_response("Failed to get friends leaderboard", 400)


@leaderboard_bp.route("/friends/add", methods=["POST"])
@require_auth
@csrf_protect
def add_friend():
    from flask import g

    data = request.get_json(silent=True) or {}
    friend_id = data.get("friend_id", "")
    if not friend_id:
        return error_response("friend_id is required", 422)
    try:
        result = _service.add_friend(g.user_id, friend_id)
        if result:
            return success_response({"message": "Friend added"})
        return error_response("Failed to add friend", 400)
    except Exception as e:
        logger.error("Failed to add friend: %s", e)
        return error_response("Failed to add friend", 400)


@leaderboard_bp.route("/friends/remove", methods=["POST"])
@require_auth
@csrf_protect
def remove_friend():
    from flask import g

    data = request.get_json(silent=True) or {}
    friend_id = data.get("friend_id", "")
    if not friend_id:
        return error_response("friend_id is required", 422)
    try:
        result = _service.remove_friend(g.user_id, friend_id)
        if result:
            return success_response({"message": "Friend removed"})
        return error_response("Failed to remove friend", 400)
    except Exception as e:
        logger.error("Failed to remove friend: %s", e)
        return error_response("Failed to remove friend", 400)
