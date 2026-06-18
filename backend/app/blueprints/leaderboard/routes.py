from flask import Blueprint

from app.middleware.auth_middleware import require_auth
from app.utils.responses import success_response, error_response
from app.extensions import db
from app.repositories.user_repository import UserRepository
from app.repositories.footprint_repository import FootprintRepository
from app.services.leaderboard_service import LeaderboardService

leaderboard_bp = Blueprint("leaderboard", __name__)

_user_repo = UserRepository(db)
_footprint_repo = FootprintRepository(db)
_service = LeaderboardService(_user_repo, _footprint_repo)


@leaderboard_bp.route("/global", methods=["GET"])
@require_auth
def get_global_leaderboard():
    try:
        data = _service.get_global_leaderboard()
        return success_response(data)
    except Exception as e:
        return error_response(str(e), 400)


@leaderboard_bp.route("/friends", methods=["GET"])
@require_auth
def get_friends_leaderboard():
    from flask import g

    try:
        data = _service.get_friends_leaderboard(g.user_id)
        return success_response(data)
    except Exception as e:
        return error_response(str(e), 400)
