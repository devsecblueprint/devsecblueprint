"""Broadcast email delivery — sends broadcast notifications to all users.

Called as a FastAPI BackgroundTask from the admin broadcast creation endpoint.
Iterates all registered users with email addresses, renders the broadcast
content (markdown → HTML), and sends via Mailgun. Failures are logged per-user
but do not halt delivery to remaining users.
"""

import logging
from typing import Any

import markdown

from app.config import Settings
from app.services.admin_service import AdminService
from app.services.email import _get_api_key, _send_email, _jinja_env

logger = logging.getLogger(__name__)


def _render_markdown_to_html(md_text: str) -> str:
    """Convert markdown text to HTML.

    Supports headings, bold, italic, links, lists, and code blocks.
    """
    return markdown.markdown(
        md_text,
        extensions=["extra", "nl2br", "sane_lists"],
    )


def send_broadcast_emails(broadcast: dict[str, Any], settings: Settings) -> None:
    """Send a broadcast notification email to all users with email addresses.

    This function is designed to be called as a BackgroundTask. It:
    1. Fetches all registered users
    2. Filters to those with non-empty email
    3. Renders the broadcast markdown to HTML
    4. Sends an email to each user via Mailgun

    Args:
        broadcast: Dict with title, message (markdown), link, created_by.
        settings: Application settings instance.
    """
    mailgun_domain = settings.mailgun_domain
    mailgun_param_name = settings.mailgun_param_name

    if not mailgun_domain or not mailgun_param_name:
        logger.error(
            "Broadcast email skipped: Mailgun not configured (domain or param_name missing)"
        )
        return

    # Get Mailgun API key
    try:
        api_key = _get_api_key(mailgun_param_name)
    except Exception as e:
        logger.error("Broadcast email skipped: failed to get Mailgun API key: %s", e)
        return

    # Render markdown to HTML
    title = broadcast.get("title", "")
    message_md = broadcast.get("message", "")
    link = broadcast.get("link", "")
    message_html = _render_markdown_to_html(message_md)

    # Render email template
    try:
        template = _jinja_env.get_template("broadcast_notification.html")
        html_body = template.render(
            title=title,
            message_html=message_html,
            link=link,
        )
    except Exception as e:
        logger.error("Broadcast email skipped: template render failed: %s", e)
        return

    # Fetch all users
    try:
        svc = AdminService(settings)
        all_users = svc.get_all_registered_users()
    except Exception as e:
        logger.error("Broadcast email skipped: failed to fetch users: %s", e)
        return

    # Filter to users with email addresses
    users_with_email = [u for u in all_users if u.get("email", "").strip()]

    if not users_with_email:
        logger.info("Broadcast email: no users with email addresses found")
        return

    logger.info(
        "Broadcast email: sending '%s' to %d users", title, len(users_with_email)
    )

    # Send to each user
    success_count = 0
    fail_count = 0

    for user in users_with_email:
        email = user["email"].strip()
        try:
            sent = _send_email(
                mailgun_domain=mailgun_domain,
                api_key=api_key,
                to_email=email,
                subject=f"DSB: {title}",
                html_body=html_body,
            )
            if sent:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            logger.warning("Broadcast email failed for %s: %s", email, e)
            fail_count += 1

    logger.info(
        "Broadcast email complete: %d sent, %d failed (total: %d)",
        success_count,
        fail_count,
        len(users_with_email),
    )
