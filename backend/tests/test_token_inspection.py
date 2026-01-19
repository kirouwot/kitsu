import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest

os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db"
)

from app.config import settings  # noqa: E402
from app.security.token_inspection import (  # noqa: E402
    ExpiredTokenError,
    InvalidTokenError,
    validate_access_token,
    validate_refresh_token,
)
from app.utils.security import hash_refresh_token  # noqa: E402


def _make_access_token(payload: dict) -> str:
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def test_validate_access_token_success():
    now = datetime.now(timezone.utc)
    token = _make_access_token({"sub": "user-id", "exp": now + timedelta(minutes=5)})

    payload = validate_access_token(token)

    assert payload["sub"] == "user-id"


def test_validate_access_token_expired():
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    token = _make_access_token({"sub": "user-id", "exp": past})

    with pytest.raises(ExpiredTokenError):
        validate_access_token(token)


def test_validate_access_token_invalid():
    with pytest.raises(InvalidTokenError):
        validate_access_token("not-a-token")


def test_validate_access_token_missing_subject():
    now = datetime.now(timezone.utc)
    token = _make_access_token({"exp": now + timedelta(minutes=5)})

    with pytest.raises(InvalidTokenError):
        validate_access_token(token)


def test_validate_refresh_token_hashes_value():
    token = "refresh-token"
    token_hash = validate_refresh_token(token)
    assert token_hash == hash_refresh_token(token)


def test_validate_refresh_token_empty():
    with pytest.raises(InvalidTokenError):
        validate_refresh_token("")
