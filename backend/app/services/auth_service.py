import logging
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

from app.utils.errors import AuthenticationError

logger = logging.getLogger(__name__)

_firebase_initialized = False


def _init_firebase_admin():
    global _firebase_initialized
    if _firebase_initialized:
        return
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            firebase_admin.initialize_app()
        except Exception as exc:
            logger.warning("Firebase Admin not configured: %s", exc)
    _firebase_initialized = True


class AuthService:
    def __init__(self, user_repository):
        self._user_repo = user_repository
        _init_firebase_admin()

    def register_user(self, data):
        email = data.get("email")
        password = data.get("password")
        name = data.get("name", "")

        try:
            user_record = firebase_auth.create_user(
                email=email, password=password, display_name=name
            )
        except firebase_auth.EmailAlreadyExistsError:
            raise AuthenticationError("Email already registered")
        except Exception as exc:
            raise AuthenticationError(f"Registration failed: {exc}")

        uid = user_record.uid
        now = datetime.now(timezone.utc).isoformat()
        profile = {
            "uid": uid,
            "email": email,
            "name": name,
            "points": 0,
            "streak": 0,
            "level": "Beginner",
            "badge": "Seedling",
            "created_at": now,
        }
        self._user_repo.set(uid, profile)
        return profile

    def authenticate_user(self, id_token):
        try:
            decoded = firebase_auth.verify_id_token(id_token)
            return decoded["uid"]
        except Exception as exc:
            raise AuthenticationError(f"Invalid token: {exc}")

    def get_user_profile(self, uid):
        user = self._user_repo.get(uid)
        if not user:
            raise AuthenticationError("User not found")
        return user

    def update_user_profile(self, uid, data):
        existing = self._user_repo.get(uid)
        if not existing:
            raise AuthenticationError("User not found")
        allowed = {"name"}
        updates = {k: v for k, v in data.items() if k in allowed}
        if not updates:
            return existing
        self._user_repo.update(uid, updates)
        return self._user_repo.get(uid)
