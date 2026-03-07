"""
GitHub OAuth 2.0 authentication flow handlers.

This module provides functions to handle the complete GitHub OAuth flow:
1. Initiate OAuth by redirecting to GitHub's authorization endpoint
2. Exchange authorization code for access token
3. Fetch user profile from GitHub API
4. Generate JWT and set authentication cookie
5. Redirect to frontend with session established

Integrates with Secrets Manager, JWT utilities, and response utilities.
"""

import os
from urllib.parse import urlencode
import requests
from services.secrets import get_secret
from auth.jwt_utils import generate_jwt
from utils.responses import redirect_response, error_response, create_cookie


def start_oauth() -> dict:
    """
    Initiate GitHub OAuth flow.

    Returns:
        dict: Redirect response to GitHub authorize URL

    Environment Variables:
        - GITHUB_SECRET_NAME: Secrets Manager secret name
        - GITHUB_CALLBACK_URL: OAuth callback URL

    Validates: Requirements 1.1, 1.2, 1.3
    """
    try:
        # Get required environment variables
        github_secret_name = os.environ.get("GITHUB_SECRET_NAME")
        callback_url = os.environ.get("GITHUB_CALLBACK_URL")

        # Validate environment variables
        if not github_secret_name or not callback_url:
            return error_response(500, "Configuration error")

        # Retrieve GitHub credentials from Secrets Manager
        github_secret = get_secret(github_secret_name)
        client_id = github_secret.get("client_id")

        if not client_id:
            return error_response(500, "Configuration error")

        # Construct GitHub OAuth authorization URL
        params = {
            "client_id": client_id,
            "redirect_uri": callback_url,
            "scope": "read:user",
        }

        github_auth_url = (
            f"https://github.com/login/oauth/authorize?{urlencode(params)}"
        )

        # Return redirect response
        return redirect_response(github_auth_url)

    except Exception as e:
        # Return generic error message without exposing internal details
        return error_response(500, "Configuration error")


def exchange_code_for_token(
    code: str, client_id: str, client_secret: str, redirect_uri: str
) -> str:
    """
    Exchange authorization code for access token.

    Args:
        code: Authorization code from GitHub
        client_id: GitHub OAuth client ID
        client_secret: GitHub OAuth client secret
        redirect_uri: Callback URL

    Returns:
        str: GitHub access token

    Raises:
        Exception: If token exchange fails

    Validates: Requirements 2.2
    """
    token_url = "https://github.com/login/oauth/access_token"

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }

    headers = {"Accept": "application/json"}

    response = requests.post(token_url, data=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(
            f"GitHub token exchange failed with status {response.status_code}"
        )

    data = response.json()

    if "access_token" not in data:
        raise Exception("No access_token in GitHub response")

    return data["access_token"]


def get_github_user(access_token: str) -> dict:
    """
    Fetch GitHub user profile.

    Args:
        access_token: GitHub access token

    Returns:
        dict: User profile with keys:
            - id: GitHub user ID
            - login: GitHub username
            - name: Display name

    Raises:
        Exception: If API request fails

    Validates: Requirements 2.3
    """
    user_url = "https://api.github.com/user"

    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

    response = requests.get(user_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"GitHub user API failed with status {response.status_code}")

    user_data = response.json()

    if "id" not in user_data:
        raise Exception("No id in GitHub user response")

    return user_data


def handle_callback(code: str) -> dict:
    """
    Handle GitHub OAuth callback.

    Args:
        code: Authorization code from GitHub

    Returns:
        dict: Redirect response to frontend with JWT cookie set

    Process:
        1. Retrieve GitHub credentials from Secrets Manager
        2. Exchange code for access token
        3. Fetch user profile from GitHub
        4. Generate JWT
        5. Set HttpOnly cookie
        6. Redirect to frontend

    Environment Variables:
        - GITHUB_SECRET_NAME: Secrets Manager secret name
        - GITHUB_CALLBACK_URL: OAuth callback URL
        - FRONTEND_URL: Frontend redirect URL

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7
    """
    try:
        # Get environment variables
        github_secret_name = os.environ.get("GITHUB_SECRET_NAME")
        callback_url = os.environ.get("GITHUB_CALLBACK_URL")
        frontend_url = os.environ.get("FRONTEND_URL")

        if not github_secret_name or not callback_url or not frontend_url:
            return error_response(500, "Configuration error")

        # Retrieve GitHub credentials from Secrets Manager
        github_secret = get_secret(github_secret_name)
        client_id = github_secret.get("client_id")
        client_secret = github_secret.get("client_secret")

        if not client_id or not client_secret:
            return error_response(500, "Configuration error")

        # Exchange code for access token
        access_token = exchange_code_for_token(
            code, client_id, client_secret, callback_url
        )

        # Fetch user profile from GitHub
        user_data = get_github_user(access_token)
        user_id = str(user_data["id"])
        avatar_url = user_data.get("avatar_url")
        # Prefer full name over username for display
        username = user_data.get("name") or user_data.get("login") or f"User {user_id}"
        # Store GitHub login separately for repository validation
        github_username = user_data.get("login") or f"user{user_id}"

        # Register user in database (creates profile if new, updates last_login if existing)
        from services.dynamo import register_user

        register_user(user_id, username, avatar_url, github_username)

        # Generate JWT for internal session management
        jwt_token = generate_jwt(user_id, avatar_url, username, github_username)

        # Redirect to frontend callback page with JWT as query parameter
        # Frontend will set it as a cookie and redirect to dashboard
        callback_page = frontend_url.replace("/dashboard", "/auth/callback")
        redirect_url = f"{callback_page}?token={jwt_token}"

        return redirect_response(redirect_url)

    except Exception as e:
        # Log the error for debugging (sanitized)
        import logging

        logger = logging.getLogger()
        logger.error(f"OAuth callback error: {type(e).__name__}: {str(e)}")

        # Return generic error message without exposing internal details
        return error_response(401, "Authentication failed")
