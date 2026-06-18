from flask import Blueprint

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/summary", methods=["GET"])
def get_summary():
    pass


@dashboard_bp.route("/history", methods=["GET"])
def get_history():
    pass


@dashboard_bp.route("/stats", methods=["GET"])
def get_stats():
    pass
