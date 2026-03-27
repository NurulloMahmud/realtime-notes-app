from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "type": "access", "exp": expire},
        settings.JWT_SECRET,
        algorithm="HS256",
    )


def create_refresh_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": user_id, "type": "refresh", "exp": expire},
        settings.JWT_SECRET,
        algorithm="HS256",
    )


def decode_token(token: str, expected_type: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None
