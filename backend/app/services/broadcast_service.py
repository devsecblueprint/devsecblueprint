"""Broadcast service — DynamoDB CRUD for admin broadcast notifications.

Stores broadcasts in a dedicated BROADCASTS_TABLE with 90-day TTL.
User dismissals are co-located in the same table for simple queries.

DynamoDB Schema (BROADCASTS_TABLE):
    Broadcast records:
        PK: "BROADCAST"
        SK: "MSG#{iso_timestamp}_{uuid_short}"
    User dismissal records:
        PK: "USER#{user_id}"
        SK: "DISMISSED#{broadcast_id}"
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings

logger = logging.getLogger(__name__)

# 90 days in seconds
BROADCAST_TTL_SECONDS = 90 * 24 * 60 * 60


class BroadcastService:
    """DynamoDB operations for broadcast notifications."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = boto3.client("dynamodb")

    @property
    def _table_name(self) -> str:
        return self._settings.broadcasts_table

    # ------------------------------------------------------------------
    # Broadcast CRUD
    # ------------------------------------------------------------------

    def create_broadcast(
        self,
        title: str,
        message: str,
        created_by: str,
        link: str = "",
    ) -> dict[str, Any]:
        """Create a broadcast notification record.

        Args:
            title: Broadcast title (max 100 chars).
            message: Markdown body (max 2000 chars).
            created_by: Admin username.
            link: Optional CTA URL.

        Returns:
            Created broadcast record dict.
        """
        now = datetime.now(timezone.utc)
        created_at = now.isoformat()
        uuid_short = uuid.uuid4().hex[:8]
        broadcast_id = f"{created_at}_{uuid_short}"
        ttl_value = int(time.time()) + BROADCAST_TTL_SECONDS

        item: dict[str, Any] = {
            "PK": {"S": "BROADCAST"},
            "SK": {"S": f"MSG#{broadcast_id}"},
            "broadcast_id": {"S": broadcast_id},
            "title": {"S": title},
            "message": {"S": message},
            "link": {"S": link},
            "created_by": {"S": created_by},
            "created_at": {"S": created_at},
            "ttl": {"N": str(ttl_value)},
        }

        self._client.put_item(TableName=self._table_name, Item=item)

        return {
            "broadcast_id": broadcast_id,
            "title": title,
            "message": message,
            "link": link,
            "created_by": created_by,
            "created_at": created_at,
        }

    def get_all_broadcasts(self) -> list[dict[str, Any]]:
        """Get all active broadcasts, sorted by created_at descending.

        Returns:
            List of broadcast dicts.
        """
        broadcasts: list[dict[str, Any]] = []
        last_key = None

        while True:
            params: dict[str, Any] = {
                "TableName": self._table_name,
                "KeyConditionExpression": "PK = :pk",
                "ExpressionAttributeValues": {":pk": {"S": "BROADCAST"}},
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key

            response = self._client.query(**params)
            for item in response.get("Items", []):
                broadcasts.append(
                    {
                        "broadcast_id": item.get("broadcast_id", {}).get("S", ""),
                        "title": item.get("title", {}).get("S", ""),
                        "message": item.get("message", {}).get("S", ""),
                        "link": item.get("link", {}).get("S", ""),
                        "created_by": item.get("created_by", {}).get("S", ""),
                        "created_at": item.get("created_at", {}).get("S", ""),
                    }
                )

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

        # Sort by created_at descending (newest first)
        broadcasts.sort(key=lambda b: b["created_at"], reverse=True)
        return broadcasts

    def delete_broadcast(self, broadcast_id: str) -> bool:
        """Delete a broadcast record.

        Args:
            broadcast_id: The broadcast_id to delete.

        Returns:
            True if deleted successfully.
        """
        try:
            self._client.delete_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": "BROADCAST"},
                    "SK": {"S": f"MSG#{broadcast_id}"},
                },
            )
            return True
        except ClientError as e:
            logger.error("Failed to delete broadcast %s: %s", broadcast_id, e)
            return False

    # ------------------------------------------------------------------
    # User-facing: unread + dismiss
    # ------------------------------------------------------------------

    def get_unread_broadcasts(self, user_id: str) -> list[dict[str, Any]]:
        """Get broadcasts the user has not dismissed.

        Args:
            user_id: Authenticated user ID.

        Returns:
            List of unread broadcast dicts, sorted oldest first (for modal stack).
        """
        # 1. Get all active broadcasts
        all_broadcasts = self.get_all_broadcasts()
        if not all_broadcasts:
            return []

        # 2. Get user's dismissed broadcast IDs
        dismissed_ids = self._get_dismissed_ids(user_id)

        # 3. Filter out dismissed ones
        unread = [b for b in all_broadcasts if b["broadcast_id"] not in dismissed_ids]

        # Sort oldest first for modal stack (chronological order)
        unread.sort(key=lambda b: b["created_at"])
        return unread

    def dismiss_broadcast(self, user_id: str, broadcast_id: str) -> bool:
        """Dismiss a single broadcast for a user.

        Args:
            user_id: Authenticated user ID.
            broadcast_id: The broadcast to dismiss.

        Returns:
            True if successful.
        """
        now = datetime.now(timezone.utc).isoformat()
        # Use same TTL as broadcasts so dismissals auto-clean
        ttl_value = int(time.time()) + BROADCAST_TTL_SECONDS

        try:
            self._client.put_item(
                TableName=self._table_name,
                Item={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": f"DISMISSED#{broadcast_id}"},
                    "dismissed_at": {"S": now},
                    "ttl": {"N": str(ttl_value)},
                },
            )
            return True
        except ClientError as e:
            logger.error(
                "Failed to dismiss broadcast %s for user %s: %s",
                broadcast_id,
                user_id,
                e,
            )
            return False

    def dismiss_all_broadcasts(self, user_id: str, broadcast_ids: list[str]) -> bool:
        """Dismiss multiple broadcasts for a user.

        Args:
            user_id: Authenticated user ID.
            broadcast_ids: List of broadcast IDs to dismiss.

        Returns:
            True if all writes succeed.
        """
        if not broadcast_ids:
            return True

        now = datetime.now(timezone.utc).isoformat()
        ttl_value = int(time.time()) + BROADCAST_TTL_SECONDS

        # BatchWriteItem supports max 25 items per call
        for i in range(0, len(broadcast_ids), 25):
            batch = broadcast_ids[i : i + 25]
            requests = [
                {
                    "PutRequest": {
                        "Item": {
                            "PK": {"S": f"USER#{user_id}"},
                            "SK": {"S": f"DISMISSED#{bid}"},
                            "dismissed_at": {"S": now},
                            "ttl": {"N": str(ttl_value)},
                        }
                    }
                }
                for bid in batch
            ]

            try:
                self._client.batch_write_item(RequestItems={self._table_name: requests})
            except ClientError as e:
                logger.error(
                    "Failed to batch dismiss broadcasts for user %s: %s",
                    user_id,
                    e,
                )
                return False

        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_dismissed_ids(self, user_id: str) -> set[str]:
        """Get set of broadcast IDs the user has dismissed."""
        dismissed: set[str] = set()
        last_key = None

        while True:
            params: dict[str, Any] = {
                "TableName": self._table_name,
                "KeyConditionExpression": "PK = :pk AND begins_with(SK, :sk_prefix)",
                "ExpressionAttributeValues": {
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk_prefix": {"S": "DISMISSED#"},
                },
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key

            response = self._client.query(**params)
            for item in response.get("Items", []):
                sk = item.get("SK", {}).get("S", "")
                if sk.startswith("DISMISSED#"):
                    dismissed.add(sk[10:])  # len("DISMISSED#") == 10

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

        return dismissed
