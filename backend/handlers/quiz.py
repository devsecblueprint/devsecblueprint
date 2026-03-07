"""
Quiz Handler Module

Thin route handler for quiz submission endpoint. Extracts request data,
validates authentication, and delegates business logic to quiz service.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 8.1, 8.3, 8.4, 8.5, 8.6, 8.8
"""

import json
import logging
from typing import Dict, Any
from auth.jwt_utils import extract_token_from_cookie, validate_jwt
from jose import JWTError
from services.quiz_service import (
    submit_quiz,
    QuizNotFoundError,
    RegistryUnavailableError,
)
from utils.responses import json_response, error_response

logger = logging.getLogger()


def handle_quiz_submit(headers: Dict[str, str], body: str) -> Dict[str, Any]:
    """
    Handle POST /quiz/submit endpoint.

    This handler:
    1. Extracts JWT token from cookie
    2. Validates JWT authentication
    3. Parses JSON request body
    4. Validates request format
    5. Delegates to quiz service for business logic
    6. Returns formatted response

    Args:
        headers: Request headers (lowercase keys) from API Gateway event
        body: JSON request body string

    Returns:
        dict: API Gateway response with quiz results or error

    Response Format (Success):
        {
            "statusCode": 200,
            "headers": {...CORS headers...},
            "body": JSON string with quiz results
        }

    Response Format (Error):
        {
            "statusCode": 400/401/404/500,
            "headers": {...CORS headers...},
            "body": '{"error": "Error message"}'
        }

    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 8.1, 8.3, 8.4, 8.5, 8.6, 8.8
    """
    try:
        # Extract JWT token from cookie (Requirement 1.5, 8.6)
        token = extract_token_from_cookie(headers)

        # Validate JWT (Requirement 1.5, 7.1)
        if not token:
            return error_response(401, "Authentication failed")

        try:
            payload = validate_jwt(token)
        except JWTError:
            return error_response(401, "Authentication failed")

        # Extract user_id from JWT payload (Requirement 8.6)
        user_id = payload.get("sub")
        if not user_id:
            return error_response(401, "Authentication failed")

        # Parse JSON body (Requirement 1.1, 8.6)
        try:
            request_data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            # Malformed JSON (Requirement 1.4, 7.2)
            return error_response(400, "Invalid request")

        # Extract module_id and answers (Requirement 1.1)
        module_id = request_data.get("module_id")
        answers = request_data.get("answers")

        # Validate required fields (Requirements 1.2, 1.3, 7.2)
        if not module_id or not answers:
            return error_response(400, "Invalid request")

        # Validate answers is a dict
        if not isinstance(answers, dict):
            return error_response(400, "Invalid request")

        # Call quiz service (Requirement 8.4)
        result = submit_quiz(user_id, module_id, answers)

        # Return success response (Requirements 6.1, 6.5, 6.10, 8.5)
        return json_response(200, result)

    except QuizNotFoundError as e:
        # Handle quiz not found errors (404) (Requirement 5.2)
        logger.warning(f"Quiz not found: {str(e)}")
        return error_response(404, str(e))

    except RegistryUnavailableError as e:
        # Handle registry unavailable errors (503) (Requirements 4.3, 4.5)
        logger.error(f"Registry unavailable: {str(e)}")
        return error_response(503, "Service temporarily unavailable")

    except ValueError as e:
        # Handle validation errors from quiz service (Requirement 7.2, 7.3)
        error_msg = str(e)
        logger.warning(f"Validation error: {error_msg}")
        return error_response(400, "Invalid request")

    except Exception as e:
        # Handle DynamoDB and unexpected exceptions (Requirements 7.4, 7.5, 7.6, 7.7)
        logger.error(f"Quiz submission error: {type(e).__name__}")

        # Check if it's a DynamoDB exception
        if "dynamodb" in str(type(e)).lower() or "boto" in str(type(e)).lower():
            return error_response(500, "Service temporarily unavailable")

        # Generic error for all other exceptions
        return error_response(500, "Internal server error")
