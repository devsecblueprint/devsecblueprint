"""
Walkthrough API endpoint handlers.

This module provides handlers for walkthrough-related API endpoints:
- GET /api/walkthroughs: List all walkthroughs with optional filtering
- GET /api/walkthroughs/[id]: Get a single walkthrough with README content
- POST /api/walkthroughs/[id]/progress: Update walkthrough progress

All endpoints require JWT authentication via cookies.

Requirements: 10.1, 10.2, 10.5, 10.6, 4.2, 8.2
"""

import json
import logging
from typing import Dict, Any
from jose import JWTError
from auth.jwt_utils import extract_token_from_cookie, validate_jwt
from services.walkthrough_service import (
    get_walkthroughs,
    get_walkthrough_by_id,
    load_readme,
    get_walkthrough_progress,
    update_walkthrough_progress,
)
from utils.responses import json_response, error_response, generate_etag

logger = logging.getLogger()


def handle_get_walkthroughs(
    headers: Dict[str, str], query_params: Dict[str, str]
) -> Dict[str, Any]:
    """
    Handle GET /api/walkthroughs endpoint.

    Returns all walkthroughs with optional filtering by difficulty, topics, and search query.
    Requires JWT authentication via cookies.

    Args:
        headers: Request headers (lowercase keys) from API Gateway event
        query_params: Query parameters with optional keys:
            - difficulty: Filter by difficulty level ("Beginner", "Intermediate", "Advanced")
            - topics: Comma-separated list of topic tags
            - search: Search query string

    Returns:
        dict: API Gateway response

    Response Format (Success):
        {
            "statusCode": 200,
            "headers": {...CORS headers...},
            "body": '{"walkthroughs": [...]}'
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

    Requirements: 10.1, 10.2, 10.3, 10.4
    """
    try:
        # Extract and validate JWT from cookie (Requirement 10.2)
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

        # Parse query parameters (Requirement 10.3)
        difficulty = query_params.get("difficulty")
        topics_str = query_params.get("topics")
        search = query_params.get("search")

        # Parse topics from comma-separated string
        topics = None
        if topics_str:
            topics = [t.strip() for t in topics_str.split(",") if t.strip()]

        # Get walkthroughs with filtering (Requirement 10.4)
        try:
            walkthroughs = get_walkthroughs(
                difficulty=difficulty, topics=topics, search=search
            )

            # Enrich with progress data for the authenticated user
            for walkthrough in walkthroughs:
                progress = get_walkthrough_progress(user_id, walkthrough["id"])
                walkthrough["progress"] = progress

        except Exception as e:
            logger.error(f"Error retrieving walkthroughs: {type(e).__name__}")
            return error_response(500, "Service temporarily unavailable")

        # Generate response body
        response_body = {"walkthroughs": walkthroughs}
        response_json = json.dumps(response_body)

        # Generate ETag from response content (Requirement 18.5)
        etag = generate_etag(response_json)

        # Return success response with caching headers (Requirement 10.1, 18.5)
        # Use private cache since response includes user-specific progress data
        # Cache for 5 minutes to balance freshness with performance
        return json_response(
            200,
            response_body,
            cache_control="private, max-age=300",  # 5 minutes
            etag=etag,
        )

    except Exception as e:
        # Catch any unexpected errors and return generic error
        logger.error(f"Unexpected error in handle_get_walkthroughs: {type(e).__name__}")
        return error_response(500, "Service temporarily unavailable")


def handle_get_walkthrough(
    headers: Dict[str, str], walkthrough_id: str
) -> Dict[str, Any]:
    """
    Handle GET /api/walkthroughs/[id] endpoint.

    Returns a single walkthrough with metadata, README content, and user progress.
    Requires JWT authentication via cookies.

    Args:
        headers: Request headers (lowercase keys) from API Gateway event
        walkthrough_id: Walkthrough identifier from path parameter

    Returns:
        dict: API Gateway response

    Response Format (Success):
        {
            "statusCode": 200,
            "headers": {...CORS headers...},
            "body": '{
                "id": "...",
                "title": "...",
                "description": "...",
                "difficulty": "...",
                "topics": [...],
                "estimatedTime": 90,
                "prerequisites": [...],
                "repository": "...",
                "readme": "...",
                "progress": {...}
            }'
        }

    Response Format (Error - 401):
        {
            "statusCode": 401,
            "headers": {...CORS headers...},
            "body": '{"error": "Authentication failed"}'
        }

    Response Format (Error - 404):
        {
            "statusCode": 404,
            "headers": {...CORS headers...},
            "body": '{"error": "Walkthrough not found"}'
        }

    Response Format (Error - 500):
        {
            "statusCode": 500,
            "headers": {...CORS headers...},
            "body": '{"error": "Service temporarily unavailable"}'
        }

    Requirements: 10.5, 10.6, 10.7, 8.4
    """
    try:
        # Extract and validate JWT from cookie (Requirement 10.6)
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

        # Get walkthrough metadata (Requirement 10.5)
        try:
            walkthrough = get_walkthrough_by_id(walkthrough_id)

            # Handle walkthrough not found (Requirement 10.7)
            if walkthrough is None:
                return error_response(404, "Walkthrough not found")

        except Exception as e:
            logger.error(
                f"Error retrieving walkthrough {walkthrough_id}: {type(e).__name__}"
            )
            return error_response(500, "Service temporarily unavailable")

        # Load README content (Requirement 8.4)
        try:
            readme_content = load_readme(walkthrough_id)
            walkthrough["readme"] = readme_content
        except FileNotFoundError:
            # README not found - return 404
            return error_response(404, "README not found")
        except ValueError:
            # Walkthrough not found (should not happen as we already checked)
            return error_response(404, "Walkthrough not found")
        except Exception as e:
            logger.error(
                f"Error loading README for {walkthrough_id}: {type(e).__name__}"
            )
            return error_response(500, "Service temporarily unavailable")

        # Get user progress for this walkthrough
        try:
            progress = get_walkthrough_progress(user_id, walkthrough_id)
            walkthrough["progress"] = progress
        except Exception as e:
            logger.error(
                f"Error retrieving progress for {walkthrough_id}: {type(e).__name__}"
            )
            # Continue without progress data rather than failing the entire request
            walkthrough["progress"] = {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
            }

        # Generate response JSON
        response_json = json.dumps(walkthrough)

        # Generate ETag from response content (Requirement 18.5)
        etag = generate_etag(response_json)

        # Return success response with caching headers (Requirement 18.5)
        # Use private cache since response includes user-specific progress data
        # Cache for 10 minutes since walkthrough content rarely changes
        return json_response(
            200,
            walkthrough,
            cache_control="private, max-age=600",  # 10 minutes
            etag=etag,
        )

    except Exception as e:
        # Catch any unexpected errors and return generic error
        logger.error(f"Unexpected error in handle_get_walkthrough: {type(e).__name__}")
        return error_response(500, "Service temporarily unavailable")


