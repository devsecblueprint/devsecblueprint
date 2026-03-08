"""
AWS Lambda handler with manual routing for DSB V3 Backend Phase 1.

This module provides the main entry point for AWS Lambda, implementing manual
routing using if/elif structure to dispatch requests to appropriate handlers.
Supports GitHub OAuth, user verification, and progress tracking endpoints.
"""

import logging
import os
import re
from typing import Dict, Any
from auth.github import start_oauth, handle_callback
from auth.jwt_utils import verify_user
from handlers.progress import handle_progress
from handlers.progress_get import (
    handle_get_progress,
    handle_get_stats,
    handle_get_recent,
    handle_get_badges,
)
from handlers.capstone import handle_get_capstone_submission
from handlers.progress_reset import handle_reset_progress
from handlers.analytics import handle_get_analytics
from handlers.user import handle_get_user_profile
from handlers.user_delete import handle_delete_account
from handlers.quiz import handle_quiz_submit
from handlers.walkthroughs import (
    handle_get_progress_for_walkthrough,
    handle_update_progress as handle_walkthrough_progress,
)
from handlers.admin_submissions import handle_get_submissions
from handlers.admin_registry import handle_get_registry_status
from handlers.admin_health import handle_get_module_health
from handlers.admin_user_search import handle_user_search
from handlers.admin_walkthrough_stats import handle_get_walkthrough_statistics
from handlers.admin_export import (
    handle_export_users,
    handle_export_capstone_submissions,
)
from handlers.email import handle_send_success_story
from utils.responses import error_response, json_response, delete_cookie

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def sanitize_error_message(error: Exception) -> str:
    """
    Sanitize error message to remove sensitive information.

    This function removes potential sensitive data from error messages before logging,
    including:
    - Secret values and tokens
    - API keys and credentials
    - File paths that might reveal internal structure
    - Environment variable values

    Args:
        error: The exception to sanitize

    Returns:
        str: Sanitized error message safe for logging

    Validates: Requirement 8.5
    """
    error_msg = str(error)

    # Remove potential tokens and secrets (anything that looks like a token)
    error_msg = re.sub(r"[A-Za-z0-9_-]{20,}", "[REDACTED_TOKEN]", error_msg)

    # Remove potential API keys
    error_msg = re.sub(
        r'(api[_-]?key|secret|token|password)["\']?\s*[:=]\s*["\']?[^\s"\']+',
        r"\1=[REDACTED]",
        error_msg,
        flags=re.IGNORECASE,
    )

    # Remove file paths (both Unix and Windows style)
    error_msg = re.sub(
        r"(/[a-zA-Z0-9_\-./]+|[A-Z]:\\[a-zA-Z0-9_\-\\]+)", "[REDACTED_PATH]", error_msg
    )

    # Remove potential environment variable values
    error_msg = re.sub(
        r'(env|ENV|environment)["\']?\s*[:=]\s*["\']?[^\s"\']+',
        r"\1=[REDACTED]",
        error_msg,
        flags=re.IGNORECASE,
    )

    return error_msg


def handle_logout() -> Dict[str, Any]:
    """
    Handle user logout by deleting the JWT cookie.

    Returns:
        dict: API Gateway response with success message and Set-Cookie header
        to delete the dsb_token cookie.

    Note: The cookie deletion must match ALL attributes used when setting the cookie,
    including Domain, Path, Secure, and SameSite. The cookie is set by the frontend
    with Domain=.devsecblueprint.com, so we must delete it with the same domain.
    """
    # Get the frontend origin for CORS
    frontend_origin = os.environ.get(
        "FRONTEND_ORIGIN", "https://staging.devsecblueprint.com"
    )

    # Create response with cookie deletion
    # CRITICAL: Must match all attributes from when cookie was set:
    # - Domain=.devsecblueprint.com (set by frontend)
    # - Path=/
    # - Secure
    # - SameSite=None
    response = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": frontend_origin,
            "Access-Control-Allow-Credentials": "true",
            # Delete the cookie by setting Max-Age=0 with matching attributes
            "Set-Cookie": "dsb_token=; Path=/; Secure; SameSite=None; Domain=.devsecblueprint.com; Max-Age=0",
        },
        "body": '{"message": "Logged out successfully"}',
    }

    return response


