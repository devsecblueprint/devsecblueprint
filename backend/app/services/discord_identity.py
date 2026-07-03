"""Discord identity service — link/unlink/status operations.

Self-contained implementation using DynamoDB directly for
DISCORD_PENDING, DISCORD_ACTIVE, and DISCORD#{id} records.

Provides:
- start_oauth: Initiate Discord OAuth flow
- handle_callback: Process the OAuth callback
- confirm_identity: Activate a pending Discord connection
- disconnect: Deactivate and clean up a Discord connection
- get_status: Query Discord connection status

Requirements: 4.3
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

import boto3
import httpx
from botocore.exceptions import ClientError

from app.config import Settings

logger = logging.getLogger(__name__)


def _get_discord_secret(settings: Settings) -> dict[str, Any]:
    """Retrieve Discord OAuth secret from Secrets Manager."""
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=settings.discord_secret_name)
    return json.loads(response["SecretString"])


def _get_bot_token(settings: Settings) -> str:
    """Retrieve Discord bot token from Secrets Manager."""
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=settings.discord_bot_secret_name)
    data = json.loads(response["SecretString"])
    return data.get("secret_key", "")


def start_oauth(user_id: str, settings: Settings) -> str:
    """Initiate Discord OAuth flow for a user.

    Returns:
        The Discord authorization URL to redirect the user to.

    Raises:
        ValueError: If user already has an active Discord connection.
    """
    dynamodb = boto3.client("dynamodb")
    table_name = settings.membership_table

    # Check if user already has active Discord connection
    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "DISCORD_ACTIVE"}},
        )
        if response.get("Item"):
            raise ValueError("Discord account already connected")
    except ClientError as e:
        logger.error("DynamoDB error checking Discord active: %s", e)
        raise

    # Get Discord OAuth credentials
    secret = _get_discord_secret(settings)
    client_id = secret.get("client_id", "")

    # Build authorization URL
    callback_url = settings.discord_callback_url
    state = f"{user_id}:{int(time.time())}"

    # Store pending state
    try:
        dynamodb.put_item(
            TableName=table_name,
            Item={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "DISCORD_PENDING"},
                "state": {"S": state},
                "created_at": {"S": datetime.now(timezone.utc).isoformat()},
            },
        )
    except ClientError as e:
        logger.error("Failed to store Discord pending state: %s", e)
        raise

    auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={callback_url}"
        f"&response_type=code"
        f"&scope=identify+guilds.join"
        f"&state={state}"
    )

    return auth_url


def handle_callback(code: str, state: str, settings: Settings) -> None:
    """Process the Discord OAuth callback.

    Exchanges the code for tokens, fetches the Discord user info,
    and stores it as a pending connection.

    Raises:
        ValueError: If state is invalid or callback processing fails.
    """
    dynamodb = boto3.client("dynamodb")
    table_name = settings.membership_table

    # Extract user_id from state
    parts = state.split(":")
    if len(parts) < 2:
        raise ValueError("Invalid state parameter")
    user_id = parts[0]

    # Verify pending state
    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "DISCORD_PENDING"}},
        )
        pending = response.get("Item")
        if not pending or pending.get("state", {}).get("S") != state:
            raise ValueError("Invalid or expired state")
    except ClientError as e:
        logger.error("DynamoDB error verifying state: %s", e)
        raise ValueError("Failed to verify state")

    # Exchange code for token
    secret = _get_discord_secret(settings)
    client_id = secret.get("client_id", "")
    client_secret = secret.get("client_secret", "")

    token_resp = httpx.post(
        "https://discord.com/api/v10/oauth2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.discord_callback_url,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )

    if token_resp.status_code != 200:
        raise ValueError("Failed to exchange Discord code for token")

    token_data = token_resp.json()
    access_token = token_data.get("access_token", "")

    # Fetch Discord user info
    user_resp = httpx.get(
        "https://discord.com/api/v10/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )

    if user_resp.status_code != 200:
        raise ValueError("Failed to fetch Discord user info")

    discord_user = user_resp.json()
    discord_user_id = discord_user.get("id", "")
    username = discord_user.get("username", "")
    display_name = discord_user.get("global_name") or username
    avatar = discord_user.get("avatar", "")
    avatar_url = (
        f"https://cdn.discordapp.com/avatars/{discord_user_id}/{avatar}.png"
        if avatar
        else ""
    )

    # Update pending record with Discord user info
    now = datetime.now(timezone.utc).isoformat()
    try:
        dynamodb.update_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "DISCORD_PENDING"}},
            UpdateExpression=(
                "SET discord_user_id = :duid, username = :uname, "
                "display_name = :dname, avatar_url = :avatar, "
                "access_token = :token, updated_at = :ts"
            ),
            ExpressionAttributeValues={
                ":duid": {"S": discord_user_id},
                ":uname": {"S": username},
                ":dname": {"S": display_name},
                ":avatar": {"S": avatar_url},
                ":token": {"S": access_token},
                ":ts": {"S": now},
            },
        )
    except ClientError as e:
        logger.error("Failed to update pending Discord record: %s", e)
        raise ValueError("Failed to store Discord identity")


def confirm_identity(user_id: str, settings: Settings) -> dict:
    """Confirm a pending Discord identity and activate the connection.

    Returns:
        dict with discord_user_id, username, display_name, avatar_url,
        and platform_state.

    Raises:
        ValueError: If no pending Discord connection is found.
    """
    dynamodb = boto3.client("dynamodb")
    table_name = settings.membership_table

    # Fetch pending record
    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "DISCORD_PENDING"}},
        )
        pending = response.get("Item")
    except ClientError as e:
        logger.error("Failed to fetch pending Discord record: %s", e)
        raise ValueError("Failed to fetch pending connection")

    if not pending:
        raise ValueError("No pending Discord connection found")

    discord_user_id = pending.get("discord_user_id", {}).get("S", "")
    if not discord_user_id:
        raise ValueError("Pending connection incomplete — no Discord user ID")

    username = pending.get("username", {}).get("S", "")
    display_name = pending.get("display_name", {}).get("S", "")
    avatar_url = pending.get("avatar_url", {}).get("S", "")

    now = datetime.now(timezone.utc).isoformat()

    # Create DISCORD_ACTIVE and DISCORD#{id} records, delete PENDING
    try:
        dynamodb.transact_write_items(
            TransactItems=[
                {
                    "Put": {
                        "TableName": table_name,
                        "Item": {
                            "PK": {"S": f"USER#{user_id}"},
                            "SK": {"S": "DISCORD_ACTIVE"},
                            "discord_user_id": {"S": discord_user_id},
                            "username": {"S": username},
                            "display_name": {"S": display_name},
                            "avatar_url": {"S": avatar_url},
                            "active": {"BOOL": True},
                            "platform_state": {"S": "Server_Joined"},
                            "connected_at": {"S": now},
                            "last_synced_at": {"S": ""},
                            "last_sync_status": {"S": ""},
                        },
                    }
                },
                {
                    "Put": {
                        "TableName": table_name,
                        "Item": {
                            "PK": {"S": f"USER#{user_id}"},
                            "SK": {"S": f"DISCORD#{discord_user_id}"},
                            "active": {"BOOL": True},
                            "connected_at": {"S": now},
                            "username": {"S": username},
                        },
                    }
                },
                {
                    "Delete": {
                        "TableName": table_name,
                        "Key": {
                            "PK": {"S": f"USER#{user_id}"},
                            "SK": {"S": "DISCORD_PENDING"},
                        },
                    }
                },
            ]
        )
    except ClientError as e:
        logger.error("Failed to activate Discord connection: %s", e)
        raise ValueError("Failed to activate Discord connection")

    return {
        "discord_user_id": discord_user_id,
        "username": username,
        "display_name": display_name,
        "avatar_url": avatar_url,
        "platform_state": "Server_Joined",
    }


def disconnect(user_id: str, settings: Settings) -> dict:
    """Disconnect the user's Discord account.

    Returns:
        dict with cleanup_status ("completed" or "failed").

    Raises:
        ValueError: If no active Discord connection is found.
    """
    dynamodb = boto3.client("dynamodb")
    table_name = settings.membership_table

    # Fetch active record
    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "DISCORD_ACTIVE"}},
        )
        active_record = response.get("Item")
    except ClientError as e:
        logger.error("Failed to fetch active Discord record: %s", e)
        raise ValueError("Failed to fetch Discord connection")

    if not active_record:
        raise ValueError("No active Discord connection found")

    discord_user_id = active_record.get("discord_user_id", {}).get("S", "")
    now = datetime.now(timezone.utc).isoformat()

    # Deactivate: update DISCORD#{id}, delete DISCORD_ACTIVE
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
                            "SET active = :active, disconnected_at = :ts, "
                            "disconnect_reason = :reason"
                        ),
                        "ExpressionAttributeValues": {
                            ":active": {"BOOL": False},
                            ":ts": {"S": now},
                            ":reason": {"S": "User initiated"},
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
        logger.error("Failed to deactivate Discord connection: %s", e)
        raise ValueError("Failed to disconnect Discord")

    # Try to remove managed roles
    cleanup_status = "completed"
    try:
        bot_token = _get_bot_token(settings)
        if bot_token and settings.discord_guild_id and discord_user_id:
            from app.services.discord_api import DiscordClient

            client = DiscordClient(bot_token, settings.discord_guild_id)
            for role_id in [
                settings.discord_role_free_id,
                settings.discord_role_explorer_id,
                settings.discord_role_builder_id,
                settings.discord_role_builder_academy_id,
            ]:
                if role_id:
                    client.remove_role(discord_user_id, role_id)
    except Exception as e:
        logger.error("Role removal failed during disconnect: %s", e)
        cleanup_status = "failed"

    return {"cleanup_status": cleanup_status}


def get_status(user_id: str, settings: Settings) -> dict:
    """Get Discord connection status for a user.

    Returns:
        dict with connected, pending, discord_username, discord_avatar_url,
        platform_state, last_synced_at, and last_sync_status.
    """
    dynamodb = boto3.client("dynamodb")
    table_name = settings.membership_table

    result = {
        "connected": False,
        "pending": False,
        "discord_username": None,
        "discord_avatar_url": None,
        "platform_state": None,
        "last_synced_at": None,
        "last_sync_status": None,
    }

    # Check active connection
    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "DISCORD_ACTIVE"}},
        )
        active = response.get("Item")
        if active:
            result["connected"] = True
            result["discord_username"] = active.get("username", {}).get("S")
            result["discord_avatar_url"] = active.get("avatar_url", {}).get("S")
            result["platform_state"] = active.get("platform_state", {}).get("S")
            result["last_synced_at"] = active.get("last_synced_at", {}).get("S") or None
            result["last_sync_status"] = (
                active.get("last_sync_status", {}).get("S") or None
            )
            return result
    except ClientError as e:
        logger.error("DynamoDB error checking Discord active: %s", e)

    # Check pending connection
    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "DISCORD_PENDING"}},
        )
        pending = response.get("Item")
        if pending:
            result["pending"] = True
            result["discord_username"] = pending.get("username", {}).get("S")
            result["discord_avatar_url"] = pending.get("avatar_url", {}).get("S")
    except ClientError as e:
        logger.error("DynamoDB error checking Discord pending: %s", e)

    return result
