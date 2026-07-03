"""Email service — sends transactional emails via Mailgun API.

Ported from backend/services/mailgun.py. Self-contained.
Retrieves the Mailgun API key from AWS Parameter Store (SSM).
"""

import logging
from pathlib import Path
from typing import Any

import boto3
import requests
from botocore.exceptions import ClientError
from jinja2 import Environment, FileSystemLoader

from app.config import Settings
from app.dependencies import get_settings

logger = logging.getLogger(__name__)

# Load templates from app/templates/ directory
_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)

# Module-level cache for the Mailgun API key
_api_key_cache: dict[str, Any] = {"value": None}


def _get_api_key(param_name: str) -> str:
    """Retrieve Mailgun API key from SSM Parameter Store with caching."""
    if _api_key_cache["value"] is not None:
        return _api_key_cache["value"]

    try:
        ssm = boto3.client("ssm")
        response = ssm.get_parameter(Name=param_name, WithDecryption=True)
        value = response["Parameter"]["Value"]
        _api_key_cache["value"] = value
        return value
    except (ClientError, KeyError) as e:
        raise Exception(f"Failed to retrieve Mailgun API key: {e}")


def _send_email(
    mailgun_domain: str,
    api_key: str,
    to_email: str,
    subject: str,
    html_body: str,
) -> bool:
    """Send an email via Mailgun HTTP API."""
    url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"
    try:
        response = requests.post(
            url,
            auth=("api", api_key),
            data={
                "from": f"The DevSec Blueprint <noreply@{mailgun_domain}>",
                "to": to_email,
                "subject": subject,
                "html": html_body,
            },
            timeout=10,
        )
        if response.status_code == 200:
            return True
        logger.error("Mailgun API error: %s - %s", response.status_code, response.text)
        return False
    except Exception as e:
        logger.error("Failed to send email: %s", e)
        return False


def send_capstone_notification(
    username: str, repo_url: str, content_id: str, submitted_at: str
) -> bool:
    """Send a capstone submission notification email to the support team.

    Args:
        username: Learner's display name.
        repo_url: Repository URL.
        content_id: Capstone content identifier.
        submitted_at: Formatted submission timestamp.

    Returns:
        True if sent successfully.
    """
    try:
        settings = get_settings()
        mailgun_domain = settings.mailgun_domain
        mailgun_param_name = settings.mailgun_param_name
        to_email = settings.testimonial_notify_email

        if not mailgun_domain or not mailgun_param_name:
            logger.error("Mailgun not configured (domain or param_name missing)")
            return False

        api_key = _get_api_key(mailgun_param_name)

        template = _jinja_env.get_template("capstone_submission_notification.html")
        html_body = template.render(
            username=username,
            repo_url=repo_url,
            content_id=content_id,
            submitted_at=submitted_at,
        )

        return _send_email(
            mailgun_domain, api_key, to_email, "New Capstone Submission", html_body
        )

    except Exception as e:
        logger.error("Failed to send capstone notification: %s", e)
        return False


def send_testimonial_notification(
    display_name: str, linkedin_url: str | None, quote: str
) -> bool:
    """Send a testimonial notification email to the admin.

    Returns:
        True if sent successfully.
    """
    try:
        settings = get_settings()
        mailgun_domain = settings.mailgun_domain
        mailgun_param_name = settings.mailgun_param_name
        to_email = settings.testimonial_notify_email

        if not mailgun_domain or not mailgun_param_name:
            logger.error("Mailgun not configured")
            return False

        api_key = _get_api_key(mailgun_param_name)

        template = _jinja_env.get_template("testimonial_notification.html")
        html_body = template.render(
            display_name=display_name,
            linkedin_url=linkedin_url or "",
            quote=quote,
        )

        return _send_email(
            mailgun_domain, api_key, to_email, "New Testimonial Submission", html_body
        )

    except Exception as e:
        logger.error("Failed to send testimonial notification: %s", e)
        return False


