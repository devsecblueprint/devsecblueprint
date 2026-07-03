"""Discord identity service for OAuth flow, confirm, disconnect, and status operations.

Handles the full Discord identity lifecycle:
- Initiating the OAuth flow with CSRF state parameter
- Processing the OAuth callback (token exchange, profile fetch, validation)
- Confirming a pending Discord connection
- Disconnecting an active Discord account
- Querying Discord connection status

Validates: Requirements 4.1-4.9, 5.1-5.6, 6.3, 6.6, 6.7, 7.1-7.7, 8.1-8.5,
           12.4, 14.5, 18.1, 18.2, 19.7, 19.8, 21.5, 23.2, 23.7
"""

import logging
import os
import secrets as secrets_module
import time
from datetime import datetime, timezone
from urllib.parse import urlencode

import boto3
import requests

from config.settings import (
    DISCORD_BOT_SECRET_NAME,
    DISCORD_GUILD_ID,
    DISCORD_SECRET_NAME,
    FRONTEND_URL,
    MANAGED_ROLE_IDS,
)
from models.audit_event import AuditEvent, AuditEventType
from models.discord_identity import DiscordIdentityRecord
from services.audit import write_audit_log
from services import membership_db
from services.membership_db import (
    activate_discord_connection,
    deactivate_discord_connection,
    get_discord_active,
    get_discord_history,
)
from services.secrets import get_secret
from services.sqs_publisher import publish_sync_event
from utils.discord_api import DiscordClient
from utils.validation import (
    reject_control_characters,
    validate_discord_id,
    validate_field_length,
)

logger = logging.getLogger(__name__)

DISCORD_OAUTH_AUTHORIZE_URL = "https://discord.com/api/v10/oauth2/authorize"
DISCORD_OAUTH_TOKEN_URL = "https://discord.com/api/v10/oauth2/token"
DISCORD_USER_PROFILE_URL = "https://discord.com/api/v10/users/@me"
DISCORD_SCOPES = "identify guilds guilds.join"


# ---------------------------------------------------------------------------
# OAuth Flow — start and callback
# ---------------------------------------------------------------------------


def start_oauth(user_id: str) -> str:
    """
    Initiate the Discord OAuth2 flow for a user.

    Validates that the user doesn't already have an active Discord connection,
    generates a cryptographically random state parameter for CSRF protection,
    stores it in DynamoDB with a 10-minute TTL, and builds the Discord
    authorization URL.

    Args:
        user_id: The DSB user ID initiating the OAuth flow.

    Returns:
        str: The Discord authorization URL to redirect the user to.

    Raises:
        ValueError: If user already has an active Discord connection.
        Exception: If DynamoDB or Secrets Manager operations fail.

    Validates: Requirements 4.1, 4.6, 4.8, 4.9
    """
    # Check no existing active connection
    existing = membership_db.get_discord_active(user_id)
    if existing:
        raise ValueError("Discord account already connected. Disconnect first.")

    # Generate cryptographically random state parameter
    state = secrets_module.token_urlsafe(32)

    # Store state in DynamoDB with 10-minute TTL
    membership_db.store_oauth_state(state, user_id)

    # Get client_id from Secrets Manager
    discord_creds = get_secret(DISCORD_SECRET_NAME)
    client_id = discord_creds.get("client_id")

    if not client_id:
        raise Exception("Discord client_id not found in secrets")

    # Build callback URL from environment
    callback_url = os.environ.get(
        "DISCORD_CALLBACK_URL", f"{FRONTEND_URL}/auth/discord/callback"
    )

    # Build Discord authorization URL
    params = {
        "client_id": client_id,
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": DISCORD_SCOPES,
        "state": state,
    }
    auth_url = f"{DISCORD_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"

    logger.info("Discord OAuth flow initiated for user %s", user_id)
    return auth_url


