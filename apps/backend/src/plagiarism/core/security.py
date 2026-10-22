"""
Security Foundations: JWT Verification, Password Hashing, and RBAC Dependencies
"""

import hmac
import hashlib
import json
import base64
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from jose import jwt, JWTError, ExpiredSignatureError

from plagiarism.core.config import get_settings
from plagiarism.core.errors import ForbiddenError, UnauthorizedError

security_scheme = HTTPBearer(auto_error=False)


class UserPrincipal(BaseModel):
    """Authenticated user context available in request dependency injection."""
    user_id: str
    email: str
    role: str = "STUDENT"
    institution_id: Optional[str] = None


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Creates a signed JWT access token using HMAC-SHA256."""
    settings = get_settings()
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": int(expire.timestamp()), "iat": int(now.timestamp())})
    
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and verifies a JWT token.
    Enforces algorithm pinning and expiration check.
    """
    settings = get_settings()
    try:
        # Enforce pinned algorithm list
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except ExpiredSignatureError:
        raise UnauthorizedError("Token has expired")
    except JWTError as e:
        raise UnauthorizedError(f"Invalid token signature: {str(e)}")
    except Exception as e:
        raise UnauthorizedError(f"Invalid access token: {str(e)}")


def decode_token(token: str) -> UserPrincipal:
    """Decodes a JWT token and returns a validated UserPrincipal instance."""
    payload = decode_access_token(token)
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise UnauthorizedError("Token payload missing subject identifier")
    return UserPrincipal(
        user_id=str(user_id),
        email=str(payload.get("email") or ""),
        role=str(payload.get("role", "STUDENT")),
        institution_id=payload.get("institution_id")
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> UserPrincipal:
    """
    Dependency that enforces authentication.
    Returns UserPrincipal or raises HTTP 401 UnauthorizedError.
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Bearer authentication credentials required")
    
    return decode_token(credentials.credentials)


async def get_current_user_or_dev(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> UserPrincipal:
    """
    Returns authenticated UserPrincipal if bearer token provided,
    or falls back to development principal when running in local development mode.
    """
    if credentials and credentials.scheme.lower() == "bearer":
        return decode_token(credentials.credentials)
    settings = get_settings()
    if settings.APP_RUNTIME_MODE == "local" or not settings.is_production:
        return UserPrincipal(
            user_id="00000000-0000-0000-0000-000000000001",
            email="researcher@plagiarism.local",
            role="RESEARCHER"
        )
    raise UnauthorizedError("Bearer authentication credentials required")


def require_role(allowed_roles: List[str]) -> Callable:
    """
    Dependency factory enforcing role-based access control (RBAC).
    """
    async def role_checker(current_user: UserPrincipal = Depends(get_current_user)) -> UserPrincipal:
        if current_user.role not in allowed_roles:
            raise ForbiddenError(f"Operation requires one of roles: {', '.join(allowed_roles)}")
        return current_user
    return role_checker
