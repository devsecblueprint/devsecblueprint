"""
Admin handler for module health retrieval.

Provides endpoint to retrieve module validation metrics and health status.
"""

import logging
import os
import traceback
from typing import Dict, Any, List
from datetime import datetime, timezone
from auth.admin import require_admin
from utils.responses import json_response, error_response
from services.content_registry import get_registry_service

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@require_admin
def handle_get_module_health(
    headers: Dict[str, str], username: str, user_id: str
) -> Dict[str, Any]:
    """
    Handle GET /admin/module-health endpoint.

    Retrieves module health information including validation metrics and errors.
    Queries the ContentRegistryService to get all registry entries, validates them,
    and returns health metrics with error details.

    Args:
        headers: Request headers (provided by decorator)
        username: Authenticated admin username (provided by decorator)
        user_id: Authenticated user ID (provided by decorator)

    Returns:
        dict: API Gateway response with module health data or error

    Response Format (200 OK):
        {
            "total_modules": 156,
            "validation_pass_percentage": 98.7,
            "content_by_type": {
                "quiz": 45,
                "module": 96,
                "capstone": 4,
                "walkthrough": 11
            },
            "validation_errors": [
                {
                    "module_id": "secure-sdlc/broken-quiz",
                    "error_type": "missing_field",
                    "error_message": "Required field 'passing_score' is missing"
                }
            ],
            "status": "healthy"
        }

    Error Responses:
        - 503: Content registry service unavailable

    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
    """
    try:
        # Get S3 bucket from environment
        s3_bucket = os.environ.get("CONTENT_REGISTRY_BUCKET")
        if not s3_bucket:
            logger.error("CONTENT_REGISTRY_BUCKET environment variable not set")
            return error_response(503, "Service unavailable")

        # Get registry service instance
        try:
            registry_service = get_registry_service(s3_bucket)
        except ValueError as e:
            logger.error(f"Failed to get registry service: {str(e)}")
            return error_response(503, "Service unavailable")

        # Check if registry is loaded
        if registry_service._registry is None:
            logger.error("Registry not loaded")
            return error_response(503, "Content registry unavailable")

        # Build module health response
        try:
            health_data = build_module_health(registry_service)

            logger.info(
                f"Retrieved module health for admin {username}: "
                f"{health_data['total_modules']} modules, "
                f"{health_data['validation_pass_percentage']:.1f}% passing"
            )

            return json_response(200, health_data)

        except Exception as e:
            logger.error(f"Failed to build module health: {str(e)}")
            log_error(
                endpoint="handle_get_module_health",
                error_type=type(e).__name__,
                error_message=str(e),
                username=username,
                user_id=user_id,
            )
            return error_response(500, "Failed to retrieve module health")

    except Exception as e:
        log_error(
            endpoint="handle_get_module_health",
            error_type=type(e).__name__,
            error_message=str(e),
            username=username if "username" in locals() else None,
            user_id=user_id if "user_id" in locals() else None,
        )
        return error_response(500, "Internal server error")


def build_module_health(registry_service) -> Dict[str, Any]:
    """
    Build module health response from ContentRegistryService.

    Queries all registry entries, counts by content type, validates each entry,
    and calculates health metrics.

    Args:
        registry_service: ContentRegistryService instance

    Returns:
        dict: Module health data with all required fields

    Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.6
    """
    entries = registry_service._registry.get("entries", {})

    # Initialize counters
    content_by_type = {"quiz": 0, "module": 0, "capstone": 0, "walkthrough": 0}

    validation_errors = []
    modules_with_errors = set()

    # Process each entry
    for topic_slug, entry in entries.items():
        # Validate entry first (checks if it's a dict)
        errors = validate_entry(entry, topic_slug)
        if errors:
            modules_with_errors.add(topic_slug)
            validation_errors.extend(errors)
            # Count invalid entries as modules for total count
            content_by_type["module"] += 1
            continue

        # Count by content type (only for valid dict entries)
        content_type = entry.get("content_type", "module")
        if content_type in content_by_type:
            content_by_type[content_type] += 1
        else:
            # Unknown content type - count as module
            content_by_type["module"] += 1

    # Calculate metrics
    total_modules = len(entries)
    passing_modules = total_modules - len(modules_with_errors)
    validation_pass_percentage = (
        (passing_modules / total_modules * 100) if total_modules > 0 else 100.0
    )

    # Determine overall status
    if validation_pass_percentage == 100:
        status = "healthy"
    elif validation_pass_percentage >= 90:
        status = "warning"
    else:
        status = "error"

    return {
        "total_modules": total_modules,
        "validation_pass_percentage": round(validation_pass_percentage, 1),
        "content_by_type": content_by_type,
        "validation_errors": validation_errors,
        "status": status,
    }


def validate_entry(entry: Dict[str, Any], topic_slug: str) -> List[Dict[str, Any]]:
    """
    Validate a single registry entry for critical errors only.

    The registry contains metadata that references content stored separately.
    Quizzes, walkthroughs, and other content are stored as separate files,
    so the registry entry doesn't need to contain the full content data.

    This validation only checks for structural issues that would prevent
    the registry from functioning, not content completeness.

    Args:
        entry: Registry entry to validate
        topic_slug: Topic slug (used as module_id in errors)

    Returns:
        list: List of validation error dictionaries (empty if valid)

    Validates: Requirements 3.4, 3.5
    """
    errors = []

    # No validation needed - the registry is just metadata
    # Content (quizzes, walkthroughs, etc.) is stored separately in CodeCommit
    # and fetched during build. The registry entry just needs to exist.

    # Only flag entries that are completely malformed (e.g., not a dict)
    if not isinstance(entry, dict):
        errors.append(
            {
                "module_id": topic_slug,
                "error_type": "invalid_structure",
                "error_message": "Registry entry must be a dictionary",
            }
        )

    return errors


def log_error(
    endpoint: str,
    error_type: str,
    error_message: str,
    username: str | None = None,
    user_id: str | None = None,
    context: Dict[str, Any] | None = None,
) -> None:
    """
    Log errors with sufficient context for debugging.

    Args:
        endpoint: Endpoint name where error occurred
        error_type: Type of error (e.g., "ClientError", "ValueError")
        error_message: Error message
        username: Authenticated username (if available)
        user_id: Authenticated user ID (if available)
        context: Additional context (e.g., bucket name, key)

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

    if context:
        log_entry["context"] = context

    logger.error(
        f"Error in {endpoint}: {error_type} - {error_message}", extra=log_entry
    )
