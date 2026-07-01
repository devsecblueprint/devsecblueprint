"""
DynamoDB service layer for the dsb_membership table.

This module provides functions for all DynamoDB operations related to membership,
Discord identity, Stripe event processing, OAuth state, audit logging, and role
mapping. Uses the low-level boto3 DynamoDB client following the existing project pattern.

Requirements: 17.1–17.11, 14.3–14.6
"""

import logging
import os
import time
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()

TABLE_NAME = os.environ.get("MEMBERSHIP_TABLE")


def _get_table_name() -> str:
    """Get the DynamoDB table name from environment, raising if not set."""
    table_name = os.environ.get("MEMBERSHIP_TABLE")
    if not table_name:
        raise Exception("MEMBERSHIP_TABLE environment variable not set")
    return table_name


def _get_client():
    """Create and return a DynamoDB client."""
    return boto3.client("dynamodb")


# ---------------------------------------------------------------------------
# Membership Record Operations
# ---------------------------------------------------------------------------


def get_membership(user_id: str) -> dict | None:
    """
    Retrieve a user's membership record.

    Args:
        user_id: DSB user identifier.

    Returns:
        The DynamoDB item as a dict, or None if not found.

    Raises:
        Exception: If DynamoDB operation fails.
    """
    table_name = _get_table_name()
    dynamodb = _get_client()

    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "MEMBERSHIP"},
            },
        )
        return response.get("Item")
    except ClientError as e:
        logger.error(
            "Failed to get membership for user %s: %s",
            user_id,
            e.response["Error"]["Code"],
        )
        raise Exception(f"Failed to get membership: {e.response['Error']['Code']}")


def put_membership(record: dict) -> None:
    """
    Create or update a user's membership record.

    Args:
        record: A DynamoDB-formatted item dict with PK, SK, and membership fields.
            Expected keys: PK, SK, membership_tier, and optional stripe_customer_id,
            stripe_subscription_id, subscription_status, current_period_end, updated_at.

    Raises:
        Exception: If DynamoDB operation fails.
    """
    table_name = _get_table_name()
    dynamodb = _get_client()

    try:
        dynamodb.put_item(TableName=table_name, Item=record)
    except ClientError as e:
        logger.error("Failed to put membership record: %s", e.response["Error"]["Code"])
        raise Exception(f"Failed to put membership: {e.response['Error']['Code']}")


# ---------------------------------------------------------------------------
# Discord Active Connection Operations
# ---------------------------------------------------------------------------


def get_discord_active(user_id: str) -> dict | None:
    """
    Retrieve the current active Discord connection for a user.

    Args:
        user_id: DSB user identifier.

    Returns:
        The DISCORD_ACTIVE DynamoDB item as a dict, or None if not found.

    Raises:
        Exception: If DynamoDB operation fails.
    """
    table_name = _get_table_name()
    dynamodb = _get_client()

    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "DISCORD_ACTIVE"},
            },
        )
        return response.get("Item")
    except ClientError as e:
        logger.error(
            "Failed to get discord active for user %s: %s",
            user_id,
            e.response["Error"]["Code"],
        )
        raise Exception(f"Failed to get discord active: {e.response['Error']['Code']}")


# ---------------------------------------------------------------------------
# Discord Identity Record Operations
# ---------------------------------------------------------------------------


def put_discord_identity(record: dict) -> None:
    """
    Store a Discord identity record (PK=USER#{user_id} SK=DISCORD#{discord_user_id}).

    Args:
        record: A DynamoDB-formatted item dict containing all Discord identity fields.
            Must include PK, SK, discord_user_id, username, display_name, avatar_url,
            connected_at, active flag, and optionally expires_at (for unverified TTL).

    Raises:
        Exception: If DynamoDB operation fails.
    """
    table_name = _get_table_name()
    dynamodb = _get_client()

    try:
        dynamodb.put_item(TableName=table_name, Item=record)
    except ClientError as e:
        logger.error("Failed to put discord identity: %s", e.response["Error"]["Code"])
        raise Exception(
            f"Failed to put discord identity: {e.response['Error']['Code']}"
        )


