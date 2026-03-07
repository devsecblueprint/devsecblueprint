"""
User profile handler.

Provides user profile information and checks if user is new.
"""

import logging
from typing import Dict, Any
from auth.jwt_utils import validate_jwt, extract_token_from_cookie
from services.dynamo import get_user_profile, get_all_users_progress
from utils.responses import error_response, json_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handle_get_user_profile(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET /user/profile endpoint.

    Returns user profile information including whether they are new.

    Args:
        headers: Request headers containing JWT cookie

    Returns:
        dict: API Gateway response with user profile or error
    """
    try:
        # Extract JWT from cookie
        token = extract_token_from_cookie(headers)

        if not token:
            return error_response(401, "Unauthorized")

        # Validate JWT to get user info
        try:
            payload = validate_jwt(token)
        except Exception as e:
            logger.error(f"JWT validation failed: {str(e)}")
            return error_response(401, "Invalid token")

        user_id = payload.get("sub")
        if not user_id:
            return error_response(401, "Invalid token")

        # Get user profile
        profile = get_user_profile(user_id)

        if not profile:
            return error_response(404, "User profile not found")

        # Check if user has any progress by querying their specific progress items
        # This is more efficient than scanning all users' progress
        from services.progress_service import get_user_progress

        user_progress = get_user_progress(user_id)
        is_new_user = len(user_progress) == 0

        return json_response(
            200,
            {
                "user_id": profile["user_id"],
                "username": profile["username"],
                "avatar_url": profile.get("avatar_url", ""),
                "github_username": profile.get("github_username", ""),
                "registered_at": profile["registered_at"],
                "last_login": profile["last_login"],
                "is_new_user": is_new_user,
                "total_completions": len(user_progress),
            },
        )

    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        return error_response(500, "Failed to fetch user profile")
