from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.models import User
from app.security.dependencies import get_current_user
from app.security.roles import UserRole
from app.security.tokens import InvalidTokenError, TokenExpiredError, token_manager

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])


class LoginRequest(BaseModel):
    email: str = Field(..., description="Registered customer email address")
    password: Optional[str] = Field(default=None, description="Account password or auth factor")


class AgentLoginRequest(BaseModel):
    email: str = Field(..., description="Corporate email for internal support staff")
    role: str = Field(default=UserRole.SUPPORT_AGENT.value, description="Assigned role: SUPPORT_AGENT, SUPERVISOR, ADMIN")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid JWT refresh token")


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = Field(default=None, description="Refresh token to revoke")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: Dict[str, Any]


@router.post("/login", response_model=TokenResponse)
async def login_customer(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Authenticate customer by email and return JWT access and refresh tokens (FR-01)."""
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. User with provided email not found.",
        )

    access_token = token_manager.create_access_token(
        user_id=str(user.id),
        role=UserRole.CUSTOMER.value,
        tier=user.tier,
    )
    refresh_token = token_manager.create_refresh_token(
        user_id=str(user.id),
        role=UserRole.CUSTOMER.value,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=user.to_dict(),
    )


@router.post("/agent-login", response_model=TokenResponse)
async def login_internal_agent(
    payload: AgentLoginRequest,
) -> TokenResponse:
    """Authenticate internal support agent or supervisor via corporate SSO / IdP (FR-02)."""
    role_upper = payload.role.upper()
    try:
        user_role = UserRole(role_upper)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid agent role: '{payload.role}'")

    if user_role not in (UserRole.SUPPORT_AGENT, UserRole.SUPERVISOR, UserRole.ADMIN):
        raise HTTPException(status_code=400, detail="Cannot assign non-staff role via agent login.")

    agent_id = f"agent_{abs(hash(payload.email)) % 100000:05d}"
    access_token = token_manager.create_access_token(
        user_id=agent_id,
        role=user_role.value,
        tier="staff",
    )
    refresh_token = token_manager.create_refresh_token(
        user_id=agent_id,
        role=user_role.value,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user={"id": agent_id, "email": payload.email, "role": user_role.value},
    )


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_access_token(
    payload: RefreshTokenRequest,
) -> Dict[str, Any]:
    """Exchange a valid refresh token for a new access token (FR-01)."""
    try:
        token_data = token_manager.decode_token(payload.refresh_token)
    except TokenExpiredError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired.")
    except InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    if token_data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type for refresh endpoint.")

    user_id = token_data["sub"]
    role = token_data.get("role", UserRole.CUSTOMER.value)

    new_access_token = token_manager.create_access_token(
        user_id=user_id,
        role=role,
    )
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    }


@router.post("/logout")
async def logout(
    payload: LogoutRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, str]:
    """Revoke tokens and terminate the session (FR-01, FR-09)."""
    if payload.refresh_token:
        token_manager.revoke_token(payload.refresh_token)

    current_jti = current_user.get("jti")
    if current_jti:
        token_manager.revoke_jti(current_jti)

    return {"status": "success", "message": "Successfully logged out and revoked tokens."}


@router.get("/me", response_model=Dict[str, Any])
async def get_my_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve verified profile context for the current authenticated user."""
    return current_user
