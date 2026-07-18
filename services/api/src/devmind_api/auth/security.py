import hmac
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import Any, Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from devmind_api.config import Settings
from devmind_api.technology.hashing import sha256_hex

_password_hasher = PasswordHasher()


class AuthSecurityError(Exception):
    pass


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def password_hash_needs_rehash(password_hash: str) -> bool:
    return _password_hasher.check_needs_rehash(password_hash)


def new_secret_token() -> str:
    return token_urlsafe(48)


def hash_token(token: str) -> str:
    return sha256_hex(token)


def constant_time_equals(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)


def ensure_signing_secret(settings: Settings) -> str:
    signing_value = settings.auth_jwt_secret
    if not signing_value:
        if settings.app_env == "test":
            return "test-only-devmind-auth-secret-with-enough-length"
        raise AuthSecurityError("AUTH_JWT_SECRET must be configured")
    unsafe = {"change-me", "devmind", "secret", "admin", "password"}
    if signing_value.lower() in unsafe or signing_value.startswith("<") or len(signing_value) < 32:
        raise AuthSecurityError("AUTH_JWT_SECRET is missing or unsafe")
    return signing_value


def create_token(
    *,
    settings: Settings,
    subject: str,
    session_id: str,
    token_id: str,
    token_type: Literal["access", "refresh"],
    expires_delta: timedelta,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "iss": settings.auth_jwt_issuer,
        "aud": settings.auth_jwt_audience,
        "sub": subject,
        "sid": session_id,
        "jti": token_id,
        "typ": token_type,
        "iat": now,
        "nbf": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, ensure_signing_secret(settings), algorithm="HS256")


def decode_token(settings: Settings, token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            ensure_signing_secret(settings),
            algorithms=["HS256"],
            audience=settings.auth_jwt_audience,
            issuer=settings.auth_jwt_issuer,
        )
    except jwt.PyJWTError as exc:
        raise AuthSecurityError("Invalid token") from exc
    if payload.get("typ") != expected_type:
        raise AuthSecurityError("Invalid token type")
    return payload
