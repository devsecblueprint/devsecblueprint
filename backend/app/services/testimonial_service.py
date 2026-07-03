"""Testimonial service — DynamoDB CRUD for testimonials.

Ported from backend/services/testimonial_service.py. Self-contained.
Uses the TESTIMONIALS_TABLE from Settings (injected via table_name parameter).

DynamoDB Schema:
    PK: USER#{user_id}
    SK: TESTIMONIAL
    GSI StatusIndex: PK=status, SK=submitted_at
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
    """Get testimonials table name from settings."""
    settings = get_settings()
    return settings.testimonials_table


def create_testimonial(
    user_id: str, display_name: str, linkedin_url: str, quote: str
) -> dict[str, Any]:
    """Create a new testimonial record.

    Returns:
        The created testimonial record dict.
    """
    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")
    now = datetime.now(timezone.utc).isoformat()

    item = {
        "PK": {"S": f"USER#{user_id}"},
        "SK": {"S": "TESTIMONIAL"},
        "display_name": {"S": display_name},
        "linkedin_url": {"S": linkedin_url or ""},
        "quote": {"S": quote},
        "status": {"S": "pending"},
        "submitted_at": {"S": now},
        "updated_at": {"S": now},
        "reviewed_at": {"S": ""},
        "reviewed_by": {"S": ""},
        "admin_note": {"S": ""},
    }

    try:
        dynamodb.put_item(TableName=table_name, Item=item)
    except ClientError as e:
        raise Exception(f"Failed to create testimonial: {e.response['Error']['Code']}")

    return {
        "user_id": user_id,
        "display_name": display_name,
        "linkedin_url": linkedin_url or "",
        "quote": quote,
        "status": "pending",
        "submitted_at": now,
        "updated_at": now,
        "reviewed_at": "",
        "reviewed_by": "",
        "admin_note": "",
    }


def get_testimonial(user_id: str) -> dict[str, Any] | None:
    """Retrieve a user's testimonial record."""
    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")

    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "TESTIMONIAL"}},
        )
    except ClientError as e:
        raise Exception(f"Failed to get testimonial: {e.response['Error']['Code']}")

    item = response.get("Item")
    if not item:
        return None
    return _parse_item(item)


def update_testimonial(user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    """Update an existing testimonial record.

    Args:
        user_id: User identifier.
        updates: Dict of field names to new values.

    Returns:
        Updated testimonial dict, or None if not found.
    """
    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")

    now = datetime.now(timezone.utc).isoformat()
    updates["updated_at"] = now

    update_parts = []
    expr_attr_values: dict[str, Any] = {}
    expr_attr_names: dict[str, str] = {}

    for key, value in updates.items():
        attr_name = f"#{key}"
        attr_value = f":{key}"
        update_parts.append(f"{attr_name} = {attr_value}")
        expr_attr_names[attr_name] = key
        expr_attr_values[attr_value] = {"S": str(value)}

    try:
        response = dynamodb.update_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "TESTIMONIAL"}},
            UpdateExpression="SET " + ", ".join(update_parts),
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
            ConditionExpression="attribute_exists(PK)",
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise Exception(f"Failed to update testimonial: {e.response['Error']['Code']}")

    return _parse_item(response.get("Attributes", {}))


def delete_testimonial(user_id: str) -> None:
    """Delete a testimonial record."""
    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")

    try:
        dynamodb.delete_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "TESTIMONIAL"}},
        )
    except ClientError as e:
        raise Exception(f"Failed to delete testimonial: {e.response['Error']['Code']}")


def get_testimonials_by_status(status: str) -> list[dict[str, Any]]:
    """Query testimonials by status using the StatusIndex GSI."""
    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")

    try:
        items: list[dict[str, Any]] = []
        last_key = None

        while True:
            params: dict[str, Any] = {
                "TableName": table_name,
                "IndexName": "StatusIndex",
                "KeyConditionExpression": "#status = :status",
                "ExpressionAttributeNames": {"#status": "status"},
                "ExpressionAttributeValues": {":status": {"S": status}},
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key

            response = dynamodb.query(**params)
            for item in response.get("Items", []):
                items.append(_parse_item(item))

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

        return items
    except ClientError as e:
        raise Exception(
            f"Failed to query testimonials by status: {e.response['Error']['Code']}"
        )


def get_all_testimonials() -> list[dict[str, Any]]:
    """Scan all testimonials (admin only, small dataset)."""
    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")

    try:
        items: list[dict[str, Any]] = []
        last_key = None

        while True:
            params: dict[str, Any] = {"TableName": table_name}
            if last_key:
                params["ExclusiveStartKey"] = last_key

            response = dynamodb.scan(**params)
            for item in response.get("Items", []):
                items.append(_parse_item(item))

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

        return items
    except ClientError as e:
        raise Exception(f"Failed to scan testimonials: {e.response['Error']['Code']}")


def _parse_item(item: dict[str, Any]) -> dict[str, Any]:
    """Parse a DynamoDB item into a testimonial dict."""
    pk = item.get("PK", {}).get("S", "")
    user_id = pk.removeprefix("USER#") if pk.startswith("USER#") else pk

    return {
        "user_id": user_id,
        "display_name": item.get("display_name", {}).get("S", ""),
        "linkedin_url": item.get("linkedin_url", {}).get("S", ""),
        "quote": item.get("quote", {}).get("S", ""),
        "status": item.get("status", {}).get("S", ""),
        "submitted_at": item.get("submitted_at", {}).get("S", ""),
        "updated_at": item.get("updated_at", {}).get("S", ""),
        "reviewed_at": item.get("reviewed_at", {}).get("S", ""),
        "reviewed_by": item.get("reviewed_by", {}).get("S", ""),
        "admin_note": item.get("admin_note", {}).get("S", ""),
    }