def activate_discord_connection(user_id: str, record: dict) -> None:
    """
    Activate a Discord connection using a DynamoDB transaction.

    Performs two operations atomically:
    1. Update the DISCORD#{discord_id} record: set active=true, verified_at, remove TTL.
    2. Put the DISCORD_ACTIVE denormalized record.

    Args:
        user_id: DSB user identifier.
        record: A dict containing discord identity fields to use for the
            DISCORD_ACTIVE item. Expected keys: discord_user_id, username,
            display_name, avatar_url.

    Raises:
        Exception: If DynamoDB transaction fails.
    """
    table_name = _get_table_name()
    dynamodb = _get_client()

    discord_user_id = record["discord_user_id"]
    verified_at = datetime.now(timezone.utc).isoformat()

    discord_active_item = {
        "PK": {"S": f"USER#{user_id}"},
        "SK": {"S": "DISCORD_ACTIVE"},
        "discord_user_id": {"S": discord_user_id},
        "username": {"S": record.get("username", "")},
        "display_name": {"S": record.get("display_name", "")},
        "avatar_url": {"S": record.get("avatar_url", "")},
        "active": {"BOOL": True},
        "verified_at": {"S": verified_at},
        "platform_state": {"S": "Discord_Verified"},
    }

    try:
        dynamodb.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "TableName": table_name,
                        "Key": {
                            "PK": {"S": f"USER#{user_id}"},
                            "SK": {"S": f"DISCORD#{discord_user_id}"},
                        },
                        "UpdateExpression": (
                            "SET active = :active, verified_at = :verified_at "
                            "REMOVE expires_at"
                        ),
                        "ExpressionAttributeValues": {
                            ":active": {"BOOL": True},
                            ":verified_at": {"S": verified_at},
                        },
                    }
                },
                {
                    "Put": {
                        "TableName": table_name,
                        "Item": discord_active_item,
                    }
                },
            ]
        )
    except ClientError as e:
        logger.error(
            "Failed to activate discord connection for user %s: %s",
            user_id,
            e.response["Error"]["Code"],
        )
        raise Exception(
            f"Failed to activate discord connection: {e.response['Error']['Code']}"
        )


def deactivate_discord_connection(user_id: str, discord_id: str, reason: str) -> None:
    """
    Deactivate a Discord connection using a DynamoDB transaction.

    Performs two operations atomically:
    1. Update the DISCORD#{discord_id} record: set active=false, disconnected_at,
       disconnect_reason.
    2. Delete the DISCORD_ACTIVE record.

    Args:
        user_id: DSB user identifier.
        discord_id: The Discord user ID to deactivate.
        reason: Reason for disconnection (max 256 chars).

    Raises:
        Exception: If DynamoDB transaction fails.
    """
    table_name = _get_table_name()
    dynamodb = _get_client()

    disconnected_at = datetime.now(timezone.utc).isoformat()

    try:
        dynamodb.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "TableName": table_name,
                        "Key": {
                            "PK": {"S": f"USER#{user_id}"},
                            "SK": {"S": f"DISCORD#{discord_id}"},
                        },
                        "UpdateExpression": (
                            "SET active = :active, "
                            "disconnected_at = :disconnected_at, "
                            "disconnect_reason = :reason"
                        ),
                        "ExpressionAttributeValues": {
                            ":active": {"BOOL": False},
                            ":disconnected_at": {"S": disconnected_at},
                            ":reason": {"S": reason},
                        },
                    }
                },
                {
                    "Delete": {
                        "TableName": table_name,
                        "Key": {
                            "PK": {"S": f"USER#{user_id}"},
                            "SK": {"S": "DISCORD_ACTIVE"},
                        },
                    }
                },
            ]
        )
    except ClientError as e:
        logger.error(
            "Failed to deactivate discord connection for user %s: %s",
            user_id,
            e.response["Error"]["Code"],
        )
        raise Exception(
            f"Failed to deactivate discord connection: {e.response['Error']['Code']}"
        )


# ---------------------------------------------------------------------------
# Duplicate Detection (GSI1)
# ---------------------------------------------------------------------------


def check_discord_duplicate(discord_user_id: str) -> dict | None:
    """
    Check if a Discord user ID is already linked to any DSB account.

    Queries GSI1 (PK=discord_user_id) to find existing active links.

    Args:
        discord_user_id: The Discord user ID to check.

    Returns:
        The first matching item from GSI1, or None if no link exists.

    Raises:
        Exception: If DynamoDB query fails.
    """
    table_name = _get_table_name()
    dynamodb = _get_client()

    try:
        response = dynamodb.query(
            TableName=table_name,
            IndexName="GSI1",
            KeyConditionExpression="discord_user_id = :discord_id",
            ExpressionAttributeValues={
                ":discord_id": {"S": discord_user_id},
            },
        )
        items = response.get("Items", [])
        # Return the first active link if any exist
        for item in items:
            if item.get("active", {}).get("BOOL", False):
                return item
        return None
    except ClientError as e:
        logger.error(
            "Failed to check discord duplicate for %s: %s",
            discord_user_id,
            e.response["Error"]["Code"],
        )
        raise Exception(
            f"Failed to check discord duplicate: {e.response['Error']['Code']}"
        )


