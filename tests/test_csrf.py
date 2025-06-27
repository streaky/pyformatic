"""Tests for CSRF token helpers."""

import pyformatic


def test_ensure_and_validate_token():
    """Valid token roundtrip succeeds."""
    session = {}
    token = pyformatic.ensure_csrf_token(session)
    assert pyformatic.validate_csrf_token(session, token)


def test_invalid_token_fails():
    """Validation fails with a mismatched token."""
    session = {}
    pyformatic.ensure_csrf_token(session)
    assert not pyformatic.validate_csrf_token(session, "bad")
