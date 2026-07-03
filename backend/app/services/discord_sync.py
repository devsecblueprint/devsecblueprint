"""Discord role synchronization service.

Provides two main entry points:
- perform_sync(user_id, operation, reason): Sync a single user's Discord roles
- reconcile_all_members(): Scan all active Discord users and sync each one

Ported from backend/membership/services/discord_sync.py and
backend/membership/handlers/sync_handlers.py (handle_reconciliation).

Requirements: 5.1-5.6, 6.1-6.5
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings
from app.dependencies import get_settings

logger = logging.getLogger("app.services.discord_sync")

# Rate limit delay between Discord API calls during reconciliation
RATE_LIMIT_DELAY_SECONDS = 1.0


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

    Imports the DiscordClient from the membership utils, which handles
    rate limiting, retries, and exponential backoff.

    Args:
        settings: Application settings instance.

    Returns:
        DiscordClient instance configured with bot token and guild ID.
    """
    import sys
    import os

    # Ensure the legacy membership utils are importable
    legacy_root = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "legacy",
    )
    membership_root = os.path.join(legacy_root, "membership")
    if membership_root not in sys.path:
        sys.path.insert(0, membership_root)

    from utils.discord_api import DiscordClient

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
    if not expected_role_id:
        logger.warning("No role mapping for tier %s, user %s", tier, user_id)
        return {"status": "skipped", "reason": f"no_role_for_tier={tier}"}

    managed_role_ids = set(_get_managed_role_ids(settings))

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

    if expected_role_id not in current_roles_set:
        roles_to_add.append(expected_role_id)

    for role_id in managed_role_ids:
        if role_id != expected_role_id and role_id in current_roles_set:
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
            result = await asyncio.to_thread(_sync_user_roles, user_id, settings)

            if result["status"] == "success":
                added = result.get("added", 0)
                removed = result.get("removed", 0)
                metrics["added"] += added
                metrics["removed"] += removed
                if added == 0 and removed == 0:
                    metrics["unchanged"] += 1
            elif result["status"] == "skipped":
                metrics["skipped"] += 1

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
