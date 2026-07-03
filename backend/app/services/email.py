"""Email service using Mailgun API.

Sends transactional emails (welcome email, notifications) via the Mailgun
HTTP API. Retrieves the API key from AWS SSM Parameter Store with caching.
"""

import logging
import time

import boto3
import httpx
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# In-memory cache for the Mailgun API key
_api_key_cache: dict = {"value": None, "ts": 0.0}
_CACHE_TTL = 900  # 15 minutes


def _get_api_key(param_name: str) -> str:
    """Retrieve Mailgun API key from SSM Parameter Store with caching."""
    now = time.time()
    if _api_key_cache["value"] and (now - _api_key_cache["ts"]) < _CACHE_TTL:
        return _api_key_cache["value"]

    try:
        client = boto3.client("ssm")
        response = client.get_parameter(Name=param_name, WithDecryption=True)
        value = response["Parameter"]["Value"]
    except (ClientError, KeyError) as e:
        raise Exception(f"Failed to retrieve Mailgun API key: {e}")

    _api_key_cache["value"] = value
    _api_key_cache["ts"] = now
    return value


def send_welcome_email(
    username: str,
    email: str,
    mailgun_domain: str,
    mailgun_param_name: str,
) -> bool:
    """Send a welcome email to a newly registered user via Mailgun API.

    Args:
        username: New user's display name for the greeting.
        email: Recipient email address.
        mailgun_domain: Mailgun sending domain.
        mailgun_param_name: SSM parameter name for the Mailgun API key.

    Returns:
        True if email sent successfully, False otherwise.
    """
    if not mailgun_domain or not mailgun_param_name:
        logger.warning("Mailgun not configured, skipping welcome email")
        return False

    try:
        api_key = _get_api_key(mailgun_param_name)
    except Exception as e:
        logger.error("Failed to get Mailgun API key: %s", e)
        return False

    mailgun_url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"

    # Simple HTML welcome email (no template dependency)
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h1 style="color: #2563eb;">Welcome to The DevSec Blueprint!</h1>
        <p>Hi {username},</p>
        <p>Thanks for joining The DevSec Blueprint platform. We're excited to have you on board!</p>
        <p>Get started by exploring our learning paths and building your DevSecOps skills.</p>
        <p><a href="https://devsecblueprint.com" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Visit Platform</a></p>
        <p>Happy learning!<br>The DevSec Blueprint Team</p>
    </body>
    </html>
    """

    try:
        response = httpx.post(
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
            logger.info("Welcome email sent successfully to %s", email)
            return True
        else:
            logger.error(
                "Mailgun API error: %d - %s", response.status_code, response.text
            )
            return False

    except Exception as e:
        logger.error("Failed to send welcome email: %s", e)
        return False
