"""Bitbucket Cloud OAuth 2.0 authentication flow — self-contained async module.

Handles the complete Bitbucket Cloud OAuth flow:
1. Initiate OAuth by building the redirect URL
2. Exchange authorization code for access token
3. Fetch user profile and email from Bitbucket API
4. Register user in DynamoDB
5. Generate session + refresh tokens
6. Return redirect data for the router

Uses httpx (async) for all HTTP calls. Imports only from app.* namespace.
"""

import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from app.config import Settings
from app.auth.token_service import (
    create_cookie,
    generate_refresh_token,
    generate_session_token,
    get_session_lifetime_hours,
    hash_token,
)
from app.auth.github import OAuthResult, _parse_admin_users
from app.services.secrets import get_secret
from app.services.session_store import store_refresh_token
from app.services.user_registration import register_user
from app.services.email import send_welcome_email

logger = logging.getLogger(__name__)


async def start_bitbucket_oauth(settings: Settings) -> str:
    """Build the Bitbucket OAuth authorization redirect URL.

    Args:
        settings: Application settings.

    Returns:
        The full Bitbucket OAuth authorize URL.

    Raises:
        Exception: If configuration or secret retrieval fails.
    """
    bitbucket_secret = get_secret(settings.bitbucket_secret_name)
    client_id = bitbucket_secret.get("client_id")

    if not client_id:
        raise Exception("Bitbucket client_id not found in secret")

    params = {
        "client_id": client_id,
        "redirect_uri": settings.bitbucket_callback_url,
        "response_type": "code",
    }

    return f"https://bitbucket.org/site/oauth2/authorize?{urlencode(params)}"


async def handle_bitbucket_callback(code: str, settings: Settings) -> OAuthResult:
    """Handle Bitbucket OAuth callback: exchange code, fetch user, register, issue tokens.

    Args:
        code: Authorization code from Bitbucket.
        settings: Application settings.

    Returns:
        OAuthResult with redirect URL and cookies to set.

    Raises:
        Exception: If any step of the OAuth flow fails.
    """
    # Retrieve credentials
    bitbucket_secret = get_secret(settings.bitbucket_secret_name)
    client_id = bitbucket_secret.get("client_id")
    client_secret = bitbucket_secret.get("client_secret")

    if not client_id or not client_secret:
        raise Exception("Bitbucket OAuth credentials not found in secret")

    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        token_response = await client.post(
            "https://bitbucket.org/site/oauth2/access_token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": settings.bitbucket_callback_url,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
        )

        if token_response.status_code != 200:
            raise Exception(
                f"Bitbucket token exchange failed: {token_response.status_code}"
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise Exception("No access_token in Bitbucket response")

        # Fetch user profile
        user_response = await client.get(
            "https://api.bitbucket.org/2.0/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if user_response.status_code != 200:
            raise Exception(f"Bitbucket user API failed: {user_response.status_code}")

        user_data = user_response.json()
        if "uuid" not in user_data:
            raise Exception("No uuid in Bitbucket user response")

        # Fetch user email
        email = await _get_bitbucket_email(client, access_token)

    # Extract user info
    raw_uuid = user_data["uuid"]
    clean_uuid = raw_uuid.replace("{", "").replace("}", "")
    user_id = f"bitbucket_{clean_uuid}"
    avatar_url = user_data.get("links", {}).get("avatar", {}).get("href", "")
    username = (
        user_data.get("display_name")
        or user_data.get("nickname")
        or f"User {clean_uuid}"
    )
    bitbucket_username = user_data.get("nickname") or f"user{clean_uuid}"

    # Register user in database
    is_new_user = register_user(
        table_name=settings.progress_table,
        user_id=user_id,
        username=username,
        avatar_url=avatar_url,
        provider="bitbucket",
        bitbucket_username=bitbucket_username,
        email=email,
    )

    # Send welcome email to new users
    if is_new_user and email:
        send_welcome_email(
            username=username,
            email=email,
            mailgun_domain=settings.mailgun_domain,
            mailgun_param_name=settings.mailgun_param_name,
        )

    # Determine admin status
    admin_entries = _parse_admin_users(settings.admin_users)
    is_admin = (
        ("bitbucket", bitbucket_username) in admin_entries
        if bitbucket_username
        else False
    )

    # Generate tokens
    lifetime_hours = get_session_lifetime_hours(settings.session_token_lifetime_hours)

    session_token = generate_session_token(
        jwt_secret_name=settings.jwt_secret_name,
        user_id=user_id,
        avatar_url=avatar_url,
        username=username,
        is_admin=is_admin,
        provider="bitbucket",
        bitbucket_username=bitbucket_username,
        lifetime_hours=lifetime_hours,
    )
    raw_refresh_token = generate_refresh_token()

    # Store refresh token
    now = datetime.now(timezone.utc)
    refresh_expires_at = now + timedelta(hours=lifetime_hours)

    store_refresh_token(
        table_name=settings.progress_table,
        user_id=user_id,
        token_hash=hash_token(raw_refresh_token),
        created_at=int(now.timestamp()),
        expires_at=int(refresh_expires_at.timestamp()),
    )

    # Build refresh cookie
    refresh_cookie = create_cookie(
        name="dsb_refresh",
        value=raw_refresh_token,
        max_age=int(lifetime_hours * 3600),
        secure=True,
        http_only=False,
        same_site="None",
        path="/",
    )

    # Build redirect URL
    callback_page = settings.frontend_url.replace("/dashboard", "/auth/callback")
    redirect_url = f"{callback_page}?token={session_token}"

    return OAuthResult(redirect_url=redirect_url, cookies=[refresh_cookie])


async def _get_bitbucket_email(
    client: httpx.AsyncClient, access_token: str
) -> str | None:
    """Fetch the primary confirmed email from Bitbucket."""
    try:
        response = await client.get(
            "https://api.bitbucket.org/2.0/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code != 200:
            return None

        data = response.json()
        emails = data.get("values", [])

        # Find primary confirmed email
        for entry in emails:
            if entry.get("is_primary") and entry.get("is_confirmed"):
                return entry.get("email")

        # Fallback: any confirmed email
        for entry in emails:
            if entry.get("is_confirmed"):
                return entry.get("email")

        return None
    except Exception:
        return None
