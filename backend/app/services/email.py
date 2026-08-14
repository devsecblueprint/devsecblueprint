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


# Inquiry type labels for display in email
_INQUIRY_TYPE_LABELS = {
    "membership-support": "Membership Support",
    "technical-support": "Technical Support",
    "contributions": "Contributions",
    "partnerships": "Partnerships",
    "speaking-media": "Speaking/Media",
    "general-inquiry": "General Inquiry",
}


def send_contact_notification(
    full_name: str,
    email: str,
    organization: str,
    inquiry_type: str,
    subject: str,
    message: str,
) -> bool:
    """Send a contact form notification email to the DSB support team.

    Args:
        full_name: Sender's full name.
        email: Sender's email address.
        organization: Sender's organization (may be empty).
        inquiry_type: Category of inquiry.
        subject: Message subject line.
        message: Message body.

    Returns:
        True if sent successfully.
    """
    try:
        settings = get_settings()
        to_email = settings.contact_notify_email

        inquiry_type_label = _INQUIRY_TYPE_LABELS.get(inquiry_type, inquiry_type)

        template = _jinja_env.get_template("contact_notification.html")
        html_body = template.render(
            full_name=full_name,
            email=email,
            organization=organization,
            inquiry_type_label=inquiry_type_label,
            subject=subject,
            message=message,
        )

        return _send_email(
            to_email,
            f"[DSB Contact] {inquiry_type_label}: {subject}",
            html_body,
        )

    except Exception as e:
        logger.error("Failed to send contact notification: %s", e)
        return False


# ---------------------------------------------------------------------------
# Certification & Credentialing Program Notifications
# ---------------------------------------------------------------------------


def send_submission_received_notification(
    email: str, username: str, pathway: str
) -> bool:
    """Send a confirmation to the learner that their capstone submission was received.

    Args:
        email: Learner's email address.
        username: Learner's display name.
        pathway: Pathway display name (e.g., "DevSecOps Engineering").

    Returns:
        True if sent successfully.
    """
    try:
        if not email:
            logger.warning("Email missing for submission received notification")
            return False

        template = _jinja_env.get_template("certification_submission_received.html")
        html_body = template.render(
            username=username,
            pathway=pathway,
            platform_url="https://devsecblueprint.com",
        )

        return _send_email(
            email,
            f"Capstone Submission Received \u2014 {pathway}",
            html_body,
        )

    except Exception as e:
        logger.error("Failed to send submission received notification: %s", e)
        return False


def send_new_submission_admin_notification(
    reviewer_emails: list[str],
    candidate_name: str,
    pathway: str,
    candidate_email: str = "",
) -> bool:
    """Notify all reviewers/admins of a new capstone submission pending review.

    Args:
        reviewer_emails: List of reviewer/admin email addresses.
        candidate_name: Name of the candidate who submitted.
        pathway: Pathway display name.
        candidate_email: The candidate's email address.

    Returns:
        True if all emails sent successfully.
    """
    try:
        if not reviewer_emails:
            logger.warning("No reviewer emails provided for admin notification")
            return False

        template = _jinja_env.get_template("certification_new_submission_admin.html")
        html_body = template.render(
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            pathway=pathway,
            platform_url="https://devsecblueprint.com",
        )

        all_sent = True
        for reviewer_email in reviewer_emails:
            if not reviewer_email:
                continue
            success = _send_email(
                reviewer_email,
                f"New Certification Submission \u2014 {pathway}",
                html_body,
            )
            if not success:
                all_sent = False

        return all_sent

    except Exception as e:
        logger.error("Failed to send new submission admin notification: %s", e)
        return False