# ---------------------------------------------------------------------------
# Stripe Customer Resolution (GSI2)
# ---------------------------------------------------------------------------


def resolve_stripe_customer(stripe_customer_id: str) -> dict | None:
    """
    Resolve a DSB user from a Stripe customer ID.

    Queries GSI2 (PK=stripe_customer_id) to find the linked user.

    Args:
        stripe_customer_id: The Stripe customer ID to look up.

    Returns:
        The first matching item from GSI2, or None if not found.

    Raises:
        Exception: If DynamoDB query fails.
    """
    table_name = _get_table_name()
    dynamodb = _get_client()

    try:
        response = dynamodb.query(
            TableName=table_name,
            IndexName="GSI2",
            KeyConditionExpression="stripe_customer_id = :stripe_id",
            ExpressionAttributeValues={
                ":stripe_id": {"S": stripe_customer_id},
            },
        )
        items = response.get("Items", [])
        return items[0] if items else None
    except ClientError as e:
        logger.error(
            "Failed to resolve stripe customer %s: %s",
            stripe_customer_id,
            e.response["Error"]["Code"],
        )
        raise Exception(
            f"Failed to resolve stripe customer: {e.response['Error']['Code']}"
        )


# ---------------------------------------------------------------------------
# Role Mapping Configuration
# ---------------------------------------------------------------------------


def get_role_mapping(tier: str) -> dict | None:
    """
    Retrieve the Discord role mapping for a membership tier.

    Args:
        tier: Membership tier name (FREE, EXPLORER, BUILDER, BUILDER_ACADEMY).

    Returns:
        The CONFIG/ROLE_MAP item as a dict (containing discord_role_id, tier_name,
        updated_at), or None if not configured.

    Raises:
        Exception: If DynamoDB operation fails.
    """
    table_name = _get_table_name()
    dynamodb = _get_client()

    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                "PK": {"S": "CONFIG"},
                "SK": {"S": f"ROLE_MAP#{tier}"},
            },
        )
        return response.get("Item")
    except ClientError as e:
        logger.error(
            "Failed to get role mapping for tier %s: %s",
            tier,
            e.response["Error"]["Code"],
        )
        raise Exception(f"Failed to get role mapping: {e.response['Error']['Code']}")


# ---------------------------------------------------------------------------
# Stripe Event Idempotency
# ---------------------------------------------------------------------------


def check_stripe_event_processed(event_id: str) -> bool:
    """
    Check if a Stripe event has already been processed.

    Args:
        event_id: The Stripe event ID.

    Returns:
        True if the event has been processed, False otherwise.

    Raises:
        Exception: If DynamoDB operation fails.
    """
    table_name = _get_table_name()
    dynamodb = _get_client()

    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"STRIPE_EVENT#{event_id}"},
                "SK": {"S": "PROCESSED"},
            },
        )
        return "Item" in response
    except ClientError as e:
        logger.error(
            "Failed to check stripe event %s: %s",
            event_id,
            e.response["Error"]["Code"],
        )
        raise Exception(f"Failed to check stripe event: {e.response['Error']['Code']}")


def mark_stripe_event_processed(event_id: str) -> None:
    """
    Mark a Stripe event as processed with a 7-day TTL.

    Args:
        event_id: The Stripe event ID to mark as processed.

    Raises:
        Exception: If DynamoDB operation fails.
    """
    table_name = _get_table_name()
    dynamodb = _get_client()

    expires_at = int(time.time()) + 604800  # 7 days

    item = {
        "PK": {"S": f"STRIPE_EVENT#{event_id}"},
        "SK": {"S": "PROCESSED"},
        "processed_at": {"S": datetime.now(timezone.utc).isoformat()},
        "expires_at": {"N": str(expires_at)},
    }

    try:
        dynamodb.put_item(TableName=table_name, Item=item)
    except ClientError as e:
        logger.error(
            "Failed to mark stripe event processed %s: %s",
            event_id,
            e.response["Error"]["Code"],
        )
        raise Exception(
            f"Failed to mark stripe event processed: {e.response['Error']['Code']}"
        )


