"""
Progress reset handler for admin users.

Allows admin users to reset their progress data.
"""

import os
import json
import logging
from typing import Dict, Any
from auth.jwt_utils import validate_jwt, extract_token_from_cookie
from services.dynamo import delete_all_user_progress
from utils.responses import error_response, json_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Admin GitHub usernames (GitHub login usernames, e.g., "damienjburks")
ADMIN_USERS = os.environ["ADMIN_USERS"].split(",")


def handle_reset_progress(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle DELETE /progress/reset endpoint.

    Deletes all progress data for the authenticated admin user.

    Args:
        headers: Request headers containing JWT cookie

    Returns:
        dict: API Gateway response with success message or error
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
        username = payload.get(
            "name"
        )  # This is the display name or username from GitHub
        github_username = payload.get("github_login")

        if not user_id:
            return error_response(401, "Invalid token")

        logger.info(
            f"Reset request from user_id: {user_id}, username: {username}, github_username: {github_username}"
        )

        # Check if user is admin (check GitHub username)
        if not github_username or github_username not in ADMIN_USERS:
            logger.warning(f"Non-admin user attempted reset: {github_username}")
            return error_response(403, "Forbidden - Admin access required")

        # Delete all progress for this user
        delete_all_user_progress(user_id)

        logger.info(f"Reset all progress for admin user: {username} (ID: {user_id})")

        return json_response(
            200, {"message": "Progress reset successfully", "user_id": user_id}
        )

    except Exception as e:
        logger.error(f"Error resetting progress: {str(e)}")
        return error_response(500, "Failed to reset progress")
