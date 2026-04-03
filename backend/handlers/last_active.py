"""
Last active lesson endpoint handlers.

This module provides handlers for the last-active lesson endpoints:
- PUT /progress/last-active: Save the learner's last active lesson
- GET /progress/last-active: Retrieve the learner's last active lesson
"""

import json
from typing import Dict, Any
from jose import JWTError
from auth.jwt_utils import extract_token_from_cookie, validate_jwt
from services.dynamo import save_last_active, get_last_active
from utils.responses import json_response, error_response


def handle_save_last_active(headers: Dict[str, str], body: str) -> Dict[str, Any]:
    """
    Handle PUT /progress/last-active endpoint to save the learner's last active lesson.

    Args:
        headers: Request headers (lowercase keys) from API Gateway event
        body: Request body (JSON string) containing page_id and page_slug

    Returns:
        dict: API Gateway response

    Response Format (Success - 200):
        {"message": "Last active lesson saved"}

    Response Format (Error - 400):
        {"error": "Invalid request"}

    Response Format (Error - 401):
        {"error": "Authentication failed"}

    Response Format (Error - 500):
        {"error": "Service temporarily unavailable"}

    Validates: Requirements 1.1, 1.2, 1.3, 1.5
    """
    try:
        # Extract and validate JWT from cookie
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

        # Parse JSON body to extract page_id and page_slug
        try:
            if not body:
                return error_response(400, "Invalid request")

            body_data = json.loads(body)
            page_id = body_data.get("page_id")
            page_slug = body_data.get("page_slug")

            if not page_id or not page_slug:
                return error_response(400, "Invalid request")

        except (json.JSONDecodeError, ValueError):
            return error_response(400, "Invalid request")

        # Save last active lesson to DynamoDB
        try:
            save_last_active(user_id, page_id, page_slug)
        except Exception:
            return error_response(500, "Service temporarily unavailable")

        return json_response(200, {"message": "Last active lesson saved"})

    except Exception:
        return error_response(500, "Service temporarily unavailable")


def handle_get_last_active(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET /progress/last-active endpoint to retrieve the learner's last active lesson.

    Args:
        headers: Request headers (lowercase keys) from API Gateway event

    Returns:
        dict: API Gateway response

    Response Format (Success - 200, with data):
        {"page_id": "the-source-version-control", "page_slug": "/learn/..."}

    Response Format (Success - 200, no data):
        {"page_id": null, "page_slug": null}

    Response Format (Error - 401):
        {"error": "Authentication failed"}

    Response Format (Error - 500):
        {"error": "Service temporarily unavailable"}

    Validates: Requirements 1.1, 1.2, 1.4
    """
    try:
        # Extract and validate JWT from cookie
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

        # Get last active lesson from DynamoDB
        try:
            last_active = get_last_active(user_id)
        except Exception:
            return error_response(500, "Service temporarily unavailable")

        return json_response(200, last_active)

    except Exception:
        return error_response(500, "Service temporarily unavailable")
