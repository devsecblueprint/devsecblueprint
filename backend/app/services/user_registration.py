"""User registration service.

Registers a user on first OAuth login (creates PROFILE record in DynamoDB)
or updates last_login for returning users. This is a self-contained version
of the register_user logic from the legacy services/dynamo.py.
"""

from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


def register_user(
    table_name: str,
    user_id: str,
    username: str,
    avatar_url: str | None = None,
    github_username: str | None = None,
    provider: str = "github",
    gitlab_username: str | None = None,
    bitbucket_username: str | None = None,
    email: str | None = None,
) -> bool:
    """Register a new user or update existing user information.

    For new users, sets registered_at to the current time.
    For existing users, only updates login-related fields.

    Args:
        table_name: DynamoDB table name (PROGRESS_TABLE).
        user_id: User ID (e.g. "12345" for GitHub, "gitlab_12345" for GitLab).
        username: Display name.
        avatar_url: Avatar URL (optional).
        github_username: GitHub login username (optional).
        provider: Authentication provider ("github", "gitlab", or "bitbucket").
        gitlab_username: GitLab login username (optional).
        bitbucket_username: Bitbucket login username (optional).
        email: User's email address (optional).

    Returns:
        True if the user is new, False if existing.

    Raises:
        Exception: If DynamoDB operation fails.
    """
    dynamodb = boto3.client("dynamodb")
    now = datetime.now(timezone.utc).isoformat()

    # Check if user already exists
    try:
        existing = dynamodb.get_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "PROFILE"}},
            ProjectionExpression="PK",
        )
    except ClientError as e:
        raise Exception(
            f"Failed to check user existence in DynamoDB: {e.response['Error']['Code']}"
        )

    is_new_user = "Item" not in existing

    # Build UpdateExpression
    update_parts = [
        "username = :username",
        "last_login = :last_login",
        "provider = :provider",
    ]
    expr_values: dict = {
        ":username": {"S": username},
        ":last_login": {"S": now},
        ":provider": {"S": provider},
    }

    if is_new_user:
        update_parts.append("registered_at = :registered_at")
        expr_values[":registered_at"] = {"S": now}

    if avatar_url:
        update_parts.append("avatar_url = :avatar_url")
        expr_values[":avatar_url"] = {"S": avatar_url}

    if github_username:
        update_parts.append("github_username = :github_username")
        expr_values[":github_username"] = {"S": github_username}

    if gitlab_username:
        update_parts.append("gitlab_username = :gitlab_username")
        expr_values[":gitlab_username"] = {"S": gitlab_username}

    if bitbucket_username:
        update_parts.append("bitbucket_username = :bitbucket_username")
        expr_values[":bitbucket_username"] = {"S": bitbucket_username}

    if email:
        update_parts.append("email = :email")
        expr_values[":email"] = {"S": email}

    update_expression = "SET " + ", ".join(update_parts)

    try:
        dynamodb.update_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "PROFILE"}},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expr_values,
        )
    except ClientError as e:
        raise Exception(
            f"Failed to register user in DynamoDB: {e.response['Error']['Code']}"
        )

    return is_new_user