# ---------------------------------------------------------------------------
# OAuth State Management
# ---------------------------------------------------------------------------


def store_oauth_state(state: str, user_id: str) -> None:
    """
    Store an OAuth state token with a 10-minute TTL.

    Args:
        state: The cryptographically random state parameter.
        user_id: The DSB user ID initiating the OAuth flow.

    Raises:
        Exception: If DynamoDB operation fails.
    """
    table_name = _get_table_name()
    dynamodb = _get_client()

    expires_at = int(time.time()) + 600  # 10 minutes

    item = {
        "PK": {"S": f"OAUTH_STATE#{state}"},
        "SK": {"S": "STATE"},
        "user_id": {"S": user_id},
        "created_at": {"S": datetime.now(timezone.utc).isoformat()},
        "expires_at": {"N": str(expires_at)},
    }

    try:
        dynamodb.put_item(TableName=table_name, Item=item)
    except ClientError as e:
        logger.error("Failed to store oauth state: %s", e.response["Error"]["Code"])
        raise Exception(f"Failed to store oauth state: {e.response['Error']['Code']}")


def validate_oauth_state(state: str) -> str | None:
    """
    Validate and consume an OAuth state token.

    Retrieves the state record and deletes it (single-use). Returns the
    associated user_id if valid, or None if not found or expired.

    Args:
        state: The state parameter to validate.

    Returns:
        The user_id associated with the state, or None if invalid/expired.

    Raises:
        Exception: If DynamoDB operation fails.
    """
    table_name = _get_table_name()
    dynamodb = _get_client()

    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"OAUTH_STATE#{state}"},
                "SK": {"S": "STATE"},
            },
        )

        item = response.get("Item")
        if not item:
            return None

        # Check if expired (belt-and-suspenders in addition to DynamoDB TTL)
        expires_at = int(item.get("expires_at", {}).get("N", "0"))
        if expires_at < int(time.time()):
            return None

        user_id = item.get("user_id", {}).get("S")

        # Delete the state record (single-use)
        dynamodb.delete_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"OAUTH_STATE#{state}"},
                "SK": {"S": "STATE"},
            },
        )

        return user_id
    except ClientError as e:
        logger.error("Failed to validate oauth state: %s", e.response["Error"]["Code"])
        raise Exception(
            f"Failed to validate oauth state: {e.response['Error']['Code']}"
        )


# ---------------------------------------------------------------------------
# Audit Log Queries
# ---------------------------------------------------------------------------


def get_user_audit_log(user_id: str, limit: int = 100) -> list:
    """
    Retrieve audit log entries for a user in reverse chronological order.

    Queries items with SK begins_with 'AUDIT#' with ScanIndexForward=false
    to get newest entries first.

    Args:
        user_id: DSB user identifier.
        limit: Maximum number of entries to return (default 100).

    Returns:
        A list of DynamoDB item dicts representing audit log entries.

    Raises:
        Exception: If DynamoDB query fails.
    """
    table_name = _get_table_name()
    dynamodb = _get_client()

    try:
        response = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"USER#{user_id}"},
                ":sk_prefix": {"S": "AUDIT#"},
            },
            ScanIndexForward=False,
            Limit=limit,
        )
        return response.get("Items", [])
    except ClientError as e:
        logger.error(
            "Failed to get audit log for user %s: %s",
            user_id,
            e.response["Error"]["Code"],
        )
        raise Exception(f"Failed to get audit log: {e.response['Error']['Code']}")


# ---------------------------------------------------------------------------
# Discord History Queries
# ---------------------------------------------------------------------------


def get_discord_history(user_id: str) -> list:
    """
    Retrieve all Discord identity records for a user (connection history).

    Queries items with SK begins_with 'DISCORD#' to return all historical
    Discord connections ordered by connected_at descending.

    Args:
        user_id: DSB user identifier.

    Returns:
        A list of DynamoDB item dicts representing Discord identity records,
        ordered by sort key (which includes discord_user_id).

    Raises:
        Exception: If DynamoDB query fails.
    """
    table_name = _get_table_name()
    dynamodb = _get_client()

    try:
        response = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"USER#{user_id}"},
                ":sk_prefix": {"S": "DISCORD#"},
            },
            ScanIndexForward=False,
        )
        return response.get("Items", [])
    except ClientError as e:
        logger.error(
            "Failed to get discord history for user %s: %s",
            user_id,
            e.response["Error"]["Code"],
        )
        raise Exception(f"Failed to get discord history: {e.response['Error']['Code']}")
