from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from app.config import get_settings


def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt.
    Enforces password byte-length limits explicitly: bcrypt natively caps passwords at 72 bytes.
    Never silently truncate; raise ValueError if limit is exceeded.
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password cannot exceed 72 bytes for bcrypt security hashing.")

    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against stored bcrypt hash safely.
    Handles bcrypt's 72-byte limit defensively without crashing.
    """
    plain_bytes = plain_password.encode("utf-8")
    if len(plain_bytes) > 72:
        return False

    hashed_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(admin_id: str, email: str) -> str:
    """
    Signs a minimal JWT access token with user claims, subject, and expiration.
    Excludes sensitive details like password hashes.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": admin_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Decodes and validates a JWT access token against the configured secret and algorithm.
    Returns payload dictionary or None if invalid or expired.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except (jwt.PyJWTError, Exception):
        return None
