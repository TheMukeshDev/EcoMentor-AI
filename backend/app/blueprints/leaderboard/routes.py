from flask import Blueprint

leaderboard_bp = Blueprint("leaderboard", __name__)


@leaderboard_bp.route("/global", methods=["GET"])
def get_global_leaderboard():
    pass


@leaderboard_bp.route("/friends", methods=["GET"])
def get_friends_leaderboard():
    pass
