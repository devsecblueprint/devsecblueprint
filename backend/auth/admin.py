"""
Admin authentication utilities.

Provides decorators and utilities for admin-only endpoints.
"""

import os
import logging
from functools import wraps
from typing import Dict, Any, Callable, List
from datetime import datetime, timezone
from auth.jwt_utils import validate_jwt, extract_token_from_cookie
from utils.responses import error_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Admin usernames (GitHub username or display name)
ADMIN_USERS = os.environ["ADMIN_USERS"].split(",")


def require_admin(handler: Callable) -> Callable:
    """
    Decorator to require admin authentication for endpoint handlers.

    This decorator:
    1. Extracts JWT token from cookie header
    2. Validates the JWT token
    3. Checks if the user is in ADMIN_USERS list
    4. Logs all access attempts
    5. Returns 401 for missing/invalid tokens
    6. Returns 403 for non-admin users

    Args:
        handler: Handler function that takes (headers, username, user_id, **kwargs)

    Returns:
        Wrapped handler function

    Example:
        @require_admin
        def handle_admin_endpoint(headers: Dict[str, str], username: str, user_id: str) -> Dict[str, Any]:
            # Handler implementation
            return json_response(200, {"data": "admin data"})

    Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7
    """

    @wraps(handler)
    def wrapper(headers: Dict[str, str], **kwargs) -> Dict[str, Any]:
        endpoint_name = handler.__name__

        try:
            # Extract JWT from cookie
            token = extract_token_from_cookie(headers)

            if not token:
                log_admin_access(
                    endpoint=endpoint_name,
                    username=None,
                    user_id=None,
                    success=False,
                    reason="Missing JWT token",
                )
                return error_response(401, "Unauthorized")

            # Validate JWT to get user info
            try:
                payload = validate_jwt(token)
            except Exception as e:
                logger.error(f"JWT validation failed: {str(e)}")
                log_admin_access(
                    endpoint=endpoint_name,
                    username=None,
                    user_id=None,
                    success=False,
                    reason=f"Invalid JWT: {type(e).__name__}",
                )
                return error_response(401, "Invalid token")

            # Extract user information
            username = payload.get("name")
            user_id = payload.get("sub")

            # Check if user is admin
            if not username or username not in ADMIN_USERS:
                log_admin_access(
                    endpoint=endpoint_name,
                    username=username,
                    user_id=user_id,
                    success=False,
                    reason="User not in ADMIN_USERS list",
                )
                logger.warning(
                    f"Non-admin user attempted to access {endpoint_name}: {username}"
                )
                return error_response(403, "Forbidden - Admin access required")

            # Log successful authentication
            log_admin_access(
                endpoint=endpoint_name, username=username, user_id=user_id, success=True
            )

            # Call the handler with authenticated user info
            return handler(
                headers=headers, username=username, user_id=user_id, **kwargs
            )

        except Exception as e:
            logger.error(f"Error in admin authentication for {endpoint_name}: {str(e)}")
            log_admin_access(
                endpoint=endpoint_name,
                username=None,
                user_id=None,
                success=False,
                reason=f"Unexpected error: {str(e)}",
            )
            return error_response(500, "Internal server error")

    return wrapper


def log_admin_access(
    endpoint: str,
    username: str | None,
    user_id: str | None,
    success: bool,
    reason: str | None = None,
) -> None:
    """
    Log admin endpoint access attempts.

    Creates structured log entries for all admin endpoint access attempts,
    including both successful and failed attempts.

    Args:
        endpoint: Endpoint name (e.g., "handle_get_submissions")
        username: GitHub username or display name (None if not authenticated)
        user_id: User ID from JWT (None if not authenticated)
        success: Whether the access was successful
        reason: Reason for failure (optional, only for failed attempts)

    Log Format:
        {
            "event": "admin_access",
            "endpoint": endpoint_name,
            "username": username,
            "user_id": user_id,
            "success": true/false,
            "reason": failure_reason,
            "timestamp": ISO 8601 timestamp
        }

    Validates: Requirements 9.7, 10.7
    """
    log_entry = {
        "event": "admin_access",
        "endpoint": endpoint,
        "username": username or "unknown",
        "user_id": user_id or "unknown",
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if reason:
        log_entry["reason"] = reason

    if success:
        logger.info(f"Admin access: {endpoint} by {username} (user_id: {user_id})")
    else:
        logger.warning(
            f"Admin access denied: {endpoint} - {reason} (username: {username}, user_id: {user_id})"
        )

    # Log structured data for CloudWatch Insights
    logger.info(f"ADMIN_ACCESS_LOG: {log_entry}")


def is_admin(username: str | None) -> bool:
    """
    Check if a username is in the admin users list.

    Args:
        username: GitHub username or display name

    Returns:
        bool: True if user is admin, False otherwise

    Example:
        >>> is_admin("damienjburks")
        True
        >>> is_admin("regular_user")
        False
    """
    if not username:
        return False
    return username in ADMIN_USERS


def get_admin_users() -> List[str]:
    """
    Get the list of admin usernames.

    Returns:
        list: List of admin usernames

    Example:
        >>> get_admin_users()
        ['damienjburks', 'Damien Burks']
    """
    return ADMIN_USERS.copy()
