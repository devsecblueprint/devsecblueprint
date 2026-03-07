"""
Admin handler for content registry status retrieval.

Provides endpoint to retrieve registry health and cache status.
"""

import logging
import os
import time
import traceback
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from botocore.exceptions import ClientError, BotoCoreError
from auth.admin import require_admin
from utils.responses import json_response, error_response
from services.content_registry import get_registry_service, SchemaVersionError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# In-memory cache for registry status (60-second TTL)
_registry_status_cache = {"data": None, "timestamp": None, "ttl_seconds": 60}


@require_admin
def handle_get_registry_status(
    headers: Dict[str, str], username: str, user_id: str
) -> Dict[str, Any]:
    """
    Handle GET /admin/registry-status endpoint.

    Retrieves content registry health and cache status information.
    Queries the ContentRegistryService to get registry metadata including
    schema version, last updated timestamp, total entries, and cache status.

    Implements 60-second in-memory cache to reduce S3 API calls and improve
    response times. Cache applies to both healthy and unavailable states.

    Args:
        headers: Request headers (provided by decorator)
        username: Authenticated admin username (provided by decorator)
        user_id: Authenticated user ID (provided by decorator)

    Returns:
        dict: API Gateway response with registry status or error

    Response Format (200 OK - Healthy):
        {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "total_entries": 156,
            "cache_status": "loaded",
            "cache_ttl_seconds": 300,
            "cache_expires_in_seconds": 180,
            "s3_bucket": "devsec-blueprint-content",
            "s3_key": "content-registry/latest.json",
            "status": "healthy"
        }

    Response Format (200 OK - Unavailable):
        {
            "schema_version": null,
            "last_updated": null,
            "total_entries": 0,
            "cache_status": "error",
            "cache_ttl_seconds": null,
            "cache_expires_in_seconds": null,
            "s3_bucket": "devsec-blueprint-content",
            "s3_key": "content-registry/latest.json",
            "status": "unavailable",
            "error": "Failed to load registry from S3: NoSuchKey"
        }

    Error Responses:
        - 503: Content registry service unavailable

    Validates: Requirements 2.1, 2.2, 2.3, 2.5, 2.6, 11.2
    """
    try:
        # Check cache first
        now = time.time()
        cache = _registry_status_cache

        if cache["data"] and cache["timestamp"]:
            age = now - cache["timestamp"]
            if age < cache["ttl_seconds"]:
                logger.info(
                    f"Returning cached registry status for admin {username} (age: {age:.1f}s)"
                )
                return json_response(200, cache["data"])

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

        # Build status response
        try:
            status_data = build_registry_status(registry_service)

            # Update cache
            cache["data"] = status_data
            cache["timestamp"] = now

            logger.info(
                f"Retrieved registry status for admin {username}: {status_data['status']}"
            )

            return json_response(200, status_data)

        except Exception as e:
            # If we can't build status, registry is unavailable
            logger.error(f"Failed to build registry status: {str(e)}")

            # Return unavailable status with error details
            unavailable_status = {
                "schema_version": None,
                "last_updated": None,
                "total_entries": 0,
                "cache_status": "error",
                "cache_ttl_seconds": None,
                "cache_expires_in_seconds": None,
                "s3_bucket": s3_bucket,
                "s3_key": "content-registry/latest.json",
                "status": "unavailable",
                "error": f"Failed to load registry: {type(e).__name__}",
            }

            # Cache unavailable status too (to avoid hammering S3 on errors)
            cache["data"] = unavailable_status
            cache["timestamp"] = now

            return json_response(200, unavailable_status)

    except Exception as e:
        log_error(
            endpoint="handle_get_registry_status",
            error_type=type(e).__name__,
            error_message=str(e),
            username=username if "username" in locals() else None,
            user_id=user_id if "user_id" in locals() else None,
        )
        return error_response(500, "Internal server error")


def build_registry_status(registry_service) -> Dict[str, Any]:
    """
    Build registry status response from ContentRegistryService.

    Args:
        registry_service: ContentRegistryService instance

    Returns:
        dict: Registry status with all required fields

    Raises:
        Exception: If registry is not loaded or accessible

    Validates: Requirements 2.2, 2.3, 2.5, 2.6
    """
    # Check if registry is loaded
    if registry_service._registry is None:
        raise ValueError("Registry not loaded")

    # Extract registry metadata
    schema_version = registry_service._registry.get("schema_version")
    last_updated = registry_service._registry.get("last_updated")
    entries = registry_service._registry.get("entries", {})
    total_entries = len(entries)

    # Calculate cache expiry
    cache_ttl_seconds = registry_service.cache_ttl_seconds
    cache_expires_in_seconds = None

    if cache_ttl_seconds is not None and registry_service._last_loaded_at is not None:
        elapsed = time.time() - registry_service._last_loaded_at
        cache_expires_in_seconds = max(0, int(cache_ttl_seconds - elapsed))

    # Build status response
    status = {
        "schema_version": schema_version,
        "last_updated": last_updated,
        "total_entries": total_entries,
        "cache_status": "loaded",
        "cache_ttl_seconds": cache_ttl_seconds,
        "cache_expires_in_seconds": cache_expires_in_seconds,
        "s3_bucket": registry_service.s3_bucket,
        "s3_key": registry_service.s3_key,
        "status": "healthy",
    }

    return status


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


def clear_cache() -> None:
    """
    Clear the registry status cache.

    Useful for testing and manual cache invalidation.
    """
    global _registry_status_cache
    _registry_status_cache["data"] = None
    _registry_status_cache["timestamp"] = None
