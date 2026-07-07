"""DynamoDB session store for refresh token management.

Stores, retrieves, and deletes refresh token records in the PROGRESS_TABLE.
Records use PK=USER#{user_id} and SK=SESSION#{token_hash}.
DynamoDB TTL is configured on the `expires_at` attribute for automatic cleanup.

Unlike the legacy version, this module receives table_name as a parameter
instead of reading from os.environ directly.
"""

import boto3
from botocore.exceptions import ClientError


def store_refresh_token(
    table_name: str, user_id: str, token_hash: str, created_at: int, expires_at: int
) -> None:
    """Store a hashed refresh token record in DynamoDB.

    Args:
        table_name: DynamoDB table name.
        user_id: User identifier.
        token_hash: SHA-256 hex digest of the raw refresh token.
        created_at: Unix epoch timestamp of token creation.
        expires_at: Unix epoch timestamp of token expiration (also used as TTL).
    """
    dynamodb = boto3.client("dynamodb")

    try:
        dynamodb.put_item(
            TableName=table_name,
            Item={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": f"SESSION#{token_hash}"},
                "created_at": {"N": str(created_at)},
                "expires_at": {"N": str(expires_at)},
                "user_id": {"S": user_id},
            },
        )
    except ClientError as e:
        raise Exception(
            f"Failed to store refresh token in DynamoDB: {e.response['Error']['Code']}"
        )


def get_refresh_token(table_name: str, user_id: str, token_hash: str) -> dict | None:
    """Retrieve a refresh token record from DynamoDB.

    Args:
        table_name: DynamoDB table name.
        user_id: User identifier.
        token_hash: SHA-256 hex digest of the refresh token.

    Returns:
        Dict with token record fields, or None if not found.
    """
    dynamodb = boto3.client("dynamodb")

    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": f"SESSION#{token_hash}"},
            },
        )
    except ClientError as e:
        raise Exception(
            f"Failed to get refresh token from DynamoDB: {e.response['Error']['Code']}"
        )

    item = response.get("Item")
    if not item:
        return None

    return {
        "user_id": item["user_id"]["S"],
        "token_hash": item["SK"]["S"].removeprefix("SESSION#"),
        "created_at": int(item["created_at"]["N"]),
        "expires_at": int(item["expires_at"]["N"]),
    }


def delete_refresh_token(table_name: str, user_id: str, token_hash: str) -> None:
    """Delete a specific refresh token record from DynamoDB.

    Args:
        table_name: DynamoDB table name.
        user_id: User identifier.
        token_hash: SHA-256 hex digest of the refresh token.
    """
    dynamodb = boto3.client("dynamodb")

    try:
        dynamodb.delete_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": f"SESSION#{token_hash}"},
            },
        )
    except ClientError as e:
        raise Exception(
            f"Failed to delete refresh token from DynamoDB: {e.response['Error']['Code']}"
        )


def delete_all_user_sessions(table_name: str, user_id: str) -> None:
    """Delete all SESSION# records for a user from DynamoDB.

    Queries all sort keys beginning with SESSION# for the given user
    and deletes them individually.

    Args:
        table_name: DynamoDB table name.
        user_id: User identifier.
    """
    dynamodb = boto3.client("dynamodb")

    try:
        response = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"USER#{user_id}"},
                ":sk_prefix": {"S": "SESSION#"},
            },
        )

        for item in response.get("Items", []):
            dynamodb.delete_item(
                TableName=table_name,
                Key={"PK": item["PK"], "SK": item["SK"]},
            )

    except ClientError as e:
        raise Exception(
            f"Failed to delete user sessions from DynamoDB: {e.response['Error']['Code']}"
        )
