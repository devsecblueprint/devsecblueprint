"""Admin Discord service functions for user management.

Provides admin-level operations for viewing user details, triggering syncs,
disconnecting Discord accounts, and viewing audit logs.

Admin authorization is handled at the handler level (require_admin decorator);
these functions assume the caller is already verified as an admin.

Validates: Requirements 14.1-14.6
"""

import logging

from config.settings import (
    DISCORD_BOT_SECRET_NAME,
    DISCORD_GUILD_ID,
    MANAGED_ROLE_IDS,
)
from models.audit_event import AuditEvent, AuditEventType
from services.audit import write_audit_log
from services.membership_db import (
    deactivate_discord_connection,
    get_discord_active,
    get_membership,
    get_user_audit_log,
)
from services.secrets import get_secret
from services.sqs_publisher import publish_sync_event
from utils.discord_api import DiscordClient

logger = logging.getLogger(__name__)


def get_admin_user_detail(target_user_id: str) -> dict | None:
    """Get detailed Discord/membership info for a user (admin view).

    Loads the MEMBERSHIP record and DISCORD_ACTIVE record for the target user
    and returns a consolidated view of their status.

    Args:
        target_user_id: The DSB user ID to look up.

    Returns:
        A dict with user detail fields, or None if the user has no
        membership or Discord records (404 indicator).
    """
    membership_item = get_membership(target_user_id)
    discord_active = get_discord_active(target_user_id)

    if not membership_item and not discord_active:
        return None

    result = {
        "user_id": target_user_id,
        "membership_tier": (
            membership_item.get("membership_tier", {}).get("S", "FREE")
            if membership_item
            else "FREE"
        ),
        "stripe_subscription_status": (
            membership_item.get("subscription_status", {}).get("S")
            if membership_item
            else None
        ),
        "stripe_customer_id": (
            membership_item.get("stripe_customer_id", {}).get("S")
            if membership_item
            else None
        ),
    }

    if discord_active:
        result.update(
            {
                "discord_connected": True,
                "discord_username": discord_active.get("username", {}).get("S"),
                "discord_user_id": discord_active.get("discord_user_id", {}).get("S"),
                "platform_state": discord_active.get("platform_state", {}).get("S"),
                "last_synced_at": discord_active.get("last_synced_at", {}).get("S"),
                "last_sync_status": discord_active.get("last_sync_status", {}).get("S"),
            }
        )
    else:
        result.update(
            {
                "discord_connected": False,
                "discord_username": None,
                "discord_user_id": None,
                "platform_state": None,
                "last_synced_at": None,
                "last_sync_status": None,
            }
        )

    return result


def admin_trigger_sync(
    admin_user_id: str, target_user_id: str, reason: str = "Admin triggered"
) -> dict:
    """Trigger Discord role sync for a user (admin action).

    Publishes a sync event to the SQS FIFO queue and writes an
    Admin_Override audit entry.

    Args:
        admin_user_id: The admin performing the action.
        target_user_id: The user whose roles should be synced.
        reason: Reason for the manual sync trigger.

    Returns:
        A dict with success status and user_id.
    """
    publish_sync_event(target_user_id, "admin_sync", None)

    write_audit_log(
        AuditEvent.build(
            AuditEventType.ADMIN_OVERRIDE, target_user_id, f"admin:{admin_user_id}"
        ).with_reason(f"Sync triggered: {reason}")
    )

    return {"success": True, "user_id": target_user_id}


def admin_disconnect(admin_user_id: str, target_user_id: str, reason: str) -> dict:
    """Disconnect a user's Discord account (admin action).

    Validates the reason field, deactivates the Discord connection,
    attempts to remove managed roles from the Discord guild, and
    writes audit entries.

    Args:
        admin_user_id: The admin performing the action.
        target_user_id: The user whose Discord should be disconnected.
        reason: Reason for the disconnect (5-500 characters).

    Returns:
        A dict with cleanup_status and user_id.

    Raises:
        ValueError: If reason is invalid or user has no active connection.
    """
    # Validate reason length
    if not reason or len(reason) < 5:
        raise ValueError("Reason must be at least 5 characters")
    if len(reason) > 500:
        raise ValueError("Reason must not exceed 500 characters")

    active_record = get_discord_active(target_user_id)
    if not active_record:
        raise ValueError("Target user has no active Discord connection")

    discord_user_id = active_record.get("discord_user_id", {}).get("S", "")

    # Deactivate the connection in DynamoDB
    deactivate_discord_connection(target_user_id, discord_user_id, f"Admin: {reason}")

    # Try to remove managed roles from the Discord guild
    cleanup_status = "completed"
    try:
        bot_token_data = get_secret(DISCORD_BOT_SECRET_NAME)
        bot_token = bot_token_data.get("secret_key")
        if bot_token and DISCORD_GUILD_ID:
            client = DiscordClient(bot_token, DISCORD_GUILD_ID)
            for role_id in MANAGED_ROLE_IDS:
                client.remove_role(discord_user_id, role_id)
    except Exception as e:
        logger.error("Role removal failed during admin disconnect: %s", e)
        cleanup_status = "failed"

    # Write Admin_Override audit entry
    write_audit_log(
        AuditEvent.build(
            AuditEventType.ADMIN_OVERRIDE, target_user_id, f"admin:{admin_user_id}"
        )
        .with_discord(discord_user_id)
        .with_reason(reason)
    )
    # Write Disconnected audit entry
    write_audit_log(
        AuditEvent.build(
            AuditEventType.DISCONNECTED, target_user_id, f"admin:{admin_user_id}"
        )
        .with_discord(discord_user_id)
        .with_reason(reason)
    )

    return {"cleanup_status": cleanup_status, "user_id": target_user_id}


def get_admin_audit_log(target_user_id: str) -> list[dict]:
    """Get audit log entries for a user (admin view).

    Queries DynamoDB with PK=USER#{target_user_id}, SK begins_with AUDIT#,
    ScanIndexForward=false, Limit=100 to return the most recent entries first.

    Args:
        target_user_id: The user whose audit log to retrieve.

    Returns:
        A list of formatted audit entry dicts with event_type, timestamp,
        actor, and optional detail fields.
    """
    items = get_user_audit_log(target_user_id, limit=100)

    formatted = []
    for item in items:
        entry = {
            "event_type": item.get("event_type", {}).get("S"),
            "timestamp": item.get("timestamp", {}).get("S"),
            "actor": item.get("actor", {}).get("S"),
            "dsb_user_id": item.get("dsb_user_id", {}).get("S"),
        }
        # Add optional fields if present
        if item.get("discord_user_id", {}).get("S"):
            entry["discord_user_id"] = item["discord_user_id"]["S"]
        if item.get("previous_state", {}).get("S"):
            entry["previous_state"] = item["previous_state"]["S"]
        if item.get("new_state", {}).get("S"):
            entry["new_state"] = item["new_state"]["S"]
        if item.get("reason", {}).get("S"):
            entry["reason"] = item["reason"]["S"]
        if item.get("error_message", {}).get("S"):
            entry["error_message"] = item["error_message"]["S"]
        # Role lists
        if "roles_added" in item and "L" in item.get("roles_added", {}):
            entry["roles_added"] = [r["S"] for r in item["roles_added"]["L"]]
        if "roles_removed" in item and "L" in item.get("roles_removed", {}):
            entry["roles_removed"] = [r["S"] for r in item["roles_removed"]["L"]]

        formatted.append(entry)

    return formatted
