"""
Token refresh handler.

Handles POST /refresh requests to issue a new session token
using the current (possibly expired) session token's claims.
"""

import logging
from datetime import datetime, timedelta, timezone

from utils.responses import error_response, json_response

logger = logging.getLogger()


def _extract_cookie(headers: dict, name: str) -> str | None:
    """Extract a named cookie value from request headers."""
    cookie_header = headers.get("cookie", "") or headers.get("Cookie", "")
    if not cookie_header:
        return None
    for cookie in cookie_header.split(";"):
        cookie = cookie.strip()
        if "=" in cookie:
            cname, cvalue = cookie.split("=", 1)
            if cname.strip() == name:
                return cvalue.strip()
    return None


def handle_refresh(headers: dict) -> dict:
    """Handle POST /refresh.

    Reads the current session token (from Authorization header or cookies),
    extracts user claims (even if expired), and issues a brand new session
    token with a fresh expiry. No refresh token involved.

    Args:
        headers: Request headers from API Gateway.

    Returns:
        API Gateway response dict.

    Requirements: 3.1, 3.2, 3.3, 3.4
    """
    from auth.token_service import (
        generate_session_token,
        _decode_session_token_unverified,
        _get_session_lifetime_hours,
        hash_token,
    )
    from services import session_store

    # Read session token from Authorization header first, then cookies
    session_token = None
    auth_header = headers.get("authorization", "") or headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        session_token = auth_header[7:].strip()
    if not session_token:
        session_token = _extract_cookie(headers, "dsb_session") or _extract_cookie(
            headers, "dsb_token"
        )
    if not session_token:
        return error_response(401, "Authentication failed")

    try:
        # Decode without verifying expiry — the token may be expired
        claims = _decode_session_token_unverified(session_token)

        new_session_token = generate_session_token(
            user_id=claims["sub"],
            avatar_url=claims.get("avatar", ""),
            username=claims.get("name", ""),
            github_username=claims.get("github_login", ""),
            is_admin=claims.get("is_admin", False),
        )

        # Record the new session in DynamoDB
        now = datetime.now(timezone.utc)
        lifetime_hours = _get_session_lifetime_hours()
        expires_at = now + timedelta(hours=lifetime_hours)

        session_store.store_refresh_token(
            user_id=claims["sub"],
            token_hash=hash_token(new_session_token),
            created_at=int(now.timestamp()),
            expires_at=int(expires_at.timestamp()),
        )
    except Exception as exc:
        logger.warning("Token refresh failed: %s", exc)
        return error_response(401, "Authentication failed")

    response = json_response(
        200,
        {"session_token": new_session_token},
    )
    return response
