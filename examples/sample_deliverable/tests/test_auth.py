"""
Basic unit tests for JWT authentication.
"""

from src.auth_service import JWTService


def test_create_and_verify_token():
    """Verify that a created token can be decoded."""
    token = JWTService.create_access_token("test-user-1", "test@example.com")
    assert token is not None
    payload = JWTService.verify_token(token)
    assert payload is not None
    assert payload["sub"] == "test-user-1"
    assert payload["email"] == "test@example.com"


def test_invalid_token_returns_none():
    """Verify that malformed token returns None."""
    result = JWTService.verify_token("invalid.token.payload")
    assert result is None
