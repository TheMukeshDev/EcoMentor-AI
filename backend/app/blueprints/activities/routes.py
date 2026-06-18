from flask import Blueprint

activities_bp = Blueprint("activities", __name__)


@activities_bp.route("", methods=["GET"])
def list_activities():
    pass


@activities_bp.route("", methods=["POST"])
def log_activity():
    pass


@activities_bp.route("/<activity_id>", methods=["GET"])
def get_activity(activity_id):
    pass


@activities_bp.route("/<activity_id>", methods=["DELETE"])
def delete_activity(activity_id):
    pass
