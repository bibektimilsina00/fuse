from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet
from jose import jwt
from passlib.context import CryptContext

from apps.api.app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

try:
    fernet = Fernet(settings.ENCRYPTION_KEY)
except ValueError as exc:
    raise ValueError("ENCRYPTION_KEY must be a valid Fernet key") from exc

ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def encrypt_credential(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()


def decrypt_credential(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()


async def get_current_user_from_token(token: str) -> Any | None:
    """
    Decodes a JWT token and returns the user object.
    Used for WebSocket authentication.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email or not isinstance(email, str):
            return None

        from apps.api.app.core.database import AsyncSessionLocal
        from apps.api.app.features.users.repository import UserRepository

        async with AsyncSessionLocal() as db:
            user_repo = UserRepository(db)
            user = await user_repo.get_by_email(email=email)
            return user
    except Exception:
        return None
