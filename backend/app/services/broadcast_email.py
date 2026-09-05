"""Broadcast email delivery — sends broadcast notifications to all users via SES.

Called as a FastAPI BackgroundTask from the admin broadcast creation endpoint.
Iterates all registered users with email addresses, renders the broadcast
content (markdown to HTML), and sends via AWS SES. Failures are logged per-user
but do not halt delivery to remaining users.
"""

import logging
import re
from typing import Any

try:
    import markdown
except ImportError:
    markdown = None  # type: ignore[assignment]

from app.config import Settings
from app.services.admin_service import AdminService
from app.services.email import _send_email, _jinja_env

logger = logging.getLogger(__name__)

# Inline styles applied to every <img> in broadcast bodies. Broadcast images are
# authored as remote markdown links (![alt](url)); we never embed binary images.
# Many email clients (Gmail, Outlook) strip or ignore <style> blocks, so the
# constraints must live inline on each tag to render responsively — especially
# on mobile, where an unconstrained wide image blows past the viewport.
_IMG_INLINE_STYLE = (
    "display:block;"
    "width:100%;"
    "max-width:100%;"
    "height:auto;"
    "margin:16px auto;"
    "border-radius:6px;"
)

# Matches an <img ...> opening tag, capturing an existing style attribute (if any)
# so we can merge rather than clobber author-provided styles.
_IMG_TAG_RE = re.compile(r"<img\b([^>]*?)\s*/?>", re.IGNORECASE)
_STYLE_ATTR_RE = re.compile(r'\sstyle\s*=\s*"([^"]*)"', re.IGNORECASE)
_SRC_ATTR_RE = re.compile(r'\ssrc\s*=\s*"([^"]*)"', re.IGNORECASE)
# Detects an <img> that is already the child of an anchor (e.g. authored as a
# linked image [![alt](img)](href)) so we don't wrap it a second time.
_ANCHOR_BEFORE_IMG_RE = re.compile(r"<a\b[^>]*>\s*$", re.IGNORECASE)


def _make_images_responsive(html: str) -> str:
    """Rewrite every <img> tag in rendered HTML for reliable email display.

    Two transformations are applied to each image:
    1. Inline responsive styles are injected so images never overflow the email
       column and scale down on mobile, regardless of intrinsic dimensions.
       Existing style declarations on the tag are preserved and take precedence.
    2. The image is wrapped in an anchor pointing at its own source so readers
       can tap to open the full-resolution version in a new tab — the practical
       escape hatch for a screenshot that is too dense to read when scaled down.
       Images that are already inside an author-supplied anchor are left as-is
       (styles still applied) to avoid nested links.
    """

    def _rewrite(match: re.Match[str]) -> str:
        attrs = match.group(1)

        existing_style_match = _STYLE_ATTR_RE.search(attrs)
        if existing_style_match:
            author_style = existing_style_match.group(1).strip()
            if author_style and not author_style.endswith(";"):
                author_style += ";"
            # Base constraints first so author declarations override on conflict.
            merged_style = f"{_IMG_INLINE_STYLE}{author_style}"
            attrs = _STYLE_ATTR_RE.sub("", attrs)
        else:
            merged_style = _IMG_INLINE_STYLE

        src_match = _SRC_ATTR_RE.search(attrs)
        src = src_match.group(1).strip() if src_match else ""

        attrs = attrs.strip()
        prefix = f"{attrs} " if attrs else ""
        img_tag = f'<img {prefix}style="{merged_style}">'

        # Skip wrapping when the image is already inside an anchor, or when it
        # has no usable http(s) source to link to.
        already_linked = bool(_ANCHOR_BEFORE_IMG_RE.search(html, 0, match.start()))
        if already_linked or not src.lower().startswith(("http://", "https://")):
            return img_tag

        return (
            f'<a href="{src}" target="_blank" rel="noopener noreferrer" '
            f'style="text-decoration:none;">{img_tag}</a>'
        )

    return _IMG_TAG_RE.sub(_rewrite, html)


def _render_markdown_to_html(md_text: str) -> str:
    """Convert markdown text to HTML.

    Supports headings, bold, italic, links, lists, and code blocks. Linked
    images are rewritten with inline responsive styles so they render cleanly
    across email clients and on mobile.
    """
    if markdown is None:
        return f"<p>{md_text}</p>"
    html = markdown.markdown(
        md_text,
        extensions=["extra", "nl2br", "sane_lists"],
    )
    return _make_images_responsive(html)


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
