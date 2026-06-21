import logging

from flask import Blueprint, request, g

from app.middleware.auth_middleware import require_auth
from app.middleware.csrf import csrf_protect
from app.utils.responses import success_response, error_response
from app.repositories.user_repository import UserRepository
from app.repositories.footprint_repository import FootprintRepository
from app.services.leaderboard_service import LeaderboardService

"""Leaderboard blueprint routes for global and friend rankings.

Provides endpoints for viewing leaderboards and managing
friend relationships with input validation.
"""

logger = logging.getLogger(__name__)

leaderboard_bp = Blueprint("leaderboard", __name__)


def _get_db():
    from flask import current_app

    return current_app.extensions["firestore"]


def _get_service():
    db = _get_db()
    return LeaderboardService(UserRepository(db), FootprintRepository(db))


@leaderboard_bp.route("/global", methods=["GET"])
@require_auth
def get_global_leaderboard():
    try:
        limit = request.args.get("limit", 20, type=int)
        data = _get_service().get_global_leaderboard(limit=limit)
        return success_response(data)
    except Exception as e:
        logger.error("Failed to get global leaderboard: %s", e)
        return error_response("Failed to get leaderboard", 400)


@leaderboard_bp.route("/friends", methods=["GET"])
@require_auth
def get_friends_leaderboard():
    try:
        data = _get_service().get_friends_leaderboard(g.user_id)
        return success_response(data)
    except Exception as e:
        logger.error("Failed to get friends leaderboard: %s", e)
        return error_response("Failed to get friends leaderboard", 400)


@leaderboard_bp.route("/friends/add", methods=["POST"])
@require_auth
@csrf_protect
def add_friend():
    data = request.get_json(silent=True) or {}
    friend_id = data.get("friend_id", "")
    if (
        not friend_id
        or len(friend_id) > 128
        or not friend_id.replace("-", "").replace("_", "").isalnum()
    ):
        return error_response("Invalid friend_id", 422)
    try:
        result = _get_service().add_friend(g.user_id, friend_id)
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
    data = request.get_json(silent=True) or {}
    friend_id = data.get("friend_id", "")
    if (
        not friend_id
        or len(friend_id) > 128
        or not friend_id.replace("-", "").replace("_", "").isalnum()
    ):
        return error_response("Invalid friend_id", 422)
    try:
        result = _get_service().remove_friend(g.user_id, friend_id)
        if result:
            return success_response({"message": "Friend removed"})
        return error_response("Failed to remove friend", 400)
    except Exception as e:
        logger.error("Failed to remove friend: %s", e)
        return error_response("Failed to remove friend", 400)
