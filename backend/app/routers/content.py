"""Content router — walkthroughs, quizzes, notifications, testimonials.

Consolidates the content-delivery routes from the Lambda handler into
a single FastAPI router. All routes require JWT authentication except
GET /api/testimonials/approved (public).

Routes:
- GET  /api/walkthroughs/{id}/progress
- POST /api/walkthroughs/{id}/progress
- POST /quiz/submit
- POST /api/testimonials
- GET  /api/testimonials/me
- GET  /api/testimonials/approved
- GET  /api/notifications
- DELETE /api/notifications/{notification_id}
- GET  /admin/testimonials
- PUT  /admin/testimonials/{user_id}/status

Requirements: 4.2
"""

import json
import logging
import random
import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.auth.jwt import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["content"])

# LinkedIn URL pattern: https://(www.)linkedin.com/in/{slug}
LINKEDIN_URL_PATTERN = re.compile(
    r"^https://(www\.)?linkedin\.com/in/[A-Za-z0-9\-_%]+/?$"
)

MAX_QUOTE_CHARS = 350


# ---------------------------------------------------------------------------
# Walkthrough Progress Routes
# ---------------------------------------------------------------------------


@router.get("/api/walkthroughs/{walkthrough_id}/progress")
async def get_walkthrough_progress(
    walkthrough_id: str,
    user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Get user progress for a specific walkthrough.

    Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6
    """
    from services.walkthrough_service import get_walkthrough_progress

    try:
        user_id = user["sub"]
        progress = get_walkthrough_progress(user_id, walkthrough_id)
        return JSONResponse(status_code=200, content={"progress": progress})
    except Exception as e:
        logger.error(f"Error retrieving walkthrough progress: {type(e).__name__}")
        # Return default not_started on error
        return JSONResponse(
            status_code=200,
            content={
                "progress": {
                    "status": "not_started",
                    "started_at": None,
                    "completed_at": None,
                }
            },
        )


@router.post("/api/walkthroughs/{walkthrough_id}/progress")
async def update_walkthrough_progress(
    walkthrough_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Update user progress for a walkthrough.

    Requirements: 10.6, 11.8
    """
    from services.walkthrough_service import (
        update_walkthrough_progress as update_progress,
    )

    user_id = user["sub"]

    # Parse body
    try:
        body = await request.body()
        body_str = body.decode("utf-8") if body else ""
        if not body_str:
            raise HTTPException(status_code=400, detail="Invalid request")
        data = json.loads(body_str)
        status = data.get("status")
        if not status:
            raise HTTPException(status_code=400, detail="Invalid request")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid request")

    try:
        update_progress(user_id, walkthrough_id, status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status value")
    except Exception as e:
        logger.error(f"Error updating walkthrough progress: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")

    return JSONResponse(
        status_code=200, content={"message": "Progress updated successfully"}
    )


# ---------------------------------------------------------------------------
# Quiz Routes
# ---------------------------------------------------------------------------


@router.post("/quiz/submit")
async def quiz_submit(
    request: Request,
    user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Handle quiz submission.

    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 8.1, 8.3, 8.4, 8.5, 8.6, 8.8
    """
    from services.quiz_service import (
        submit_quiz,
        QuizNotFoundError,
        RegistryUnavailableError,
    )

    user_id = user["sub"]

    # Parse body
    try:
        body = await request.body()
        body_str = body.decode("utf-8") if body else ""
        request_data = json.loads(body_str) if body_str else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid request")

    module_id = request_data.get("module_id")
    answers = request_data.get("answers")

    # Validate required fields
    if not module_id or not answers:
        raise HTTPException(status_code=400, detail="Invalid request")

    if not isinstance(answers, dict):
        raise HTTPException(status_code=400, detail="Invalid request")

    try:
        result = submit_quiz(user_id, module_id, answers)
        return JSONResponse(status_code=200, content=result)
    except QuizNotFoundError as e:
        logger.warning(f"Quiz not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except RegistryUnavailableError:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid request")
    except Exception as e:
        logger.error(f"Quiz submission error: {type(e).__name__}")
        if "dynamodb" in str(type(e)).lower() or "boto" in str(type(e)).lower():
            raise HTTPException(
                status_code=500, detail="Service temporarily unavailable"
            )
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Testimonial Routes
# ---------------------------------------------------------------------------


def _validate_testimonial_fields(
    display_name: str, linkedin_url: str, quote: str
) -> list[str]:
    """Validate testimonial submission fields. Returns list of error messages."""
    errors: list[str] = []

    if not display_name or not display_name.strip():
        errors.append("display_name is required and cannot be empty")

    if linkedin_url and not LINKEDIN_URL_PATTERN.match(linkedin_url):
        errors.append(
            "linkedin_url must match https://(www.)linkedin.com/in/{profile_slug}"
        )

    if not quote or not quote.strip():
        errors.append("quote is required and cannot be empty")
    elif len(quote.strip()) > MAX_QUOTE_CHARS:
        errors.append(
            f"quote exceeds maximum of {MAX_QUOTE_CHARS} characters "
            f"(has {len(quote.strip())})"
        )

    return errors


def _send_notification_email(display_name: str, linkedin_url: str, quote: str) -> None:
    """Fire-and-forget email notification to admin."""
    try:
        from services.mailgun import send_testimonial_notification

        result = send_testimonial_notification(display_name, linkedin_url, quote)
        if not result:
            logger.warning(
                "Testimonial notification email was not sent (returned False)"
            )
    except Exception as e:
        logger.error(f"Failed to send testimonial notification email: {e}")


@router.post("/api/testimonials")
async def submit_testimonial(
    request: Request,
    user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Submit or update a testimonial.

    Requirements: 7.1, 7.6, 7.8, 8.1, 8.2, 8.3, 8.4, 8.5, 2.1, 11.1, 11.4, 11.5
    """
    from services.testimonial_service import (
        create_testimonial,
        get_testimonial,
        update_testimonial,
    )

    user_id = user["sub"]

    # Parse body
    try:
        body = await request.body()
        body_str = body.decode("utf-8") if body else ""
        data = json.loads(body_str) if body_str else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")

    display_name = data.get("display_name", "").strip()
    linkedin_url = data.get("linkedin_url", "").strip()
    quote = data.get("quote", "").strip()

    # Validate fields
    errors = _validate_testimonial_fields(display_name, linkedin_url, quote)
    if errors:
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {'; '.join(errors)}",
        )

    try:
        # Check for existing testimonial
        existing = get_testimonial(user_id)

        if existing and existing.get("status") == "approved":
            raise HTTPException(status_code=409, detail="Testimonial already exists")

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
            _send_notification_email(display_name, linkedin_url, quote)
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Testimonial updated successfully",
                    "testimonial": updated,
                },
            )

        # Create new testimonial
        record = create_testimonial(user_id, display_name, linkedin_url or "", quote)
        logger.info(f"Testimonial created for user {user_id}")
        _send_notification_email(display_name, linkedin_url, quote)
        return JSONResponse(
            status_code=201,
            content={
                "message": "Testimonial submitted successfully",
                "testimonial": record,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting testimonial: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/testimonials/me")
async def get_my_testimonial(
    user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Get the authenticated user's testimonial.

    Requirements: 7.2, 7.6
    """
    from services.testimonial_service import get_testimonial

    user_id = user["sub"]

    try:
        record = get_testimonial(user_id)
        if not record:
            raise HTTPException(status_code=404, detail="No testimonial found")
        return JSONResponse(status_code=200, content={"testimonial": record})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching testimonial for user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/testimonials/approved")
async def get_approved_testimonials() -> JSONResponse:
    """Get randomly sampled approved testimonials (public endpoint).

    Requirements: 7.3, 7.9, 7.10, 2.2
    """
    from services.testimonial_service import get_testimonials_by_status

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

        return JSONResponse(
            status_code=200, content={"testimonials": public_testimonials}
        )
    except Exception as e:
        logger.error(f"Error fetching approved testimonials: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Notification Routes
# ---------------------------------------------------------------------------


@router.get("/api/notifications")
async def get_notifications(
    user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Get all notifications for the authenticated user.

    Requirements: 5.4, 5.6, 12.2
    """
    from services.notification_service import get_notifications as get_notifs

    user_id = user["sub"]

    try:
        notifications = get_notifs(user_id)
        return JSONResponse(status_code=200, content={"notifications": notifications})
    except Exception as e:
        logger.error(f"Error in get_notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")


@router.delete("/api/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Acknowledge and delete a notification.

    Requirements: 5.5, 5.6, 12.2
    """
    from services.notification_service import (
        delete_notification as delete_notif,
    )

    user_id = user["sub"]

    try:
        delete_notif(user_id, notification_id)
        return JSONResponse(
            status_code=200, content={"message": "Notification deleted"}
        )
    except Exception as e:
        logger.error(f"Error in delete_notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")


# ---------------------------------------------------------------------------
# Admin Testimonial Routes
# ---------------------------------------------------------------------------


@router.get("/admin/testimonials")
async def admin_list_testimonials(
    request: Request,
    user: dict = Depends(require_admin),
) -> JSONResponse:
    """List testimonials with optional status filter (admin only).

    Requirements: 7.4, 7.7, 5.10
    """
    from services.testimonial_service import (
        get_testimonials_by_status,
        get_all_testimonials,
    )

    username = (
        user.get("github_login")
        or user.get("gitlab_login")
        or user.get("bitbucket_login")
        or user.get("sub")
    )

    try:
        status_filter = request.query_params.get("status", "").strip().lower()

        if status_filter and status_filter in ("pending", "approved"):
            testimonials = get_testimonials_by_status(status_filter)
        elif status_filter:
            raise HTTPException(
                status_code=400,
                detail="Invalid status filter. Use 'pending' or 'approved'",
            )
        else:
            testimonials = get_all_testimonials()

        logger.info(
            f"Admin {username} listed testimonials: "
            f"count={len(testimonials)}, filter={status_filter or 'all'}"
        )

        return JSONResponse(status_code=200, content={"testimonials": testimonials})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing testimonials: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/admin/testimonials/{target_user_id}/status")
async def admin_update_testimonial_status(
    target_user_id: str,
    request: Request,
    user: dict = Depends(require_admin),
) -> JSONResponse:
    """Admin moderation: approve, reject, or revoke a testimonial.

    Valid transitions:
    - pending -> approved (approve)
    - pending -> deleted (reject)
    - approved -> pending (revoke)

    Requirements: 7.5, 7.7, 2.3, 2.4, 2.5, 2.6, 5.10
    """
    from datetime import datetime, timezone

    from services.testimonial_service import (
        get_testimonial,
        update_testimonial,
        delete_testimonial,
    )

    username = (
        user.get("github_login")
        or user.get("gitlab_login")
        or user.get("bitbucket_login")
        or user.get("sub")
    )
    admin_user_id = user.get("sub")

    if not target_user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    # Parse body
    try:
        body = await request.body()
        body_str = body.decode("utf-8") if body else ""
        data = json.loads(body_str) if body_str else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")

    action = data.get("action", "").strip().lower()
    note = data.get("note", "").strip()

    if action not in ("approve", "reject", "revoke"):
        raise HTTPException(
            status_code=400,
            detail="Invalid action. Use 'approve', 'reject', or 'revoke'",
        )

    try:
        # Fetch existing testimonial
        existing = get_testimonial(target_user_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Testimonial not found")

        current_status = existing.get("status")
        now = datetime.now(timezone.utc).isoformat()

        if action == "approve":
            if current_status != "pending":
                raise HTTPException(
                    status_code=400,
                    detail="Invalid status transition: can only approve pending testimonials",
                )
            updated = update_testimonial(
                target_user_id,
                {
                    "status": "approved",
                    "reviewed_at": now,
                    "reviewed_by": username or admin_user_id,
                    "admin_note": note,
                },
            )
            logger.info(
                f"Admin {username} approved testimonial for user {target_user_id}"
            )
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Testimonial approved",
                    "testimonial": updated,
                },
            )

        elif action == "reject":
            if current_status != "pending":
                raise HTTPException(
                    status_code=400,
                    detail="Invalid status transition: can only reject pending testimonials",
                )
            delete_testimonial(target_user_id)
            logger.info(
                f"Admin {username} rejected testimonial for user {target_user_id}"
            )
            return JSONResponse(
                status_code=200,
                content={"message": "Testimonial rejected and deleted"},
            )

        elif action == "revoke":
            if current_status != "approved":
                raise HTTPException(
                    status_code=400,
                    detail="Invalid status transition: can only revoke approved testimonials",
                )
            updated = update_testimonial(
                target_user_id,
                {
                    "status": "pending",
                    "reviewed_at": now,
                    "reviewed_by": username or admin_user_id,
                    "admin_note": note,
                },
            )
            logger.info(
                f"Admin {username} revoked testimonial for user {target_user_id}"
            )
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Testimonial revoked to pending",
                    "testimonial": updated,
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating testimonial status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
