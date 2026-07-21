"""Admin Discord service for user management operations.

Provides admin-level operations for viewing user Discord details,
triggering manual syncs, disconnecting accounts, and viewing audit logs.
Ported from backend/membership/services/admin_discord.py.

Admin authorization is handled at the router level (Depends(require_admin));
these functions assume the caller is already verified as an admin.

Requirements: 4.3
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings
from app.services.membership_db import MembershipDB

logger = logging.getLogger(__name__)


class AdminDiscordService:
    """Admin-level Discord/membership operations.

    Encapsulates the logic from the Lambda admin_discord service,
    using MembershipDB for DynamoDB access and Settings for configuration.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._db = MembershipDB(settings)

    # ------------------------------------------------------------------
    # GET /admin/discord/users/{user_id}
    # ------------------------------------------------------------------

    def get_user_detail(self, target_user_id: str) -> dict[str, Any] | None:
        """Get detailed Discord/membership info for a user (admin view).

        Loads the MEMBERSHIP record and DISCORD_ACTIVE record for the target
        user and returns a consolidated view of their status.

        Args:
            target_user_id: The DSB user ID to look up.

        Returns:
            A dict with user detail fields, or None if no records exist.
        """
        membership_item = self._db.get_membership(target_user_id)
        discord_active = self._db.get_discord_active(target_user_id)

        if not membership_item and not discord_active:
            return None

        result: dict[str, Any] = {
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
                    "discord_user_id": discord_active.get("discord_user_id", {}).get(
                        "S"
                    ),
                    "platform_state": discord_active.get("platform_state", {}).get("S"),
                    "last_synced_at": discord_active.get("last_synced_at", {}).get("S"),
                    "last_sync_status": discord_active.get("last_sync_status", {}).get(
                        "S"
                    ),
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

    # ------------------------------------------------------------------
    # POST /admin/discord/users/{user_id}/sync
    # ------------------------------------------------------------------

    def trigger_sync(
        self,
        admin_user_id: str,
        target_user_id: str,
        reason: str = "Admin triggered",
    ) -> dict[str, Any]:
        """Trigger Discord role sync for a user (admin action).

        Writes an Admin_Override audit entry. The actual sync is handled
        by the background task layer (enqueue_discord_sync) at the router level.

        Args:
            admin_user_id: The admin performing the action.
            target_user_id: The user whose roles should be synced.
            reason: Reason for the manual sync trigger.

        Returns:
            A dict with success status and user_id.
        """
        self._write_audit(
            target_user_id=target_user_id,
            event_type="ADMIN_OVERRIDE",
            actor=f"admin:{admin_user_id}",
            reason=f"Sync triggered: {reason}",
        )

        return {"success": True, "user_id": target_user_id}

    # ------------------------------------------------------------------
    # DELETE /admin/discord/users/{user_id}/disconnect
    # ------------------------------------------------------------------

    def disconnect(
        self, admin_user_id: str, target_user_id: str, reason: str
    ) -> dict[str, Any]:
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

        active_record = self._db.get_discord_active(target_user_id)
        if not active_record:
            raise ValueError("Target user has no active Discord connection")

        discord_user_id = active_record.get("discord_user_id", {}).get("S", "")

        # Deactivate the connection in DynamoDB
        self._db.deactivate_discord_connection(
            target_user_id, discord_user_id, f"Admin: {reason}"
        )

        # Try to remove managed roles from the Discord guild
        cleanup_status = "completed"
        try:
            bot_token = self._get_bot_token()
            if bot_token and self._settings.discord_guild_id:
                managed_role_ids = [
                    self._settings.discord_role_free_id,
                    self._settings.discord_role_explorer_id,
                    self._settings.discord_role_builder_id,
                    self._settings.discord_role_builder_academy_id,
                ]
                self._remove_discord_roles(bot_token, discord_user_id, managed_role_ids)
        except Exception as e:
            logger.error("Role removal failed during admin disconnect: %s", e)
            cleanup_status = "failed"

        # Write audit entries
        self._write_audit(
            target_user_id=target_user_id,
            event_type="ADMIN_OVERRIDE",
            actor=f"admin:{admin_user_id}",
            reason=reason,
            discord_user_id=discord_user_id,
        )
        self._write_audit(
            target_user_id=target_user_id,
            event_type="DISCONNECTED",
            actor=f"admin:{admin_user_id}",
            reason=reason,
            discord_user_id=discord_user_id,
        )

        return {"cleanup_status": cleanup_status, "user_id": target_user_id}

    # ------------------------------------------------------------------
    # GET /admin/discord/users/{user_id}/audit
    # ------------------------------------------------------------------

    def get_audit_log(self, target_user_id: str) -> list[dict[str, Any]]:
        """Get audit log entries for a user (admin view).

        Args:
            target_user_id: The user whose audit log to retrieve.

        Returns:
            A list of formatted audit entry dicts.
        """
        items = self._db.get_user_audit_log(target_user_id, limit=100)

        formatted = []
        for item in items:
            entry: dict[str, Any] = {
                "event_type": item.get("event_type", {}).get("S"),
                "timestamp": item.get("timestamp", {}).get("S"),
                "actor": item.get("actor", {}).get("S"),
                "dsb_user_id": item.get("dsb_user_id", {}).get("S"),
            }
            # Optional fields
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

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_bot_token(self) -> str | None:
        """Retrieve the Discord bot token from Secrets Manager."""
        try:
            client = boto3.client("secretsmanager")
            response = client.get_secret_value(
                SecretId=self._settings.discord_bot_secret_name
            )
            secret_data = json.loads(response["SecretString"])
            return secret_data.get("secret_key")
        except (ClientError, json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to retrieve bot token: %s", e)
            return None

    def _remove_discord_roles(
        self, bot_token: str, discord_user_id: str, role_ids: list[str]
    ) -> None:
        """Remove managed roles from a Discord guild member.

        Uses the Discord REST API directly via httpx.
        """
        import httpx

        guild_id = self._settings.discord_guild_id
        headers = {"Authorization": f"Bot {bot_token}"}

        for role_id in role_ids:
            if not role_id:
                continue
            url = (
                f"https://discord.com/api/v10/guilds/{guild_id}"
                f"/members/{discord_user_id}/roles/{role_id}"
            )
            try:
                resp = httpx.delete(url, headers=headers, timeout=10)
                if resp.status_code not in (204, 404):
                    logger.warning(
                        "Failed to remove role %s from user %s: %s",
                        role_id,
                        discord_user_id,
                        resp.status_code,
                    )
            except httpx.HTTPError as e:
                logger.error("HTTP error removing role %s: %s", role_id, e)

    def _write_audit(
        self,
        target_user_id: str,
        event_type: str,
        actor: str,
        reason: str = "",
        discord_user_id: str = "",
    ) -> None:
        """Write an audit log entry to the membership table."""
        timestamp = datetime.now(timezone.utc).isoformat()
        # Use timestamp in SK for chronological ordering
        sk = f"AUDIT#{timestamp}#{event_type}"

        item: dict[str, Any] = {
            "PK": {"S": f"USER#{target_user_id}"},
            "SK": {"S": sk},
            "event_type": {"S": event_type},
            "timestamp": {"S": timestamp},
            "actor": {"S": actor},
            "dsb_user_id": {"S": target_user_id},
        }

        if discord_user_id:
            item["discord_user_id"] = {"S": discord_user_id}
        if reason:
            item["reason"] = {"S": reason}

        try:
            self._db.write_audit_event(item)
        except Exception as e:
            logger.error("Failed to write audit event: %s", e)
