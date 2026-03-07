"""
Capstone submission endpoint handler.

This module provides the handler for the GET /progress/capstone/{content_id} endpoint,
which allows authenticated users to retrieve their capstone submission data.
"""

import logging
from typing import Dict, Any
from jose import JWTError
from auth.jwt_utils import extract_token_from_cookie, validate_jwt
from services.dynamo import get_capstone_submission
from utils.responses import json_response, error_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handle_get_capstone_submission(
    headers: Dict[str, str], content_id: str
) -> Dict[str, Any]:
    """
    Handle GET /progress/capstone/{content_id} endpoint.

    Retrieves the capstone submission for a specific content_id for the authenticated user.

    Args:
        headers: Request headers containing JWT cookie
        content_id: Capstone content identifier

    Returns:
        dict: API Gateway response with submission data or error

    Response Format (Success with submission):
        {
            "statusCode": 200,
            "headers": {...CORS headers...},
            "body": '{
                "repo_url": "...",
                "github_username": "...",
                "repo_name": "...",
                "submitted_at": "...",
                "updated_at": "..."
            }'
        }

    Response Format (Success without submission):
        {
            "statusCode": 200,
            "headers": {...CORS headers...},
            "body": '{
                "submission": null
            }'
        }

    Response Format (Error - 401):
        {
            "statusCode": 401,
            "headers": {...CORS headers...},
            "body": '{"error": "Authentication failed"}'
        }

    Response Format (Error - 500):
        {
            "statusCode": 500,
            "headers": {...CORS headers...},
            "body": '{"error": "Service temporarily unavailable"}'
        }
    """
    try:
        # Extract and validate JWT from cookie
        token = extract_token_from_cookie(headers)

        if not token:
            return error_response(401, "Authentication failed")

        # Validate JWT
        try:
            payload = validate_jwt(token)
        except JWTError:
            return error_response(401, "Authentication failed")

        # Extract user_id from JWT payload
        user_id = payload.get("sub")
        if not user_id:
            return error_response(401, "Authentication failed")

        # Get capstone submission from DynamoDB
        try:
            submission = get_capstone_submission(user_id, content_id)

            if submission:
                return json_response(200, submission)
            else:
                return json_response(200, {"submission": None})

        except Exception as e:
            logger.error(f"Error fetching capstone submission: {str(e)}")
            return error_response(500, "Service temporarily unavailable")

    except Exception as e:
        logger.error(f"Unexpected error in handle_get_capstone_submission: {str(e)}")
        return error_response(500, "Service temporarily unavailable")
