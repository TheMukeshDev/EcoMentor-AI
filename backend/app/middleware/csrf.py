import secrets
import hmac
import time
import logging
from functools import wraps

from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)


def generate_csrf_token():
    return secrets.token_hex(32)


def validate_csrf_token(token, secret):
    expected = hmac.new(secret.encode(), b"csrf-token", "sha256").hexdigest()
    return hmac.compare_digest(token, expected)


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
        expected = hmac.new(secret.encode(), b"csrf-token", "sha256").hexdigest()

        if not hmac.compare_digest(token, expected):
            logger.warning("CSRF token mismatch on %s %s", request.method, request.path)
            return jsonify(
                {
                    "status": "error",
                    "message": "Invalid CSRF token",
                }
            ), 403

        return f(*args, **kwargs)

    return wrapper


def csrf_token_endpoint():
    token = generate_csrf_token()
    secret = current_app.config.get("SECRET_KEY", "")
    expected = hmac.new(secret.encode(), b"csrf-token", "sha256").hexdigest()
    return jsonify(
        {
            "csrf_token": expected,
        }
    )
