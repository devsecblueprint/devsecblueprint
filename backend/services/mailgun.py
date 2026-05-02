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

import markdown as md
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

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
                "from": f"The DevSec Blueprint <noreply@{mailgun_domain}>",
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


def send_capstone_notification(
    username: str, repo_url: str, content_id: str, submitted_at: str
) -> bool:
    """
    Send a capstone submission notification email to the support team via Mailgun API.

    Loads the Jinja2 HTML template, renders it with submission data,
    and sends via Mailgun. Logs errors but never raises.

    Args:
        username: Learner's username
        repo_url: Repository URL submitted
        content_id: Capstone content identifier
        submitted_at: ISO 8601 submission timestamp

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

        templates_dir = Path(__file__).resolve().parent.parent / "templates"
        logger.info(f"Loading email template from: {templates_dir}")

        if not templates_dir.exists():
            logger.error(f"Templates directory not found: {templates_dir}")
            return False

        env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
        template = env.get_template("capstone_submission_notification.html")
        html_body = template.render(
            username=username,
            repo_url=repo_url,
            content_id=content_id,
            submitted_at=submitted_at,
        )

        mailgun_url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"

        response = requests.post(
            mailgun_url,
            auth=("api", api_key),
            data={
                "from": f"The DevSec Blueprint <noreply@{mailgun_domain}>",
                "to": to_email,
                "subject": "New Capstone Submission",
                "html": html_body,
            },
            timeout=10,
        )

        if response.status_code == 200:
            logger.info("Capstone submission notification email sent successfully")
            return True
        else:
            logger.error(f"Mailgun API error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Failed to send capstone notification email: {str(e)}")
        return False


def send_welcome_email(username: str, email: str) -> bool:
    """
    Send a welcome email to a newly registered user via Mailgun API.

    Loads the Jinja2 HTML template, renders it with the user's display name
    and platform URL, and sends via Mailgun. Logs errors but never raises.

    Args:
        username: New user's display name for the greeting
        email: Recipient email address

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        mailgun_param_name = os.environ.get(
            "MAILGUN_PARAM_NAME", "/app/mailgun/api-key"
        )
        api_key = get_parameter(mailgun_param_name)

        mailgun_domain = os.environ.get("MAILGUN_DOMAIN")

        if not mailgun_domain:
            logger.error("MAILGUN_DOMAIN environment variable not set")
            return False

        # Load and render Jinja2 HTML template
        templates_dir = Path(__file__).resolve().parent.parent / "templates"
        logger.info(f"Loading email template from: {templates_dir}")

        if not templates_dir.exists():
            logger.error(f"Templates directory not found: {templates_dir}")
            return False

        env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
        template = env.get_template("welcome_email.html")
        html_body = template.render(
            username=username,
            platform_url="https://devsecblueprint.com",
        )

        mailgun_url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"

        response = requests.post(
            mailgun_url,
            auth=("api", api_key),
            data={
                "from": f"The DevSec Blueprint <noreply@{mailgun_domain}>",
                "to": email,
                "subject": "Welcome to The DevSec Blueprint!",
                "html": html_body,
            },
            timeout=10,
        )

        if response.status_code == 200:
            logger.info("Welcome email sent successfully")
            return True
        else:
            logger.error(f"Mailgun API error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return False


def send_review_notification_to_learner(
    email: str, username: str, content_id: str, feedback: str = ""
) -> bool:
    """
    Send a review completion notification email to the learner via Mailgun API.

    Loads the Jinja2 HTML template, renders it with review data including
    the feedback converted from markdown to HTML, and sends via Mailgun.
    Logs errors but never raises.

    Args:
        email: Learner's email address
        username: Learner's username
        content_id: Capstone content identifier
        feedback: Markdown feedback text from the reviewer

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        mailgun_param_name = os.environ.get(
            "MAILGUN_PARAM_NAME", "/app/mailgun/api-key"
        )
        api_key = get_parameter(mailgun_param_name)

        mailgun_domain = os.environ.get("MAILGUN_DOMAIN")

        if not mailgun_domain:
            logger.error("MAILGUN_DOMAIN environment variable not set")
            return False

        if not email:
            logger.error("Learner email address not provided")
            return False

        # Convert markdown feedback to HTML
        feedback_html = ""
        if feedback:
            feedback_html = md.markdown(
                feedback,
                extensions=["fenced_code", "tables", "nl2br"],
            )

        templates_dir = Path(__file__).resolve().parent.parent / "templates"
        logger.info(f"Loading email template from: {templates_dir}")

        if not templates_dir.exists():
            logger.error(f"Templates directory not found: {templates_dir}")
            return False

        env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
        template = env.get_template("capstone_review_notification.html")

        # Map content_id to the correct page path
        capstone_paths = {
            "devsecops-capstone": "learn/devsecops/capstone/index",
            "cloud_security_development-capstone": "learn/cloud_security_development/capstone/index",
        }
        capstone_path = capstone_paths.get(
            content_id,
            f"learn/{content_id.replace('-capstone', '')}/capstone/index",
        )

        # Map content_id to a human-friendly display name
        capstone_names = {
            "devsecops-capstone": "DevSecOps",
            "cloud_security_development-capstone": "Cloud Security Development",
        }
        capstone_name = capstone_names.get(
            content_id,
            content_id.replace("-capstone", "")
            .replace("_", " ")
            .replace("-", " ")
            .title(),
        )

        html_body = template.render(
            username=username,
            content_id=content_id,
            capstone_name=capstone_name,
            capstone_path=capstone_path,
            feedback_html=Markup(feedback_html),
            platform_url="https://devsecblueprint.com",
        )

        mailgun_url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"

        response = requests.post(
            mailgun_url,
            auth=("api", api_key),
            data={
                "from": f"The DevSec Blueprint <noreply@{mailgun_domain}>",
                "to": email,
                "subject": "Your Capstone Feedback is Ready",
                "html": html_body,
            },
            timeout=10,
        )

        if response.status_code == 200:
            logger.info(f"Review notification email sent successfully to {username}")
            return True
        else:
            logger.error(f"Mailgun API error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Failed to send review notification email: {str(e)}")
        return False
