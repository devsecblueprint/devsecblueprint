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

# Admin users as provider:username pairs (e.g., "github:damienjburks,gitlab:damienjburks")
# Legacy format without provider prefix is treated as github for backward compatibility.
_raw_admin_users = os.environ["ADMIN_USERS"].split(",")
ADMIN_USERS: list[tuple[str, str]] = []
for _entry in _raw_admin_users:
    _entry = _entry.strip()
    if not _entry:
        continue
    if ":" in _entry:
        _provider, _username = _entry.split(":", 1)
        ADMIN_USERS.append((_provider.strip(), _username.strip()))
    else:
        # Backward compat: bare username treated as github
        ADMIN_USERS.append(("github", _entry))


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
            provider = payload.get("provider", "github")
            github_username = payload.get("github_login")
            gitlab_username = payload.get("gitlab_login")
            bitbucket_username = payload.get("bitbucket_login")

            # Check if user is admin (using provider-specific username)
            if provider == "bitbucket":
                provider_login = bitbucket_username
            elif provider == "gitlab":
                provider_login = gitlab_username
            else:
                provider_login = github_username
            if not provider_login or (provider, provider_login) not in ADMIN_USERS:
                log_admin_access(
                    endpoint=endpoint_name,
                    username=username,
                    user_id=user_id,
                    success=False,
                    reason="Username not in ADMIN_USERS list",
                )
                logger.warning(
                    f"Non-admin user attempted to access {endpoint_name}: {provider_login} (user_id: {user_id})"
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


def is_admin(
    github_username: str | None = None,
    gitlab_username: str | None = None,
    bitbucket_username: str | None = None,
) -> bool:
    """
    Check if a username is in the admin users list.

    Args:
        github_username: GitHub login username (from JWT github_login claim)
        gitlab_username: GitLab login username (from JWT gitlab_login claim)
        bitbucket_username: Bitbucket login username (from JWT bitbucket_login claim)

    Returns:
        bool: True if user is admin, False otherwise

    Example:
        >>> is_admin(github_username="damienjburks")
        True
        >>> is_admin(gitlab_username="someadmin")
        True
        >>> is_admin(bitbucket_username="someadmin")
        True
        >>> is_admin(github_username="someuser")
        False
    """
    if github_username and ("github", github_username) in ADMIN_USERS:
        return True
    if gitlab_username and ("gitlab", gitlab_username) in ADMIN_USERS:
        return True
    if bitbucket_username and ("bitbucket", bitbucket_username) in ADMIN_USERS:
        return True
    return False


def get_admin_users() -> List[str]:
    """
    Get the list of admin users as provider:username strings.

    Returns:
        list: List of admin users in "provider:username" format

    Example:
        >>> get_admin_users()
        ['github:damienjburks', 'gitlab:damienjburks']
    """
    return [f"{provider}:{username}" for provider, username in ADMIN_USERS]
