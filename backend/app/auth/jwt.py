"""JWT authentication for the FastAPI application.

Provides a unified JWT validation dependency that can be injected into any
route via FastAPI's `Depends()`. Combines the authentication logic from both
the dsb-platform-api Lambda (backend/auth/jwt_utils.py, token_service.py)
and the dsb-platform-membership Lambda (backend/membership/auth/auth_middleware.py).

Token extraction order:
1. Authorization: Bearer <token> header
2. dsb_session cookie
3. dsb_token cookie (legacy fallback)

The JWT secret is retrieved from AWS Secrets Manager and cached in-memory
to avoid repeated API calls on every request.

Requirements: 4.5
"""

import json
import logging
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError
from fastapi import Depends, HTTPException, Request
from jose import jwt, JWTError

from app.config import Settings
from app.dependencies import get_settings

logger = logging.getLogger(__name__)

# In-memory cache for the JWT secret
_jwt_secret_cache: dict[str, Any] = {
    "secret_key": None,
    "fetched_at": 0.0,
}

# Cache TTL in seconds (15 minutes). Unlike Lambda where the module cache
# relies on container lifecycle, ECS tasks are long-lived so we use a TTL.
_CACHE_TTL_SECONDS = 900


def _get_jwt_secret(settings: Settings) -> str:
    """Retrieve the JWT signing secret from AWS Secrets Manager with caching.

    The secret is cached for `_CACHE_TTL_SECONDS` to avoid hitting Secrets
    Manager on every request while still allowing secret rotation.

    Args:
        settings: Application settings containing jwt_secret_name.

    Returns:
        The secret_key string used for HS256 JWT verification.

    Raises:
        HTTPException(401): If the secret cannot be retrieved or is malformed.
    """
    now = time.time()

    # Return cached value if still fresh
    if (
        _jwt_secret_cache["secret_key"] is not None
        and (now - _jwt_secret_cache["fetched_at"]) < _CACHE_TTL_SECONDS
    ):
        return _jwt_secret_cache["secret_key"]

    secret_name = settings.jwt_secret_name
    if not secret_name:
        logger.error("jwt_secret_name is not configured")
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(response["SecretString"])
    except (ClientError, json.JSONDecodeError, KeyError) as exc:
        logger.error("Failed to retrieve JWT secret: %s", exc)
        raise HTTPException(status_code=401, detail="Unauthorized")

    secret_key = secret_data.get("secret_key")
    if not secret_key:
        logger.error("secret_key not found in JWT secret payload")
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Update cache
    _jwt_secret_cache["secret_key"] = secret_key
    _jwt_secret_cache["fetched_at"] = now

    return secret_key


def _extract_token(request: Request) -> str | None:
    """Extract JWT token from the request.

    Checks in order:
    1. Authorization: Bearer <token> header
    2. dsb_session cookie
    3. dsb_token cookie (legacy fallback)

    Args:
        request: The incoming FastAPI request.

    Returns:
        The token string, or None if no token is found.
    """
    # 1. Authorization header
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            return token

    # 2. dsb_session cookie (preferred)
    token = request.cookies.get("dsb_session")
    if token:
        return token

    # 3. dsb_token cookie (legacy)
    token = request.cookies.get("dsb_token")
    if token:
        return token

    return None


def _parse_admin_users(admin_users_str: str) -> list[tuple[str, str]]:
    """Parse the ADMIN_USERS config string into (provider, username) tuples.

    Format: comma-separated entries of "provider:username".
    Bare usernames (no colon) are treated as "github" for backward compatibility.

    Args:
        admin_users_str: Raw ADMIN_USERS environment variable value.

    Returns:
        List of (provider, username) tuples.
    """
    entries: list[tuple[str, str]] = []
    for entry in admin_users_str.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" in entry:
            provider, username = entry.split(":", 1)
            entries.append((provider.strip(), username.strip()))
        else:
            entries.append(("github", entry))
    return entries


async def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict:
    """FastAPI dependency that validates the JWT and returns the user payload.

    Extracts the JWT from the request (Authorization header or cookies),
    validates it against the cached secret from Secrets Manager, and returns
    the decoded payload with an `is_admin` flag.

    Usage:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            ...

    Args:
        request: The incoming FastAPI request.
        settings: Injected application settings.

    Returns:
        Decoded JWT payload dict with added `is_admin` field.

    Raises:
        HTTPException(401): If no token is present, or the token is
            invalid/expired/malformed.
    """
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    secret_key = _get_jwt_secret(settings)

    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Ensure the token has a subject claim
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Determine admin status based on provider and login
    provider = payload.get("provider", "github")
    provider_login: str | None = None
    if provider == "github":
        provider_login = payload.get("github_login")
    elif provider == "gitlab":
        provider_login = payload.get("gitlab_login")
    elif provider == "bitbucket":
        provider_login = payload.get("bitbucket_login")

    admin_entries = _parse_admin_users(settings.admin_users)
    is_admin = (provider, provider_login) in admin_entries if provider_login else False

    payload["is_admin"] = is_admin
    return payload


async def require_admin(
    user: dict = Depends(get_current_user),
) -> dict:
    """FastAPI dependency that requires the authenticated user to be an admin.

    Usage:
        @router.get("/admin-only")
        async def admin_route(user: dict = Depends(require_admin)):
            ...

    Args:
        user: The authenticated user payload from get_current_user.

    Returns:
        The user payload if the user is an admin.

    Raises:
        HTTPException(403): If the user is not an admin.
    """
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return user
