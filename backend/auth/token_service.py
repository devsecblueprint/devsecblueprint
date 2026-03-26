"""
Token service for session token management.

This module provides functions to generate, validate, and hash session tokens
and refresh tokens. Session tokens are HS256 JWTs with configurable 4-8 hour
lifetimes. Refresh tokens are cryptographically random opaque strings.

Integrates with AWS Secrets Manager for JWT secret retrieval.
"""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple

from jose import jwt, JWTError

from services.secrets import get_secret
from services import session_store

logger = logging.getLogger()

# Default session token lifetime in hours
_DEFAULT_LIFETIME_HOURS = 6

# Minimum refresh token byte length
_REFRESH_TOKEN_BYTES = 32


def _get_jwt_secret() -> str:
    """Retrieve the JWT signing secret from AWS Secrets Manager.

    Returns:
        The secret key string.

    Raises:
        Exception: If JWT_SECRET_NAME env var is missing or secret_key not found.
    """
    jwt_secret_name = os.environ.get("JWT_SECRET_NAME")
    if not jwt_secret_name:
        raise Exception("JWT_SECRET_NAME environment variable not set")

    secret_data = get_secret(jwt_secret_name)
    secret_key = secret_data.get("secret_key")
    if not secret_key:
        raise Exception("secret_key not found in JWT secret")
    return secret_key


def _get_session_lifetime_hours() -> float:
    """Read SESSION_TOKEN_LIFETIME_HOURS env var.

    Accepts decimal values (e.g. ``0.25`` for 15 minutes).
    No clamping — any positive value is accepted.

    Returns:
        Lifetime in hours (float), default 6.
    """
    raw = os.environ.get("SESSION_TOKEN_LIFETIME_HOURS", str(_DEFAULT_LIFETIME_HOURS))
    try:
        value = float(raw)
    except (ValueError, TypeError):
        logger.warning(
            "Invalid SESSION_TOKEN_LIFETIME_HOURS '%s', using default %d",
            raw,
            _DEFAULT_LIFETIME_HOURS,
        )
        value = float(_DEFAULT_LIFETIME_HOURS)
    if value <= 0:
        logger.warning(
            "SESSION_TOKEN_LIFETIME_HOURS must be positive, using default %d",
            _DEFAULT_LIFETIME_HOURS,
        )
        value = float(_DEFAULT_LIFETIME_HOURS)
    return value


def generate_session_token(
    user_id: str,
    avatar_url: str,
    username: str,
    github_username: str = "",
    is_admin: bool = False,
    provider: str = "github",
    gitlab_username: str = "",
) -> str:
    """Generate a signed HS256 JWT session token.

    Args:
        user_id: User ID (becomes ``sub`` claim).
        avatar_url: Avatar URL.
        username: Display name.
        github_username: GitHub login username (used when provider is "github").
        is_admin: Whether the user has admin privileges.
        provider: Authentication provider ("github" or "gitlab").
        gitlab_username: GitLab login username (used when provider is "gitlab").

    Returns:
        Encoded JWT string.

    The token includes ``sub``, ``avatar``, ``name``, ``provider``,
    ``is_admin``, ``iat``, ``exp``, and a provider-specific login claim
    (``github_login`` or ``gitlab_login``).  Lifetime is controlled by
    the ``SESSION_TOKEN_LIFETIME_HOURS`` env var (default 6).

    Requirements: 4.1, 4.2, 4.3, 4.5
    """
    secret_key = _get_jwt_secret()
    lifetime_hours = _get_session_lifetime_hours()

    now = datetime.now(timezone.utc)
    expiration = now + timedelta(hours=lifetime_hours)

    payload = {
        "sub": user_id,
        "avatar": avatar_url,
        "name": username,
        "provider": provider,
        "is_admin": is_admin,
        "iat": now,
        "exp": expiration,
    }

    if provider == "gitlab":
        payload["gitlab_login"] = gitlab_username
    else:
        payload["github_login"] = github_username

    return jwt.encode(payload, secret_key, algorithm="HS256")


