"""Discord role synchronization service.

Resolves the expected Discord role from a user's membership tier and
synchronizes it via the Discord API. Ensures exactly one managed role is
assigned (the one matching the current tier) and all other managed roles
are removed.

Designed for idempotency — multiple calls produce the same state.

Validates: Requirements 9.1–9.7, 11.1–11.12
"""

import logging
import os
from datetime import datetime, timezone

import boto3

from config.settings import (
    DISCORD_BOT_SECRET_NAME,
    DISCORD_GUILD_ID,
    MANAGED_ROLE_IDS,
    TIER_ROLE_MAP,
)
from models.audit_event import AuditEvent, AuditEventType
from services.audit import write_audit_log
from services import membership_db
from services.secrets import get_secret
from utils.discord_api import DiscordClient

logger = logging.getLogger(__name__)


class DiscordSyncError(Exception):
    """Raised when Discord API operations fail during sync."""

    pass


def sync_discord_roles(user_id: str) -> None:
    """Synchronize a user's Discord roles to match their membership tier.

    Loads the user's membership tier, verifies Discord connection preconditions,
    computes the expected role, fetches current Discord roles, and makes
    add/remove API calls as needed.

    This function is idempotent — calling it multiple times for the same user
    and state produces the same result without duplicate side effects.

    Args:
        user_id: The DSB user identifier.

    Raises:
        DiscordSyncError: If Discord API calls fail. The caller (SQS handler)
            should let this propagate so the message returns to the queue for retry.

    Validates: Requirements 9.1–9.7, 11.1–11.12
    """
    # --- Load membership tier (default FREE if missing) ---
    membership = membership_db.get_membership(user_id)
    if membership:
        tier = membership.get("membership_tier", {}).get("S", "FREE")
    else:
        tier = "FREE"

    # --- Load DISCORD_ACTIVE record and verify preconditions ---
    discord_active = membership_db.get_discord_active(user_id)

    if not discord_active:
        logger.info("Sync skipped for user %s: no DISCORD_ACTIVE record", user_id)
        return

    active = discord_active.get("active", {}).get("BOOL", False)
    platform_state = discord_active.get("platform_state", {}).get("S", "")
    discord_user_id = discord_active.get("discord_user_id", {}).get("S", "")

    if not active:
        logger.info("Sync skipped for user %s: connection not active", user_id)
        _update_sync_status(user_id, "SKIPPED")
        return

    if platform_state != "Server_Joined" and platform_state != "Roles_Synced":
        logger.info(
            "Sync skipped for user %s: platform_state=%s (requires Server_Joined or Roles_Synced)",
            user_id,
            platform_state,
        )
        _update_sync_status(user_id, "SKIPPED")
        return

    if not discord_user_id:
        logger.info("Sync skipped for user %s: missing discord_user_id", user_id)
        _update_sync_status(user_id, "SKIPPED")
        return

    # --- Determine expected role from tier ---
    expected_role_id = TIER_ROLE_MAP.get(tier)
    if not expected_role_id:
        logger.warning("No role mapping found for tier %s, user %s", tier, user_id)
        _update_sync_status(user_id, "SKIPPED")
        return

    # --- Build set of managed role IDs ---
    managed_role_ids = set(MANAGED_ROLE_IDS)

    # --- Fetch current Discord roles via Discord API ---
    try:
        bot_token_data = get_secret(DISCORD_BOT_SECRET_NAME)
        bot_token = bot_token_data.get("secret_key")
        if not bot_token:
            raise DiscordSyncError("Bot token not found in secrets")

        if not DISCORD_GUILD_ID:
            raise DiscordSyncError("DISCORD_GUILD_ID not configured")

        client = DiscordClient(bot_token, DISCORD_GUILD_ID)
        current_roles = client.get_member_roles(discord_user_id)
    except DiscordSyncError:
        raise
    except Exception as e:
        error_msg = f"Failed to fetch Discord roles for user {user_id}: {e}"
        logger.error(error_msg)
        _update_sync_status(user_id, "FAILED")
        write_audit_log(
            AuditEvent.build(AuditEventType.SYNC_FAILED, user_id, "system")
            .with_discord(discord_user_id)
            .with_error(error_msg)
        )
        raise DiscordSyncError(error_msg) from e

    if current_roles is None:
        # User is not in the guild
        logger.info("Sync skipped for user %s: user not in guild", user_id)
        _update_sync_status(user_id, "SKIPPED")
        return

    current_roles_set = set(current_roles)

    # --- Compare: identify roles to add and remove ---
    roles_to_add = []
    roles_to_remove = []

    # Expected role should be present
    if expected_role_id not in current_roles_set:
        roles_to_add.append(expected_role_id)

    # Other managed roles should be absent
    for role_id in managed_role_ids:
        if role_id != expected_role_id and role_id in current_roles_set:
            roles_to_remove.append(role_id)

    # --- If no diff, skip API calls ---
    if not roles_to_add and not roles_to_remove:
        logger.info(
            "Sync for user %s: roles already correct, no changes needed", user_id
        )
        _update_sync_status(user_id, "SUCCESS")
        _update_platform_state(user_id, "Roles_Synced")
        return

    # --- Execute role changes via Discord API ---
    try:
        for role_id in roles_to_add:
            success = client.add_role(discord_user_id, role_id)
            if not success:
                raise DiscordSyncError(
                    f"Failed to add role {role_id} to user {discord_user_id}"
                )

        for role_id in roles_to_remove:
            success = client.remove_role(discord_user_id, role_id)
            if not success:
                raise DiscordSyncError(
                    f"Failed to remove role {role_id} from user {discord_user_id}"
                )
    except DiscordSyncError as e:
        error_msg = str(e)
        logger.error(
            "Discord API failure during sync for user %s: %s", user_id, error_msg
        )
        _update_sync_status(user_id, "FAILED")
        write_audit_log(
            AuditEvent.build(AuditEventType.SYNC_FAILED, user_id, "system")
            .with_discord(discord_user_id)
            .with_error(error_msg)
        )
        raise

    # --- Success: update status and write audit ---
    _update_sync_status(user_id, "SUCCESS")
    _update_platform_state(user_id, "Roles_Synced")

    # Write audit entries for role changes
    if roles_to_add:
        write_audit_log(
            AuditEvent.build(AuditEventType.ROLES_ADDED, user_id, "system")
            .with_discord(discord_user_id)
            .with_roles(added=roles_to_add)
        )

    if roles_to_remove:
        write_audit_log(
            AuditEvent.build(AuditEventType.ROLES_REMOVED, user_id, "system")
            .with_discord(discord_user_id)
            .with_roles(removed=roles_to_remove)
        )

    # Write overall sync success audit
    write_audit_log(
        AuditEvent.build(AuditEventType.SYNC_SUCCESSFUL, user_id, "system")
        .with_discord(discord_user_id)
        .with_roles(added=roles_to_add or None, removed=roles_to_remove or None)
    )

    logger.info(
        "Sync completed for user %s: added=%s, removed=%s",
        user_id,
        roles_to_add,
        roles_to_remove,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _update_sync_status(user_id: str, status: str) -> None:
    """Update last_synced_at and last_sync_status on the DISCORD_ACTIVE record.

    Args:
        user_id: DSB user identifier.
        status: Sync status value (SUCCESS, FAILED, SKIPPED).
    """
    table_name = os.environ.get("MEMBERSHIP_TABLE")
    if not table_name:
        logger.error("MEMBERSHIP_TABLE environment variable not set")
        return

    now = datetime.now(timezone.utc).isoformat()

    dynamodb = boto3.client("dynamodb")
    try:
        dynamodb.update_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "DISCORD_ACTIVE"},
            },
            UpdateExpression="SET last_synced_at = :ts, last_sync_status = :st",
            ExpressionAttributeValues={
                ":ts": {"S": now},
                ":st": {"S": status},
            },
        )
    except Exception as e:
        logger.error("Failed to update sync status for user %s: %s", user_id, e)


def _update_platform_state(user_id: str, platform_state: str) -> None:
    """Update the platform_state field on the DISCORD_ACTIVE record.

    Args:
        user_id: DSB user identifier.
        platform_state: New platform state value.
    """
    table_name = os.environ.get("MEMBERSHIP_TABLE")
    if not table_name:
        logger.error("MEMBERSHIP_TABLE environment variable not set")
        return

    dynamodb = boto3.client("dynamodb")
    try:
        dynamodb.update_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "DISCORD_ACTIVE"},
            },
            UpdateExpression="SET platform_state = :ps",
            ExpressionAttributeValues={
                ":ps": {"S": platform_state},
            },
        )
    except Exception as e:
        logger.error("Failed to update platform_state for user %s: %s", user_id, e)