def handle_callback(code: str, state: str) -> str:
    """
    Handle the Discord OAuth2 callback.

    Validates the state parameter, exchanges the authorization code for an
    access token, fetches the Discord user profile, validates response fields,
    checks for duplicate Discord IDs, and stores an unverified identity record
    with a 15-minute TTL.

    The access token is stored temporarily on the pending record (with the same
    15-minute TTL) so it can be used during confirm_identity to add the user to
    the guild via guilds.join. It is cleared immediately after use.

    Args:
        code: The authorization code from Discord.
        state: The state parameter for CSRF validation.

    Returns:
        str: The user_id associated with the OAuth flow.

    Raises:
        ValueError: If state is invalid/expired, token exchange fails,
            profile fetch fails, validation fails, or duplicate Discord ID detected.
        Exception: If DynamoDB or external service operations fail unexpectedly.

    Validates: Requirements 4.2-4.5, 4.7, 4.9, 6.3, 6.6, 6.7, 18.1, 18.2, 19.7, 19.8
    """
    # Validate state and extract user_id (also deletes state record - single use)
    user_id = membership_db.validate_oauth_state(state)
    if not user_id:
        logger.warning("Invalid or expired OAuth state parameter")
        raise ValueError("Invalid or expired state parameter")

    # Get Discord credentials from Secrets Manager
    discord_creds = get_secret(DISCORD_SECRET_NAME)
    client_id = discord_creds.get("client_id")
    client_secret = discord_creds.get("client_secret")

    if not client_id or not client_secret:
        raise Exception("Discord OAuth credentials incomplete in secrets")

    callback_url = os.environ.get(
        "DISCORD_CALLBACK_URL", f"{FRONTEND_URL}/auth/discord/callback"
    )

    # Exchange authorization code for access token
    access_token = _exchange_code_for_token(
        code, client_id, client_secret, callback_url
    )

    # Fetch Discord user profile
    profile = _fetch_discord_profile(access_token)

    # Extract and validate profile fields
    discord_user_id = profile.get("id", "")
    username = profile.get("username", "")
    display_name = profile.get("global_name") or username
    avatar_hash = profile.get("avatar")
    avatar_url = (
        f"https://cdn.discordapp.com/avatars/{discord_user_id}/{avatar_hash}.png"
        if avatar_hash
        else None
    )

    # Validate Discord User ID format
    if not validate_discord_id(discord_user_id):
        logger.error(
            "Invalid Discord user ID format received: %s", discord_user_id[:20]
        )
        raise ValueError("Invalid Discord user ID format")

    # Validate field lengths (max 100 characters)
    validate_field_length(username, 100, "username")
    reject_control_characters(username)

    if display_name:
        validate_field_length(display_name, 100, "display_name")
        reject_control_characters(display_name)

    # Check for duplicate Discord User ID via GSI1
    duplicate = membership_db.check_discord_duplicate(discord_user_id)
    if duplicate:
        logger.warning(
            "Duplicate Discord ID %s already linked to another user",
            discord_user_id,
        )
        raise ValueError(
            "This Discord account is already linked to another DSB account"
        )

    # Store unverified Discord identity record with 15-minute TTL
    record = DiscordIdentityRecord(
        user_id=user_id,
        discord_user_id=discord_user_id,
        username=username,
        display_name=display_name,
        avatar_url=avatar_url,
        connected_at=datetime.now(timezone.utc).isoformat(),
        active=False,
        platform_state="Discord_Connected",
    )
    item = record.to_dynamo_item()
    item["expires_at"] = {"N": str(int(time.time()) + 900)}  # 15-min TTL
    # Store access token temporarily for guild join during confirmation
    # This will auto-expire with the record's TTL (15 minutes)
    item["_oauth_token"] = {"S": access_token}
    membership_db.put_discord_identity(item)

    logger.info(
        "Discord identity record stored (unverified) for user %s, discord_id %s",
        user_id,
        discord_user_id,
    )

    return user_id


