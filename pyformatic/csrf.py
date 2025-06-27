"""Helpers for CSRF token management."""

from __future__ import annotations

from hmac import compare_digest
from secrets import token_urlsafe
from typing import Mapping, MutableMapping

_TOKEN_KEY = "_pyformatic_csrf_token"


def ensure_csrf_token(session: MutableMapping[str, str]) -> str:
    """Return existing token in ``session`` or create a new one."""
    token = session.get(_TOKEN_KEY)
    if not token:
        token = token_urlsafe(32)
        session[_TOKEN_KEY] = token
    return token


def validate_csrf_token(session: Mapping[str, str], token: str) -> bool:
    """Return True if ``token`` matches the value stored in ``session``."""
    expected = session.get(_TOKEN_KEY)
    if not expected:
        return False
    return compare_digest(str(expected), str(token))
