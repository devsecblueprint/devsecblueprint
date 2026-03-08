"""
Admin handler for walkthrough statistics retrieval.

Provides endpoint to retrieve aggregate walkthrough statistics across all users.
"""

import logging
import traceback
from typing import Dict, Any
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from auth.admin import require_admin
from utils.responses import json_response, error_response
from services import progress_service

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@require_admin
def handle_get_walkthrough_statistics(
    headers: Dict[str, str],
    username: str,
    user_id: str,
) -> Dict[str, Any]:
    """
    Handle GET /admin/walkthrough-statistics endpoint.

    Retrieves aggregate walkthrough statistics across all users including:
    - Total completed walkthroughs
    - Total in-progress walkthroughs
    - Most popular walkthrough (by combined count)

    Args:
        headers: Request headers (provided by decorator)
        username: Authenticated admin username (provided by decorator)
        user_id: Authenticated user ID (provided by decorator)

    Returns:
        dict: API Gateway response with statistics data or error

    Response Format (200 OK):
        {
            "completed_count": int,
            "in_progress_count": int,
            "most_popular_walkthrough": str | null
        }

    Error Responses:
        - 403: Non-admin user (handled by decorator)
        - 500: Unexpected error
        - 503: DynamoDB table unavailable

    Validates: Requirements 4.1, 4.5, 4.6, 6.1, 6.2
    """
    try:
        # Call progress service to get statistics
        statistics = progress_service.get_walkthrough_statistics()

        logger.info(
            f"Retrieved walkthrough statistics for admin {username}: "
            f"completed={statistics['completed_count']}, "
            f"in_progress={statistics['in_progress_count']}, "
            f"most_popular={statistics['most_popular_walkthrough']}"
        )

        return json_response(200, statistics)

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        log_error(
            endpoint="handle_get_walkthrough_statistics",
            error_type="DynamoDB ClientError",
            error_code=error_code,
            error_message=str(e),
            username=username,
            user_id=user_id,
        )

        if error_code in ["ResourceNotFoundException", "TableNotFoundException"]:
            return error_response(503, "Service unavailable")
        else:
            return error_response(500, "Failed to retrieve statistics")

    except Exception as e:
        log_error(
            endpoint="handle_get_walkthrough_statistics",
            error_type=type(e).__name__,
            error_message=str(e),
            username=username if "username" in locals() else None,
            user_id=user_id if "user_id" in locals() else None,
        )
        return error_response(500, "Internal server error")


def log_error(
    endpoint: str,
    error_type: str,
    error_message: str,
    username: str | None = None,
    user_id: str | None = None,
    error_code: str | None = None,
    context: Dict[str, Any] | None = None,
) -> None:
    """
    Log errors with structured data for CloudWatch.

    Args:
        endpoint: Endpoint name where error occurred
        error_type: Type of error (e.g., "DynamoDB ClientError", "ValueError")
        error_message: Error message
        username: Authenticated username (if available)
        user_id: Authenticated user ID (if available)
        error_code: Error code (e.g., DynamoDB error code)
        context: Additional context (e.g., query parameters, table name)

    Validates: Requirements 4.6
    """
    log_entry = {
        "event": "admin_endpoint_error",
        "endpoint": endpoint,
        "error_type": error_type,
        "error_message": error_message,
        "username": username or "unknown",
        "user_id": user_id or "unknown",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stack_trace": traceback.format_exc(),
    }

    if error_code:
        log_entry["error_code"] = error_code

    if context:
        log_entry["context"] = context

    logger.error(
        f"Error in {endpoint}: {error_type} - {error_message}", extra=log_entry
    )
