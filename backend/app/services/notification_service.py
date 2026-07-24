"""Notification service — DynamoDB CRUD for in-app notifications.

Ported from backend/services/notification_service.py. Self-contained.

DynamoDB Schema (NOTIFICATIONS_TABLE):
    PK: USER#{user_id}
    SK: NOTIFICATION#{timestamp_id}
    Fields: message, link, created_at, ttl
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings
from app.dependencies import get_settings

logger = logging.getLogger(__name__)

# TTL: 7 days in seconds
NOTIFICATION_TTL_SECONDS = 7 * 24 * 60 * 60


def _get_table_name() -> str:
    """Get notifications table name from settings."""
    settings = get_settings()
    return settings.notifications_table


def create_notification(user_id: str, message: str, link: str) -> dict[str, Any]:
    """Create a notification record.

    Args:
        user_id: Recipient user ID.
        message: Notification message text.
        link: Path to relevant page.

    Returns:
        Created notification record dict.
    """
    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")

    created_at = datetime.now(timezone.utc).isoformat()
    timestamp_id = f"{created_at}_{uuid.uuid4().hex[:8]}"
    ttl_value = int(time.time()) + NOTIFICATION_TTL_SECONDS

    item = {
        "PK": {"S": f"USER#{user_id}"},
        "SK": {"S": f"NOTIFICATION#{timestamp_id}"},
        "message": {"S": message},
        "link": {"S": link},
        "created_at": {"S": created_at},
        "ttl": {"N": str(ttl_value)},
    }

    try:
        dynamodb.put_item(TableName=table_name, Item=item)
    except ClientError as e:
        raise Exception(f"Failed to create notification: {e.response['Error']['Code']}")

    return {
        "notification_id": timestamp_id,
        "message": message,
        "link": link,
        "created_at": created_at,
    }


def get_notifications(user_id: str) -> list[dict[str, Any]]:
    """Get all notifications for a user, sorted by created_at descending.

    Returns:
        List of notification dicts.
    """
    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")

    try:
        response = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": {"S": f"USER#{user_id}"}},
        )

        notifications = []
        for item in response.get("Items", []):
            sk = item.get("SK", {}).get("S", "")
            notification_id = sk.replace("NOTIFICATION#", "")
            notifications.append(
                {
                    "notification_id": notification_id,
                    "message": item.get("message", {}).get("S", ""),
                    "link": item.get("link", {}).get("S", ""),
                    "created_at": item.get("created_at", {}).get("S", ""),
                }
            )

        notifications.sort(key=lambda n: n["created_at"], reverse=True)
        return notifications

    except ClientError as e:
        raise Exception(f"Failed to get notifications: {e.response['Error']['Code']}")


def delete_notification(user_id: str, notification_id: str) -> bool:
    """Delete (acknowledge) a notification.

    Returns:
        True if deletion succeeded.
    """
    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")

    try:
        dynamodb.delete_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": f"NOTIFICATION#{notification_id}"},
            },
        )
        return True
    except ClientError as e:
        raise Exception(f"Failed to delete notification: {e.response['Error']['Code']}")
