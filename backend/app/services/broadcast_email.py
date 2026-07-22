"""Broadcast email delivery — sends broadcast notifications to all users via SES.

Called as a FastAPI BackgroundTask from the admin broadcast creation endpoint.
Iterates all registered users with email addresses, renders the broadcast
content (markdown to HTML), and sends via AWS SES. Failures are logged per-user
but do not halt delivery to remaining users.
"""

import logging
from typing import Any

try:
    import markdown
except ImportError:
    markdown = None  # type: ignore[assignment]

from app.config import Settings
from app.services.admin_service import AdminService
from app.services.email import _send_email, _jinja_env

logger = logging.getLogger(__name__)


def _render_markdown_to_html(md_text: str) -> str:
    """Convert markdown text to HTML.

    Supports headings, bold, italic, links, lists, and code blocks.
    """
    if markdown is None:
        return f"<p>{md_text}</p>"
    return markdown.markdown(
        md_text,
        extensions=["extra", "nl2br", "sane_lists"],
    )


def send_broadcast_emails(broadcast: dict[str, Any], settings: Settings) -> None:
    """Send a broadcast notification email to all users with email addresses.

    This function is designed to be called as a BackgroundTask. It:
    1. Fetches all registered users
    2. Filters to those with non-empty email, deduplicates
    3. Renders the broadcast markdown to HTML
    4. Sends an email to each user via AWS SES

    Args:
        broadcast: Dict with title, message (markdown), link, created_by.
        settings: Application settings instance.
    """
    # Render markdown to HTML
    title = broadcast.get("title", "")
    message_md = broadcast.get("message", "")
    link = broadcast.get("link", "")
    message_html = _render_markdown_to_html(message_md)

    # Load email template
    try:
        template = _jinja_env.get_template("broadcast_notification.html")
    except Exception as e:
        logger.error("Broadcast email skipped: template load failed: %s", e)
        return

    # Fetch all users
    try:
        svc = AdminService(settings)
        all_users = svc.get_all_registered_users()
    except Exception as e:
        logger.error("Broadcast email skipped: failed to fetch users: %s", e)
        return

    # Filter to users with email addresses and deduplicate
    seen_emails: set[str] = set()
    unique_users = []
    for user in all_users:
        email = user.get("email", "").strip().lower()
        if email and email not in seen_emails:
            seen_emails.add(email)
            unique_users.append(user)

    if not unique_users:
        logger.info("Broadcast email: no users with email addresses found")
        return

    logger.info("Broadcast email: sending '%s' to %d users", title, len(unique_users))

    # Send to each user (personalized with username)
    success_count = 0
    fail_count = 0

    for user in unique_users:
        email = user["email"].strip()
        username = (
            user.get("username", "").strip() or user.get("github_username", "").strip()
        )

        try:
            html_body = template.render(
                title=title,
                message_html=message_html,
                link=link,
                username=username,
            )
        except Exception as e:
            logger.warning("Broadcast email render failed for %s: %s", email, e)
            fail_count += 1
            continue

        try:
            sent = _send_email(
                to_email=email,
                subject=f"{title}",
                html_body=html_body,
                sender_email=settings.ses_sender_email,
                ses_region=settings.ses_region,
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
        len(unique_users),
    )
