"""
Authentication and Identity Verification Foundation
"""

from typing import Dict, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from plagiarism.core.config import get_settings
from plagiarism.core.errors import ForbiddenError, UnauthorizedError
from plagiarism.core.security import (
    UserPrincipal,
    create_access_token,
    get_current_user,
    require_role
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class TestTokenRequest(BaseModel):
    user_id: str = "00000000-0000-0000-0000-000000000001"
    email: str = "test.user@plagiarism.internal"
    role: str = "STUDENT"
    expires_minutes: Optional[int] = 60


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


@router.post(
    "/test-token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Test JWT Token (Development/Test Only)",
    include_in_schema=False
)
async def generate_test_token(req: TestTokenRequest) -> TokenResponse:
    """
    Creates a valid test JWT token for local testing and CI assertions.
    Blocked in production environments.
    """
    settings = get_settings()
    if settings.is_production:
        raise ForbiddenError("Test token generation is permanently blocked in production environments")

    payload = {
        "sub": req.user_id,
        "user_id": req.user_id,
        "email": req.email,
        "role": req.role
    }
    token = create_access_token(payload)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=(req.expires_minutes or 60) * 60
    )


@router.get(
    "/me",
    response_model=UserPrincipal,
    status_code=status.HTTP_200_OK,
    summary="Inspect Current Authenticated User Principal"
)
async def get_current_user_profile(
    current_user: UserPrincipal = Depends(get_current_user)
) -> UserPrincipal:
    """
    Verifies that the caller's JWT bearer token is valid and active,
    returning the decoded UserPrincipal identity.
    """
    return current_user


@router.get(
    "/admin-probe",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="RBAC Probe Endpoint (Admin Only)"
)
async def admin_role_probe(
    admin_user: UserPrincipal = Depends(require_role(["ADMIN"]))
) -> Dict[str, str]:
    """
    Demonstrates RBAC enforcement: accessible only to users with ADMIN role.
    """
    return {"status": "authorized", "user_id": admin_user.user_id, "role": admin_user.role}
