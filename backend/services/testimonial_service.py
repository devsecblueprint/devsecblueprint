"""
DynamoDB service for testimonial management.

This module provides functions to interact with the TESTIMONIALS_TABLE
DynamoDB table for creating, reading, updating, and deleting testimonial
records. It uses boto3 DynamoDB client and follows the data model
specified in the design document.

DynamoDB Item Structure:
    - PK: "USER#{user_id}"
    - SK: "TESTIMONIAL"
    - display_name, linkedin_url, quote, status, submitted_at, updated_at
    - reviewed_at, reviewed_by, admin_note (set by admin actions)

GSI StatusIndex:
    - PK: status
    - SK: submitted_at
"""

import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


def _get_table_name() -> str:
    """Get the DynamoDB table name from environment."""
    table_name = os.environ.get("TESTIMONIALS_TABLE")
    if not table_name:
        raise Exception("TESTIMONIALS_TABLE environment variable not set")
    return table_name


def create_testimonial(
    user_id: str, display_name: str, linkedin_url: str, quote: str
) -> dict:
    """
    Create a new testimonial record in DynamoDB.

    Args:
        user_id: User identifier (e.g. "github|12345678")
        display_name: Display name for the testimonial
        linkedin_url: Optional LinkedIn profile URL (can be empty string)
        quote: Testimonial quote text

    Returns:
        dict: The created testimonial record

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
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
        raise Exception(
            f"Failed to create testimonial in DynamoDB: {e.response['Error']['Code']}"
        )

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


def get_testimonial(user_id: str) -> dict | None:
    """
    Retrieve a testimonial record from DynamoDB.

    Args:
        user_id: User identifier

    Returns:
        dict: Testimonial record, or None if not found

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")

    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "TESTIMONIAL"},
            },
        )
    except ClientError as e:
        raise Exception(
            f"Failed to get testimonial from DynamoDB: {e.response['Error']['Code']}"
        )

    item = response.get("Item")
    if not item:
        return None

    return _parse_testimonial_item(item)


def update_testimonial(user_id: str, updates: dict) -> dict | None:
    """
    Update an existing testimonial record in DynamoDB.

    Args:
        user_id: User identifier
        updates: Dictionary of fields to update (e.g. display_name, linkedin_url,
                 quote, status, reviewed_at, reviewed_by, admin_note)

    Returns:
        dict: Updated testimonial record, or None if not found

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")

    # Always update the updated_at timestamp
    now = datetime.now(timezone.utc).isoformat()
    updates["updated_at"] = now

    # Build UpdateExpression dynamically
    update_parts = []
    expr_attr_values = {}
    expr_attr_names = {}

    for key, value in updates.items():
        # Use expression attribute names to handle reserved words
        attr_name = f"#{key}"
        attr_value = f":{key}"
        update_parts.append(f"{attr_name} = {attr_value}")
        expr_attr_names[attr_name] = key
        expr_attr_values[attr_value] = {"S": str(value)}

    update_expression = "SET " + ", ".join(update_parts)

    try:
        response = dynamodb.update_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "TESTIMONIAL"},
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
            ConditionExpression="attribute_exists(PK)",
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise Exception(
            f"Failed to update testimonial in DynamoDB: {e.response['Error']['Code']}"
        )

    return _parse_testimonial_item(response.get("Attributes", {}))


def delete_testimonial(user_id: str) -> None:
    """
    Delete a testimonial record from DynamoDB.

    Args:
        user_id: User identifier

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")

    try:
        dynamodb.delete_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "TESTIMONIAL"},
            },
        )
    except ClientError as e:
        raise Exception(
            f"Failed to delete testimonial from DynamoDB: {e.response['Error']['Code']}"
        )


def get_testimonials_by_status(status: str) -> list:
    """
    Query testimonials by status using the StatusIndex GSI.

    Args:
        status: Testimonial status to filter by (e.g. "pending", "approved")

    Returns:
        list: List of testimonial records matching the status

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")

    try:
        items = []
        last_evaluated_key = None

        while True:
            query_params = {
                "TableName": table_name,
                "IndexName": "StatusIndex",
                "KeyConditionExpression": "#status = :status",
                "ExpressionAttributeNames": {"#status": "status"},
                "ExpressionAttributeValues": {":status": {"S": status}},
            }

            if last_evaluated_key:
                query_params["ExclusiveStartKey"] = last_evaluated_key

            response = dynamodb.query(**query_params)

            for item in response.get("Items", []):
                items.append(_parse_testimonial_item(item))

            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break

        return items

    except ClientError as e:
        raise Exception(
            f"Failed to query testimonials by status from DynamoDB: {e.response['Error']['Code']}"
        )


def get_all_testimonials() -> list:
    """
    Scan all testimonials from the table (admin only, small dataset).

    Returns:
        list: List of all testimonial records

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = _get_table_name()
    dynamodb = boto3.client("dynamodb")

    try:
        items = []
        last_evaluated_key = None

        while True:
            scan_params = {"TableName": table_name}

            if last_evaluated_key:
                scan_params["ExclusiveStartKey"] = last_evaluated_key

            response = dynamodb.scan(**scan_params)

            for item in response.get("Items", []):
                items.append(_parse_testimonial_item(item))

            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break

        return items

    except ClientError as e:
        raise Exception(
            f"Failed to scan testimonials from DynamoDB: {e.response['Error']['Code']}"
        )


def _parse_testimonial_item(item: dict) -> dict:
    """
    Parse a DynamoDB item into a testimonial record dict.

    Args:
        item: Raw DynamoDB item with typed attribute values

    Returns:
        dict: Parsed testimonial record
    """
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
