import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set
import jwt
from pydantic import BaseModel, Field

from app.core.config import settings
from app.security.roles import UserRole


class TokenPayload(BaseModel):
    sub: str = Field(..., description="Subject user ID")
    role: str = Field(default=UserRole.CUSTOMER.value)
    tier: str = Field(default="standard")
    type: str = Field(default="access")  # "access" or "refresh"
    jti: str = Field(default_factory=lambda: str(uuid.uuid4()))
    iat: int = Field(default_factory=lambda: int(datetime.now(timezone.utc).timestamp()))
    exp: int


class TokenError(Exception):
    """Base exception for token errors."""
    pass


class TokenExpiredError(TokenError):
    pass


class InvalidTokenError(TokenError):
    pass


class TokenManager:
    """Manages JWT generation, verification, and refresh token revocation."""

    def __init__(self, secret_key: Optional[str] = None, algorithm: Optional[str] = None):
        self.secret_key = secret_key or settings.JWT_SECRET_KEY
        self.algorithm = algorithm or settings.JWT_ALGORITHM
        self._revoked_jtis: Set[str] = set()

    def create_access_token(
        self,
        user_id: str,
        role: str = UserRole.CUSTOMER.value,
        tier: str = "standard",
        expires_delta: Optional[timedelta] = None,
        custom_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a short-lived signed JWT access token (15 mins default)."""
        now = datetime.now(timezone.utc)
        delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        exp = int((now + delta).timestamp())

        payload = {
            "sub": str(user_id),
            "role": role.upper(),
            "tier": tier,
            "type": "access",
            "jti": str(uuid.uuid4()),
            "iat": int(now.timestamp()),
            "exp": exp,
            **(custom_claims or {}),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        user_id: str,
        role: str = UserRole.CUSTOMER.value,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a signed JWT refresh token (7 days default)."""
        now = datetime.now(timezone.utc)
        delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        exp = int((now + delta).timestamp())

        payload = {
            "sub": str(user_id),
            "role": role.upper(),
            "type": "refresh",
            "jti": str(uuid.uuid4()),
            "iat": int(now.timestamp()),
            "exp": exp,
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate token signature, expiration, and revocation status."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"require": ["sub", "exp", "iat"]},
            )
        except jwt.ExpiredSignatureError as e:
            raise TokenExpiredError("Token has expired.") from e
        except jwt.PyJWTError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}") from e

        jti = payload.get("jti")
        if jti and jti in self._revoked_jtis:
            raise InvalidTokenError("Token has been revoked.")

        return payload

    def revoke_token(self, token: str) -> None:
        """Revoke a token by blacklisting its unique JTI."""
        try:
            payload = self.decode_token(token)
            jti = payload.get("jti")
            if jti:
                self._revoked_jtis.add(jti)
        except TokenExpiredError:
            pass  # Already expired, no harm

    def revoke_jti(self, jti: str) -> None:
        self._revoked_jtis.add(jti)


# Singleton instance
token_manager = TokenManager()
