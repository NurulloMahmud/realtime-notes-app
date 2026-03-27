import uuid
from datetime import datetime
import re
from pydantic import BaseModel, EmailStr, field_validator

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")


class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not USERNAME_RE.match(v):
            raise ValueError("username must be 3-32 chars, letters/digits/underscore only")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