def send_review_notification_to_learner(
    email: str, username: str, content_id: str, feedback: str = ""
) -> bool:
    """Send a capstone review notification email to the learner.

    Returns:
        True if sent successfully.
    """
    try:
        settings = get_settings()
        mailgun_domain = settings.mailgun_domain
        mailgun_param_name = settings.mailgun_param_name

        if not mailgun_domain or not mailgun_param_name or not email:
            logger.error("Mailgun not configured or email missing")
            return False

        api_key = _get_api_key(mailgun_param_name)

        # Convert markdown feedback to HTML
        feedback_html = ""
        if feedback:
            import markdown as md

            feedback_html = md.markdown(
                feedback, extensions=["fenced_code", "tables", "nl2br"]
            )

        from markupsafe import Markup

        template = _jinja_env.get_template("capstone_review_notification.html")

        capstone_paths = {
            "devsecops-capstone": "learn/devsecops/capstone/index",
            "cloud_security_development-capstone": "learn/cloud_security_development/capstone/index",
        }
        capstone_path = capstone_paths.get(
            content_id,
            f"learn/{content_id.replace('-capstone', '')}/capstone/index",
        )
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

        return _send_email(
            mailgun_domain, api_key, email, "Your Capstone Feedback is Ready", html_body
        )

    except Exception as e:
        logger.error("Failed to send review notification: %s", e)
        return False


def send_welcome_email(username: str, email: str) -> bool:
    """Send a welcome email to a newly registered user.

    Returns:
        True if sent successfully.
    """
    try:
        settings = get_settings()
        mailgun_domain = settings.mailgun_domain
        mailgun_param_name = settings.mailgun_param_name

        if not mailgun_domain or not mailgun_param_name or not email:
            logger.error("Mailgun not configured or email missing")
            return False

        api_key = _get_api_key(mailgun_param_name)

        template = _jinja_env.get_template("welcome_email.html")
        html_body = template.render(
            username=username,
            platform_url="https://devsecblueprint.com",
        )

        return _send_email(
            mailgun_domain,
            api_key,
            email,
            "Welcome to The DevSec Blueprint!",
            html_body,
        )

    except Exception as e:
        logger.error("Failed to send welcome email: %s", e)
        return False


def send_subscription_expired_email(
    username: str, email: str, previous_tier: str
) -> bool:
    """Send a subscription expiration notification to the user.

    Args:
        username: User's display name.
        email: User's email address.
        previous_tier: The tier they were on before expiration (e.g. "EXPLORER").

    Returns:
        True if sent successfully.
    """
    try:
        settings = get_settings()
        mailgun_domain = settings.mailgun_domain
        mailgun_param_name = settings.mailgun_param_name

        if not mailgun_domain or not mailgun_param_name or not email:
            logger.warning(
                "Mailgun not configured or email missing, skipping expiration email"
            )
            return False

        api_key = _get_api_key(mailgun_param_name)

        # Format tier name for display
        tier_display = (
            previous_tier.replace("_", " ").title() if previous_tier else "Premium"
        )

        template = _jinja_env.get_template("subscription_expired.html")
        html_body = template.render(
            username=username,
            previous_tier=tier_display,
            platform_url="https://devsecblueprint.com",
        )

        return _send_email(
            mailgun_domain,
            api_key,
            email,
            "Your DevSec Blueprint Subscription Has Ended",
            html_body,
        )

    except Exception as e:
        logger.error("Failed to send subscription expired email: %s", e)
        return False


def send_subscription_welcome_email(username: str, email: str, tier: str) -> bool:
    """Send a congratulations email when a user subscribes.

    Args:
        username: User's display name.
        email: User's email address.
        tier: The tier they subscribed to (e.g. "EXPLORER").

    Returns:
        True if sent successfully.
    """
    try:
        settings = get_settings()
        mailgun_domain = settings.mailgun_domain
        mailgun_param_name = settings.mailgun_param_name

        if not mailgun_domain or not mailgun_param_name or not email:
            logger.warning(
                "Mailgun not configured or email missing, skipping subscription welcome"
            )
            return False

        api_key = _get_api_key(mailgun_param_name)

        tier_display = tier.replace("_", " ").title() if tier else "Premium"

        template = _jinja_env.get_template("subscription_welcome.html")
        html_body = template.render(
            username=username,
            tier_display=tier_display,
            platform_url="https://devsecblueprint.com",
        )

        return _send_email(
            mailgun_domain,
            api_key,
            email,
            f"Welcome to DSB {tier_display}! 🎉",
            html_body,
        )

    except Exception as e:
        logger.error("Failed to send subscription welcome email: %s", e)
        return False
