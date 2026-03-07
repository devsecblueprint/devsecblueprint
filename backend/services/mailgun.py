"""
Mailgun email service for sending success story emails.

This module provides functions to send emails via the Mailgun API,
retrieving credentials securely from AWS Parameter Store.
"""

import os
import logging
import requests
from typing import Optional

from services.parameter_store import get_parameter

logger = logging.getLogger(__name__)


def send_success_story_email(
    name: str, email: str, story: str, share_publicly: bool
) -> bool:
    """
    Send a success story email via Mailgun API.

    Args:
        name: User's name
        email: User's email address
        story: Success story text
        share_publicly: Whether user gave permission to share publicly

    Returns:
        bool: True if email sent successfully, False otherwise

    Raises:
        Exception: If Mailgun credentials cannot be retrieved
    """
    try:
        # Retrieve Mailgun API key from Parameter Store
        mailgun_param_name = os.environ.get(
            "MAILGUN_PARAM_NAME", "/app/mailgun/api-key"
        )
        api_key = get_parameter(mailgun_param_name)

        # Get Mailgun domain and recipient email from environment
        mailgun_domain = os.environ.get("MAILGUN_DOMAIN")
        to_email = os.environ.get("SUCCESS_STORY_TO_EMAIL")

        if not mailgun_domain:
            logger.error("MAILGUN_DOMAIN environment variable not set")
            return False

        if not to_email:
            logger.error("SUCCESS_STORY_TO_EMAIL environment variable not set")
            return False

        # Construct email body
        permission_text = "Yes" if share_publicly else "No"
        email_body = f"""Name: {name}
Email: {email}

Success Story:
{story}

Public Sharing Permission: {permission_text}"""

        # Prepare Mailgun API request
        mailgun_url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"

        # Send email via Mailgun API
        response = requests.post(
            mailgun_url,
            auth=("api", api_key),
            data={
                "from": f"DSB Testimonials <testimonials@{mailgun_domain}>",
                "to": to_email,
                "subject": "New Success Story Submission",
                "text": email_body,
            },
            timeout=10,
        )

        # Check response status
        if response.status_code == 200:
            logger.info(f"Success story email sent successfully for {email}")
            return True
        else:
            logger.error(f"Mailgun API error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Failed to send success story email: {str(e)}")
        # Re-raise if it's a Parameter Store error (credential retrieval failure)
        if "Failed to retrieve parameter" in str(e):
            raise
        return False
