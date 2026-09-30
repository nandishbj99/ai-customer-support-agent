from datetime import timedelta
import pytest
from app.security.roles import UserRole
from app.security.tokens import (
    InvalidTokenError,
    TokenExpiredError,
    TokenManager,
)


def test_create_and_decode_access_token():
    tm = TokenManager(secret_key="test_secret_key_32_characters_long_12345", algorithm="HS256")
    token = tm.create_access_token(
        user_id="user_123",
        role=UserRole.CUSTOMER.value,
        tier="premium",
    )
    payload = tm.decode_token(token)
    assert payload["sub"] == "user_123"
    assert payload["role"] == "CUSTOMER"
    assert payload["tier"] == "premium"
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "jti" in payload


def test_token_expiration_raises_error():
    tm = TokenManager(secret_key="test_secret_key_32_characters_long_12345", algorithm="HS256")
    # Token expired 10 seconds ago
    expired_token = tm.create_access_token(
        user_id="user_expired",
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(TokenExpiredError):
        tm.decode_token(expired_token)


def test_signature_tampering_raises_error():
    tm1 = TokenManager(secret_key="correct_key_32_characters_long_abcdef", algorithm="HS256")
    tm2 = TokenManager(secret_key="wrong_key_32_characters_long_ghijklmn", algorithm="HS256")

    token = tm1.create_access_token(user_id="user_tamper")
    # Attempt decoding with wrong key
    with pytest.raises(InvalidTokenError):
        tm2.decode_token(token)


def test_refresh_token_revocation():
    tm = TokenManager(secret_key="test_secret_key_32_characters_long_12345", algorithm="HS256")
    refresh_token = tm.create_refresh_token(user_id="user_refresh")

    # Initial decode succeeds
    payload = tm.decode_token(refresh_token)
    assert payload["sub"] == "user_refresh"
    assert payload["type"] == "refresh"

    # Revoke token
    tm.revoke_token(refresh_token)

    # Next decode fails with InvalidTokenError
    with pytest.raises(InvalidTokenError, match="revoked"):
        tm.decode_token(refresh_token)
