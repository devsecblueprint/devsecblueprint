"""Email service — sends transactional emails via AWS SES.

Uses boto3 SES client to send HTML emails. No API keys needed — relies on
the ECS task role's IAM permissions for ses:SendEmail.
"""

import logging
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from app.config import Settings
from app.dependencies import get_settings

logger = logging.getLogger(__name__)

# Load templates from app/templates/ directory
_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)


def _send_email(
    to_email: str,
    subject: str,
    html_body: str,
    sender_email: str = "",
    ses_region: str = "",
) -> bool:
    """Send an email via AWS SES.

    Args:
        to_email: Recipient email address.
        subject: Email subject line.
        html_body: Rendered HTML body.
        sender_email: From address (defaults to settings if empty).
        ses_region: AWS region for SES (defaults to settings if empty).

    Returns:
        True if sent successfully.
    """
    if not sender_email or not ses_region:
        settings = get_settings()
        sender_email = sender_email or settings.ses_sender_email
        ses_region = ses_region or settings.ses_region

    try:
        ses = boto3.client("ses", region_name=ses_region)
        ses.send_email(
            Source=f"The DevSec Blueprint <{sender_email}>",
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                },
            },
        )
        return True
    except ClientError as e:
        logger.error(
            "SES send failed for %s: %s",
            to_email,
            e.response["Error"]["Message"],
        )
        return False
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
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
        to_email = settings.testimonial_notify_email

        template = _jinja_env.get_template("capstone_submission_notification.html")
        html_body = template.render(
            username=username,
            repo_url=repo_url,
            content_id=content_id,
            submitted_at=submitted_at,
        )

        return _send_email(to_email, "New Capstone Submission", html_body)

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
        to_email = settings.testimonial_notify_email

        template = _jinja_env.get_template("testimonial_notification.html")
        html_body = template.render(
            display_name=display_name,
            linkedin_url=linkedin_url or "",
            quote=quote,
        )

        return _send_email(to_email, "New Testimonial Submission", html_body)

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
        if not email:
            logger.error("Email missing for review notification")
            return False

        # Convert markdown feedback to HTML
        feedback_html = ""
        if feedback:
            try:
                import markdown as md

                feedback_html = md.markdown(
                    feedback, extensions=["fenced_code", "tables", "nl2br"]
                )
            except ImportError:
                feedback_html = f"<p>{feedback}</p>"

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

        return _send_email(email, "Your Capstone Feedback is Ready", html_body)

    except Exception as e:
        logger.error("Failed to send review notification: %s", e)
        return False


def send_welcome_email(username: str, email: str) -> bool:
    """Send a welcome email to a newly registered user.

    Returns:
        True if sent successfully.
    """
    try:
        if not email:
            logger.error("Email missing for welcome email")
            return False

        template = _jinja_env.get_template("welcome_email.html")
        html_body = template.render(
            username=username,
            platform_url="https://devsecblueprint.com",
        )

        return _send_email(email, "Welcome to The DevSec Blueprint!", html_body)

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
        previous_tier: The tier they were on before expiration.

    Returns:
        True if sent successfully.
    """
    try:
        if not email:
            logger.warning("Email missing, skipping expiration email")
            return False

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
            email, "Your DevSec Blueprint Subscription Has Ended", html_body
        )

    except Exception as e:
        logger.error("Failed to send subscription expired email: %s", e)
        return False


def send_subscription_welcome_email(username: str, email: str, tier: str) -> bool:
    """Send a congratulations email when a user subscribes.

    Args:
        username: User's display name.
        email: User's email address.
        tier: The tier they subscribed to.

    Returns:
        True if sent successfully.
    """
    try:
        if not email:
            logger.warning("Email missing, skipping subscription welcome")
            return False

        tier_display = tier.replace("_", " ").title() if tier else "Premium"

        template = _jinja_env.get_template("subscription_welcome.html")
        html_body = template.render(
            username=username,
            tier_display=tier_display,
            platform_url="https://devsecblueprint.com",
        )

        return _send_email(email, f"Welcome to DSB {tier_display}!", html_body)

    except Exception as e:
        logger.error("Failed to send subscription welcome email: %s", e)
        return False
