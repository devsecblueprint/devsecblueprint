"""Discord role synchronization service.

Provides main entry points:
- sync_discord_access(user_id, settings): Full lifecycle sync (check/enroll guild + roles)
- perform_sync(user_id, operation, reason): Async wrapper for background tasks
- reconcile_all_members(): Scan all active Discord users and sync each one

Ported from backend/membership/services/discord_sync.py and
backend/membership/handlers/sync_handlers.py (handle_reconciliation).

Requirements: 5.1-5.6, 6.1-6.5
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings
from app.dependencies import get_settings

logger = logging.getLogger("app.services.discord_sync")

# Rate limit delay between Discord API calls during reconciliation
RATE_LIMIT_DELAY_SECONDS = 1.0


# ---------------------------------------------------------------------------
# SyncResult dataclass — structured return from sync operations
# ---------------------------------------------------------------------------


@dataclass
class SyncResult:
    """Structured result from Discord sync operations.

    Describes what actions were taken: guild enrollment, role changes,
    sync status, and any errors encountered.
    """

    sync_status: str = "skipped"
    """Overall status: 'success', 'partial', 'failed', or 'skipped'."""

    guild_action: str = "not_attempted"
    """Guild enrollment action: 'joined', 'already_member', 'join_failed', 'not_attempted'."""

    roles_added: list[str] = field(default_factory=list)
    """List of role IDs that were added."""

    roles_removed: list[str] = field(default_factory=list)
    """List of role IDs that were removed."""

    error_code: str | None = None
    """Error code if sync failed: DISCORD_NOT_CONNECTED, DISCORD_OAUTH_EXPIRED,
    DISCORD_GUILD_JOIN_FAILED, DISCORD_ROLE_SYNC_FAILED, DISCORD_API_ERROR."""

    error_message: str | None = None
    """Human-readable error message."""


class DiscordSyncError(Exception):
    """Raised when Discord API operations fail during sync."""

    pass


def _get_tier_role_map(settings: Settings) -> dict[str, str]:
    """Build the tier-to-role mapping from settings.

    Args:
        settings: Application settings instance.

    Returns:
        Mapping of membership tier name to Discord role ID.
    """
    return {
        "FREE": settings.discord_role_free_id,
        "EXPLORER": settings.discord_role_explorer_id,
        "BUILDER": settings.discord_role_builder_id,
        "BUILDER_ACADEMY": settings.discord_role_builder_academy_id,
    }


def _get_managed_role_ids(settings: Settings) -> list[str]:
    """Get all managed role IDs (non-empty values from tier map).

    Args:
        settings: Application settings instance.

    Returns:
        List of Discord role IDs managed by this application.
    """
    tier_map = _get_tier_role_map(settings)
    return [role_id for role_id in tier_map.values() if role_id]


def _get_bot_token(settings: Settings) -> str:
    """Retrieve the Discord bot token from Secrets Manager.

    Args:
        settings: Application settings instance.

    Returns:
        The bot token string.

    Raises:
        DiscordSyncError: If the token cannot be retrieved.
    """
    try:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=settings.discord_bot_secret_name)
        secret_data = json.loads(response["SecretString"])
        token = secret_data.get("secret_key")
        if not token:
            raise DiscordSyncError("Bot token not found in secret")
        return token
    except ClientError as e:
        raise DiscordSyncError(f"Failed to retrieve bot token: {e}") from e
    except (json.JSONDecodeError, KeyError) as e:
        raise DiscordSyncError(f"Failed to parse bot token secret: {e}") from e


def _get_discord_client(settings: Settings):
    """Create a DiscordClient instance using settings.

    Args:
        settings: Application settings instance.

    Returns:
        DiscordClient instance configured with bot token and guild ID.
    """
    from app.services.discord_api import DiscordClient

    bot_token = _get_bot_token(settings)
    guild_id = settings.discord_guild_id

    if not guild_id:
        raise DiscordSyncError("DISCORD_GUILD_ID not configured")

    return DiscordClient(bot_token, guild_id)


def _sync_user_roles(user_id: str, settings: Settings) -> dict[str, Any]:
    """Synchronize a single user's Discord roles to match their membership tier.

    This is the core sync logic ported from the Lambda service. It:
    1. Loads the user's membership tier from DynamoDB
    2. Verifies Discord connection preconditions
    3. Computes the expected role from the tier
    4. Fetches current Discord roles
    5. Adds/removes roles as needed

    Args:
        user_id: DSB user identifier.
        settings: Application settings instance.

    Returns:
        Dict with sync result: {"status": "success"|"skipped"|"failed", ...}

    Raises:
        DiscordSyncError: On Discord API failures.
    """
    dynamodb = boto3.client("dynamodb")
    table_name = settings.membership_table

    # Load membership tier (default FREE if missing)
    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "MEMBERSHIP"},
            },
        )
        membership = response.get("Item")
        tier = (
            membership.get("membership_tier", {}).get("S", "FREE")
            if membership
            else "FREE"
        )
    except ClientError as e:
        logger.error("Failed to get membership for user %s: %s", user_id, e)
        raise DiscordSyncError(f"DynamoDB error: {e}") from e

    # Load DISCORD_ACTIVE record
    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "DISCORD_ACTIVE"},
            },
        )
        discord_active = response.get("Item")
    except ClientError as e:
        logger.error("Failed to get discord active for user %s: %s", user_id, e)
        raise DiscordSyncError(f"DynamoDB error: {e}") from e

    if not discord_active:
        logger.info("Sync skipped for user %s: no DISCORD_ACTIVE record", user_id)
        return {"status": "skipped", "reason": "no_discord_active"}

    # Verify preconditions
    active = discord_active.get("active", {}).get("BOOL", False)
    platform_state = discord_active.get("platform_state", {}).get("S", "")
    discord_user_id = discord_active.get("discord_user_id", {}).get("S", "")

    if not active:
        logger.info("Sync skipped for user %s: connection not active", user_id)
        return {"status": "skipped", "reason": "not_active"}

    if platform_state not in ("Server_Joined", "Roles_Synced"):
        logger.info(
            "Sync skipped for user %s: platform_state=%s", user_id, platform_state
        )
        return {"status": "skipped", "reason": f"platform_state={platform_state}"}

    if not discord_user_id:
        logger.info("Sync skipped for user %s: missing discord_user_id", user_id)
        return {"status": "skipped", "reason": "no_discord_user_id"}

    # Determine expected role from tier
    tier_role_map = _get_tier_role_map(settings)
    expected_role_id = tier_role_map.get(tier)
    managed_role_ids = set(_get_managed_role_ids(settings))

    # If no expected role and no managed roles to remove, skip
    if not expected_role_id and not managed_role_ids:
        logger.warning(
            "No role mapping for tier %s and no managed roles, user %s", tier, user_id
        )
        return {"status": "skipped", "reason": f"no_role_for_tier={tier}"}

    # Fetch current Discord roles
    client = _get_discord_client(settings)
    current_roles = client.get_member_roles(discord_user_id)

    if current_roles is None:
        logger.info("Sync skipped for user %s: user not in guild", user_id)
        return {"status": "skipped", "reason": "not_in_guild"}

    current_roles_set = set(current_roles)

    # Compare: identify roles to add and remove
    roles_to_add = []
    roles_to_remove = []

    # Add expected role if set and not already present
    if expected_role_id and expected_role_id not in current_roles_set:
        roles_to_add.append(expected_role_id)

    # Remove any managed roles that don't match the expected role
    for role_id in managed_role_ids:
        if role_id and role_id != expected_role_id and role_id in current_roles_set:
            roles_to_remove.append(role_id)

    # If no changes needed, done
    if not roles_to_add and not roles_to_remove:
        logger.info("Sync for user %s: roles already correct", user_id)
        return {"status": "success", "added": 0, "removed": 0}

    # Execute role changes
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

    logger.info(
        "Sync completed for user %s: added=%s, removed=%s",
        user_id,
        roles_to_add,
        roles_to_remove,
    )

    return {
        "status": "success",
        "added": len(roles_to_add),
        "removed": len(roles_to_remove),
    }


def sync_discord_access(user_id: str, settings: Settings) -> SyncResult:
    """Centralized Discord access sync — check connection, enroll guild, reconcile roles.

    This is the primary entry point for all Discord sync operations. It extends
    the original _sync_user_roles with:
    1. Auto-enrollment for users not in the guild
    2. Structured SyncResult return type
    3. last_synced_at / last_sync_status updates on DISCORD_ACTIVE record

    Args:
        user_id: DSB user identifier.
        settings: Application settings instance.

    Returns:
        SyncResult with structured details of what was done.
    """
    dynamodb = boto3.client("dynamodb")
    table_name = settings.membership_table

    # Step 1: Load membership tier
    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "MEMBERSHIP"},
            },
        )
        membership = response.get("Item")
        tier = (
            membership.get("membership_tier", {}).get("S", "FREE")
            if membership
            else "FREE"
        )
    except ClientError as e:
        logger.error("sync_discord_access: DynamoDB error for user %s: %s", user_id, e)
        return SyncResult(
            sync_status="failed",
            error_code="DISCORD_API_ERROR",
            error_message=f"DynamoDB error: {e}",
        )

    # Step 2: Load DISCORD_ACTIVE record, verify connection
    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "DISCORD_ACTIVE"},
            },
        )
        discord_active = response.get("Item")
    except ClientError as e:
        logger.error("sync_discord_access: DynamoDB error for user %s: %s", user_id, e)
        return SyncResult(
            sync_status="failed",
            error_code="DISCORD_API_ERROR",
            error_message=f"DynamoDB error: {e}",
        )

    if not discord_active:
        return SyncResult(
            sync_status="skipped",
            error_code="DISCORD_NOT_CONNECTED",
            error_message="No active Discord connection",
        )

    active = discord_active.get("active", {}).get("BOOL", False)
    discord_user_id = discord_active.get("discord_user_id", {}).get("S", "")
    platform_state = discord_active.get("platform_state", {}).get("S", "")

    if not active:
        return SyncResult(
            sync_status="skipped",
            error_code="DISCORD_NOT_CONNECTED",
            error_message="Discord connection not active",
        )

    if not discord_user_id:
        return SyncResult(
            sync_status="skipped",
            error_code="DISCORD_NOT_CONNECTED",
            error_message="Missing discord_user_id",
        )

    if platform_state not in ("Server_Joined", "Roles_Synced"):
        return SyncResult(
            sync_status="skipped",
            error_code="DISCORD_NOT_CONNECTED",
            error_message=f"Invalid platform_state: {platform_state}",
        )

    # Step 3: Check guild membership and enroll if needed
    client = _get_discord_client(settings)
    current_roles = client.get_member_roles(discord_user_id)
    guild_action = "already_member"

    if current_roles is None:
        # User not in guild — attempt enrollment
        logger.info(
            "sync_discord_access: user %s not in guild, attempting enrollment",
            user_id,
        )
        # Pass the user's OAuth access token for guild join
        user_access_token = discord_active.get("access_token", {}).get("S", "")

        if not user_access_token:
            # No stored token — skip guild join, proceed to role sync.
            # User may have joined the guild manually via invite link.
            logger.warning(
                "sync_discord_access: user %s has no stored access token, skipping guild join — proceeding to role sync",
                user_id,
            )
            guild_action = "skipped_no_token"
            current_roles = []
        else:
            enrolled = client.add_member_with_bot(discord_user_id, user_access_token)

            if not enrolled:
                # Update last_sync_status to record the failure
                _update_sync_status(dynamodb, table_name, user_id, "guild_join_failed")
                return SyncResult(
                    sync_status="failed",
                    guild_action="join_failed",
                    error_code="DISCORD_GUILD_JOIN_FAILED",
                    error_message="Failed to enroll user into guild",
                )

            guild_action = "joined"
            logger.info("sync_discord_access: user %s enrolled into guild", user_id)

            # Update platform_state to Server_Joined
            try:
                dynamodb.update_item(
                    TableName=table_name,
                    Key={
                        "PK": {"S": f"USER#{user_id}"},
                        "SK": {"S": "DISCORD_ACTIVE"},
                    },
                    UpdateExpression="SET platform_state = :ps",
                    ExpressionAttributeValues={":ps": {"S": "Server_Joined"}},
                )
            except ClientError:
                pass  # Non-critical

            # Re-fetch roles after enrollment
            current_roles = client.get_member_roles(discord_user_id)
            if current_roles is None:
                current_roles = []

    # Step 4: Role reconciliation (same logic as _sync_user_roles)
    tier_role_map = _get_tier_role_map(settings)
    expected_role_id = tier_role_map.get(tier)
    managed_role_ids = set(_get_managed_role_ids(settings))

    current_roles_set = set(current_roles)

    roles_to_add = []
    roles_to_remove = []

    if expected_role_id and expected_role_id not in current_roles_set:
        roles_to_add.append(expected_role_id)

    for role_id in managed_role_ids:
        if role_id and role_id != expected_role_id and role_id in current_roles_set:
            roles_to_remove.append(role_id)

    # Execute role changes
    roles_added = []
    roles_removed = []

    for role_id in roles_to_add:
        success = client.add_role(discord_user_id, role_id)
        if success:
            roles_added.append(role_id)
        else:
            logger.error(
                "sync_discord_access: Failed to add role %s to user %s",
                role_id,
                discord_user_id,
            )
            _update_sync_status(dynamodb, table_name, user_id, "role_sync_failed")
            return SyncResult(
                sync_status="partial" if roles_added or roles_removed else "failed",
                guild_action=guild_action,
                roles_added=roles_added,
                roles_removed=roles_removed,
                error_code="DISCORD_ROLE_SYNC_FAILED",
                error_message=f"Failed to add role {role_id}",
            )

    for role_id in roles_to_remove:
        success = client.remove_role(discord_user_id, role_id)
        if success:
            roles_removed.append(role_id)
        else:
            logger.error(
                "sync_discord_access: Failed to remove role %s from user %s",
                role_id,
                discord_user_id,
            )
            _update_sync_status(dynamodb, table_name, user_id, "role_sync_failed")
            return SyncResult(
                sync_status="partial",
                guild_action=guild_action,
                roles_added=roles_added,
                roles_removed=roles_removed,
                error_code="DISCORD_ROLE_SYNC_FAILED",
                error_message=f"Failed to remove role {role_id}",
            )

    # Step 5: Update last_synced_at and last_sync_status
    _update_sync_status(dynamodb, table_name, user_id, "success")

    logger.info(
        "sync_discord_access completed: user=%s, guild_action=%s, added=%d, removed=%d",
        user_id,
        guild_action,
        len(roles_added),
        len(roles_removed),
    )

    return SyncResult(
        sync_status="success",
        guild_action=guild_action,
        roles_added=roles_added,
        roles_removed=roles_removed,
    )


def _update_sync_status(dynamodb, table_name: str, user_id: str, status: str) -> None:
    """Update last_synced_at and last_sync_status on DISCORD_ACTIVE record."""
    now = datetime.now(timezone.utc).isoformat()
    try:
        dynamodb.update_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "DISCORD_ACTIVE"},
            },
            UpdateExpression="SET last_synced_at = :ts, last_sync_status = :status",
            ExpressionAttributeValues={
                ":ts": {"S": now},
                ":status": {"S": status},
            },
        )
    except ClientError as e:
        logger.error("Failed to update sync status for user %s: %s", user_id, e)


async def perform_sync(
    user_id: str, operation: str, reason: str = ""
) -> dict[str, Any]:
    """Perform Discord sync for a single user (async wrapper).

    Called by background tasks when a Stripe webhook, Discord link,
    or admin action triggers a sync.

    Args:
        user_id: DSB user identifier.
        operation: Type of operation that triggered the sync.
        reason: Human-readable reason for the sync.

    Returns:
        Dict with sync result details.

    Raises:
        DiscordSyncError: On Discord API or DynamoDB failures.
    """
    settings = get_settings()
    logger.info(
        "Performing Discord sync: user=%s, operation=%s, reason=%s",
        user_id,
        operation,
        reason,
    )
    # Run the synchronous sync logic in a thread to avoid blocking the event loop
    result = await asyncio.to_thread(_sync_user_roles, user_id, settings)
    return result


async def reconcile_all_members() -> dict[str, int]:
    """Run Discord role reconciliation for all active members.

    Scans DynamoDB for all DISCORD_ACTIVE items and synchronizes each
    user's Discord roles with their current membership tier.

    Implements:
    - 1-second delay between Discord API calls (rate limit respect)
    - Per-user error isolation (failures don't stop processing)
    - Metrics tracking (added/removed/unchanged counts)

    Returns:
        Dict with reconciliation metrics: {"added": N, "removed": N, "unchanged": N}
    """
    settings = get_settings()
    dynamodb = boto3.client("dynamodb")
    table_name = settings.membership_table

    # Scan for all active Discord users (SK=DISCORD_ACTIVE)
    active_users = await asyncio.to_thread(
        _scan_active_discord_users, dynamodb, table_name
    )

    logger.info("Reconciliation found %d active Discord users", len(active_users))

    metrics = {"added": 0, "removed": 0, "unchanged": 0, "failed": 0, "skipped": 0}

    for item in active_users:
        # Extract user_id from PK (format: USER#{user_id})
        pk = item.get("PK", {}).get("S", "")
        if not pk.startswith("USER#"):
            continue
        user_id = pk[5:]  # Strip "USER#" prefix

        try:
            result = await asyncio.to_thread(sync_discord_access, user_id, settings)

            if result.sync_status == "success":
                added = len(result.roles_added)
                removed = len(result.roles_removed)
                metrics["added"] += added
                metrics["removed"] += removed
                if added == 0 and removed == 0:
                    metrics["unchanged"] += 1
            elif result.sync_status == "skipped":
                metrics["skipped"] += 1
            else:
                metrics["failed"] += 1
                logger.warning(
                    "Reconciliation sync issue: user=%s, status=%s, error=%s",
                    user_id,
                    result.sync_status,
                    result.error_code,
                )

        except Exception as e:
            metrics["failed"] += 1
            logger.error(
                "Reconciliation sync failed: user=%s, error=%s", user_id, str(e)
            )

        # Rate limit: wait between Discord API calls
        await asyncio.sleep(RATE_LIMIT_DELAY_SECONDS)

    logger.info(
        "Reconciliation scan complete: total=%d, added=%d, removed=%d, "
        "unchanged=%d, skipped=%d, failed=%d",
        len(active_users),
        metrics["added"],
        metrics["removed"],
        metrics["unchanged"],
        metrics["skipped"],
        metrics["failed"],
    )

    return metrics


def _scan_active_discord_users(dynamodb, table_name: str) -> list[dict[str, Any]]:
    """Scan DynamoDB for all items where SK=DISCORD_ACTIVE.

    Handles pagination for large result sets.

    Args:
        dynamodb: boto3 DynamoDB client.
        table_name: DynamoDB table name.

    Returns:
        List of DynamoDB items representing active Discord connections.
    """
    items: list[dict[str, Any]] = []
    last_evaluated_key = None

    while True:
        scan_kwargs: dict[str, Any] = {
            "TableName": table_name,
            "FilterExpression": "SK = :sk",
            "ExpressionAttributeValues": {":sk": {"S": "DISCORD_ACTIVE"}},
        }
        if last_evaluated_key:
            scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

        response = dynamodb.scan(**scan_kwargs)
        items.extend(response.get("Items", []))

        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break

    return items
