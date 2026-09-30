from typing import Any, Dict, List, Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.models import User
from app.security.roles import UserRole, has_role
from app.security.tokens import InvalidTokenError, TokenExpiredError, token_manager

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    """Extract and validate the JWT Bearer token from the Authorization header."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = token_manager.decode_token(token)
        return payload
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token_payload: Dict[str, Any] = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve verified user context from the database or token claims."""
    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject claim.")

    return {
        "user_id": user_id,
        "role": token_payload.get("role", UserRole.CUSTOMER.value),
        "tier": token_payload.get("tier", "standard"),
        "jti": token_payload.get("jti"),
    }


def requires_role(allowed_roles: List[UserRole]):
    """FastAPI dependency factory enforcing strict Role-Based Access Control (RBAC)."""
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role", "")
        if not has_role(user_role, allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: User role '{user_role}' lacks required permissions ({[r.value for r in allowed_roles]}).",
            )
        return current_user

    return role_checker


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> str:
    """Validate internal service API key."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header for service authentication.",
        )

    valid_keys = [k.strip() for k in settings.INTERNAL_API_KEYS.split(",") if k.strip()]
    if x_api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or unauthorized API key.",
        )

    return x_api_key
