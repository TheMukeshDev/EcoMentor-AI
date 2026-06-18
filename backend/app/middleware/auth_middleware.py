from functools import wraps

from flask import request, g

from app.utils.errors import AuthenticationError


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise AuthenticationError("Missing or invalid Authorization header")
        id_token = auth_header.split(" ", 1)[1]
        from firebase_admin import auth as firebase_auth

        try:
            decoded = firebase_auth.verify_id_token(id_token)
            g.current_user = decoded
            g.user_id = decoded["uid"]
        except Exception as exc:
            raise AuthenticationError(f"Invalid token: {exc}")
        return f(*args, **kwargs)

    return decorated
