"""
Notification service for in-app notifications.

This module provides functions to interact with the NOTIFICATIONS_TABLE DynamoDB
table for creating, retrieving, and deleting user notifications. It follows the
same patterns as dynamo.py (boto3 client, env var, ClientError handling).
"""

import os
import time
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

# TTL duration: 7 days in seconds
NOTIFICATION_TTL_SECONDS = 7 * 24 * 60 * 60


def create_notification(user_id: str, message: str, link: str) -> dict:
    """
    Create a notification record in NOTIFICATIONS_TABLE.

    Args:
        user_id: User identifier (recipient)
        message: Notification message text
        link: Path to relevant page (e.g., /courses/capstone/devsecops-capstone)

    Returns:
        dict: Created notification record with notification_id, message, link, created_at

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("NOTIFICATIONS_TABLE")
    if not table_name:
        raise Exception("NOTIFICATIONS_TABLE environment variable not set")

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
        raise Exception(
            f"Failed to create notification in DynamoDB: {e.response['Error']['Code']}"
        )

    return {
        "notification_id": timestamp_id,
        "message": message,
        "link": link,
        "created_at": created_at,
    }


def get_notifications(user_id: str) -> list[dict]:
    """
    Get all notifications for a user, sorted by created_at descending.

    Args:
        user_id: User identifier

    Returns:
        list[dict]: List of notification records sorted by created_at descending,
            each containing notification_id, message, link, created_at

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("NOTIFICATIONS_TABLE")
    if not table_name:
        raise Exception("NOTIFICATIONS_TABLE environment variable not set")

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

        # Sort by created_at descending
        notifications.sort(key=lambda n: n["created_at"], reverse=True)

        return notifications

    except ClientError as e:
        raise Exception(
            f"Failed to get notifications from DynamoDB: {e.response['Error']['Code']}"
        )


def delete_notification(user_id: str, notification_id: str) -> bool:
    """
    Delete a notification record from NOTIFICATIONS_TABLE (acknowledge).

    Args:
        user_id: User identifier
        notification_id: The timestamp_id portion of the notification SK

    Returns:
        bool: True if deletion succeeded, False otherwise

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("NOTIFICATIONS_TABLE")
    if not table_name:
        raise Exception("NOTIFICATIONS_TABLE environment variable not set")

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
        raise Exception(
            f"Failed to delete notification from DynamoDB: {e.response['Error']['Code']}"
        )
