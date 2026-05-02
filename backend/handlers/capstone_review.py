"""
Capstone review endpoint handlers.

Provides endpoints for admins to submit reviews on capstone submissions
and for learners to retrieve their review feedback.
"""

import json
import logging
from typing import Dict, Any

from auth.admin import require_admin
from auth.jwt_utils import extract_token_from_cookie, validate_jwt
from jose import JWTError
from services.dynamo import (
    get_capstone_submission,
    save_capstone_review,
    update_capstone_submission_status,
    get_capstone_review,
    get_user_profile,
)
from services.notification_service import create_notification
from services.mailgun import send_review_notification_to_learner
from utils.responses import json_response, error_response

logger = logging.getLogger(__name__)


@require_admin
def handle_submit_review(
    headers: Dict[str, str],
    username: str,
    user_id: str,
    target_user_id: str,
    content_id: str,
    body: str,
) -> Dict[str, Any]:
    """
    Handle POST /admin/submissions/{user_id}/{content_id}/review endpoint.

    Allows an admin to submit qualitative markdown feedback for a capstone submission.
    Validates the submission exists and is in pending_review state, creates the review
    record, transitions the submission status, creates an in-app notification, and
    sends an email to the learner (if email is available).

    Args:
        headers: Request headers (provided by decorator)
        username: Authenticated admin username (provided by decorator)
        user_id: Authenticated admin user ID (provided by decorator)
        target_user_id: The learner's user ID (from URL path)
        content_id: Capstone content identifier (from URL path)
        body: Request body (JSON string) containing feedback

    Returns:
        dict: API Gateway response

    Requirements: 1.4, 3.6, 3.7, 3.8, 3.9, 5.1, 7.1, 7.5, 7.6, 12.2, 13.1, 13.4, 13.5
    """
    try:
        # Parse request body for feedback
        try:
            body_data = json.loads(body) if body else {}
        except (json.JSONDecodeError, ValueError):
            return error_response(400, "Invalid request body")

        feedback = body_data.get("feedback", "").strip()

        # Validate non-empty feedback (Requirement 3.9)
        if not feedback:
            return error_response(400, "Feedback is required")

        # Verify submission exists (Requirement 7.5)
        submission = get_capstone_submission(target_user_id, content_id)
        if not submission:
            return error_response(404, "Submission not found")

        # Verify submission is in pending_review state (Requirement 7.6)
        if submission.get("status") != "pending_review":
            return error_response(400, "Submission is not in a reviewable state")

        # Create review record (Requirement 3.6, 3.8)
        save_capstone_review(target_user_id, content_id, feedback, username)

        # Update submission status to reviewed (Requirement 1.4, 3.7)
        update_capstone_submission_status(target_user_id, content_id, "reviewed")

        # Create in-app notification for the learner (fire-and-forget) (Requirement 5.1)
        try:
            # Map content_id to the correct page path
            capstone_paths = {
                "devsecops-capstone": "/learn/devsecops/capstone/index",
                "cloud_security_development-capstone": "/learn/cloud_security_development/capstone/index",
            }
            notification_link = capstone_paths.get(
                content_id,
                f"/learn/{content_id.replace('-capstone', '')}/capstone/index",
            )

            create_notification(
                user_id=target_user_id,
                message=f"Your capstone submission for {content_id} has been reviewed. Feedback is now available.",
                link=notification_link,
            )
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")

        # Send email to learner (fire-and-forget, skip if no email) (Requirement 13.1, 13.4, 13.5)
        try:
            profile = get_user_profile(target_user_id)
            if profile and profile.get("email"):
                learner_username = profile.get("username", "")
                send_review_notification_to_learner(
                    email=profile["email"],
                    username=learner_username,
                    content_id=content_id,
                    feedback=feedback,
                )
        except Exception as e:
            logger.error(f"Failed to send review email to learner: {str(e)}")

        return json_response(200, {"message": "Review submitted successfully"})

    except Exception as e:
        logger.error(f"Error in handle_submit_review: {str(e)}")
        return error_response(500, "Service temporarily unavailable")


def handle_get_review(
    headers: Dict[str, str],
    content_id: str,
) -> Dict[str, Any]:
    """
    Handle GET /progress/capstone/{content_id}/review endpoint.

    Allows an authenticated learner to retrieve the review for their capstone
    submission. Returns the review data or null if no review exists.

    Args:
        headers: Request headers
        content_id: Capstone content identifier (from URL path)

    Returns:
        dict: API Gateway response with review data or {"review": null}

    Requirements: 7.2, 7.7, 12.2
    """
    try:
        # Extract and validate JWT
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

        # Get review for this user's submission
        review = get_capstone_review(user_id, content_id)

        if not review:
            return json_response(200, {"review": None})

        return json_response(200, {"review": review})

    except Exception as e:
        logger.error(f"Error in handle_get_review: {str(e)}")
        return error_response(500, "Service temporarily unavailable")


@require_admin
def handle_get_review_admin(
    headers: Dict[str, str],
    username: str,
    user_id: str,
    target_user_id: str,
    content_id: str,
) -> Dict[str, Any]:
    """
    Handle GET /admin/submissions/{user_id}/{content_id}/review endpoint.

    Allows an admin to retrieve the review for a specific learner's capstone
    submission. Returns the review data or null if no review exists.

    Args:
        headers: Request headers (provided by decorator)
        username: Authenticated admin username (provided by decorator)
        user_id: Authenticated admin user ID (provided by decorator)
        target_user_id: The learner's user ID (from URL path)
        content_id: Capstone content identifier (from URL path)

    Returns:
        dict: API Gateway response with review data or {"review": null}
    """
    try:
        review = get_capstone_review(target_user_id, content_id)

        if not review:
            return json_response(200, {"review": None})

        return json_response(200, {"review": review})

    except Exception as e:
        logger.error(f"Error in handle_get_review_admin: {str(e)}")
        return error_response(500, "Service temporarily unavailable")
