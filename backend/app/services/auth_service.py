"""Authentication service for user registration, login, and profile management.

Handles Firebase Authentication integration for email/password and
Google OAuth sign-in flows, plus Firestore user profile persistence.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import requests
from firebase_admin import auth as firebase_auth
from flask import current_app

from app.utils.errors import AuthenticationError

logger = logging.getLogger(__name__)

FIREBASE_AUTH_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
)

_ALLOWED_PROFILE_FIELDS: frozenset[str] = frozenset({"name"})


class AuthService:
    """Manages user authentication and profile operations."""

    def __init__(self, user_repository: Any) -> None:
        self._user_repo = user_repository

    def register_user(self, data: dict[str, Any]) -> dict[str, Any]:
        """Register a new user with email and password.

        Args:
            data: Dictionary containing 'email', 'password', and optional 'name'.

        Returns:
            Dictionary with 'profile' and 'id_token' keys.

        Raises:
            AuthenticationError: If registration fails.
        """
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

    def login_user(
        self, email: str, password: str
    ) -> dict[str, Any]:
        """Authenticate an existing user with email and password.

        Args:
            email: The user's email address.
            password: The user's password.

        Returns:
            Dictionary with 'uid', 'profile', and 'id_token' keys.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        try:
            user = firebase_auth.get_user_by_email(email)
        except firebase_auth.UserNotFoundError:
            raise AuthenticationError("Invalid email or password")
        except Exception as exc:
            raise AuthenticationError(f"Login failed: {exc}")

        id_token = self._sign_in_with_password(email, password)
        profile = self.get_user_profile(user.uid)
        return {"uid": user.uid, "profile": profile, "id_token": id_token}

    def authenticate_user(self, id_token: str) -> str:
        """Verify a Firebase ID token and extract the user ID.

        Args:
            id_token: A Firebase ID token string.

        Returns:
            The authenticated user's UID.

        Raises:
            AuthenticationError: If the token is invalid.
        """
        try:
            decoded = firebase_auth.verify_id_token(id_token)
            return decoded["uid"]
        except Exception as exc:
            raise AuthenticationError(f"Invalid token: {exc}")

    def get_user_profile(self, uid: str) -> dict[str, Any]:
        """Retrieve a user's profile from the database.

        Args:
            uid: The user's unique identifier.

        Returns:
            The user profile dictionary.

        Raises:
            AuthenticationError: If the user does not exist.
        """
        user = self._user_repo.get(uid)
        if not user:
            raise AuthenticationError("User not found")
        return user

    def update_user_profile(
        self, uid: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update allowed fields on a user's profile.

        Args:
            uid: The user's unique identifier.
            data: Dictionary of fields to update.

        Returns:
            The updated user profile dictionary.

        Raises:
            AuthenticationError: If the user does not exist.
        """
        existing = self._user_repo.get(uid)
        if not existing:
            raise AuthenticationError("User not found")
        updates = {
            key: value
            for key, value in data.items()
            if key in _ALLOWED_PROFILE_FIELDS
        }
        if not updates:
            return existing
        self._user_repo.update(uid, updates)
        return self._user_repo.get(uid)

    def google_auth(self, id_token: str) -> dict[str, Any]:
        """Authenticate or register a user via Google OAuth.

        Args:
            id_token: A Firebase ID token from Google sign-in.

        Returns:
            Dictionary with 'profile' key.

        Raises:
            AuthenticationError: If token verification fails.
        """
        try:
            decoded = firebase_auth.verify_id_token(id_token)
        except Exception as exc:
            raise AuthenticationError(f"Invalid token: {exc}")

        uid = decoded["uid"]
        email = decoded.get("email", "")
        name = decoded.get("name", decoded.get("display_name", ""))
        photo_url = decoded.get("picture", "")

        existing = self._user_repo.get(uid)
        now = datetime.now(timezone.utc).isoformat()

        if existing:
            profile = self._update_existing_google_user(
                uid, existing, name, email, photo_url, now
            )
        else:
            profile = self._create_new_google_user(
                uid, name, email, photo_url, now
            )

        return {"profile": profile}

    def _update_existing_google_user(
        self,
        uid: str,
        existing: dict[str, Any],
        name: str,
        email: str,
        photo_url: str,
        timestamp: str,
    ) -> dict[str, Any]:
        """Update an existing Google-authenticated user's profile.

        Args:
            uid: The user's unique identifier.
            existing: The current profile data.
            name: Display name from Google.
            email: Email from Google.
            photo_url: Profile photo URL from Google.
            timestamp: ISO-format timestamp for the login event.

        Returns:
            The updated profile dictionary.
        """
        updates = {
            "lastLogin": timestamp,
            "name": name or existing.get("name", ""),
            "email": email or existing.get("email", ""),
            "photoURL": photo_url or existing.get("photoURL", ""),
        }
        self._user_repo.update(uid, updates)
        return self._user_repo.get(uid)

    def _create_new_google_user(
        self,
        uid: str,
        name: str,
        email: str,
        photo_url: str,
        timestamp: str,
    ) -> dict[str, Any]:
        """Create a new user profile from Google sign-in data.

        Args:
            uid: The user's unique identifier.
            name: Display name from Google.
            email: Email from Google.
            photo_url: Profile photo URL from Google.
            timestamp: ISO-format timestamp for account creation.

        Returns:
            The newly created profile dictionary.
        """
        profile = {
            "uid": uid,
            "name": name or email.split("@")[0] or "User",
            "email": email,
            "photoURL": photo_url,
            "createdAt": timestamp,
            "lastLogin": timestamp,
            "onboardingCompleted": False,
            "level": 1,
            "streak": 0,
            "totalCarbonSaved": 0.0,
            "achievements": [],
            "ecoScore": 50,
            "badges": ["Eco Beginner"],
        }
        self._user_repo.set(uid, profile)
        return profile

    def _sign_in_with_password(
        self, email: str, password: str
    ) -> str:
        """Exchange email/password for a Firebase ID token.

        Args:
            email: The user's email address.
            password: The user's password.

        Returns:
            A Firebase ID token string.

        Raises:
            AuthenticationError: If sign-in fails.
        """
        api_key = current_app.config.get("FIREBASE_API_KEY", "")
        if not api_key:
            raise AuthenticationError("Firebase API key not configured")

        try:
            response = requests.post(
                FIREBASE_AUTH_URL,
                params={"key": api_key},
                json={
                    "email": email,
                    "password": password,
                    "returnSecureToken": True,
                },
                timeout=10,
            )
            response_data = response.json()
            if not response.ok:
                error_message = response_data.get("error", {}).get(
                    "message", "Authentication failed"
                )
                raise AuthenticationError(error_message)
            return response_data["idToken"]
        except requests.RequestException as exc:
            raise AuthenticationError(
                f"Authentication service unavailable: {exc}"
            )
