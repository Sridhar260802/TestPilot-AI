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
    plan: str

    class Config:
        from_attributes = True


class PlanUpdateRequest(BaseModel):
    plan: Literal["basic", "standard", "premium"]