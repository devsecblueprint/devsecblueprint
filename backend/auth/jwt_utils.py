"""
JWT utilities for session management.

This module provides functions to generate and validate JWT tokens for user sessions,
using HS256 algorithm with 1-hour expiration. Integrates with AWS Secrets Manager
for secure JWT secret retrieval.
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from jose import jwt, JWTError
from services.secrets import get_secret
from auth.token_service import validate_session_token
from utils.responses import json_response, error_response

logger = logging.getLogger()


def generate_jwt(
    user_id: str,
    avatar_url: Optional[str] = None,
    username: Optional[str] = None,
    github_username: Optional[str] = None,
) -> str:
    """
    Generate JWT token for user session.

    Args:
        user_id: GitHub user ID
        avatar_url: GitHub avatar URL (optional)
        username: GitHub username or display name (optional)
        github_username: GitHub login username (optional)

    Returns:
        str: Signed JWT token

    Token Structure:
        - Algorithm: HS256
        - Expiration: 1 hour
        - Payload: {"sub": user_id, "avatar": avatar_url, "name": username, "github_login": github_username, "exp": timestamp}

    Environment Variables:
        - JWT_SECRET_NAME: Secrets Manager secret name

    Validates: Requirements 11.1, 11.2, 11.3
    """
    # Get JWT secret from Secrets Manager
    jwt_secret_name = os.environ.get("JWT_SECRET_NAME")
    if not jwt_secret_name:
        raise Exception("JWT_SECRET_NAME environment variable not set")

    secret_data = get_secret(jwt_secret_name)
    secret_key = secret_data.get("secret_key")
    if not secret_key:
        raise Exception("secret_key not found in JWT secret")

    # Create payload with 1-hour expiration
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {"sub": user_id, "exp": expiration}

    # Add avatar URL if provided
    if avatar_url:
        payload["avatar"] = avatar_url

    # Add username if provided
    if username:
        payload["name"] = username

    # Add GitHub login username if provided
    if github_username:
        payload["github_login"] = github_username

    # Generate and sign JWT
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token


def validate_jwt(token: str) -> Dict[str, str]:
    """
    Validate JWT token and extract payload.

    Args:
        token: JWT token string

    Returns:
        dict: Token payload with user_id

    Raises:
        jose.exceptions.JWTError: If token is invalid or expired

    Environment Variables:
        - JWT_SECRET_NAME: Secrets Manager secret name

    Validates: Requirements 11.4, 11.5, 11.6
    """
    # Get JWT secret from Secrets Manager
    jwt_secret_name = os.environ.get("JWT_SECRET_NAME")
    if not jwt_secret_name:
        raise Exception("JWT_SECRET_NAME environment variable not set")

    secret_data = get_secret(jwt_secret_name)
    secret_key = secret_data.get("secret_key")
    if not secret_key:
        raise Exception("secret_key not found in JWT secret")

    # Decode and validate JWT
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except JWTError as e:
        raise e


def extract_token_from_cookie(headers: Dict[str, str]) -> Optional[str]:
    """
    Extract session token from cookie header.

    Checks ``dsb_session`` first (new token system), then falls back to
    ``dsb_token`` (legacy) for backward compatibility.

    Args:
        headers: Request headers (may have mixed case keys)

    Returns:
        str | None: Token string or None if not found

    Validates: Requirements 4.1, 8.1
    """
    token, _ = _extract_token_and_source(headers)
    return token


def _extract_token_and_source(headers: Dict[str, str]) -> tuple:
    """Extract session token and its source from headers.

    Checks in order:
    1. ``Authorization: Bearer <token>`` header
    2. ``dsb_session`` cookie
    3. ``dsb_token`` cookie (legacy)

    Returns:
        Tuple of (token_string | None, source_name | None).
        ``source_name`` is ``"bearer"``, ``"dsb_session"``, or ``"dsb_token"``.
    """
    # 1. Check Authorization header first
    auth_header = headers.get("authorization", "") or headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            return token, "bearer"

    # 2. Check cookies
    cookie_header = headers.get("cookie", "") or headers.get("Cookie", "")

    if not cookie_header:
        return None, None

    cookies = {}
    for cookie in cookie_header.split(";"):
        cookie = cookie.strip()
        if "=" in cookie:
            name, value = cookie.split("=", 1)
            cookies[name.strip()] = value.strip()

    if cookies.get("dsb_session"):
        return cookies["dsb_session"], "dsb_session"
    if cookies.get("dsb_token"):
        return cookies["dsb_token"], "dsb_token"
    return None, None


def verify_user(headers: Dict[str, str]) -> Dict[str, any]:
    """
    Verify user authentication and return user information.

    This is the handler for the GET /me endpoint. It extracts the JWT from cookies,
    validates it, and returns the user information.

    When a legacy ``dsb_token`` cookie is detected (and ``dsb_session`` is absent),
    the response includes ``Set-Cookie`` headers that migrate the user to the new
    ``dsb_session`` + ``dsb_refresh`` token pair and delete the legacy cookie.

    Args:
        headers: Request headers (lowercase keys) from API Gateway event

    Returns:
        dict: API Gateway response with user_id and authenticated status

    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 8.1, 8.3
    """
    try:
        cookie_header = headers.get("cookie", "")
        logger.info(
            f"Cookie header: {cookie_header[:100] if cookie_header else 'NONE'}"
        )

        token, source = _extract_token_and_source(headers)

        logger.info(f"Extracted token: {'YES' if token else 'NO'} (source={source})")

        if not token:
            return error_response(401, "Authentication failed")

        # Track whether we used legacy validation so we can migrate
        is_legacy = False

        # Validate JWT and extract payload
        try:
            payload = validate_session_token(token)
        except Exception as e:
            logger.info(
                "Session token validation failed, trying legacy: %s", type(e).__name__
            )
            try:
                payload = validate_jwt(token)
                is_legacy = True
            except Exception as e2:
                logger.error("Legacy JWT validation also failed: %s", type(e2).__name__)
                return error_response(401, "Authentication failed")

        # If the token came from dsb_token cookie, mark as legacy
        if source == "dsb_token":
            is_legacy = True

        user_id = payload.get("sub")
        if not user_id:
            return error_response(401, "Authentication failed")

        avatar_url = payload.get("avatar")
        logger.info(f"Avatar URL from JWT: {avatar_url[:50] if avatar_url else 'NONE'}")

        username = payload.get("name")
        logger.info(f"Username from JWT: {username if username else 'NONE'}")

        github_username = payload.get("github_login")
        logger.info(
            f"GitHub username from JWT: {github_username if github_username else 'NONE'}"
        )

        admin_users_str = os.environ.get("ADMIN_USERS", "")
        admin_users = [u.strip() for u in admin_users_str.split(",") if u.strip()]
        is_admin = github_username in admin_users if github_username else False
        logger.info(f"User is admin: {is_admin}")

        response_data = {
            "user_id": user_id,
            "authenticated": True,
            "is_admin": is_admin,
        }
        if avatar_url:
            response_data["avatar_url"] = avatar_url
        if username:
            response_data["username"] = username
        if github_username:
            response_data["github_username"] = github_username

        logger.info(
            f"Response includes avatar: {'avatar_url' in response_data}, "
            f"username: {'username' in response_data}, "
            f"github_username: {'github_username' in response_data}, "
            f"is_admin: {is_admin}"
        )

        response = json_response(200, response_data)

        # --- Legacy token migration (Requirements 8.1, 8.3) ---
        if is_legacy:
            response = _attach_migration_cookies(response, payload, user_id)

        return response

    except Exception:
        return error_response(401, "Authentication failed")


def _attach_migration_cookies(
    response: Dict[str, any], legacy_payload: dict, user_id: str
) -> Dict[str, any]:
    """Issue new session + refresh tokens and attach migration cookies to *response*.

    Called when a request was authenticated via the legacy ``dsb_token`` cookie.
    Generates a new ``dsb_session`` / ``dsb_refresh`` pair, stores the hashed
    refresh token in DynamoDB, and adds ``Set-Cookie`` headers that:
    - set ``dsb_session`` (the new session JWT)
    - set ``dsb_refresh`` (HttpOnly, scoped to ``/refresh``)
    - delete the legacy ``dsb_token`` cookie

    Args:
        response: The existing API Gateway response dict to augment.
        legacy_payload: Decoded claims from the legacy JWT.
        user_id: The authenticated user's ID.

    Returns:
        The augmented response dict with ``multiValueHeaders.Set-Cookie``.

    Requirements: 8.1, 8.3
    """
    from auth.token_service import (
        generate_session_token,
        generate_refresh_token,
        hash_token,
        _get_session_lifetime_hours,
    )
    from services import session_store as _session_store
    from utils.responses import create_cookie, delete_cookie, get_cookie_domain

    try:
        admin_users_str = os.environ.get("ADMIN_USERS", "")
        admin_users = [u.strip() for u in admin_users_str.split(",") if u.strip()]
        github_username = legacy_payload.get("github_login", "")
        is_admin = github_username in admin_users if github_username else False

        session_token = generate_session_token(
            user_id=user_id,
            avatar_url=legacy_payload.get("avatar", ""),
            username=legacy_payload.get("name", ""),
            github_username=github_username,
            is_admin=is_admin,
        )
        raw_refresh = generate_refresh_token()

        lifetime_hours = _get_session_lifetime_hours()
        now = datetime.now(timezone.utc)
        refresh_expires = now + timedelta(hours=lifetime_hours)

        _session_store.store_refresh_token(
            user_id=user_id,
            token_hash=hash_token(raw_refresh),
            created_at=now.isoformat(),
            expires_at=refresh_expires.isoformat(),
        )

        session_cookie = create_cookie(
            name="dsb_session",
            value=session_token,
            max_age=int(lifetime_hours * 3600),
            secure=True,
            http_only=False,
            same_site="None",
            path="/",
        )
        refresh_cookie = create_cookie(
            name="dsb_refresh",
            value=raw_refresh,
            max_age=int(lifetime_hours * 3600),
            secure=True,
            http_only=True,
            same_site="None",
            path="/refresh",
        )
        legacy_delete = delete_cookie("dsb_token", domain=get_cookie_domain(), path="/")

        response.setdefault("multiValueHeaders", {})
        response["multiValueHeaders"]["Set-Cookie"] = [
            session_cookie,
            refresh_cookie,
            legacy_delete,
        ]

        logger.info("Legacy token migrated for user %s", user_id)
    except Exception as exc:
        # Migration is best-effort; don't break the authenticated response
        logger.warning("Legacy token migration failed: %s", exc)

    return response
