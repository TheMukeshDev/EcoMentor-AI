from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=128)
    name: str = Field("", max_length=100)


class LoginRequest(BaseModel):
    id_token: str = Field(..., min_length=10)


class UpdateProfileRequest(BaseModel):
    name: str = Field(None, max_length=100)
