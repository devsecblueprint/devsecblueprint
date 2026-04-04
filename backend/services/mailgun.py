"""
Mailgun email service for sending emails.

This module provides functions to send emails via the Mailgun API,
retrieving credentials securely from AWS Parameter Store.
"""

import os
import logging
import requests
from typing import Optional
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from services.parameter_store import get_parameter

logger = logging.getLogger(__name__)


def send_testimonial_notification(
    display_name: str, linkedin_url: Optional[str], quote: str
) -> bool:
    """
    Send a testimonial notification email to the admin via Mailgun API.

    Loads the Jinja2 HTML template, renders it with testimonial data,
    and sends via Mailgun. Logs errors but never raises.

    Args:
        display_name: Submitter's display name (or "Anonymous")
        linkedin_url: Optional LinkedIn profile URL
        quote: Testimonial quote text

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        mailgun_param_name = os.environ.get(
            "MAILGUN_PARAM_NAME", "/app/mailgun/api-key"
        )
        api_key = get_parameter(mailgun_param_name)

        mailgun_domain = os.environ.get("MAILGUN_DOMAIN")
        to_email = os.environ.get("TESTIMONIAL_NOTIFY_EMAIL")

        if not mailgun_domain:
            logger.error("MAILGUN_DOMAIN environment variable not set")
            return False

        if not to_email:
            logger.error("TESTIMONIAL_NOTIFY_EMAIL environment variable not set")
            return False

        # Load and render Jinja2 HTML template
        # In Lambda, __file__ is /var/task/services/mailgun.py
        # so parent.parent gives /var/task/ and templates/ is at /var/task/templates/
        templates_dir = Path(__file__).resolve().parent.parent / "templates"
        logger.info(f"Loading email template from: {templates_dir}")

        if not templates_dir.exists():
            logger.error(f"Templates directory not found: {templates_dir}")
            return False

        env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
        template = env.get_template("testimonial_notification.html")
        html_body = template.render(
            display_name=display_name,
            linkedin_url=linkedin_url or "",
            quote=quote,
        )

        mailgun_url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"

        response = requests.post(
            mailgun_url,
            auth=("api", api_key),
            data={
                "from": f"DSB Testimonials <testimonials@{mailgun_domain}>",
                "to": to_email,
                "subject": "New Testimonial Submission",
                "html": html_body,
            },
            timeout=10,
        )

        if response.status_code == 200:
            logger.info("Testimonial notification email sent successfully")
            return True
        else:
            logger.error(f"Mailgun API error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Failed to send testimonial notification email: {str(e)}")
        return False
