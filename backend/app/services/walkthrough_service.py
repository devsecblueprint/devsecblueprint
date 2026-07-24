"""Walkthrough service — progress tracking for walkthroughs.

Ported from backend/services/walkthrough_service.py. Self-contained.
Uses DynamoDB directly for WALKTHROUGH# records in PROGRESS_TABLE.
"""

import logging
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings
from app.dependencies import get_settings

logger = logging.getLogger(__name__)


def _get_table_name() -> str:
    """Get progress table name from settings."""
    settings = get_settings()
    return settings.progress_table


def get_walkthrough_progress(user_id: str, walkthrough_id: str) -> dict[str, Any]:
    """Retrieve user's progress for a walkthrough.

    Returns:
        dict with status, started_at, completed_at. Defaults to not_started.
    """
    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")

    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": f"WALKTHROUGH#{walkthrough_id}"},
            },
        )

        item = response.get("Item")
        if not item:
            return {"status": "not_started", "started_at": None, "completed_at": None}

        return {
            "status": item.get("status", {}).get("S", "not_started"),
            "started_at": item.get("started_at", {}).get("S") or None,
            "completed_at": item.get("completed_at", {}).get("S") or None,
        }

    except ClientError as e:
        logger.error("Failed to get walkthrough progress: %s", e)
        return {"status": "not_started", "started_at": None, "completed_at": None}


def update_walkthrough_progress(user_id: str, walkthrough_id: str, status: str) -> None:
    """Update user's progress for a walkthrough.

    Args:
        user_id: Authenticated user ID.
        walkthrough_id: Walkthrough identifier.
        status: New status ("in_progress" or "completed").

    Raises:
        ValueError: If status is not valid.
    """
    valid_statuses = ["in_progress", "completed"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")

    # Get current progress
    current = get_walkthrough_progress(user_id, walkthrough_id)

    started_at = None
    completed_at = None

    if status == "in_progress":
        if current["status"] == "not_started":
            started_at = datetime.now(timezone.utc).isoformat()
        else:
            started_at = current.get("started_at")
    elif status == "completed":
        completed_at = datetime.now(timezone.utc).isoformat()
        if current.get("started_at"):
            started_at = current["started_at"]
        else:
            started_at = completed_at

    # Build item
    item: dict[str, Any] = {
        "PK": {"S": f"USER#{user_id}"},
        "SK": {"S": f"WALKTHROUGH#{walkthrough_id}"},
        "status": {"S": status},
    }
    if started_at:
        item["started_at"] = {"S": started_at}
    if completed_at:
        item["completed_at"] = {"S": completed_at}

    try:
        dynamodb.put_item(TableName=table_name, Item=item)
    except ClientError as e:
        raise Exception(
            f"Failed to save walkthrough progress: {e.response['Error']['Code']}"
        )
