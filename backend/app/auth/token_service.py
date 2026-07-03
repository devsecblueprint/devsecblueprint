"""Token service for session and refresh token management.

Self-contained module for generating, validating, and hashing tokens.
Uses app.services.secrets for JWT secret retrieval from AWS Secrets Manager.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

from app.services.secrets import get_secret

logger = logging.getLogger(__name__)

# Default session token lifetime in hours
_DEFAULT_LIFETIME_HOURS = 6

# Refresh token byte length (produces 64 hex chars)
_REFRESH_TOKEN_BYTES = 32


def _get_jwt_secret(jwt_secret_name: str) -> str:
    """Retrieve the JWT signing secret from AWS Secrets Manager.

    Args:
        jwt_secret_name: Name of the secret in Secrets Manager.

    Returns:
        The secret_key string.

    Raises:
        Exception: If jwt_secret_name is empty or secret_key not found.
    """
    if not jwt_secret_name:
        raise Exception("JWT secret name not configured")

    secret_data = get_secret(jwt_secret_name)
    secret_key = secret_data.get("secret_key")
    if not secret_key:
        raise Exception("secret_key not found in JWT secret")
    return secret_key


def get_session_lifetime_hours(
    lifetime_setting: int | float = _DEFAULT_LIFETIME_HOURS,
) -> float:
    """Determine session token lifetime in hours.

    Args:
        lifetime_setting: Value from Settings.session_token_lifetime_hours.

    Returns:
        Lifetime in hours (float). Falls back to default if invalid.
    """
    try:
        value = float(lifetime_setting)
    except (ValueError, TypeError):
        value = float(_DEFAULT_LIFETIME_HOURS)
    if value <= 0:
        value = float(_DEFAULT_LIFETIME_HOURS)
    return value


def generate_session_token(
    jwt_secret_name: str,
    user_id: str,
    avatar_url: str,
    username: str,
    is_admin: bool = False,
    provider: str = "github",
    github_username: str = "",
    gitlab_username: str = "",
    bitbucket_username: str = "",
    lifetime_hours: float = _DEFAULT_LIFETIME_HOURS,
) -> str:
    """Generate a signed HS256 JWT session token.

    Args:
        jwt_secret_name: Secrets Manager secret name for the JWT key.
        user_id: User ID (becomes ``sub`` claim).
        avatar_url: Avatar URL.
        username: Display name.
        is_admin: Whether the user has admin privileges.
        provider: Authentication provider.
        github_username: GitHub login username.
        gitlab_username: GitLab login username.
        bitbucket_username: Bitbucket login username.
        lifetime_hours: Token lifetime in hours.

    Returns:
        Encoded JWT string.
    """
    secret_key = _get_jwt_secret(jwt_secret_name)

    now = datetime.now(timezone.utc)
    expiration = now + timedelta(hours=lifetime_hours)

    payload: dict = {
        "sub": user_id,
        "avatar": avatar_url,
        "name": username,
        "provider": provider,
        "is_admin": is_admin,
        "iat": now,
        "exp": expiration,
    }

    if provider == "bitbucket":
        payload["bitbucket_login"] = bitbucket_username
    elif provider == "gitlab":
        payload["gitlab_login"] = gitlab_username
    else:
        payload["github_login"] = github_username

    return jwt.encode(payload, secret_key, algorithm="HS256")


def generate_refresh_token() -> str:
    """Generate a cryptographically random refresh token.

    Returns:
        Hex-encoded string of 64 characters (32 bytes).
    """
    return secrets.token_hex(_REFRESH_TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest of a token string."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def validate_session_token(token: str, jwt_secret_name: str) -> dict:
    """Decode and validate a session token JWT.

    Args:
        token: Encoded JWT string.
        jwt_secret_name: Secrets Manager secret name for the JWT key.

    Returns:
        Decoded payload dictionary.

    Raises:
        jose.JWTError: If the token is expired, malformed, or tampered with.
    """
    secret_key = _get_jwt_secret(jwt_secret_name)
    return jwt.decode(token, secret_key, algorithms=["HS256"])


def decode_session_token_unverified(token: str, jwt_secret_name: str) -> dict:
    """Decode a session token without verifying expiration.

    Used during token refresh to extract user claims from an expired
    session token. Signature is still verified.

    Args:
        token: Encoded JWT string (may be expired).
        jwt_secret_name: Secrets Manager secret name for the JWT key.

    Returns:
        Decoded payload dictionary.

    Raises:
        jose.JWTError: If the token is malformed or tampered with.
    """
    secret_key = _get_jwt_secret(jwt_secret_name)
    return jwt.decode(
        token, secret_key, algorithms=["HS256"], options={"verify_exp": False}
    )


def create_cookie(
    name: str,
    value: str,
    max_age: int,
    secure: bool = True,
    http_only: bool = True,
    same_site: str = "Lax",
    domain: str | None = None,
    path: str = "/",
) -> str:
    """Create a Set-Cookie header value.

    Args:
        name: Cookie name.
        value: Cookie value.
        max_age: Max age in seconds.
        secure: Secure flag.
        http_only: HttpOnly flag.
        same_site: SameSite attribute.
        domain: Domain attribute (optional).
        path: Path attribute.

    Returns:
        Formatted Set-Cookie header string.
    """
    cookie_parts = [f"{name}={value}", f"Max-Age={max_age}", f"Path={path}"]

    if domain:
        cookie_parts.append(f"Domain={domain}")

    if secure:
        cookie_parts.append("Secure")

    if http_only:
        cookie_parts.append("HttpOnly")

    if same_site:
        cookie_parts.append(f"SameSite={same_site}")

    return "; ".join(cookie_parts)
