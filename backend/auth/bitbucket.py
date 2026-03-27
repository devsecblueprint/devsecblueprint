"""
Bitbucket Cloud OAuth 2.0 authentication flow handlers.

This module provides functions to handle the complete Bitbucket Cloud OAuth flow:
1. Initiate OAuth by redirecting to Bitbucket's authorization endpoint
2. Exchange authorization code for access token
3. Fetch user profile from Bitbucket API
4. Generate JWT and set authentication cookie
5. Redirect to frontend with session established

Integrates with Secrets Manager, JWT utilities, and response utilities.
"""

import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import requests
from services.secrets import get_secret
from auth.token_service import (
    generate_session_token,
    generate_refresh_token,
    hash_token,
    _get_session_lifetime_hours,
)
from services import session_store
from utils.responses import redirect_response, error_response, create_cookie


def start_oauth() -> dict:
    """
    Initiate Bitbucket Cloud OAuth flow.

    Returns:
        dict: Redirect response to Bitbucket authorize URL

    Environment Variables:
        - BITBUCKET_SECRET_NAME: Secrets Manager secret name
        - BITBUCKET_CALLBACK_URL: OAuth callback URL

    Validates: Requirements 1.1, 1.2, 1.3, 1.4
    """
    try:
        bitbucket_secret_name = os.environ.get("BITBUCKET_SECRET_NAME")
        callback_url = os.environ.get("BITBUCKET_CALLBACK_URL")

        if not bitbucket_secret_name or not callback_url:
            return error_response(500, "Configuration error")

        bitbucket_secret = get_secret(bitbucket_secret_name)
        client_id = bitbucket_secret.get("client_id")

        if not client_id:
            return error_response(500, "Configuration error")

        params = {
            "client_id": client_id,
            "redirect_uri": callback_url,
            "response_type": "code",
        }

        bitbucket_auth_url = (
            f"https://bitbucket.org/site/oauth2/authorize?{urlencode(params)}"
        )

        return redirect_response(bitbucket_auth_url)

    except Exception:
        return error_response(500, "Configuration error")


