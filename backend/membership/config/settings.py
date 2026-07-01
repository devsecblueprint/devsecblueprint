"""
Environment variable loading and validation for the membership service.

Loads configuration from environment variables at module initialization.
Validates Discord IDs (guild and role IDs) format but does not crash on
invalid values — instead logs a warning and sets them to None.

Validates: Requirements 10.4, 10.5, 10.6, 19.1
"""

import os
import logging

logger = logging.getLogger(__name__)


def _validate_snowflake(value: str, name: str) -> str | None:
    """
    Validate a Discord snowflake ID (17-20 numeric chars).

    Returns the value if valid, None otherwise. Logs a warning on invalid values
    so the service can start without crashing.
    """
    if not value:
        logger.warning("Environment variable %s is not set", name)
        return None
    if not (17 <= len(value) <= 20 and value.isdigit()):
        logger.warning(
            "Environment variable %s has invalid snowflake format: '%s'", name, value
        )
        return None
    return value


# --- Required environment variables (service won't function without these) ---

MEMBERSHIP_TABLE: str = os.environ.get("MEMBERSHIP_TABLE", "")
DISCORD_SYNC_QUEUE_URL: str = os.environ.get("DISCORD_SYNC_QUEUE_URL", "")

# --- Secret names for AWS Secrets Manager lookups ---

DISCORD_SECRET_NAME: str = os.environ.get("DISCORD_SECRET_NAME", "")
DISCORD_BOT_SECRET_NAME: str = os.environ.get("DISCORD_BOT_SECRET_NAME", "")
STRIPE_SECRET_NAME: str = os.environ.get("STRIPE_SECRET_NAME", "")
STRIPE_WEBHOOK_SECRET_NAME: str = os.environ.get("STRIPE_WEBHOOK_SECRET_NAME", "")
JWT_SECRET_NAME: str = os.environ.get("JWT_SECRET_NAME", "")

# --- Frontend URL for redirects and CORS ---

FRONTEND_URL: str = os.environ.get(
    "FRONTEND_URL", "https://staging.devsecblueprint.com"
)

# --- Admin users (comma-separated "provider:username" pairs) ---

ADMIN_USERS: str = os.environ.get("ADMIN_USERS", "")

# --- Discord snowflake IDs (validated at load time, warn on invalid) ---

DISCORD_GUILD_ID: str | None = _validate_snowflake(
    os.environ.get("DISCORD_GUILD_ID", ""), "DISCORD_GUILD_ID"
)
DISCORD_ROLE_FREE_ID: str | None = _validate_snowflake(
    os.environ.get("DISCORD_ROLE_FREE_ID", ""), "DISCORD_ROLE_FREE_ID"
)
DISCORD_ROLE_EXPLORER_ID: str | None = _validate_snowflake(
    os.environ.get("DISCORD_ROLE_EXPLORER_ID", ""), "DISCORD_ROLE_EXPLORER_ID"
)
DISCORD_ROLE_BUILDER_ID: str | None = _validate_snowflake(
    os.environ.get("DISCORD_ROLE_BUILDER_ID", ""), "DISCORD_ROLE_BUILDER_ID"
)
DISCORD_ROLE_BUILDER_ACADEMY_ID: str | None = _validate_snowflake(
    os.environ.get("DISCORD_ROLE_BUILDER_ACADEMY_ID", ""),
    "DISCORD_ROLE_BUILDER_ACADEMY_ID",
)

# --- Tier-to-role mapping ---

TIER_ROLE_MAP: dict[str, str | None] = {
    "FREE": DISCORD_ROLE_FREE_ID,
    "EXPLORER": DISCORD_ROLE_EXPLORER_ID,
    "BUILDER": DISCORD_ROLE_BUILDER_ID,
    "BUILDER_ACADEMY": DISCORD_ROLE_BUILDER_ACADEMY_ID,
}

# --- All managed role IDs (excluding None) ---

MANAGED_ROLE_IDS: list[str] = [
    role_id for role_id in TIER_ROLE_MAP.values() if role_id is not None
]


def get_settings() -> dict:
    """
    Return all settings as a dictionary.

    Useful for debugging and testing.
    """
    return {
        "MEMBERSHIP_TABLE": MEMBERSHIP_TABLE,
        "DISCORD_SYNC_QUEUE_URL": DISCORD_SYNC_QUEUE_URL,
        "DISCORD_SECRET_NAME": DISCORD_SECRET_NAME,
        "DISCORD_BOT_SECRET_NAME": DISCORD_BOT_SECRET_NAME,
        "STRIPE_SECRET_NAME": STRIPE_SECRET_NAME,
        "STRIPE_WEBHOOK_SECRET_NAME": STRIPE_WEBHOOK_SECRET_NAME,
        "JWT_SECRET_NAME": JWT_SECRET_NAME,
        "FRONTEND_URL": FRONTEND_URL,
        "ADMIN_USERS": ADMIN_USERS,
        "DISCORD_GUILD_ID": DISCORD_GUILD_ID,
        "DISCORD_ROLE_FREE_ID": DISCORD_ROLE_FREE_ID,
        "DISCORD_ROLE_EXPLORER_ID": DISCORD_ROLE_EXPLORER_ID,
        "DISCORD_ROLE_BUILDER_ID": DISCORD_ROLE_BUILDER_ID,
        "DISCORD_ROLE_BUILDER_ACADEMY_ID": DISCORD_ROLE_BUILDER_ACADEMY_ID,
        "TIER_ROLE_MAP": TIER_ROLE_MAP,
        "MANAGED_ROLE_IDS": MANAGED_ROLE_IDS,
    }
