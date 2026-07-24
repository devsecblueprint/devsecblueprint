"""Discord identity management router — /api/discord/* routes.

Provides endpoints for managing a user's Discord identity link:
- POST /api/discord/confirm — confirm a pending Discord connection
- DELETE /api/discord/disconnect — unlink an active Discord account
- GET /api/discord/status — get current Discord link status

All routes require JWT authentication via the get_current_user dependency.

Note: Discord OAuth start/callback are handled in the auth router.

Requirements: 4.3, 5.2
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth.jwt import get_current_user
from app.background.discord_tasks import enqueue_discord_sync
from app.config import Settings
from app.dependencies import get_settings
from app.services.discord_identity import (
    confirm_identity,
    disconnect,
    get_status,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/discord", tags=["discord"])


@router.post("/confirm")
async def discord_confirm(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Confirm a pending Discord identity link.

    After a user completes the Discord OAuth flow, their identity is stored
    in a pending state. This endpoint confirms the link, activates the
    connection, and triggers guild join + role assignment via a background task.

    Returns:
        dict with discord_user_id, username, display_name, avatar_url,
        and platform_state.
    """
    user_id = user.get("sub")
    try:
        result = confirm_identity(user_id, settings)

        # Enqueue Discord role sync as background task (replaces SQS publish)
        enqueue_discord_sync(
            background_tasks,
            user_id=user_id,
            operation="discord_connected",
            reason="Discord identity confirmed",
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/disconnect")
async def discord_disconnect(
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Disconnect (unlink) the user's Discord account.

    Deactivates the Discord connection, removes managed roles from the
    Discord guild, and writes an audit log entry.

    Returns:
        dict with cleanup_status ("completed" or "failed").
    """
    user_id = user.get("sub")
    try:
        result = disconnect(user_id, settings)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def discord_status(
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Get the current Discord connection status for the authenticated user.

    Returns connection state including whether an active or pending connection
    exists, the linked Discord username and avatar, platform state, and sync info.

    Returns:
        dict with connected, pending, discord_username, discord_avatar_url,
        platform_state, last_synced_at, and last_sync_status.
    """
    user_id = user.get("sub")
    result = get_status(user_id, settings)
    return result
