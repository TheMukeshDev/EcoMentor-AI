import logging

from flask import Blueprint, request

from app.middleware.auth_middleware import require_auth
from app.middleware.csrf import csrf_protect
from app.utils.responses import success_response, error_response
from app.utils.rate_limiter import rate_limiter
from app.utils.audit import log_event
from app.utils.validators import validate_body
from app.blueprints.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    UpdateProfileRequest,
)
from app.extensions import db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

_user_repo = UserRepository(db)

_service = AuthService(_user_repo)


@auth_bp.route("/register", methods=["POST"])
@csrf_protect
@rate_limiter.limit(scope="ip", capacity=5, refill_rate=1)
@validate_body(RegisterRequest)
def register():
    data = request.validated_body
    ip = request.remote_addr or "unknown"
    try:
        result = _service.register_user(data)
        log_event(
            "user_registered", user_id=result.get("profile", {}).get("uid"), ip=ip
        )
        return success_response(
            {"id_token": result["id_token"], "profile": result["profile"]}, 201
        )
    except Exception as e:
        logger.error("Registration failed: %s", e)
        log_event(
            "registration_failed", ip=ip, details={"email": data.get("email", "")}
        )
        return error_response("Registration failed", 400)


@auth_bp.route("/login", methods=["POST"])
@csrf_protect
@rate_limiter.limit(scope="ip", capacity=10, refill_rate=1)
@validate_body(LoginRequest)
def login():
    data = request.validated_body
    ip = request.remote_addr or "unknown"
    try:
        result = _service.login_user(data["email"], data["password"])
        log_event("user_login", user_id=result.get("uid"), ip=ip)
        return success_response(
            {"id_token": result["id_token"], "profile": result["profile"]}
        )
    except Exception as e:
        logger.error("Login failed: %s", e)
        log_event("login_failed", ip=ip, details={"email": data.get("email", "")})
        return error_response("Invalid credentials", 401)


@auth_bp.route("/google", methods=["POST"])
@rate_limiter.limit(scope="ip", capacity=5, refill_rate=1)
def google_auth():
    data = request.get_json(silent=True) or {}
    id_token = data.get("idToken", "")
    if not id_token:
        return error_response("Missing ID token", 400)
    ip = request.remote_addr or "unknown"
    try:
        result = _service.google_auth(id_token)
        log_event("google_auth", user_id=result.get("profile", {}).get("uid"), ip=ip)
        return success_response(result["profile"])
    except Exception as e:
        logger.error("Google auth failed: %s", e)
        log_event("google_auth_failed", ip=ip)
        return error_response("Google authentication failed", 401)


@auth_bp.route("/profile", methods=["GET"])
@require_auth
def get_profile():
    from flask import g

    try:
        profile = _service.get_user_profile(g.user_id)
        return success_response(profile)
    except Exception as e:
        logger.error("Failed to get profile: %s", e)
        return error_response("Profile not found", 404)


@auth_bp.route("/profile", methods=["PUT"])
@require_auth
@csrf_protect
@validate_body(UpdateProfileRequest)
def update_profile():
    from flask import g

    data = request.validated_body
    try:
        profile = _service.update_user_profile(g.user_id, data)
        return success_response(profile)
    except Exception as e:
        logger.error("Failed to update profile: %s", e)
        return error_response("Failed to update profile", 400)