def send_review_outcome_notification(
    email: str, username: str, pathway: str, status: str, feedback: str
) -> bool:
    """Send the review outcome (PASSED/REVISIONS_REQUIRED/FAILED) to the learner.

    Args:
        email: Learner's email address.
        username: Learner's display name.
        pathway: Pathway display name.
        status: Review outcome status (PASSED, REVISIONS_REQUIRED, FAILED).
        feedback: Reviewer feedback text.

    Returns:
        True if sent successfully.
    """
    try:
        if not email:
            logger.warning("Email missing for review outcome notification")
            return False

        template = _jinja_env.get_template("certification_review_outcome.html")
        html_body = template.render(
            username=username,
            pathway=pathway,
            status=status,
            feedback=feedback,
            platform_url="https://devsecblueprint.com",
        )

        return _send_email(
            email,
            f"Certification Review Outcome \u2014 {pathway}",
            html_body,
        )

    except Exception as e:
        logger.error("Failed to send review outcome notification: %s", e)
        return False


def send_credential_issued_notification(
    email: str, username: str, pathway: str, credential_id: str
) -> bool:
    """Send a congratulations email when a credential is issued.

    Args:
        email: Learner's email address.
        username: Learner's display name.
        pathway: Pathway display name.
        credential_id: Issued credential identifier.

    Returns:
        True if sent successfully.
    """
    try:
        if not email:
            logger.warning("Email missing for credential issued notification")
            return False

        template = _jinja_env.get_template("certification_credential_issued.html")
        html_body = template.render(
            username=username,
            pathway=pathway,
            credential_id=credential_id,
            platform_url="https://devsecblueprint.com",
        )

        return _send_email(
            email,
            f"Credential Issued \u2014 {pathway}",
            html_body,
        )

    except Exception as e:
        logger.error("Failed to send credential issued notification: %s", e)
        return False


def send_credential_renewal_notification(
    email: str, username: str, pathway: str, credential_id: str, expires_at: str
) -> bool:
    """Send a 30-day warning that a credential is expiring soon.

    Args:
        email: Learner's email address.
        username: Learner's display name.
        pathway: Pathway display name.
        credential_id: Credential identifier.
        expires_at: ISO 8601 expiration timestamp.

    Returns:
        True if sent successfully.
    """
    try:
        if not email:
            logger.warning("Email missing for credential renewal notification")
            return False

        template = _jinja_env.get_template("certification_credential_renewal.html")
        html_body = template.render(
            username=username,
            pathway=pathway,
            credential_id=credential_id,
            expires_at=expires_at,
            platform_url="https://devsecblueprint.com",
        )

        return _send_email(
            email,
            f"Credential Expiring Soon \u2014 {pathway}",
            html_body,
        )

    except Exception as e:
        logger.error("Failed to send credential renewal notification: %s", e)
        return False


def send_credential_expired_notification(
    email: str, username: str, pathway: str, credential_id: str
) -> bool:
    """Notify the learner that their credential has expired.

    Args:
        email: Learner's email address.
        username: Learner's display name.
        pathway: Pathway display name.
        credential_id: Credential identifier.

    Returns:
        True if sent successfully.
    """
    try:
        if not email:
            logger.warning("Email missing for credential expired notification")
            return False

        template = _jinja_env.get_template("certification_credential_expired.html")
        html_body = template.render(
            username=username,
            pathway=pathway,
            credential_id=credential_id,
            platform_url="https://devsecblueprint.com",
        )

        return _send_email(
            email,
            f"Credential Expired \u2014 {pathway}",
            html_body,
        )

    except Exception as e:
        logger.error("Failed to send credential expired notification: %s", e)
        return False


def send_credential_revoked_notification(
    email: str, username: str, pathway: str, credential_id: str, reason: str
) -> bool:
    """Notify the learner that their credential has been revoked.

    Args:
        email: Learner's email address.
        username: Learner's display name.
        pathway: Pathway display name.
        credential_id: Credential identifier.
        reason: Reason for revocation.

    Returns:
        True if sent successfully.
    """
    try:
        if not email:
            logger.warning("Email missing for credential revoked notification")
            return False

        template = _jinja_env.get_template("certification_credential_revoked.html")
        html_body = template.render(
            username=username,
            pathway=pathway,
            credential_id=credential_id,
            reason=reason,
            platform_url="https://devsecblueprint.com",
        )

        return _send_email(
            email,
            f"Credential Revoked \u2014 {pathway}",
            html_body,
        )

    except Exception as e:
        logger.error("Failed to send credential revoked notification: %s", e)
        return False
