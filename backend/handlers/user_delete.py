"""
User Account Deletion Handler

Handles permanent deletion of user accounts and all associated data.
"""

from services.dynamo import delete_user_account
from utils.responses import json_response, error_response
from auth.jwt_utils import validate_jwt, extract_token_from_cookie
from jose.exceptions import JWTError
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handle_delete_account(headers: dict) -> dict:
    """
    DELETE /user/account

    Permanently deletes the authenticated user's account and all associated data.
    This includes:
    - User profile
    - All progress records
    - All capstone submissions

    Args:
        headers: Request headers containing JWT token

    Returns:
        200: Account successfully deleted
        401: Unauthorized (invalid/missing token)
        500: Server error
    """
    try:
        # Extract JWT token from cookie
        token = extract_token_from_cookie(headers)

        if not token:
            return error_response(401, "Unauthorized")

        # Validate JWT token
        try:
            payload = validate_jwt(token)
        except JWTError as e:
            logger.error(f"JWT validation failed: {str(e)}")
            return error_response(401, "Invalid or expired token")

        user_id = payload.get("sub")
        if not user_id:
            return error_response(401, "Invalid token payload")

        logger.info(f"Deleting account for user: {user_id}")

        # Delete user account and all associated data
        success = delete_user_account(user_id)

        if not success:
            logger.error(f"Failed to delete account for user: {user_id}")
            return error_response(500, "Failed to delete account")

        logger.info(f"Successfully deleted account for user: {user_id}")

        return json_response(200, {"message": "Account successfully deleted"})

    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        import traceback

        traceback.print_exc()
        return error_response(500, "Internal server error")