def main(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function with dictionary-based routing.

    This is the main entry point for all HTTP requests. It extracts the HTTP method
    and path from the API Gateway event, routes to the appropriate handler using
    a routing dictionary, and returns properly formatted responses.

    Args:
        event: API Gateway HTTP API event with keys:
            - requestContext.http.method: HTTP method (GET, PUT, etc.)
            - requestContext.http.path: Request path (/auth/github/start, etc.)
            - headers: Request headers (lowercase keys)
            - queryStringParameters: Query parameters (dict or None)
            - body: Request body (JSON string or None)
        context: Lambda context object (not used)

    Returns:
        dict: API Gateway response with keys:
            - statusCode: HTTP status code
            - headers: Response headers (including CORS)
            - body: Response body (JSON string)

    Supported Routes:
        - GET /auth/github/start: Initiate GitHub OAuth flow
        - GET /auth/github/callback: Handle GitHub OAuth callback
        - GET /me: Verify user authentication
        - POST /logout: Logout user
        - PUT /progress: Save user progress
        - GET /progress: Get all user progress
        - GET /progress/stats: Get aggregated statistics
        - GET /progress/recent: Get recent activities
        - GET /progress/badges: Get user badges
        - DELETE /progress/reset: Reset all progress (admin only)
        - GET /admin/analytics: Get system analytics (admin only)
        - GET /user/profile: Get user profile

    Error Handling:
        - Returns 404 for unknown routes
        - Returns 500 for unexpected exceptions
        - All errors include CORS headers and generic messages

    Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 8.1, 8.2, 8.3
    """
    try:
        # Extract HTTP method and path from API Gateway event (Requirement 5.1)
        # Support both payload format 1.0 and 2.0
        method = event.get("requestContext", {}).get("http", {}).get(
            "method", ""
        ) or event.get("httpMethod", "")
        path = event.get("requestContext", {}).get("http", {}).get(
            "path", ""
        ) or event.get("path", "")

        # Log incoming request for debugging
        logger.info(f"Raw event keys: {list(event.keys())}")
        logger.info(f"Request context: {event.get('requestContext', {})}")
        logger.info(f"Incoming request: method={method}, path={path}")

        # Extract headers (API Gateway normalizes to lowercase)
        headers = event.get("headers", {})

        # Log all headers for debugging
        logger.info(f"All headers: {list(headers.keys())}")
        logger.info(f"Cookie header present: {'cookie' in headers}")

        # Extract query parameters
        query_params = event.get("queryStringParameters") or {}

        # Extract body
        body = event.get("body", "")

        # Handle OPTIONS requests for CORS preflight
        if method == "OPTIONS":
            frontend_origin = os.environ.get(
                "FRONTEND_ORIGIN", "https://staging.devsecblueprint.com"
            )
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": frontend_origin,
                    "Access-Control-Allow-Methods": "GET, PUT, POST, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "300",
                },
                "body": "",
            }

        # Define routing table: (method, path) -> handler function
        routes = {
            ("GET", "/auth/github/start"): lambda: start_oauth(),
            ("GET", "/auth/github/callback"): lambda: (
                handle_callback(query_params.get("code"))
                if query_params.get("code")
                else error_response(400, "Invalid request")
            ),
            ("GET", "/me"): lambda: verify_user(headers),
            ("POST", "/logout"): lambda: handle_logout(),
            ("PUT", "/progress"): lambda: handle_progress(headers, body),
            ("GET", "/progress"): lambda: handle_get_progress(headers),
            ("GET", "/progress/stats"): lambda: handle_get_stats(headers),
            ("GET", "/progress/recent"): lambda: handle_get_recent(headers),
            ("GET", "/progress/badges"): lambda: handle_get_badges(headers),
            ("DELETE", "/progress/reset"): lambda: handle_reset_progress(headers),
            ("GET", "/admin/analytics"): lambda: handle_get_analytics(headers),
            ("GET", "/admin/submissions"): lambda: handle_get_submissions(
                headers, query_params=query_params
            ),
            ("GET", "/admin/registry-status"): lambda: handle_get_registry_status(
                headers
            ),
            ("GET", "/admin/module-health"): lambda: handle_get_module_health(headers),
            (
                "GET",
                "/admin/walkthrough-statistics",
            ): lambda: handle_get_walkthrough_statistics(headers),
            ("GET", "/admin/users/search"): lambda: handle_user_search(
                headers, query_params=query_params
            ),
            ("GET", "/admin/export/users"): lambda: handle_export_users(headers),
            (
                "GET",
                "/admin/export/capstone-submissions",
            ): lambda: handle_export_capstone_submissions(headers),
            ("GET", "/user/profile"): lambda: handle_get_user_profile(headers),
            ("DELETE", "/user/account"): lambda: handle_delete_account(headers),
            ("POST", "/quiz/submit"): lambda: handle_quiz_submit(headers, body),
            ("POST", "/api/email/success-story"): lambda: handle_send_success_story(
                headers, body
            ),
        }

        # Look up route in routing table
        route_key = (method, path)
        logger.info(f"Looking up route: {route_key}")
        logger.info(f"Available routes: {list(routes.keys())}")
        handler = routes.get(route_key)

        if handler:
            return handler()

        # Check for dynamic walkthrough progress routes with path parameters
        # Pattern: GET /api/walkthroughs/{id}/progress - Get progress for a walkthrough
        # Pattern: POST /api/walkthroughs/{id}/progress - Update progress for a walkthrough
        walkthrough_progress_match = re.match(
            r"^/api/walkthroughs/([^/]+)/progress$", path
        )
        if walkthrough_progress_match:
            walkthrough_id = walkthrough_progress_match.group(1)
            if method == "GET":
                return handle_get_progress_for_walkthrough(headers, walkthrough_id)
            elif method == "POST":
                return handle_walkthrough_progress(headers, walkthrough_id, body)

        # Check for capstone submission route with path parameter
        # Pattern: GET /progress/capstone/{content_id} - Get capstone submission
        capstone_match = re.match(r"^/progress/capstone/([^/]+)$", path)
        if capstone_match and method == "GET":
            content_id = capstone_match.group(1)
            return handle_get_capstone_submission(headers, content_id)

        # Unknown route (Requirement 5.6)
        return error_response(404, "Not found")

    except Exception as e:
        # Global exception handler (Requirement 8.1)
        # Catch all unhandled exceptions and return generic error
        # Don't expose stack traces or sensitive information (Requirements 8.2, 8.3)

        # Log error internally with sanitization (Requirement 8.5)
        sanitized_msg = sanitize_error_message(e)
        logger.error(
            f"Unhandled exception in lambda_handler: {type(e).__name__}: {sanitized_msg}"
        )

        # Return generic error response without sensitive details
        return error_response(500, "Internal server error")
