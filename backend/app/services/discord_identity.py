"""Discord identity service for link/unlink/status operations.

Provides a bridge to the existing membership Discord identity service,
adapting it for use with the FastAPI application's dependency injection
and settings model.

This service covers:
- Initiating Discord OAuth (start_oauth)
- Processing the OAuth callback (handle_callback)
- Confirming a pending Discord connection (POST /api/discord/confirm)
- Disconnecting an active Discord account (DELETE /api/discord/disconnect)
- Querying Discord connection status (GET /api/discord/status)

The membership service layer is deeply coupled to its own config and models,
so we bridge environment variables from Settings before calling it.

Requirements: 4.3
"""

import logging
import os
import sys

from app.config import Settings

logger = logging.getLogger(__name__)

# The membership package has its own internal imports (config.settings, models, etc.)
# We need its root on sys.path for those to resolve.
_MEMBERSHIP_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "membership",
)
_MEMBERSHIP_ROOT = os.path.normpath(_MEMBERSHIP_ROOT)


def _ensure_path() -> None:
    """Ensure membership package root is on sys.path."""
    if _MEMBERSHIP_ROOT not in sys.path and os.path.isdir(_MEMBERSHIP_ROOT):
        sys.path.insert(0, _MEMBERSHIP_ROOT)


def _ensure_membership_env(settings: Settings) -> None:
    """Set environment variables expected by the membership service layer."""
    env_map = {
        "MEMBERSHIP_TABLE": settings.membership_table,
        "DISCORD_SECRET_NAME": settings.discord_secret_name,
        "DISCORD_BOT_SECRET_NAME": settings.discord_bot_secret_name,
        "DISCORD_GUILD_ID": settings.discord_guild_id,
        "DISCORD_ROLE_FREE_ID": settings.discord_role_free_id,
        "DISCORD_ROLE_EXPLORER_ID": settings.discord_role_explorer_id,
        "DISCORD_ROLE_BUILDER_ID": settings.discord_role_builder_id,
        "DISCORD_ROLE_BUILDER_ACADEMY_ID": settings.discord_role_builder_academy_id,
        "DISCORD_CALLBACK_URL": settings.discord_callback_url,
        "FRONTEND_URL": settings.frontend_url,
    }
    for key, value in env_map.items():
        if value and not os.environ.get(key):
            os.environ[key] = value


def start_oauth(user_id: str, settings: Settings) -> str:
    """Initiate Discord OAuth flow for a user.

    Args:
        user_id: The authenticated user's ID (from JWT sub claim).
        settings: Application settings.

    Returns:
        The Discord authorization URL to redirect the user to.

    Raises:
        ValueError: If user already has an active Discord connection.
    """
    _ensure_path()
    _ensure_membership_env(settings)

    from services.discord_identity import start_oauth as _start

    return _start(user_id)


def handle_callback(code: str, state: str, settings: Settings) -> None:
    """Process the Discord OAuth callback.

    Args:
        code: Authorization code from Discord.
        state: State parameter for CSRF validation.
        settings: Application settings.

    Raises:
        ValueError: If state is invalid or callback processing fails.
    """
    _ensure_path()
    _ensure_membership_env(settings)

    from services.discord_identity import handle_callback as _handle

    _handle(code, state)


def confirm_identity(user_id: str, settings: Settings) -> dict:
    """Confirm a pending Discord identity and activate the connection.

    Args:
        user_id: The authenticated user's ID (from JWT sub claim).
        settings: Application settings.

    Returns:
        dict with discord_user_id, username, display_name, avatar_url,
        and platform_state.

    Raises:
        ValueError: If no pending Discord connection is found.
    """
    _ensure_path()
    _ensure_membership_env(settings)

    from services.discord_identity import confirm_identity as _confirm

    return _confirm(user_id)


def disconnect(user_id: str, settings: Settings) -> dict:
    """Disconnect the user's Discord account.

    Args:
        user_id: The authenticated user's ID (from JWT sub claim).
        settings: Application settings.

    Returns:
        dict with cleanup_status ("completed" or "failed").

    Raises:
        ValueError: If no active Discord connection is found.
    """
    _ensure_path()
    _ensure_membership_env(settings)

    from services.discord_identity import disconnect as _disconnect

    return _disconnect(user_id)


def get_status(user_id: str, settings: Settings) -> dict:
    """Get Discord connection status for a user.

    Args:
        user_id: The authenticated user's ID (from JWT sub claim).
        settings: Application settings.

    Returns:
        dict with connected, pending, discord_username, discord_avatar_url,
        platform_state, last_synced_at, and last_sync_status.
    """
    _ensure_path()
    _ensure_membership_env(settings)

    from services.discord_identity import get_status as _get_status

    return _get_status(user_id)
