import logging
from datetime import datetime, timezone

import firebase_admin
import requests
from firebase_admin import auth as firebase_auth, credentials
from flask import current_app

from app.utils.errors import AuthenticationError

logger = logging.getLogger(__name__)

_firebase_initialized = False

FIREBASE_AUTH_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
)


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

        id_token = self._sign_in_with_password(email, password)
        return {"profile": profile, "id_token": id_token}

    def login_user(self, email, password):
        try:
            user = firebase_auth.get_user_by_email(email)
        except firebase_auth.UserNotFoundError:
            raise AuthenticationError("Invalid email or password")
        except Exception as exc:
            raise AuthenticationError(f"Login failed: {exc}")

        id_token = self._sign_in_with_password(email, password)

        profile = self.get_user_profile(user.uid)
        return {"uid": user.uid, "profile": profile, "id_token": id_token}

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

    def _sign_in_with_password(self, email, password):
        api_key = current_app.config.get("FIREBASE_API_KEY", "")
        if not api_key:
            raise AuthenticationError("Firebase API key not configured")

        try:
            resp = requests.post(
                FIREBASE_AUTH_URL,
                params={"key": api_key},
                json={"email": email, "password": password, "returnSecureToken": True},
                timeout=10,
            )
            data = resp.json()
            if not resp.ok:
                error_msg = data.get("error", {}).get(
                    "message", "Authentication failed"
                )
                raise AuthenticationError(error_msg)
            return data["idToken"]
        except requests.RequestException as exc:
            raise AuthenticationError(f"Authentication service unavailable: {exc}")
