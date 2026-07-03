"""DynamoDB operations for the membership table.

Wraps the membership DynamoDB service layer from the Lambda codebase,
providing the same operations with settings-based table name resolution.
Used by admin Discord operations and other membership-related routes.

Requirements: 4.3
"""

import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings

logger = logging.getLogger(__name__)


class MembershipDB:
    """DynamoDB membership operations.

    Accepts a Settings instance to resolve the membership table name.
    Provides methods used by admin Discord operations and other admin routes.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = boto3.client("dynamodb")

    @property
    def _table_name(self) -> str:
        return self._settings.membership_table

    # ------------------------------------------------------------------
    # Membership record
    # ------------------------------------------------------------------

    def get_membership(self, user_id: str) -> dict[str, Any] | None:
        """Retrieve a user's membership record.

        Args:
            user_id: DSB user identifier.

        Returns:
            The DynamoDB item as a dict, or None if not found.
        """
        try:
            response = self._client.get_item(
                TableName=self._table_name,
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
            raise

    # ------------------------------------------------------------------
    # Discord active connection
    # ------------------------------------------------------------------

    def get_discord_active(self, user_id: str) -> dict[str, Any] | None:
        """Retrieve the active Discord connection for a user.

        Args:
            user_id: DSB user identifier.

        Returns:
            The DISCORD_ACTIVE DynamoDB item, or None if not found.
        """
        try:
            response = self._client.get_item(
                TableName=self._table_name,
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
            raise

    # ------------------------------------------------------------------
    # Deactivate Discord connection
    # ------------------------------------------------------------------

    def deactivate_discord_connection(
        self, user_id: str, discord_id: str, reason: str
    ) -> None:
        """Deactivate a Discord connection via DynamoDB transaction.

        Sets the DISCORD#{discord_id} record to inactive and deletes
        the DISCORD_ACTIVE denormalized record.

        Args:
            user_id: DSB user identifier.
            discord_id: The Discord user ID to deactivate.
            reason: Reason for disconnection.
        """
        from datetime import datetime, timezone

        disconnected_at = datetime.now(timezone.utc).isoformat()

        try:
            self._client.transact_write_items(
                TransactItems=[
                    {
                        "Update": {
                            "TableName": self._table_name,
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
                            "TableName": self._table_name,
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
            raise

    # ------------------------------------------------------------------
    # Audit log
    # ------------------------------------------------------------------

    def get_user_audit_log(
        self, user_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Retrieve audit log entries for a user (newest first).

        Args:
            user_id: DSB user identifier.
            limit: Maximum entries to return.

        Returns:
            List of DynamoDB item dicts representing audit entries.
        """
        try:
            response = self._client.query(
                TableName=self._table_name,
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
            raise

    # ------------------------------------------------------------------
    # Write audit event
    # ------------------------------------------------------------------

    def write_audit_event(self, event: dict[str, Any]) -> None:
        """Write an audit log event to the membership table.

        Args:
            event: A DynamoDB-formatted item dict containing PK, SK,
                   and audit event fields.
        """
        try:
            self._client.put_item(TableName=self._table_name, Item=event)
        except ClientError as e:
            logger.error("Failed to write audit event: %s", e.response["Error"]["Code"])
            raise
