"""Refresh router — POST /refresh.

Issues a new session token using the current (possibly expired) session token's
claims. The token is extracted from the Authorization header or cookies. Unlike
normal authenticated routes, this endpoint accepts expired tokens (signature is
still verified) to allow seamless session renewal.

Requirements: 4.2
"""

import json
import logging
import time
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from jose import jwt, JWTError

from app.config import Settings
from app.dependencies import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["refresh"])

# In-memory JWT secret cache (shared with auth/jwt.py pattern)
_jwt_secret_cache: dict = {
    "secret_key": None,
    "fetched_at": 0.0,
}
_CACHE_TTL_SECONDS = 900


def _get_jwt_secret(settings: Settings) -> str:
    """Retrieve the JWT signing secret from Secrets Manager with caching."""
    now = time.time()

    if (
        _jwt_secret_cache["secret_key"] is not None
        and (now - _jwt_secret_cache["fetched_at"]) < _CACHE_TTL_SECONDS
    ):
        return _jwt_secret_cache["secret_key"]

    secret_name = settings.jwt_secret_name
    if not secret_name:
        logger.error("jwt_secret_name is not configured")
        raise HTTPException(status_code=401, detail="Authentication failed")

    try:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(response["SecretString"])
    except (ClientError, json.JSONDecodeError, KeyError) as exc:
        logger.error("Failed to retrieve JWT secret: %s", exc)
        raise HTTPException(status_code=401, detail="Authentication failed")

    secret_key = secret_data.get("secret_key")
    if not secret_key:
        logger.error("secret_key not found in JWT secret payload")
        raise HTTPException(status_code=401, detail="Authentication failed")

    _jwt_secret_cache["secret_key"] = secret_key
    _jwt_secret_cache["fetched_at"] = now
    return secret_key


def _extract_session_token(request: Request) -> str | None:
    """Extract the session token from the request.

    Checks in order:
    1. Authorization: Bearer <token> header
    2. dsb_session cookie
    3. dsb_token cookie (legacy fallback)
    """
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            return token

    token = request.cookies.get("dsb_session")
    if token:
        return token

    token = request.cookies.get("dsb_token")
    if token:
        return token

    return None


def _get_session_lifetime_hours(settings: Settings) -> float:
    """Get the session token lifetime from settings."""
    return float(settings.session_token_lifetime_hours)


def _generate_session_token(
    claims: dict, secret_key: str, lifetime_hours: float
) -> str:
    """Generate a new HS256 JWT session token from existing claims."""
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(hours=lifetime_hours)

    provider = claims.get("provider", "github")

    payload = {
        "sub": claims["sub"],
        "avatar": claims.get("avatar", ""),
        "name": claims.get("name", ""),
        "provider": provider,
        "is_admin": claims.get("is_admin", False),
        "iat": now,
        "exp": expiration,
    }

    # Include provider-specific login claim
    if provider == "bitbucket":
        payload["bitbucket_login"] = claims.get("bitbucket_login", "")
    elif provider == "gitlab":
        payload["gitlab_login"] = claims.get("gitlab_login", "")
    else:
        payload["github_login"] = claims.get("github_login", "")

    return jwt.encode(payload, secret_key, algorithm="HS256")


def _hash_token(token: str) -> str:
    """Return the SHA-256 hex digest of a token string."""
    import hashlib

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@router.post("/refresh")
async def refresh_session(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Issue a new session token using the current (possibly expired) token.

    Reads the session token from the Authorization header or cookies,
    decodes it without verifying expiry (signature is still checked),
    and issues a fresh session token with updated expiration.

    Returns:
        JSON response with the new session_token.

    Raises:
        HTTPException(401): If no token is present or decoding fails.
    """
    session_token = _extract_session_token(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Authentication failed")

    secret_key = _get_jwt_secret(settings)

    try:
        # Decode without verifying expiry — the token may be expired
        claims = jwt.decode(
            session_token,
            secret_key,
            algorithms=["HS256"],
            options={"verify_exp": False},
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Authentication failed")

    if not claims.get("sub"):
        raise HTTPException(status_code=401, detail="Authentication failed")

    try:
        lifetime_hours = _get_session_lifetime_hours(settings)
        new_session_token = _generate_session_token(claims, secret_key, lifetime_hours)

        # Record the new session in DynamoDB
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=lifetime_hours)

        _store_session_record(
            user_id=claims["sub"],
            token_hash=_hash_token(new_session_token),
            created_at=int(now.timestamp()),
            expires_at=int(expires_at.timestamp()),
            settings=settings,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Token refresh failed: %s", exc)
        raise HTTPException(status_code=401, detail="Authentication failed")

    return JSONResponse(
        status_code=200,
        content={"session_token": new_session_token},
    )


def _store_session_record(
    user_id: str,
    token_hash: str,
    created_at: int,
    expires_at: int,
    settings: Settings,
) -> None:
    """Store the session token hash in DynamoDB for tracking."""
    table_name = settings.progress_table
    if not table_name:
        logger.warning("PROGRESS_TABLE not configured, skipping session record storage")
        return

    dynamodb = boto3.client("dynamodb")
    dynamodb.put_item(
        TableName=table_name,
        Item={
            "PK": {"S": f"USER#{user_id}"},
            "SK": {"S": f"SESSION#{token_hash}"},
            "created_at": {"N": str(created_at)},
            "expires_at": {"N": str(expires_at)},
            "user_id": {"S": user_id},
        },
    )
