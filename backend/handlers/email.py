"""
Email handler for success story submissions.

Handles POST requests to send success story emails via Mailgun.
"""

import json
import logging
import re
from typing import Dict, Any

from services.mailgun import send_success_story_email
from utils.responses import error_response, json_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handle_send_success_story(headers: Dict[str, str], body: str) -> Dict[str, Any]:
    """
    Handle POST /api/email/success-story endpoint.

    Validates request data and sends success story email via Mailgun.

    Args:
        headers: Request headers
        body: Request body (JSON string)

    Returns:
        dict: API Gateway response with success/error message

    Request Body:
        {
            "name": str,
            "email": str,
            "story": str,
            "sharePublicly": bool
        }

    Responses:
        200: Success story sent successfully
        400: Invalid request (missing fields, invalid email, story too short)
        500: Failed to send email

    Validates: Requirements 8.1, 8.8, 8.10
    """
    try:
        # Parse request body
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return error_response(400, "Invalid JSON in request body")

        # Validate required fields
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        story = data.get("story", "").strip()
        share_publicly = data.get("sharePublicly", False)

        # Check for missing fields
        if not name:
            return error_response(400, "Invalid request: missing required field 'name'")

        if not email:
            return error_response(
                400, "Invalid request: missing required field 'email'"
            )

        if not story:
            return error_response(
                400, "Invalid request: missing required field 'story'"
            )

        # Validate email format
        email_pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
        if not re.match(email_pattern, email):
            return error_response(400, "Invalid request: email format is invalid")

        # Validate story minimum length (50 characters)
        if len(story) < 50:
            return error_response(
                400, "Invalid request: story must be at least 50 characters"
            )

        # Send email via Mailgun service
        try:
            success = send_success_story_email(name, email, story, share_publicly)

            if success:
                logger.info(f"Success story email sent for {email}")
                return json_response(
                    200, {"message": "Success story sent successfully"}
                )
            else:
                logger.error(f"Failed to send success story email for {email}")
                return error_response(
                    500, "Failed to send email. Please try again later."
                )

        except Exception as e:
            # Handle Parameter Store or credential retrieval errors
            if "Failed to retrieve parameter" in str(e):
                logger.error(f"Credential retrieval failed: {str(e)}")
                return error_response(500, "Email service temporarily unavailable")
            raise

    except Exception as e:
        logger.error(f"Error handling success story submission: {str(e)}")
        return error_response(500, "Failed to send email. Please try again later.")
