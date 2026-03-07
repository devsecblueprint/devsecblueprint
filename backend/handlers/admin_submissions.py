"""
Admin handler for capstone submissions retrieval.

Provides endpoint to retrieve all capstone submissions with pagination.
"""

import logging
import os
import traceback
from typing import Dict, Any
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
from auth.admin import require_admin
from utils.responses import json_response, error_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@require_admin
def handle_get_submissions(
    headers: Dict[str, str],
    username: str,
    user_id: str,
    query_params: Dict[str, str] = None,
) -> Dict[str, Any]:
    """
    Handle GET /admin/submissions endpoint.

    Retrieves all capstone submissions from DynamoDB with pagination support.
    Submissions are sorted by submitted_at timestamp in descending order.

    Args:
        headers: Request headers (provided by decorator)
        username: Authenticated admin username (provided by decorator)
        user_id: Authenticated user ID (provided by decorator)
        query_params: Query string parameters (page, page_size)

    Query Parameters:
        - page: Page number (default: 1, min: 1)
        - page_size: Items per page (default: 50, min: 1, max: 100)

    Returns:
        dict: API Gateway response with submissions data or error

    Response Format (200 OK):
        {
            "submissions": [
                {
                    "user_id": "github|12345678",
                    "github_username": "learner123",
                    "repo_url": "https://github.com/learner123/capstone-project",
                    "submitted_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z"
                }
            ],
            "total_count": 42,
            "page": 1,
            "page_size": 50,
            "total_pages": 1
        }

    Error Responses:
        - 400: Invalid pagination parameters
        - 500: DynamoDB query failure
        - 503: DynamoDB table unavailable

    Validates: Requirements 1.1, 1.2, 1.3, 1.6, 1.7
    """
    try:
        # Parse pagination parameters
        if query_params is None:
            query_params = {}

        try:
            page = int(query_params.get("page", "1"))
            page_size = int(query_params.get("page_size", "50"))
        except ValueError:
            logger.warning(f"Invalid pagination parameters: {query_params}")
            return error_response(400, "Invalid pagination parameters")

        # Validate pagination parameters
        if page < 1:
            return error_response(400, "Page must be >= 1")
        if page_size < 1 or page_size > 100:
            return error_response(400, "Page size must be between 1 and 100")

        # Get table name from environment
        table_name = os.environ.get("PROGRESS_TABLE")
        if not table_name:
            logger.error("PROGRESS_TABLE environment variable not set")
            return error_response(503, "Service unavailable")

        # Query DynamoDB for capstone submissions
        try:
            submissions, total_count = get_capstone_submissions(
                table_name, page, page_size
            )
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            log_error(
                endpoint="handle_get_submissions",
                error_type="DynamoDB ClientError",
                error_code=error_code,
                error_message=str(e),
                username=username,
                user_id=user_id,
                context={
                    "table_name": table_name,
                    "page": page,
                    "page_size": page_size,
                },
            )

            if error_code in ["ResourceNotFoundException", "TableNotFoundException"]:
                return error_response(503, "Service unavailable")
            else:
                return error_response(500, "Failed to retrieve submissions")

        # Calculate total pages
        total_pages = (
            (total_count + page_size - 1) // page_size if total_count > 0 else 0
        )

        # Format response
        response_data = {
            "submissions": submissions,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

        logger.info(
            f"Retrieved {len(submissions)} submissions (page {page}/{total_pages}) "
            f"for admin {username}"
        )

        return json_response(200, response_data)

    except Exception as e:
        log_error(
            endpoint="handle_get_submissions",
            error_type=type(e).__name__,
            error_message=str(e),
            username=username if "username" in locals() else None,
            user_id=user_id if "user_id" in locals() else None,
            context={"query_params": query_params},
        )
        return error_response(500, "Internal server error")


def get_capstone_submissions(
    table_name: str, page: int, page_size: int
) -> tuple[list, int]:
    """
    Scan DynamoDB for capstone submissions.

    Args:
        table_name: DynamoDB table name
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        tuple: (submissions_list, total_count)

    DynamoDB Query Strategy:
        1. Scan table with filter for SK starting with "CAPSTONE_SUBMISSION#"
        2. Sort by submitted_at descending (most recent first)
        3. Paginate in memory after sorting

    Note: This uses scan instead of GSI query because SK values vary by content_id.
    For better performance, a GSI on SK with BEGINS_WITH would be ideal, but
    DynamoDB GSI only supports exact match on hash key.

    Validates: Requirements 1.1, 1.2, 1.3, 1.7
    """
    dynamodb = boto3.client("dynamodb")

    submissions = []
    last_evaluated_key = None

    # Scan entire table for capstone submissions
    while True:
        scan_params = {
            "TableName": table_name,
            "FilterExpression": "begins_with(SK, :sk_prefix)",
            "ExpressionAttributeValues": {":sk_prefix": {"S": "CAPSTONE_SUBMISSION#"}},
        }

        if last_evaluated_key:
            scan_params["ExclusiveStartKey"] = last_evaluated_key

        response = dynamodb.scan(**scan_params)

        for item in response.get("Items", []):
            submissions.append(parse_submission_item(item))

        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break

    # Sort by submitted_at descending
    submissions.sort(key=lambda x: x["submitted_at"], reverse=True)

    # Calculate pagination
    total_count = len(submissions)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    return submissions[start_idx:end_idx], total_count


def parse_submission_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse DynamoDB item into submission object.

    Args:
        item: DynamoDB item with attribute types

    Returns:
        dict: Parsed submission with required fields including content_id

    Validates: Requirements 1.2
    """
    pk = item.get("PK", {}).get("S", "")
    user_id = pk.replace("USER#", "") if pk.startswith("USER#") else ""

    # Extract content_id from SK (format: "CAPSTONE_SUBMISSION#{content_id}")
    sk = item.get("SK", {}).get("S", "")
    content_id = (
        sk.replace("CAPSTONE_SUBMISSION#", "")
        if sk.startswith("CAPSTONE_SUBMISSION#")
        else ""
    )

    return {
        "user_id": user_id,
        "content_id": content_id,
        "github_username": item.get("github_username", {}).get("S", ""),
        "repo_url": item.get("repo_url", {}).get("S", ""),
        "submitted_at": item.get("submitted_at", {}).get("S", ""),
        "updated_at": item.get("updated_at", {}).get("S", ""),
    }


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
    Log errors with sufficient context for debugging.

    Args:
        endpoint: Endpoint name where error occurred
        error_type: Type of error (e.g., "DynamoDB ClientError", "ValueError")
        error_message: Error message
        username: Authenticated username (if available)
        user_id: Authenticated user ID (if available)
        error_code: Error code (e.g., DynamoDB error code)
        context: Additional context (e.g., query parameters, table name)

    Validates: Requirements 10.7
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