def _exchange_code_for_token(
    code: str, client_id: str, client_secret: str, callback_url: str
) -> str:
    """
    Exchange an authorization code for a Discord access token.

    Args:
        code: The authorization code from Discord callback.
        client_id: Discord application client ID.
        client_secret: Discord application client secret.
        callback_url: The redirect URI used in the initial authorization request.

    Returns:
        str: The access token from Discord.

    Raises:
        ValueError: If the token exchange fails.
    """
    try:
        token_response = requests.post(
            DISCORD_OAUTH_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": callback_url,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
    except requests.exceptions.RequestException as e:
        logger.error("Discord token exchange request failed: %s", str(e))
        raise ValueError("Failed to exchange authorization code")

    if token_response.status_code != 200:
        logger.error(
            "Discord token exchange failed: %d %s",
            token_response.status_code,
            token_response.text[:200],
        )
        raise ValueError("Failed to exchange authorization code")

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        logger.error("No access_token in Discord token response")
        raise ValueError("Failed to exchange authorization code")

    return access_token


def _fetch_discord_profile(access_token: str) -> dict:
    """
    Fetch the Discord user profile using the access token.

    Args:
        access_token: A valid Discord OAuth2 access token.

    Returns:
        dict: The Discord user profile data.

    Raises:
        ValueError: If the profile fetch fails.
    """
    try:
        profile_response = requests.get(
            DISCORD_USER_PROFILE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
    except requests.exceptions.RequestException as e:
        logger.error("Discord profile fetch request failed: %s", str(e))
        raise ValueError("Failed to fetch Discord profile")

    if profile_response.status_code != 200:
        logger.error(
            "Discord profile fetch failed: %d %s",
            profile_response.status_code,
            profile_response.text[:200],
        )
        raise ValueError("Failed to fetch Discord profile")

    return profile_response.json()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


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


def confirm_identity(user_id: str) -> dict:
    """Confirm a pending Discord identity and activate the connection.

    Loads the pending (unverified) Discord identity record, activates via
    DynamoDB transaction, checks guild membership, publishes a sync event,
    and writes audit logs.

    Args:
        user_id: DSB user identifier.

    Returns:
        dict with discord_user_id, username, display_name, avatar_url,
        and platform_state.

    Raises:
        ValueError: If no pending Discord connection is found.
    """
    # Find pending record - query Discord history, find unverified one
    history = get_discord_history(user_id)
    pending_record = None
    for item in history:
        if (
            item.get("active", {}).get("BOOL", False) is False
            and item.get("verified_at") is None
        ):
            pending_record = item
            break

    if not pending_record:
        raise ValueError("No pending Discord connection found. It may have expired.")

    discord_user_id = pending_record.get("discord_user_id", {}).get("S", "")
    username = pending_record.get("username", {}).get("S", "")
    display_name = pending_record.get("display_name", {}).get("S", "")
    avatar_url = pending_record.get("avatar_url", {}).get("S", "")

    # Activate connection via transaction
    record_data = {
        "discord_user_id": discord_user_id,
        "username": username,
        "display_name": display_name,
        "avatar_url": avatar_url,
    }
    activate_discord_connection(user_id, record_data)

    # Add user to guild using stored OAuth token, then assign role
    platform_state = "Discord_Verified"
    try:
        bot_token_data = get_secret(DISCORD_BOT_SECRET_NAME)
        bot_token = bot_token_data.get("secret_key")

        if bot_token and DISCORD_GUILD_ID:
            client = DiscordClient(bot_token, DISCORD_GUILD_ID)

            # Check if user is already in the guild
            member = client.get_member(discord_user_id)
            if member is not None:
                platform_state = "Server_Joined"
            else:
                # User not in guild — try to add them using the stored OAuth token
                oauth_token = pending_record.get("_oauth_token", {}).get("S")
                if oauth_token:
                    added = client.add_member_to_guild(discord_user_id, oauth_token)
                    if added:
                        platform_state = "Server_Joined"
                        logger.info(
                            "Added user %s to guild via guilds.join", discord_user_id
                        )
                    else:
                        logger.warning(
                            "Failed to add user %s to guild", discord_user_id
                        )
                        platform_state = "Not_in_Server"
                else:
                    logger.warning(
                        "No OAuth token stored for user %s, cannot add to guild",
                        user_id,
                    )
                    platform_state = "Not_in_Server"
    except Exception as e:
        logger.warning("Guild join failed for user %s: %s", user_id, e)
        platform_state = "Not_in_Server"

    # Update platform_state on DISCORD_ACTIVE if Server_Joined
    if platform_state == "Server_Joined":
        _update_platform_state(user_id, platform_state)

    # Clear the stored OAuth token from the pending record (security: don't leave tokens around)
    try:
        table_name = os.environ.get("MEMBERSHIP_TABLE")
        if table_name:
            dynamodb = boto3.client("dynamodb")
            dynamodb.update_item(
                TableName=table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": f"DISCORD#{discord_user_id}"},
                },
                UpdateExpression="REMOVE #token",
                ExpressionAttributeNames={"#token": "_oauth_token"},
            )
    except Exception as e:
        logger.debug("Failed to clear oauth token (non-critical): %s", e)

    # Publish sync event
    publish_sync_event(user_id, "discord_connected", None)

    # Write audit logs
    write_audit_log(
        AuditEvent.build(
            AuditEventType.CONNECTED, user_id, f"user:{user_id}"
        ).with_discord(discord_user_id)
    )
    write_audit_log(
        AuditEvent.build(
            AuditEventType.VERIFIED, user_id, f"user:{user_id}"
        ).with_discord(discord_user_id)
    )
    if platform_state == "Server_Joined":
        write_audit_log(
            AuditEvent.build(
                AuditEventType.GUILD_JOINED, user_id, f"user:{user_id}"
            ).with_discord(discord_user_id)
        )

    return {
        "discord_user_id": discord_user_id,
        "username": username,
        "display_name": display_name,
        "avatar_url": avatar_url,
        "platform_state": platform_state,
    }


def disconnect(user_id: str) -> dict:
    """Disconnect the user's Discord account.

    Deactivates the connection via DynamoDB transaction, attempts to remove
    all managed Discord roles, and writes an audit log.

    Args:
        user_id: DSB user identifier.

    Returns:
        dict with cleanup_status ("completed" or "failed").

    Raises:
        ValueError: If no active Discord connection is found.
    """
    active_record = get_discord_active(user_id)
    if not active_record:
        raise ValueError("No active Discord connection found")

    discord_user_id = active_record.get("discord_user_id", {}).get("S", "")

    # Deactivate via transaction
    deactivate_discord_connection(user_id, discord_user_id, "User requested")

    # Try to remove managed roles
    cleanup_status = "completed"
    try:
        bot_token_data = get_secret(DISCORD_BOT_SECRET_NAME)
        bot_token = bot_token_data.get("secret_key")
        if bot_token and DISCORD_GUILD_ID:
            client = DiscordClient(bot_token, DISCORD_GUILD_ID)
            for role_id in MANAGED_ROLE_IDS:
                client.remove_role(discord_user_id, role_id)
    except Exception as e:
        logger.error("Role removal failed for user %s: %s", user_id, e)
        cleanup_status = "failed"

    # Write audit log
    write_audit_log(
        AuditEvent.build(AuditEventType.DISCONNECTED, user_id, f"user:{user_id}")
        .with_discord(discord_user_id)
        .with_reason("User requested")
    )

    return {"cleanup_status": cleanup_status}


def get_status(user_id: str) -> dict:
    """Get Discord connection status for a user.

    Args:
        user_id: DSB user identifier.

    Returns:
        dict with connected, discord_username, discord_avatar_url,
        platform_state, last_synced_at, and last_sync_status.
        Also includes pending flag and discord_display_name when a
        pending (unverified) connection exists.
    """
    active_record = get_discord_active(user_id)
    if not active_record:
        # Check for pending (unverified) connection
        history = get_discord_history(user_id)
        pending = None
        for item in history:
            if (
                item.get("active", {}).get("BOOL", False) is False
                and item.get("verified_at") is None
            ):
                pending = item
                break

        if pending:
            return {
                "connected": False,
                "pending": True,
                "discord_username": pending.get("username", {}).get("S"),
                "discord_avatar_url": pending.get("avatar_url", {}).get("S"),
                "discord_display_name": pending.get("display_name", {}).get("S"),
                "platform_state": "Discord_Connected",
                "last_synced_at": None,
                "last_sync_status": None,
            }

        return {
            "connected": False,
            "pending": False,
            "discord_username": None,
            "discord_avatar_url": None,
            "platform_state": None,
            "last_synced_at": None,
            "last_sync_status": None,
        }

    return {
        "connected": True,
        "pending": False,
        "discord_username": active_record.get("username", {}).get("S"),
        "discord_avatar_url": active_record.get("avatar_url", {}).get("S"),
        "platform_state": active_record.get("platform_state", {}).get("S"),
        "last_synced_at": active_record.get("last_synced_at", {}).get("S"),
        "last_sync_status": active_record.get("last_sync_status", {}).get("S"),
    }