def generate_refresh_token() -> str:
    """Generate a cryptographically random refresh token.

    Returns:
        Hex-encoded string of at least 64 characters (32 bytes).

    Requirements: 2.1
    """
    return secrets.token_hex(_REFRESH_TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest of *token*.

    Requirements: 9.1
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def validate_session_token(token: str) -> dict:
    """Decode and validate a session token JWT.

    Args:
        token: Encoded JWT string.

    Returns:
        Decoded payload dictionary.

    Raises:
        jose.JWTError: If the token is expired, malformed, or tampered with.

    Requirements: 4.2, 4.3, 4.4
    """
    secret_key = _get_jwt_secret()
    return jwt.decode(token, secret_key, algorithms=["HS256"])


def _decode_session_token_unverified(token: str) -> dict:
    """Decode a session token without verifying expiration.

    Used during token refresh to extract user claims from an expired
    session token. Signature is still verified.

    Args:
        token: Encoded JWT string (may be expired).

    Returns:
        Decoded payload dictionary.

    Raises:
        jose.JWTError: If the token is malformed or tampered with.
    """
    secret_key = _get_jwt_secret()
    return jwt.decode(
        token, secret_key, algorithms=["HS256"], options={"verify_exp": False}
    )


def refresh_tokens(
    refresh_token_raw: str, expired_session_token: str
) -> Tuple[str, str]:
    """Validate a refresh token and issue a new session + refresh token pair.

    Implements single-use refresh tokens with reuse detection:
    1. Decode the expired session token (skip exp check) to get user claims.
    2. Hash the incoming refresh token and look it up in the session store.
    3. If not found, the token was already consumed — assume reuse, revoke
       all sessions for the user, and raise.
    4. If found but expired, clean up and raise.
    5. Delete the old refresh token record (single-use enforcement).
    6. Generate a new session token and refresh token.
    7. Store the new hashed refresh token with matching expiry.
    8. Return the new pair.

    Args:
        refresh_token_raw: The raw (unhashed) refresh token string.
        expired_session_token: The current session JWT (may be expired)
            used to extract user identity claims.

    Returns:
        Tuple of (new_session_token, new_refresh_token).

    Raises:
        ValueError: If the refresh token is invalid, expired, or reused.
        jose.JWTError: If the session token is malformed/tampered.

    Requirements: 3.2, 3.5, 9.2, 9.5
    """
    # Extract user claims from the (possibly expired) session token
    claims = _decode_session_token_unverified(expired_session_token)
    user_id = claims["sub"]

    # Look up the hashed refresh token in the session store
    token_hash = hash_token(refresh_token_raw)
    record = session_store.get_refresh_token(user_id, token_hash)

    if record is None:
        # Token not found — previously invalidated, possible reuse attack.
        # Revoke all sessions for this user as a precaution (Req 9.5).
        logger.warning("Refresh token reuse detected for user %s", user_id)
        session_store.delete_all_user_sessions(user_id)
        raise ValueError("Invalid refresh token")

    # Check expiry
    expires_at_epoch = record["expires_at"]
    now = datetime.now(timezone.utc)
    if now.timestamp() >= expires_at_epoch:
        session_store.delete_refresh_token(user_id, token_hash)
        raise ValueError("Refresh token expired")

    # Delete old refresh token — single-use enforcement (Req 9.2)
    session_store.delete_refresh_token(user_id, token_hash)

    # Generate new token pair (provider-aware)
    provider = claims.get("provider", "github")
    new_session_token = generate_session_token(
        user_id=user_id,
        avatar_url=claims.get("avatar", ""),
        username=claims.get("name", ""),
        github_username=claims.get("github_login", ""),
        is_admin=claims.get("is_admin", False),
        provider=provider,
        gitlab_username=claims.get("gitlab_login", ""),
    )
    new_refresh_token = generate_refresh_token()

    # Store new refresh token with expiry >= session token expiry
    new_refresh_hash = hash_token(new_refresh_token)
    lifetime_hours = _get_session_lifetime_hours()
    refresh_expires_at = now + timedelta(hours=lifetime_hours)

    session_store.store_refresh_token(
        user_id=user_id,
        token_hash=new_refresh_hash,
        created_at=int(now.timestamp()),
        expires_at=int(refresh_expires_at.timestamp()),
    )

    return new_session_token, new_refresh_token


def revoke_user_sessions(user_id: str) -> None:
    """Delete all refresh token records for a user.

    Args:
        user_id: GitHub user ID whose sessions should be revoked.

    Requirements: 3.5, 7.1
    """
    session_store.delete_all_user_sessions(user_id)