def handle_get_progress_for_walkthrough(
    headers: Dict[str, str], walkthrough_id: str
) -> Dict[str, Any]:
    """
    Handle GET /api/walkthroughs/[id]/progress endpoint.

    Returns user progress for a specific walkthrough.
    Requires JWT authentication via cookies.

    Args:
        headers: Request headers (lowercase keys) from API Gateway event
        walkthrough_id: Walkthrough identifier from path parameter

    Returns:
        dict: API Gateway response

    Response Format (Success):
        {
            "statusCode": 200,
            "headers": {...CORS headers...},
            "body": '{
                "progress": {
                    "status": "not_started" | "in_progress" | "completed",
                    "started_at": "ISO timestamp" | null,
                    "completed_at": "ISO timestamp" | null
                }
            }'
        }

    Response Format (Error - 401):
        {
            "statusCode": 401,
            "headers": {...CORS headers...},
            "body": '{"error": "Authentication failed"}'
        }

    Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6
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

        # Get progress for this walkthrough
        try:
            progress = get_walkthrough_progress(user_id, walkthrough_id)

            # Add short-lived cache for progress data (5 minutes)
            # Progress can change frequently, so we use a short cache duration
            return json_response(
                200,
                {"progress": progress},
                cache_control="private, max-age=300",  # 5 minutes
            )
        except Exception as e:
            logger.error(
                f"Error retrieving progress for {walkthrough_id}: {type(e).__name__}"
            )
            # Return not_started as default if error occurs
            return json_response(
                200,
                {
                    "progress": {
                        "status": "not_started",
                        "started_at": None,
                        "completed_at": None,
                    }
                },
            )

    except Exception as e:
        # Catch any unexpected errors and return generic error
        logger.error(
            f"Unexpected error in handle_get_progress_for_walkthrough: {type(e).__name__}"
        )
        return error_response(500, "Service temporarily unavailable")


def handle_update_progress(
    headers: Dict[str, str], walkthrough_id: str, body: str
) -> Dict[str, Any]:
    """
    Handle POST /api/walkthroughs/[id]/progress endpoint.

    Updates user progress for a walkthrough. Validates that status is either
    "in_progress" or "completed".
    Requires JWT authentication via cookies.

    Args:
        headers: Request headers (lowercase keys) from API Gateway event
        walkthrough_id: Walkthrough identifier from path parameter
        body: JSON request body with required field:
            - status: Progress status ("in_progress" or "completed")

    Returns:
        dict: API Gateway response

    Response Format (Success):
        {
            "statusCode": 200,
            "headers": {...CORS headers...},
            "body": '{"message": "Progress updated successfully"}'
        }

    Response Format (Error - 401):
        {
            "statusCode": 401,
            "headers": {...CORS headers...},
            "body": '{"error": "Authentication failed"}'
        }

    Response Format (Error - 400):
        {
            "statusCode": 400,
            "headers": {...CORS headers...},
            "body": '{"error": "Invalid request"}'
        }

    Response Format (Error - 500):
        {
            "statusCode": 500,
            "headers": {...CORS headers...},
            "body": '{"error": "Service temporarily unavailable"}'
        }

    Requirements: 10.6, 11.8
    """
    try:
        # Extract and validate JWT from cookie (Requirement 10.6)
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

        # Parse JSON body to extract status
        try:
            if not body:
                return error_response(400, "Invalid request")

            body_data = json.loads(body)
            status = body_data.get("status")

            # Validate status field is present
            if not status:
                return error_response(400, "Invalid request")

        except (json.JSONDecodeError, ValueError):
            # Invalid JSON body
            return error_response(400, "Invalid request")

        # Update progress with status validation (Requirement 11.8)
        try:
            update_walkthrough_progress(user_id, walkthrough_id, status)
        except ValueError as e:
            # Invalid status value
            logger.warning(f"Invalid status value: {status}")
            return error_response(400, "Invalid status value")
        except Exception as e:
            # Handle DynamoDB or other service errors
            logger.error(
                f"Error updating progress for {walkthrough_id}: {type(e).__name__}"
            )
            return error_response(500, "Service temporarily unavailable")

        # Return success response
        return json_response(200, {"message": "Progress updated successfully"})

    except Exception as e:
        # Catch any unexpected errors and return generic error
        logger.error(f"Unexpected error in handle_update_progress: {type(e).__name__}")
        return error_response(500, "Service temporarily unavailable")
