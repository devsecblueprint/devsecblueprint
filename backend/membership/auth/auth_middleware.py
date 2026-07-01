"""
Authentication middleware for the membership Lambda.

Provides JWT extraction from cookies (dsb_session, dsb_token) and Authorization
Bearer header, validation using the JWT secret from AWS Secrets Manager, and
admin authorization checks.

Follows the pattern established in backend/auth/jwt_utils.py.

Validates: Requirements 10.5, 10.6, 18.7, 21.15, 21.16
"""

import os
import logging
from typing import Dict, Optional

from jose import jwt, JWTError

from services.secrets import get_secret
from utils.responses import error_response

logger = logging.getLogger(__name__)


def _extract_token(headers: Dict[str, str]) -> Optional[str]:
    """
    Extract JWT token from request headers.

    Checks in order:
    1. Authorization: Bearer <token> header
    2. dsb_session cookie
    3. dsb_token cookie (legacy fallback)

    Args:
        headers: Request headers (may have mixed case keys)

    Returns:
        str | None: Token string or None if not found
    """
    # Normalize header keys to lowercase for consistent lookup
    normalized = {k.lower(): v for k, v in headers.items()} if headers else {}

    # 1. Check Authorization header
    auth_header = normalized.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            return token

    # 2. Check cookies
    cookie_header = normalized.get("cookie", "")
    if not cookie_header:
        return None

    cookies = {}
    for cookie in cookie_header.split(";"):
        cookie = cookie.strip()
        if "=" in cookie:
            name, value = cookie.split("=", 1)
            cookies[name.strip()] = value.strip()

    # Prefer dsb_session, fall back to dsb_token
    if cookies.get("dsb_session"):
        return cookies["dsb_session"]
    if cookies.get("dsb_token"):
        return cookies["dsb_token"]

    return None


def _get_jwt_secret() -> str:
    """
    Retrieve the JWT signing secret from AWS Secrets Manager.

    Returns:
        str: The secret key for JWT verification

    Raises:
        Exception: If the secret cannot be retrieved or parsed
    """
    jwt_secret_name = os.environ.get("JWT_SECRET_NAME")
    if not jwt_secret_name:
        raise Exception("JWT_SECRET_NAME environment variable not set")

    secret_data = get_secret(jwt_secret_name)
    secret_key = secret_data.get("secret_key")
    if not secret_key:
        raise Exception("secret_key not found in JWT secret")

    return secret_key


def _parse_admin_users() -> list[tuple[str, str]]:
    """
    Parse the ADMIN_USERS environment variable into a list of (provider, username) tuples.

    Format: comma-separated "provider:username" pairs.
    Bare usernames (without provider) are treated as "github" for backward compatibility.

    Returns:
        list[tuple[str, str]]: List of (provider, username) tuples
    """
    admin_users_str = os.environ.get("ADMIN_USERS", "")
    entries = []
    for entry in admin_users_str.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" in entry:
            provider, username = entry.split(":", 1)
            entries.append((provider.strip(), username.strip()))
        else:
            # Backward compat: bare username treated as github
            entries.append(("github", entry.strip()))
    return entries


def authenticate(event: Dict) -> Optional[Dict]:
    """
    Authenticate a request by extracting and validating the JWT.

    Extracts the JWT from cookies or Authorization header, validates it
    against the JWT secret from Secrets Manager, and returns the decoded
    payload with an `is_admin` flag added.

    Args:
        event: API Gateway HTTP API event dict

    Returns:
        dict | None: Decoded JWT payload with added `is_admin` field,
                     or None if authentication fails

    Payload fields:
        - sub: User ID
        - is_admin: Whether the user is in the admin list
        - (other JWT claims as encoded)
    """
    headers = event.get("headers", {})
    if not headers:
        return None

    token = _extract_token(headers)
    if not token:
        return None

    try:
        secret_key = _get_jwt_secret()
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except JWTError as e:
        logger.info("JWT validation failed: %s", type(e).__name__)
        return None
    except Exception as e:
        logger.error("JWT secret retrieval failed: %s", str(e))
        return None

    # Determine admin status
    user_id = payload.get("sub")
    if not user_id:
        return None

    provider = payload.get("provider", "github")
    provider_login = None
    if provider == "github":
        provider_login = payload.get("github_login")
    elif provider == "gitlab":
        provider_login = payload.get("gitlab_login")
    elif provider == "bitbucket":
        provider_login = payload.get("bitbucket_login")

    admin_entries = _parse_admin_users()
    is_admin = (provider, provider_login) in admin_entries if provider_login else False

    payload["is_admin"] = is_admin
    return payload


def require_auth(event: Dict) -> tuple[Optional[Dict], Optional[Dict]]:
    """
    Require authentication for a request.

    Returns the user payload if authenticated, or a 401 error response if not.

    Args:
        event: API Gateway HTTP API event dict

    Returns:
        tuple: (user_payload, None) if authenticated,
               (None, error_response) if not authenticated

    Usage:
        user, err = require_auth(event)
        if err:
            return err
        # user is authenticated, proceed
    """
    user = authenticate(event)
    if not user:
        return None, error_response(401, "Authentication required")
    return user, None


def require_admin(event: Dict) -> tuple[Optional[Dict], Optional[Dict]]:
    """
    Require admin authentication for a request.

    Returns the user payload if authenticated and admin, or an appropriate
    error response (401 if not authenticated, 403 if not admin).

    Args:
        event: API Gateway HTTP API event dict

    Returns:
        tuple: (user_payload, None) if admin,
               (None, error_response) if not authenticated or not admin

    Usage:
        user, err = require_admin(event)
        if err:
            return err
        # user is an authenticated admin, proceed
    """
    user, err = require_auth(event)
    if err:
        return None, err

    if not user.get("is_admin"):
        return None, error_response(403, "Admin access required")

    return user, None
