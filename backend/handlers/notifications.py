"""
Notification endpoint handlers.

Provides endpoints for authenticated users to retrieve and acknowledge
their in-app notifications.
"""

import logging
from typing import Dict, Any

from auth.jwt_utils import extract_token_from_cookie, validate_jwt
from jose import JWTError
from services.notification_service import get_notifications, delete_notification
from utils.responses import json_response, error_response

logger = logging.getLogger(__name__)


def handle_get_notifications(
    headers: Dict[str, str],
) -> Dict[str, Any]:
    """
    Handle GET /api/notifications endpoint.

    Returns all notifications for the authenticated user, sorted by
    created_at descending.

    Args:
        headers: Request headers

    Returns:
        dict: API Gateway response with notifications list

    Requirements: 5.4, 5.6, 12.2
    """
    try:
        # Extract and validate JWT
        token = extract_token_from_cookie(headers)
        if not token:
            return error_response(401, "Authentication failed")

        try:
            payload = validate_jwt(token)
        except JWTError:
            return error_response(401, "Authentication failed")

        user_id = payload.get("sub")
        if not user_id:
            return error_response(401, "Authentication failed")

        # Get notifications (already sorted by created_at descending)
        notifications = get_notifications(user_id)

        return json_response(200, {"notifications": notifications})

    except Exception as e:
        logger.error(f"Error in handle_get_notifications: {str(e)}")
        return error_response(500, "Service temporarily unavailable")


def handle_delete_notification(
    headers: Dict[str, str],
    notification_id: str,
) -> Dict[str, Any]:
    """
    Handle DELETE /api/notifications/{notification_id} endpoint.

    Acknowledges and removes a notification from the database.

    Args:
        headers: Request headers
        notification_id: The notification identifier (from URL path)

    Returns:
        dict: API Gateway response

    Requirements: 5.5, 5.6, 12.2
    """
    try:
        # Extract and validate JWT
        token = extract_token_from_cookie(headers)
        if not token:
            return error_response(401, "Authentication failed")

        try:
            payload = validate_jwt(token)
        except JWTError:
            return error_response(401, "Authentication failed")

        user_id = payload.get("sub")
        if not user_id:
            return error_response(401, "Authentication failed")

        # Delete the notification
        delete_notification(user_id, notification_id)

        return json_response(200, {"message": "Notification deleted"})

    except Exception as e:
        logger.error(f"Error in handle_delete_notification: {str(e)}")
        return error_response(500, "Service temporarily unavailable")
