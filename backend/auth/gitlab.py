"""
GitLab OAuth 2.0 authentication flow handlers.

This module provides functions to handle the complete GitLab OAuth flow:
1. Initiate OAuth by redirecting to GitLab's authorization endpoint
2. Exchange authorization code for access token
3. Fetch user profile from GitLab API
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
    Initiate GitLab OAuth flow.

    Returns:
        dict: Redirect response to GitLab authorize URL

    Environment Variables:
        - GITLAB_SECRET_NAME: Secrets Manager secret name
        - GITLAB_CALLBACK_URL: OAuth callback URL

    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 10.1, 10.2
    """
    try:
        gitlab_secret_name = os.environ.get("GITLAB_SECRET_NAME")
        callback_url = os.environ.get("GITLAB_CALLBACK_URL")

        if not gitlab_secret_name or not callback_url:
            return error_response(500, "Configuration error")

        gitlab_secret = get_secret(gitlab_secret_name)
        client_id = gitlab_secret.get("client_id")

        if not client_id:
            return error_response(500, "Configuration error")

        params = {
            "client_id": client_id,
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": "read_user",
        }

        gitlab_auth_url = f"https://gitlab.com/oauth/authorize?{urlencode(params)}"

        return redirect_response(gitlab_auth_url)

    except Exception:
        return error_response(500, "Configuration error")


def exchange_code_for_token(
    code: str, client_id: str, client_secret: str, redirect_uri: str
) -> str:
    """
    Exchange authorization code for access token.

    Args:
        code: Authorization code from GitLab
        client_id: GitLab OAuth client ID
        client_secret: GitLab OAuth client secret
        redirect_uri: Callback URL

    Returns:
        str: GitLab access token

    Raises:
        Exception: If token exchange fails

    Validates: Requirements 2.1
    """
    token_url = "https://gitlab.com/oauth/token"

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
            f"GitLab token exchange failed with status {response.status_code}"
        )

    data = response.json()

    if "access_token" not in data:
        raise Exception("No access_token in GitLab response")

    return data["access_token"]


def get_gitlab_user(access_token: str) -> dict:
    """
    Fetch GitLab user profile.

    Args:
        access_token: GitLab access token

    Returns:
        dict: User profile with keys:
            - id: GitLab user ID
            - username: GitLab username
            - name: Display name
            - avatar_url: Avatar URL

    Raises:
        Exception: If API request fails

    Validates: Requirements 2.2, 2.3
    """
    user_url = "https://gitlab.com/api/v4/user"

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(user_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"GitLab user API failed with status {response.status_code}")

    user_data = response.json()

    if "id" not in user_data:
        raise Exception("No id in GitLab user response")

    return user_data


def handle_callback(code: str) -> dict:
    """
    Handle GitLab OAuth callback.

    Args:
        code: Authorization code from GitLab

    Returns:
        dict: Redirect response to frontend with JWT cookie set

    Process:
        1. Retrieve GitLab credentials from Secrets Manager
        2. Exchange code for access token
        3. Fetch user profile from GitLab
        4. Register user with gitlab_ prefixed ID
        5. Generate session token with provider="gitlab"
        6. Generate + store refresh token
        7. Redirect to frontend callback with session token

    Environment Variables:
        - GITLAB_SECRET_NAME: Secrets Manager secret name
        - GITLAB_CALLBACK_URL: OAuth callback URL
        - FRONTEND_URL: Frontend redirect URL

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 4.1, 4.2, 4.3, 4.4, 10.1, 10.2, 10.3, 11.1, 11.2, 11.3
    """
    try:
        gitlab_secret_name = os.environ.get("GITLAB_SECRET_NAME")
        callback_url = os.environ.get("GITLAB_CALLBACK_URL")
        frontend_url = os.environ.get("FRONTEND_URL")

        if not gitlab_secret_name or not callback_url or not frontend_url:
            return error_response(500, "Configuration error")

        gitlab_secret = get_secret(gitlab_secret_name)
        client_id = gitlab_secret.get("client_id")
        client_secret = gitlab_secret.get("client_secret")

        if not client_id or not client_secret:
            return error_response(500, "Configuration error")

        # Exchange code for access token
        access_token = exchange_code_for_token(
            code, client_id, client_secret, callback_url
        )

        # Fetch user profile from GitLab
        user_data = get_gitlab_user(access_token)
        gitlab_id = user_data["id"]
        user_id = f"gitlab_{gitlab_id}"
        avatar_url = user_data.get("avatar_url")
        username = (
            user_data.get("name") or user_data.get("username") or f"User {gitlab_id}"
        )
        gitlab_username = user_data.get("username") or f"user{gitlab_id}"

        # Register user in database
        from services.dynamo import register_user

        register_user(
            user_id,
            username,
            avatar_url,
            github_username=None,
            provider="gitlab",
            gitlab_username=gitlab_username,
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
            ("gitlab", gitlab_username) in admin_entries if gitlab_username else False
        )

        # Generate session token with provider="gitlab"
        session_token = generate_session_token(
            user_id=user_id,
            avatar_url=avatar_url or "",
            username=username,
            github_username="",
            is_admin=is_admin,
            provider="gitlab",
            gitlab_username=gitlab_username,
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
        logger.error(f"GitLab OAuth callback error: {type(e).__name__}: {str(e)}")

        return error_response(401, "Authentication failed")
