import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken
from app.common.exceptions import BankingException
from app.common.logging import get_logger
from app.config import settings
from app.users.models import User

logger = get_logger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": "access"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def register(db: AsyncSession, email: str, password: str, full_name: str) -> User:
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise BankingException("Email already registered", 409, "EMAIL_TAKEN")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    await db.flush()
    logger.info("user_registered", user_id=user.id)
    return user


async def login(
    db: AsyncSession, email: str, password: str
) -> tuple[str, str]:
    result = await db.execute(
        select(User).where(User.email == email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise BankingException("Invalid credentials", 401, "INVALID_CREDENTIALS")
    if not user.is_active:
        raise BankingException("Account is disabled", 403, "ACCOUNT_DISABLED")

    access_token = create_access_token(user.id)

    raw_refresh = str(uuid.uuid4())
    token_hash = _hash_token(raw_refresh)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    await db.flush()

    logger.info("user_logged_in", user_id=user.id)
    return access_token, raw_refresh


async def refresh_access_token(db: AsyncSession, raw_refresh: str) -> str:
    token_hash = _hash_token(raw_refresh)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )
    token = result.scalar_one_or_none()

    if not token or token.expires_at < datetime.now(timezone.utc):
        raise BankingException("Invalid or expired refresh token", 401, "INVALID_REFRESH_TOKEN")

    return create_access_token(token.user_id)


async def logout(db: AsyncSession, raw_refresh: str) -> None:
    token_hash = _hash_token(raw_refresh)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token = result.scalar_one_or_none()
    if token:
        token.revoked_at = datetime.now(timezone.utc)
        await db.flush()
