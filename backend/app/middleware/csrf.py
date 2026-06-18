import secrets
import hmac
import time
import logging
from functools import wraps

from flask import request, jsonify, current_app, g

logger = logging.getLogger(__name__)

CSRF_TOKEN_TTL = 3600


def generate_csrf_token(user_id=None):
    nonce = secrets.token_hex(32)
    timestamp = str(int(time.time()))
    secret = current_app.config.get("SECRET_KEY", "")
    uid_part = user_id or ""
    raw = f"{nonce}:{timestamp}:{uid_part}"
    signature = hmac.new(secret.encode(), raw.encode(), "sha256").hexdigest()
    return f"{nonce}:{timestamp}:{uid_part}:{signature}"


def validate_csrf_token(token, secret, user_id=None):
    try:
        parts = token.split(":")
        if len(parts) != 4:
            return False
        nonce, timestamp, uid_part, signature = parts
        expected = hmac.new(
            secret.encode(), f"{nonce}:{timestamp}:{uid_part}".encode(), "sha256"
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return False
        
        # Enforce that uid_part in the CSRF token matches the current authenticated user state
        if (uid_part or "") != (user_id or ""):
            return False
            
        token_time = int(timestamp)
        if time.time() - token_time > CSRF_TOKEN_TTL:
            return False
        return True
    except (ValueError, IndexError):
        return False


def csrf_protect(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return f(*args, **kwargs)

        if current_app.config.get("TESTING"):
            return f(*args, **kwargs)

        token = request.headers.get("X-CSRF-Token") or request.headers.get(
            "X-CSRFToken"
        )

        if not token:
            logger.warning("CSRF token missing on %s %s", request.method, request.path)
            return jsonify(
                {
                    "status": "error",
                    "message": "CSRF token required",
                }
            ), 403

        secret = current_app.config.get("SECRET_KEY", "")
        uid = getattr(g, "user_id", None)
        if not validate_csrf_token(token, secret, uid):
            logger.warning(
                "CSRF token invalid/expired on %s %s", request.method, request.path
            )
            return jsonify(
                {
                    "status": "error",
                    "message": "Invalid or expired CSRF token",
                }
            ), 403

        return f(*args, **kwargs)

    return wrapper


def csrf_token_endpoint():
    uid = getattr(g, "user_id", None)
    
    # If uid isn't already set but an Authorization header is provided, try to decode it
    if not uid:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                id_token = auth_header.split(" ", 1)[1]
                from firebase_admin import auth as firebase_auth
                decoded = firebase_auth.verify_id_token(id_token)
                uid = decoded["uid"]
            except Exception:
                pass

    token = generate_csrf_token(uid)
    return jsonify(
        {
            "csrf_token": token,
        }
    )
