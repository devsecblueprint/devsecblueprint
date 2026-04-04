"""
Testimonial handlers for learner submission, retrieval, and admin moderation.

Provides endpoints for:
- POST /api/testimonials — submit or update a testimonial
- GET /api/testimonials/me — get learner's own testimonial
- GET /api/testimonials/approved — get random approved testimonials (public)
- GET /admin/testimonials — list testimonials with optional status filter
- PUT /admin/testimonials/{user_id}/status — admin moderation actions
"""

import json
import logging
import random
import re
from datetime import datetime, timezone
from typing import Dict, Any

from auth.admin import require_admin
from auth.jwt_utils import extract_token_from_cookie, validate_jwt
from services.testimonial_service import (
    create_testimonial,
    get_testimonial,
    update_testimonial,
    delete_testimonial,
    get_testimonials_by_status,
    get_all_testimonials,
)
from utils.responses import json_response, error_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# LinkedIn URL pattern: https://(www.)linkedin.com/in/{slug}
LINKEDIN_URL_PATTERN = re.compile(
    r"^https://(www\.)?linkedin\.com/in/[A-Za-z0-9\-_%]+/?$"
)

MAX_QUOTE_CHARS = 350


def _authenticate(headers: Dict[str, str]) -> tuple:
    """
    Extract and validate JWT from cookie headers.

    Returns:
        tuple: (user_id, error_response) — one will be None.
    """
    token = extract_token_from_cookie(headers)
    if not token:
        return None, error_response(401, "Unauthorized")

    try:
        payload = validate_jwt(token)
    except Exception as e:
        logger.error(f"JWT validation failed: {type(e).__name__}")
        return None, error_response(401, "Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        return None, error_response(401, "Invalid token")

    return user_id, None


def _validate_display_name(display_name: str) -> str | None:
    """Return error message if display_name is invalid, else None."""
    if not display_name or not display_name.strip():
        return "display_name is required and cannot be empty"
    return None


def _validate_linkedin_url(linkedin_url: str) -> str | None:
    """Return error message if linkedin_url is provided but invalid, else None."""
    if not linkedin_url:
        return None
    if not LINKEDIN_URL_PATTERN.match(linkedin_url):
        return "linkedin_url must match https://(www.)linkedin.com/in/{profile_slug}"
    return None


def _validate_quote(quote: str) -> str | None:
    """Return error message if quote is invalid, else None."""
    if not quote or not quote.strip():
        return "quote is required and cannot be empty"
    if len(quote.strip()) > MAX_QUOTE_CHARS:
        return f"quote exceeds maximum of {MAX_QUOTE_CHARS} characters (has {len(quote.strip())})"
    return None


def _send_notification_email(display_name: str, linkedin_url: str, quote: str) -> None:
    """Fire-and-forget email notification to admin. Errors are logged, never raised."""
    try:
        from services.mailgun import send_testimonial_notification

        result = send_testimonial_notification(display_name, linkedin_url, quote)
        if not result:
            logger.warning(
                "Testimonial notification email was not sent (returned False)"
            )
    except Exception as e:
        logger.error(f"Failed to send testimonial notification email: {e}")


def handle_submit_testimonial(headers: Dict[str, str], body: str) -> Dict[str, Any]:
    """
    Handle POST /api/testimonials endpoint.

    Authenticated learners submit or update a testimonial. If the learner already
    has an approved testimonial, returns 409. If a pending testimonial exists, it
    is updated in place (200). Otherwise a new record is created (201).

    Args:
        headers: Request headers containing JWT cookie
        body: JSON request body with display_name, linkedin_url, quote

    Returns:
        dict: API Gateway response

    Validates: Requirements 7.1, 7.6, 7.8, 8.1, 8.2, 8.3, 8.4, 8.5,
               2.1, 11.1, 11.4, 11.5
    """
    try:
        # Authenticate
        user_id, auth_error = _authenticate(headers)
        if auth_error:
            return auth_error

        # Parse body
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            return error_response(400, "Invalid JSON in request body")

        display_name = data.get("display_name", "").strip()
        linkedin_url = data.get("linkedin_url", "").strip()
        quote = data.get("quote", "").strip()

        # Validate fields
        errors = []
        name_err = _validate_display_name(display_name)
        if name_err:
            errors.append(name_err)
        url_err = _validate_linkedin_url(linkedin_url)
        if url_err:
            errors.append(url_err)
        quote_err = _validate_quote(quote)
        if quote_err:
            errors.append(quote_err)

        if errors:
            return error_response(400, f"Validation error: {'; '.join(errors)}")

        # Check for existing testimonial
        existing = get_testimonial(user_id)

        if existing and existing.get("status") == "approved":
            logger.info(
                f"User {user_id} attempted to submit but already has approved testimonial"
            )
            return error_response(409, "Testimonial already exists")

        if existing and existing.get("status") == "pending":
            # Update existing pending testimonial
            updated = update_testimonial(
                user_id,
                {
                    "display_name": display_name,
                    "linkedin_url": linkedin_url or "",
                    "quote": quote,
                },
            )
            logger.info(f"Testimonial updated for user {user_id}")

            # Fire-and-forget email notification
            _send_notification_email(display_name, linkedin_url, quote)

            return json_response(
                200,
                {
                    "message": "Testimonial updated successfully",
                    "testimonial": updated,
                },
            )

        # Create new testimonial
        record = create_testimonial(user_id, display_name, linkedin_url or "", quote)
        logger.info(f"Testimonial created for user {user_id}")

        # Fire-and-forget email notification
        _send_notification_email(display_name, linkedin_url, quote)

        return json_response(
            201,
            {
                "message": "Testimonial submitted successfully",
                "testimonial": record,
            },
        )

    except Exception as e:
        logger.error(f"Error submitting testimonial: {e}")
        return error_response(500, "Internal server error")


def handle_get_my_testimonial(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET /api/testimonials/me endpoint.

    Returns the authenticated learner's testimonial record, or 404 if none exists.

    Args:
        headers: Request headers containing JWT cookie

    Returns:
        dict: API Gateway response with testimonial or 404

    Validates: Requirements 7.2, 7.6
    """
    try:
        user_id, auth_error = _authenticate(headers)
        if auth_error:
            return auth_error

        record = get_testimonial(user_id)
        if not record:
            return error_response(404, "No testimonial found")

        return json_response(200, {"testimonial": record})

    except Exception as e:
        logger.error(f"Error fetching testimonial for user: {e}")
        return error_response(500, "Internal server error")


def handle_get_approved_testimonials() -> Dict[str, Any]:
    """
    Handle GET /api/testimonials/approved endpoint (public).

    Queries the StatusIndex GSI for approved testimonials, filters out records
    with missing display_name or quote, randomly samples up to 10, and returns
    only public fields (no user_id).

    Returns:
        dict: API Gateway response with list of public testimonials

    Validates: Requirements 7.3, 7.9, 7.10, 2.2
    """
    try:
        all_approved = get_testimonials_by_status("approved")

        # Filter out records with missing display_name or quote
        valid = [
            t
            for t in all_approved
            if t.get("display_name", "").strip() and t.get("quote", "").strip()
        ]

        # Randomly sample up to 9
        sample_size = min(len(valid), 9)
        selected = random.sample(valid, sample_size) if valid else []

        # Return only public fields (no user_id)
        public_testimonials = [
            {
                "display_name": t["display_name"],
                "linkedin_url": t.get("linkedin_url", ""),
                "quote": t["quote"],
            }
            for t in selected
        ]

        return json_response(200, {"testimonials": public_testimonials})

    except Exception as e:
        logger.error(f"Error fetching approved testimonials: {e}")
        return error_response(500, "Internal server error")


@require_admin
def handle_admin_list_testimonials(
    headers: Dict[str, str],
    username: str,
    user_id: str,
    query_params: Dict[str, str] = None,
) -> Dict[str, Any]:
    """
    Handle GET /admin/testimonials endpoint.

    Returns all testimonials, optionally filtered by status query parameter.

    Args:
        headers: Request headers (provided by decorator)
        username: Authenticated admin username (provided by decorator)
        user_id: Authenticated admin user ID (provided by decorator)
        query_params: Optional query string parameters (?status=pending|approved)

    Returns:
        dict: API Gateway response with list of testimonials

    Validates: Requirements 7.4, 7.7, 5.10
    """
    try:
        if query_params is None:
            query_params = {}

        status_filter = query_params.get("status", "").strip().lower()

        if status_filter and status_filter in ("pending", "approved"):
            testimonials = get_testimonials_by_status(status_filter)
        elif status_filter:
            return error_response(
                400, "Invalid status filter. Use 'pending' or 'approved'"
            )
        else:
            testimonials = get_all_testimonials()

        logger.info(
            f"Admin {username} listed testimonials: count={len(testimonials)}, filter={status_filter or 'all'}"
        )

        return json_response(200, {"testimonials": testimonials})

    except Exception as e:
        logger.error(f"Error listing testimonials: {e}")
        return error_response(500, "Internal server error")


@require_admin
def handle_admin_update_status(
    headers: Dict[str, str],
    username: str,
    user_id: str,
    target_user_id: str = "",
    body: str = "",
) -> Dict[str, Any]:
    """
    Handle PUT /admin/testimonials/{user_id}/status endpoint.

    Performs moderation actions: approve, reject, or revoke a testimonial.
    Valid transitions:
        - pending → approved (approve)
        - pending → deleted (reject)
        - approved → pending (revoke)

    Args:
        headers: Request headers (provided by decorator)
        username: Authenticated admin username (provided by decorator)
        user_id: Authenticated admin user ID (provided by decorator)
        target_user_id: The learner's user_id extracted from the path
        body: JSON request body with action and optional note

    Returns:
        dict: API Gateway response

    Validates: Requirements 7.5, 7.7, 2.3, 2.4, 2.5, 2.6, 5.10
    """
    try:
        if not target_user_id:
            return error_response(400, "User ID is required")

        # Parse body
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            return error_response(400, "Invalid JSON in request body")

        action = data.get("action", "").strip().lower()
        note = data.get("note", "").strip()

        if action not in ("approve", "reject", "revoke"):
            return error_response(
                400, "Invalid action. Use 'approve', 'reject', or 'revoke'"
            )

        # Fetch existing testimonial
        existing = get_testimonial(target_user_id)
        if not existing:
            return error_response(404, "Testimonial not found")

        current_status = existing.get("status")
        now = datetime.now(timezone.utc).isoformat()

        # Validate state transitions
        if action == "approve":
            if current_status != "pending":
                return error_response(
                    400,
                    "Invalid status transition: can only approve pending testimonials",
                )
            updated = update_testimonial(
                target_user_id,
                {
                    "status": "approved",
                    "reviewed_at": now,
                    "reviewed_by": username or user_id,
                    "admin_note": note,
                },
            )
            logger.info(
                f"Admin {username} approved testimonial for user {target_user_id}"
            )
            return json_response(
                200,
                {
                    "message": "Testimonial approved",
                    "testimonial": updated,
                },
            )

        elif action == "reject":
            if current_status != "pending":
                return error_response(
                    400,
                    "Invalid status transition: can only reject pending testimonials",
                )
            delete_testimonial(target_user_id)
            logger.info(
                f"Admin {username} rejected testimonial for user {target_user_id}"
            )
            return json_response(200, {"message": "Testimonial rejected and deleted"})

        elif action == "revoke":
            if current_status != "approved":
                return error_response(
                    400,
                    "Invalid status transition: can only revoke approved testimonials",
                )
            updated = update_testimonial(
                target_user_id,
                {
                    "status": "pending",
                    "reviewed_at": now,
                    "reviewed_by": username or user_id,
                    "admin_note": note,
                },
            )
            logger.info(
                f"Admin {username} revoked testimonial for user {target_user_id}"
            )
            return json_response(
                200,
                {
                    "message": "Testimonial revoked to pending",
                    "testimonial": updated,
                },
            )

    except Exception as e:
        logger.error(f"Error updating testimonial status: {e}")
        return error_response(500, "Internal server error")