def exchange_code_for_token(
    code: str, client_id: str, client_secret: str, redirect_uri: str
) -> str:
    """
    Exchange authorization code for access token.

    Args:
        code: Authorization code from Bitbucket
        client_id: Bitbucket OAuth client ID
        client_secret: Bitbucket OAuth client secret
        redirect_uri: Callback URL

    Returns:
        str: Bitbucket access token

    Raises:
        Exception: If token exchange fails

    Validates: Requirements 2.1, 2.3, 2.4
    """
    token_url = "https://bitbucket.org/site/oauth2/access_token"

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    headers = {"Accept": "application/json"}

    response = requests.post(token_url, data=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(
            f"Bitbucket token exchange failed with status {response.status_code}"
        )

    data = response.json()

    if "access_token" not in data:
        raise Exception("No access_token in Bitbucket response")

    return data["access_token"]


def get_bitbucket_user(access_token: str) -> dict:
    """
    Fetch Bitbucket Cloud user profile.

    Args:
        access_token: Bitbucket access token

    Returns:
        dict: User profile with keys:
            - uuid: Bitbucket user UUID
            - display_name: Display name
            - nickname: Bitbucket username
            - avatar_url: Avatar URL (extracted from links.avatar.href)

    Raises:
        Exception: If API request fails

    Validates: Requirements 3.1, 3.2, 3.3, 3.4
    """
    user_url = "https://api.bitbucket.org/2.0/user"

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(user_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Bitbucket user API failed with status {response.status_code}")

    user_data = response.json()

    if "uuid" not in user_data:
        raise Exception("No uuid in Bitbucket user response")

    return {
        "uuid": user_data["uuid"],
        "display_name": user_data.get("display_name", ""),
        "nickname": user_data.get("nickname", ""),
        "avatar_url": user_data.get("links", {}).get("avatar", {}).get("href", ""),
    }


def handle_callback(code: str) -> dict:
    """
    Handle Bitbucket Cloud OAuth callback.

    Args:
        code: Authorization code from Bitbucket

    Returns:
        dict: Redirect response to frontend with JWT cookie set

    Process:
        1. Retrieve Bitbucket credentials from Secrets Manager
        2. Exchange code for access token
        3. Fetch user profile from Bitbucket
        4. Register user with bitbucket_ prefixed ID (curly braces stripped)
        5. Generate session token with provider="bitbucket"
        6. Generate + store refresh token
        7. Redirect to frontend callback with session token

    Environment Variables:
        - BITBUCKET_SECRET_NAME: Secrets Manager secret name
        - BITBUCKET_CALLBACK_URL: OAuth callback URL
        - FRONTEND_URL: Frontend redirect URL

    Validates: Requirements 2.1, 2.2, 2.5, 3.1, 4.1, 5.1, 5.2, 5.3
    """
    try:
        bitbucket_secret_name = os.environ.get("BITBUCKET_SECRET_NAME")
        callback_url = os.environ.get("BITBUCKET_CALLBACK_URL")
        frontend_url = os.environ.get("FRONTEND_URL")

        if not bitbucket_secret_name or not callback_url or not frontend_url:
            return error_response(500, "Configuration error")

        bitbucket_secret = get_secret(bitbucket_secret_name)
        client_id = bitbucket_secret.get("client_id")
        client_secret = bitbucket_secret.get("client_secret")

        if not client_id or not client_secret:
            return error_response(500, "Configuration error")

        # Exchange code for access token
        access_token = exchange_code_for_token(
            code, client_id, client_secret, callback_url
        )

        # Fetch user profile from Bitbucket
        user_data = get_bitbucket_user(access_token)
        raw_uuid = user_data["uuid"]
        # Strip curly braces from Bitbucket UUID
        clean_uuid = raw_uuid.replace("{", "").replace("}", "")
        user_id = f"bitbucket_{clean_uuid}"
        avatar_url = user_data.get("avatar_url", "")
        username = (
            user_data.get("display_name")
            or user_data.get("nickname")
            or f"User {clean_uuid}"
        )
        bitbucket_username = user_data.get("nickname") or f"user{clean_uuid}"

        # Register user in database
        from services.dynamo import register_user

        register_user(
            user_id,
            username,
            avatar_url,
            provider="bitbucket",
            bitbucket_username=bitbucket_username,
        )

        # Determine admin status
        admin_users_str = os.environ.get("ADMIN_USERS", "")
        admin_entries = []
        for entry in admin_users_str.split(","):
            entry = entry.strip()
            if not entry:
                continue
            if ":" in entry:
                p, u = entry.split(":", 1)
                admin_entries.append((p.strip(), u.strip()))
            else:
                admin_entries.append(("github", entry))
        is_admin = (
            ("bitbucket", bitbucket_username) in admin_entries
            if bitbucket_username
            else False
        )

        # Generate session token with provider="bitbucket"
        session_token = generate_session_token(
            user_id=user_id,
            avatar_url=avatar_url or "",
            username=username,
            is_admin=is_admin,
            provider="bitbucket",
            bitbucket_username=bitbucket_username,
        )
        raw_refresh_token = generate_refresh_token()

        # Store hashed refresh token in DynamoDB
        now = datetime.now(timezone.utc)
        lifetime_hours = _get_session_lifetime_hours()
        refresh_expires_at = now + timedelta(hours=lifetime_hours)

        session_store.store_refresh_token(
            user_id=user_id,
            token_hash=hash_token(raw_refresh_token),
            created_at=int(now.timestamp()),
            expires_at=int(refresh_expires_at.timestamp()),
        )

        # Build refresh token cookie
        refresh_cookie = create_cookie(
            name="dsb_refresh",
            value=raw_refresh_token,
            max_age=int(lifetime_hours * 3600),
            secure=True,
            http_only=False,
            same_site="None",
            path="/",
        )

        # Redirect to frontend callback page with session token
        callback_page = frontend_url.replace("/dashboard", "/auth/callback")
        redirect_url = f"{callback_page}?token={session_token}"

        return redirect_response(redirect_url, cookies=[refresh_cookie])

    except Exception as e:
        import logging

        logger = logging.getLogger()
        logger.error(f"Bitbucket OAuth callback error: {type(e).__name__}: {str(e)}")

        return error_response(401, "Authentication failed")
