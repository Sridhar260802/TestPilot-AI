from typing import Literal

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    # None until the user actually pays for a plan (basic/standard/premium).
    plan: str | None = None
    auth_provider: str
    picture: str | None = None

    class Config:
        from_attributes = True


class GoogleLoginRequest(BaseModel):
    # The ID token (credential) returned by Google Identity Services
    # on the frontend after the user signs in with Google.
    token: str


class GoogleLoginResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    # None until the user actually pays for a plan (basic/standard/premium).
    plan: str | None = None
    auth_provider: str
    picture: str | None = None
    access_token: str
    token_type: str = "bearer"

    class Config:
        from_attributes = True


class PlanUpdateRequest(BaseModel):
    plan: Literal["basic", "standard", "premium"]