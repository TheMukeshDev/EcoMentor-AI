"""Pydantic schemas for authentication endpoints.

All schemas enforce extra='forbid' to reject unknown fields.
"""

from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    """Schema for user registration requests."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=128)
    name: str = Field("", max_length=100)


class LoginRequest(BaseModel):
    """Schema for user login requests."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=1, max_length=128)


class UpdateProfileRequest(BaseModel):
    """Schema for profile update requests."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, max_length=100)


class GoogleAuthRequest(BaseModel):
    """Schema for Google auth requests."""

    model_config = ConfigDict(extra="forbid")

    idToken: str = Field(..., min_length=10, max_length=5000)


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password requests."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(..., min_length=5, max_length=120)


class ConfirmResetRequest(BaseModel):
    """Schema for password reset confirmation."""

    model_config = ConfigDict(extra="forbid")

    oob_code: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=128)
