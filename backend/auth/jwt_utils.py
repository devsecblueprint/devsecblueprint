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
    Extract JWT token from cookie header.

    Args:
        headers: Request headers (may have mixed case keys)

    Returns:
        str | None: Token string or None if not found

    Validates: Requirements 3.1
    """
    # API Gateway HTTP API may send headers with mixed case
    # Check both lowercase and capitalized versions
    cookie_header = headers.get("cookie", "") or headers.get("Cookie", "")

    if not cookie_header:
        return None

    # Parse cookies (format: "name1=value1; name2=value2")
    cookies = {}
    for cookie in cookie_header.split(";"):
        cookie = cookie.strip()
        if "=" in cookie:
            name, value = cookie.split("=", 1)
            cookies[name.strip()] = value.strip()

    return cookies.get("dsb_token")


def verify_user(headers: Dict[str, str]) -> Dict[str, any]:
    """
    Verify user authentication and return user information.

    This is the handler for the GET /me endpoint. It extracts the JWT from cookies,
    validates it, and returns the user information.

    Args:
        headers: Request headers (lowercase keys) from API Gateway event

    Returns:
        dict: API Gateway response with user_id and authenticated status

    Response Format (Success):
        {
            "statusCode": 200,
            "headers": {...CORS headers...},
            "body": '{"user_id": "12345678", "authenticated": true}'
        }

    Response Format (Error):
        {
            "statusCode": 401,
            "headers": {...CORS headers...},
            "body": '{"error": "Authentication failed"}'
        }

    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
    """
    try:
        # Log cookie header for debugging
        cookie_header = headers.get("cookie", "")
        logger.info(
            f"Cookie header: {cookie_header[:100] if cookie_header else 'NONE'}"
        )

        # Extract JWT from cookie
        token = extract_token_from_cookie(headers)

        logger.info(f"Extracted token: {'YES' if token else 'NO'}")

        # Handle missing token
        if not token:
            return error_response(401, "Authentication failed")

        # Validate JWT and extract payload
        try:
            payload = validate_jwt(token)
        except JWTError as e:
            logger.error(f"JWT validation failed: {type(e).__name__}")
            # Invalid or expired JWT
            return error_response(401, "Authentication failed")

        # Extract user_id from payload
        user_id = payload.get("sub")
        if not user_id:
            return error_response(401, "Authentication failed")

        # Extract avatar URL if present
        avatar_url = payload.get("avatar")
        logger.info(f"Avatar URL from JWT: {avatar_url[:50] if avatar_url else 'NONE'}")

        # Extract username if present
        username = payload.get("name")
        logger.info(f"Username from JWT: {username if username else 'NONE'}")

        # Extract GitHub login username if present
        github_username = payload.get("github_login")
        logger.info(
            f"GitHub username from JWT: {github_username if github_username else 'NONE'}"
        )

        # Check if user is admin
        admin_users_str = os.environ.get("ADMIN_USERS", "")
        admin_users = [u.strip() for u in admin_users_str.split(",") if u.strip()]
        is_admin = github_username in admin_users if github_username else False
        logger.info(f"User is admin: {is_admin}")

        # Return success response
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
            f"Response includes avatar: {'avatar_url' in response_data}, username: {'username' in response_data}, github_username: {'github_username' in response_data}, is_admin: {is_admin}"
        )

        return json_response(200, response_data)

    except Exception:
        # Catch any unexpected errors and return generic error
        # Don't expose internal details or stack traces
        return error_response(401, "Authentication failed")
