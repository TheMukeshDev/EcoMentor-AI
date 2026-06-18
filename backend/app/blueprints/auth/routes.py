from flask import Blueprint, request

from app.middleware.auth_middleware import require_auth
from app.utils.responses import success_response, error_response
from app.utils.validators import validate_body
from app.blueprints.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    UpdateProfileRequest,
)
from app.extensions import db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)

_user_repo = UserRepository(db)

_service = AuthService(_user_repo)


@auth_bp.route("/register", methods=["POST"])
@validate_body(RegisterRequest)
def register():
    data = request.validated_body
    try:
        user = _service.register_user(data)
        return success_response(user, 201)
    except Exception as e:
        return error_response(str(e), 400)


@auth_bp.route("/login", methods=["POST"])
@validate_body(LoginRequest)
def login():
    data = request.validated_body
    try:
        uid = _service.authenticate_user(data["id_token"])
        profile = _service.get_user_profile(uid)
        return success_response({"uid": uid, "profile": profile})
    except Exception as e:
        return error_response(str(e), 401)


@auth_bp.route("/profile", methods=["GET"])
@require_auth
def get_profile():
    from flask import g

    try:
        profile = _service.get_user_profile(g.user_id)
        return success_response(profile)
    except Exception as e:
        return error_response(str(e), 404)


@auth_bp.route("/profile", methods=["PUT"])
@require_auth
@validate_body(UpdateProfileRequest)
def update_profile():
    from flask import g

    data = request.validated_body
    try:
        profile = _service.update_user_profile(g.user_id, data)
        return success_response(profile)
    except Exception as e:
        return error_response(str(e), 400)
