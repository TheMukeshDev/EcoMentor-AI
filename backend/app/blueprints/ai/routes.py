from flask import Blueprint

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/recommendations", methods=["GET"])
def get_recommendations():
    pass


@ai_bp.route("/insights", methods=["GET"])
def get_insights():
    pass


@ai_bp.route("/chat", methods=["POST"])
def chat():
    pass
