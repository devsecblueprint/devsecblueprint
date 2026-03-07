"""
Progress retrieval endpoint handlers.

This module provides handlers for GET endpoints to retrieve user progress data:
- GET /progress: Get all completed content for a user
- GET /progress/stats: Get aggregated statistics
- GET /progress/recent: Get recently completed activities
- GET /progress/badges: Get user badges with earned status
"""

import json
from typing import Dict, Any
from jose import JWTError
from auth.jwt_utils import extract_token_from_cookie, validate_jwt
from services.progress_service import (
    get_user_progress,
    get_user_stats,
    get_recent_activities,
)
from services.badge_service import calculate_user_badges
from utils.responses import json_response, error_response


def handle_get_progress(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET /progress endpoint to retrieve user's completed content.

    Args:
        headers: Request headers (lowercase keys) from API Gateway event

    Returns:
        dict: API Gateway response with list of completed content

    Response Format (Success):
        {
            "statusCode": 200,
            "headers": {...CORS headers...},
            "body": '{"progress": [{"content_id": "...", "completed_at": "..."}]}'
        }

    Response Format (Error - 401):
        {
            "statusCode": 401,
            "headers": {...CORS headers...},
            "body": '{"error": "Authentication failed"}'
        }
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

        # Get user progress from DynamoDB
        try:
            progress_items = get_user_progress(user_id)
        except Exception:
            return error_response(500, "Service temporarily unavailable")

        # Return progress data
        return json_response(200, {"progress": progress_items})

    except Exception:
        return error_response(500, "Service temporarily unavailable")


def handle_get_stats(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET /progress/stats endpoint to retrieve aggregated statistics.

    Args:
        headers: Request headers (lowercase keys) from API Gateway event

    Returns:
        dict: API Gateway response with user statistics

    Response Format (Success):
        {
            "statusCode": 200,
            "headers": {...CORS headers...},
            "body": '{
                "current_streak": 5,
                "longest_streak": 10,
                "overall_completion": 25,
                "completed_count": 15
            }'
        }
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

        # Get user statistics
        try:
            stats = get_user_stats(user_id)
        except Exception:
            return error_response(500, "Service temporarily unavailable")

        # Return statistics
        return json_response(200, stats)

    except Exception:
        return error_response(500, "Service temporarily unavailable")


def handle_get_recent(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET /progress/recent endpoint to retrieve recent activities.

    Args:
        headers: Request headers (lowercase keys) from API Gateway event

    Returns:
        dict: API Gateway response with recent activities

    Response Format (Success):
        {
            "statusCode": 200,
            "headers": {...CORS headers...},
            "body": '{
                "recent": [
                    {"content_id": "...", "completed_at": "..."},
                    ...
                ]
            }'
        }
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

        # Get user progress and extract recent activities
        try:
            progress_items = get_user_progress(user_id)
            recent = get_recent_activities(progress_items, limit=10)
        except Exception:
            return error_response(500, "Service temporarily unavailable")

        # Return recent activities
        return json_response(200, {"recent": recent})

    except Exception:
        return error_response(500, "Service temporarily unavailable")


def handle_get_badges(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET /progress/badges endpoint to retrieve user badges.

    Args:
        headers: Request headers (lowercase keys) from API Gateway event

    Returns:
        dict: API Gateway response with badges list

    Response Format (Success):
        {
            "statusCode": 200,
            "headers": {...CORS headers...},
            "body": '{
                "badges": [
                    {
                        "id": "b1",
                        "title": "First Steps",
                        "description": "Complete your first lesson",
                        "icon": "🎯",
                        "earned": true,
                        "earned_date": "2024-01-15T10:30:00Z"
                    },
                    ...
                ]
            }'
        }
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

        # Get user progress and stats
        try:
            progress_items = get_user_progress(user_id)
            stats = get_user_stats(user_id)
            # Add user_id to stats for badge calculation
            stats["user_id"] = user_id
            badges = calculate_user_badges(stats, progress_items)
        except Exception:
            return error_response(500, "Service temporarily unavailable")

        # Return badges
        return json_response(200, {"badges": badges})

    except Exception:
        return error_response(500, "Service temporarily unavailable")
