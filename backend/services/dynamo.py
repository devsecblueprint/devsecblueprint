"""
DynamoDB service for user progress tracking.

This module provides functions to interact with DynamoDB tables for persisting
user progress data. It uses boto3 DynamoDB client and follows the data model
specified in the design document.
"""

import os
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError


def save_progress(user_id: str, content_id: str) -> None:
    """
    Save user progress to DynamoDB.

    Args:
        user_id: GitHub user ID
        content_id: Content identifier (e.g., "devsecops/topic/page-id" or just "page-id")

    DynamoDB Item Structure:
        - PK: "USER#<user_id>"
        - SK: "CONTENT#<content_id>"
        - status: "complete"
        - completed_at: ISO 8601 timestamp

    Note: If content_id is in path format (contains /), also saves with just the page ID
    for backward compatibility with sidebar completion checks.

    Environment Variables:
        - PROGRESS_TABLE: DynamoDB table name

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    # Create DynamoDB client
    dynamodb = boto3.client("dynamodb")

    # Generate ISO 8601 timestamp
    completed_at = datetime.now(timezone.utc).isoformat()

    # Format item with proper DynamoDB attribute types
    item = {
        "PK": {"S": f"USER#{user_id}"},
        "SK": {"S": f"CONTENT#{content_id}"},
        "status": {"S": "complete"},
        "completed_at": {"S": completed_at},
    }

    try:
        dynamodb.put_item(TableName=table_name, Item=item)

    except ClientError as e:
        raise Exception(
            f"Failed to save progress to DynamoDB: {e.response['Error']['Code']}"
        )


def delete_all_user_progress(user_id: str) -> None:
    """
    Delete all progress data for a user.

    Args:
        user_id: GitHub user ID

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    try:
        # Query all items for this user
        response = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": {"S": f"USER#{user_id}"}},
        )

        # Delete each item
        for item in response.get("Items", []):
            dynamodb.delete_item(
                TableName=table_name, Key={"PK": item["PK"], "SK": item["SK"]}
            )

    except ClientError as e:
        raise Exception(
            f"Failed to delete progress from DynamoDB: {e.response['Error']['Code']}"
        )


def get_all_users_progress() -> list:
    """
    Get progress data for all users (admin only).

    Returns:
        list: List of all progress items with user_id and content_id

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    try:
        # Scan the entire table (admin operation)
        items = []
        last_evaluated_key = None

        while True:
            if last_evaluated_key:
                response = dynamodb.scan(
                    TableName=table_name, ExclusiveStartKey=last_evaluated_key
                )
            else:
                response = dynamodb.scan(TableName=table_name)

            # Parse items
            for item in response.get("Items", []):
                pk = item.get("PK", {}).get("S", "")
                sk = item.get("SK", {}).get("S", "")

                # Extract user_id from PK (format: USER#<user_id>)
                if pk.startswith("USER#"):
                    user_id = pk.replace("USER#", "")

                    # Extract content_id from SK (format: CONTENT#<content_id>)
                    if sk.startswith("CONTENT#"):
                        content_id = sk.replace("CONTENT#", "")

                        items.append(
                            {
                                "user_id": user_id,
                                "content_id": content_id,
                                "status": item.get("status", {}).get("S", ""),
                                "completed_at": item.get("completed_at", {}).get(
                                    "S", ""
                                ),
                            }
                        )

            # Check if there are more items
            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break

        return items

    except ClientError as e:
        raise Exception(
            f"Failed to scan progress from DynamoDB: {e.response['Error']['Code']}"
        )


def register_user(
    user_id: str,
    username: str,
    avatar_url: str = None,
    github_username: str = None,
    provider: str = "github",
    gitlab_username: str = None,
) -> None:
    """
    Register a new user or update existing user information.

    For new users, sets registered_at to the current time.
    For existing users, only updates login-related fields — registered_at is never touched.

    Args:
        user_id: User ID (e.g. "12345" for GitHub, "gitlab_12345" for GitLab)
        username: Display name
        avatar_url: Avatar URL (optional)
        github_username: GitHub login username (optional)
        provider: Authentication provider ("github" or "gitlab")
        gitlab_username: GitLab login username (optional)

    Raises:
        Exception: If DynamoDB operation fails or table name is missing

    Requirements: 3.1, 3.2, 3.3, 3.4, 12.1, 12.2, 12.3
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

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

    # Build UpdateExpression — only include registered_at for new users
    update_parts = [
        "username = :username",
        "last_login = :last_login",
        "provider = :provider",
    ]
    expr_values = {
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


def get_user_profile(user_id: str) -> dict:
    """
    Get user profile information.

    Args:
        user_id: GitHub user ID

    Returns:
        dict: User profile data or None if not found

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "PROFILE"}},
        )

        item = response.get("Item")
        if not item:
            return None

        return {
            "user_id": user_id,
            "username": item.get("username", {}).get("S", ""),
            "avatar_url": item.get("avatar_url", {}).get("S", ""),
            "registered_at": item.get("registered_at", {}).get("S", ""),
            "last_login": item.get("last_login", {}).get("S", ""),
            "github_username": item.get("github_username", {}).get("S", ""),
        }

    except ClientError as e:
        raise Exception(
            f"Failed to get user profile from DynamoDB: {e.response['Error']['Code']}"
        )


def get_all_registered_users() -> list:
    """
    Get all registered users (admin only).

    Returns:
        list: List of all registered users

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    try:
        users = []
        last_evaluated_key = None

        while True:
            # Query for all PROFILE items
            if last_evaluated_key:
                response = dynamodb.scan(
                    TableName=table_name,
                    FilterExpression="SK = :sk",
                    ExpressionAttributeValues={":sk": {"S": "PROFILE"}},
                    ExclusiveStartKey=last_evaluated_key,
                )
            else:
                response = dynamodb.scan(
                    TableName=table_name,
                    FilterExpression="SK = :sk",
                    ExpressionAttributeValues={":sk": {"S": "PROFILE"}},
                )

            # Parse items
            for item in response.get("Items", []):
                pk = item.get("PK", {}).get("S", "")
                if pk.startswith("USER#"):
                    user_id = pk.replace("USER#", "")
                    users.append(
                        {
                            "user_id": user_id,
                            "username": item.get("username", {}).get("S", ""),
                            "github_username": item.get("github_username", {}).get(
                                "S", ""
                            ),
                            "gitlab_username": item.get("gitlab_username", {}).get(
                                "S", ""
                            ),
                            "provider": item.get("provider", {}).get("S", "github"),
                            "avatar_url": item.get("avatar_url", {}).get("S", ""),
                            "registered_at": item.get("registered_at", {}).get("S", ""),
                            "last_login": item.get("last_login", {}).get("S", ""),
                        }
                    )

            # Check if there are more items
            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break

        return users

    except ClientError as e:
        raise Exception(
            f"Failed to get registered users from DynamoDB: {e.response['Error']['Code']}"
        )


def get_module_completion(user_id: str, module_id: str) -> dict | None:
    """
    Retrieve module completion record.

    Args:
        user_id: User identifier
        module_id: Module identifier

    Returns:
        dict: {
            "score": int,
            "first_completed_at": str,
            "completed_at": str
        } or None if not found

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": f"MODULE#{module_id}"}},
        )

        item = response.get("Item")
        if not item:
            return None

        return {
            "score": int(item.get("score", {}).get("N", "0")),
            "first_completed_at": item.get("first_completed_at", {}).get("S", ""),
            "completed_at": item.get("completed_at", {}).get("S", ""),
        }

    except ClientError as e:
        raise Exception(
            f"Failed to get module completion from DynamoDB: {e.response['Error']['Code']}"
        )


def save_module_completion(
    user_id: str, module_id: str, score: int, is_first_completion: bool
) -> None:
    """
    Save or update module completion record.

    Args:
        user_id: User identifier
        module_id: Module identifier
        score: Quiz score (0-100)
        is_first_completion: True if this is the first completion, False for re-completion

    Behavior:
        - First completion: Sets score, first_completed_at, and completed_at
        - Re-completion: Updates score only if higher, always updates completed_at

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    # Generate ISO 8601 timestamp
    completed_at = datetime.now(timezone.utc).isoformat()

    try:
        if is_first_completion:
            # First completion: set all fields
            item = {
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": f"MODULE#{module_id}"},
                "score": {"N": str(score)},
                "first_completed_at": {"S": completed_at},
                "completed_at": {"S": completed_at},
            }
            dynamodb.put_item(TableName=table_name, Item=item)
        else:
            # Re-completion: update score only if higher, always update completed_at
            # Get existing record to compare scores
            existing = get_module_completion(user_id, module_id)
            if existing:
                existing_score = existing["score"]
                # Update score only if new score is higher
                if score > existing_score:
                    dynamodb.update_item(
                        TableName=table_name,
                        Key={
                            "PK": {"S": f"USER#{user_id}"},
                            "SK": {"S": f"MODULE#{module_id}"},
                        },
                        UpdateExpression="SET score = :score, completed_at = :completed_at",
                        ExpressionAttributeValues={
                            ":score": {"N": str(score)},
                            ":completed_at": {"S": completed_at},
                        },
                    )
                else:
                    # Only update completed_at
                    dynamodb.update_item(
                        TableName=table_name,
                        Key={
                            "PK": {"S": f"USER#{user_id}"},
                            "SK": {"S": f"MODULE#{module_id}"},
                        },
                        UpdateExpression="SET completed_at = :completed_at",
                        ExpressionAttributeValues={
                            ":completed_at": {"S": completed_at},
                        },
                    )

    except ClientError as e:
        raise Exception(
            f"Failed to save module completion to DynamoDB: {e.response['Error']['Code']}"
        )


def get_streak_data(user_id: str) -> dict:
    """
    Retrieve user streak data.

    Args:
        user_id: User identifier

    Returns:
        dict: {
            "current_streak": int,
            "longest_streak": int,
            "last_activity_date": str | None  # YYYY-MM-DD format
        }
        Returns default values (0, 0, None) if no streak record exists

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "STREAK"}},
        )

        item = response.get("Item")
        if not item:
            # Return default values if no streak record exists
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "last_activity_date": None,
            }

        return {
            "current_streak": int(item.get("current_streak", {}).get("N", "0")),
            "longest_streak": int(item.get("longest_streak", {}).get("N", "0")),
            "last_activity_date": item.get("last_activity_date", {}).get("S"),
        }

    except ClientError as e:
        raise Exception(
            f"Failed to get streak data from DynamoDB: {e.response['Error']['Code']}"
        )


def update_streak_data(
    user_id: str, current_streak: int, longest_streak: int, last_activity_date: str
) -> None:
    """
    Update user streak data.

    Args:
        user_id: User identifier
        current_streak: Current consecutive days streak
        longest_streak: Longest streak ever achieved
        last_activity_date: Last activity date in YYYY-MM-DD format

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    try:
        item = {
            "PK": {"S": f"USER#{user_id}"},
            "SK": {"S": "STREAK"},
            "current_streak": {"N": str(current_streak)},
            "longest_streak": {"N": str(longest_streak)},
            "last_activity_date": {"S": last_activity_date},
        }
        dynamodb.put_item(TableName=table_name, Item=item)

    except ClientError as e:
        raise Exception(
            f"Failed to update streak data in DynamoDB: {e.response['Error']['Code']}"
        )


def get_walkthrough_progress(user_id: str, walkthrough_id: str) -> dict | None:
    """
    Retrieve walkthrough progress record.

    Args:
        user_id: User identifier
        walkthrough_id: Walkthrough identifier

    Returns:
        dict: {
            "status": str,  # "not_started", "in_progress", "completed"
            "started_at": str,
            "completed_at": str | None
        } or None if not started

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

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
            return None

        return {
            "status": item.get("status", {}).get("S", "not_started"),
            "started_at": item.get("started_at", {}).get("S", ""),
            "completed_at": item.get("completed_at", {}).get("S"),
        }

    except ClientError as e:
        raise Exception(
            f"Failed to get walkthrough progress from DynamoDB: {e.response['Error']['Code']}"
        )


def save_walkthrough_progress(
    user_id: str,
    walkthrough_id: str,
    status: str,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> None:
    """
    Save or update walkthrough progress record.

    Args:
        user_id: User identifier
        walkthrough_id: Walkthrough identifier
        status: Progress status ("not_started", "in_progress", "completed")
        started_at: ISO timestamp when started (set on first save)
        completed_at: ISO timestamp when completed (set when status is "completed")

    DynamoDB Item Structure:
        - PK: "USER#<user_id>"
        - SK: "WALKTHROUGH#<walkthrough_id>"
        - status: "not_started" | "in_progress" | "completed"
        - started_at: ISO 8601 timestamp
        - completed_at: ISO 8601 timestamp | null

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    # Build the item
    item = {
        "PK": {"S": f"USER#{user_id}"},
        "SK": {"S": f"WALKTHROUGH#{walkthrough_id}"},
        "status": {"S": status},
    }

    # Add started_at if provided
    if started_at:
        item["started_at"] = {"S": started_at}

    # Add completed_at if provided
    if completed_at:
        item["completed_at"] = {"S": completed_at}

    try:
        dynamodb.put_item(TableName=table_name, Item=item)
    except ClientError as e:
        raise Exception(
            f"Failed to save walkthrough progress to DynamoDB: {e.response['Error']['Code']}"
        )


def save_capstone_submission(
    user_id: str,
    content_id: str,
    repo_url: str,
    github_username: str,
    repo_name: str,
    provider: str = "github",
) -> None:
    """
    Save capstone submission to DynamoDB.

    Args:
        user_id: User identifier from JWT
        content_id: Capstone content identifier
        repo_url: Full repository URL
        github_username: Extracted username from the repo URL
        repo_name: Extracted repository name
        provider: Authentication provider ("github" or "gitlab")

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    # Generate ISO 8601 timestamp
    timestamp = datetime.now(timezone.utc).isoformat()

    # Format item with proper DynamoDB attribute types
    item = {
        "PK": {"S": f"USER#{user_id}"},
        "SK": {"S": f"CAPSTONE_SUBMISSION#{content_id}"},
        "repo_url": {"S": repo_url},
        "github_username": {"S": github_username},
        "repo_name": {"S": repo_name},
        "provider": {"S": provider},
        "submitted_at": {"S": timestamp},
        "updated_at": {"S": timestamp},
    }

    try:
        dynamodb.put_item(TableName=table_name, Item=item)
    except ClientError as e:
        raise Exception(
            f"Failed to save capstone submission to DynamoDB: {e.response['Error']['Code']}"
        )


def get_capstone_submission(user_id: str, content_id: str) -> dict | None:
    """
    Retrieve capstone submission from DynamoDB.

    Args:
        user_id: User identifier
        content_id: Capstone content identifier

    Returns:
        dict: Capstone submission data with keys:
            - repo_url: string
            - github_username: string
            - repo_name: string
            - submitted_at: ISO 8601 timestamp
            - updated_at: ISO 8601 timestamp
        None: If no submission exists

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": f"CAPSTONE_SUBMISSION#{content_id}"},
            },
        )

        item = response.get("Item")
        if not item:
            return None

        return {
            "repo_url": item.get("repo_url", {}).get("S", ""),
            "github_username": item.get("github_username", {}).get("S", ""),
            "repo_name": item.get("repo_name", {}).get("S", ""),
            "submitted_at": item.get("submitted_at", {}).get("S", ""),
            "updated_at": item.get("updated_at", {}).get("S", ""),
        }

    except ClientError as e:
        raise Exception(
            f"Failed to get capstone submission from DynamoDB: {e.response['Error']['Code']}"
        )


def delete_user_account(user_id: str) -> bool:
    """
    Permanently delete a user account and all associated data.

    This includes:
    - User profile (PROFILE)
    - All progress records (CONTENT#*)
    - All module completions (MODULE#*)
    - Streak data (STREAK)
    - Walkthrough progress (WALKTHROUGH#*)
    - Capstone submissions (CAPSTONE_SUBMISSION#*)

    Args:
        user_id: GitHub user ID

    Returns:
        bool: True if deletion was successful, False otherwise

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    try:
        # Query all items for this user
        items_to_delete = []
        last_evaluated_key = None

        while True:
            query_params = {
                "TableName": table_name,
                "KeyConditionExpression": "PK = :pk",
                "ExpressionAttributeValues": {":pk": {"S": f"USER#{user_id}"}},
            }

            if last_evaluated_key:
                query_params["ExclusiveStartKey"] = last_evaluated_key

            response = dynamodb.query(**query_params)

            # Collect all items to delete
            for item in response.get("Items", []):
                items_to_delete.append({"PK": item["PK"], "SK": item["SK"]})

            # Check if there are more items
            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break

        # Delete all items
        for key in items_to_delete:
            dynamodb.delete_item(TableName=table_name, Key=key)

        return True

    except ClientError as e:
        print(
            f"Failed to delete user account from DynamoDB: {e.response['Error']['Code']}"
        )
        return False
    except Exception as e:
        print(f"Unexpected error deleting user account: {str(e)}")
        return False


def get_total_capstone_submissions_count() -> int:
    """
    Get the total count of all capstone submissions across all users.

    Returns:
        int: Total number of capstone submissions

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    try:
        count = 0
        last_evaluated_key = None

        # Scan table for all capstone submissions
        while True:
            scan_params = {
                "TableName": table_name,
                "FilterExpression": "begins_with(SK, :sk_prefix)",
                "ExpressionAttributeValues": {
                    ":sk_prefix": {"S": "CAPSTONE_SUBMISSION#"}
                },
                "Select": "COUNT",  # Only count, don't return items
            }

            if last_evaluated_key:
                scan_params["ExclusiveStartKey"] = last_evaluated_key

            response = dynamodb.scan(**scan_params)
            count += response.get("Count", 0)

            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break

        return count

    except ClientError as e:
        raise Exception(
            f"Failed to count capstone submissions from DynamoDB: {e.response['Error']['Code']}"
        )


def get_all_badge_stats() -> dict:
    """
    Get badge statistics across all users (optimized - counts key achievements only).

    Returns:
        dict: {
            "total_badges_earned": int,
            "unique_users_with_badges": int,
            "badge_distribution": [
                {"badge_id": str, "badge_title": str, "count": int},
                ...
            ]
        }

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    # Badge definitions for titles
    from services.badge_service import BADGE_DEFINITIONS

    badge_titles = {b["id"]: b["title"] for b in BADGE_DEFINITIONS}

    try:
        # Get progress data (fast - single scan)
        all_progress = get_all_users_progress()

        # Count key achievements that map to badges
        users_with_progress = set()
        devsecops_completions = set()
        cloud_security_completions = set()

        for item in all_progress:
            user_id = item.get("user_id")
            content_id = item.get("content_id", "")

            if user_id:
                users_with_progress.add(user_id)

            # Count capstone completions (path completion badges)
            if content_id == "devsecops-capstone":
                devsecops_completions.add(user_id)
            elif content_id == "cloud_security_development-capstone":
                cloud_security_completions.add(user_id)

        # Count actual capstone submissions (not just page completions)
        # This should match the individual user badge calculation
        capstone_submissions = set()
        table_name = os.environ.get("PROGRESS_TABLE")
        if table_name:
            try:
                dynamodb = boto3.client("dynamodb")
                last_evaluated_key = None

                while True:
                    scan_params = {
                        "TableName": table_name,
                        "FilterExpression": "begins_with(SK, :sk_prefix)",
                        "ExpressionAttributeValues": {
                            ":sk_prefix": {"S": "CAPSTONE_SUBMISSION#"}
                        },
                    }

                    if last_evaluated_key:
                        scan_params["ExclusiveStartKey"] = last_evaluated_key

                    response = dynamodb.scan(**scan_params)

                    for item in response.get("Items", []):
                        pk = item.get("PK", {}).get("S", "")
                        if pk.startswith("USER#"):
                            user_id = pk.replace("USER#", "")
                            capstone_submissions.add(user_id)

                    last_evaluated_key = response.get("LastEvaluatedKey")
                    if not last_evaluated_key:
                        break

            except ClientError:
                # If scan fails, default to empty set
                capstone_submissions = set()

        # Get perfect quiz scores (fast - filtered scan with COUNT)
        perfect_scores = get_perfect_quiz_count()

        # Build badge distribution (only badges we can efficiently count)
        badge_distribution = [
            {
                "badge_id": "b1",
                "badge_title": badge_titles.get("b1", "First Steps"),
                "count": len(users_with_progress),
            },
            {
                "badge_id": "b2",
                "badge_title": badge_titles.get("b2", "DevSecOps Guru"),
                "count": len(devsecops_completions),
            },
            {
                "badge_id": "b3",
                "badge_title": badge_titles.get("b3", "Cloud Security Developer"),
                "count": len(cloud_security_completions),
            },
            {
                "badge_id": "b8",
                "badge_title": badge_titles.get("b8", "Perfect Score"),
                "count": perfect_scores,
            },
            {
                "badge_id": "b9",
                "badge_title": badge_titles.get("b9", "Capstone Champion"),
                "count": len(capstone_submissions),
            },
        ]

        # Sort by count descending
        badge_distribution.sort(key=lambda x: x["count"], reverse=True)

        # Calculate totals
        total_badges_earned = sum(b["count"] for b in badge_distribution)
        unique_users_with_badges = len(users_with_progress)

        return {
            "total_badges_earned": total_badges_earned,
            "unique_users_with_badges": unique_users_with_badges,
            "badge_distribution": badge_distribution,
        }

    except ClientError as e:
        raise Exception(
            f"Failed to get badge stats from DynamoDB: {e.response['Error']['Code']}"
        )


def get_all_quiz_stats() -> dict:
    """
    Get quiz statistics across all users.

    Returns:
        dict: {
            "total_quiz_attempts": int,
            "average_score": float,
            "perfect_scores": int,
            "quiz_performance": [
                {"module_id": str, "avg_score": float, "attempts": int},
                ...
            ]
        }

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    try:
        quiz_scores = []
        perfect_scores = 0
        module_scores = {}
        last_evaluated_key = None

        # Scan table for all MODULE records (quiz completions)
        while True:
            scan_params = {
                "TableName": table_name,
                "FilterExpression": "begins_with(SK, :sk_prefix)",
                "ExpressionAttributeValues": {":sk_prefix": {"S": "MODULE#"}},
            }

            if last_evaluated_key:
                scan_params["ExclusiveStartKey"] = last_evaluated_key

            response = dynamodb.scan(**scan_params)

            for item in response.get("Items", []):
                score = int(item.get("score", {}).get("N", "0"))
                module_id = item.get("SK", {}).get("S", "").replace("MODULE#", "")

                quiz_scores.append(score)

                if score >= 100:
                    perfect_scores += 1

                # Track scores by module
                if module_id:
                    if module_id not in module_scores:
                        module_scores[module_id] = []
                    module_scores[module_id].append(score)

            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break

        # Calculate statistics
        total_attempts = len(quiz_scores)
        avg_score = (
            round(sum(quiz_scores) / total_attempts, 1) if total_attempts > 0 else 0
        )

        # Calculate per-module performance (top 5 most challenging)
        quiz_performance = []
        for module_id, scores in module_scores.items():
            avg_module_score = round(sum(scores) / len(scores), 1)
            quiz_performance.append(
                {
                    "module_id": module_id,
                    "avg_score": avg_module_score,
                    "attempts": len(scores),
                }
            )

        # Sort by average score (ascending) to show most challenging first
        quiz_performance.sort(key=lambda x: x["avg_score"])

        return {
            "total_quiz_attempts": total_attempts,
            "average_score": avg_score,
            "perfect_scores": perfect_scores,
            "quiz_performance": quiz_performance[:5],  # Top 5 most challenging
        }

    except ClientError as e:
        raise Exception(
            f"Failed to get quiz stats from DynamoDB: {e.response['Error']['Code']}"
        )


def get_perfect_quiz_count() -> int:
    """
    Get count of perfect quiz scores (100%) across all users.

    Returns:
        int: Number of perfect quiz scores

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    try:
        count = 0
        last_evaluated_key = None

        while True:
            scan_params = {
                "TableName": table_name,
                "FilterExpression": "begins_with(SK, :sk_prefix) AND score >= :perfect_score",
                "ExpressionAttributeValues": {
                    ":sk_prefix": {"S": "MODULE#"},
                    ":perfect_score": {"N": "100"},
                },
                "Select": "COUNT",
            }

            if last_evaluated_key:
                scan_params["ExclusiveStartKey"] = last_evaluated_key

            response = dynamodb.scan(**scan_params)
            count += response.get("Count", 0)

            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break

        return count

    except ClientError as e:
        raise Exception(
            f"Failed to count perfect quiz scores from DynamoDB: {e.response['Error']['Code']}"
        )


def get_all_walkthrough_progress() -> list:
    """
    Scan DynamoDB for all walkthrough progress records.

    Returns all items where SK starts with "WALKTHROUGH#".
    Handles pagination with LastEvaluatedKey for large datasets.

    Returns:
        list: [
            {
                "user_id": str,
                "walkthrough_id": str,
                "status": str,  # "in_progress" | "completed"
                "started_at": str,
                "completed_at": str | None
            },
            ...
        ]

    Raises:
        Exception: If DynamoDB operation fails or table name is missing
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    try:
        items = []
        last_evaluated_key = None

        # Scan table for all WALKTHROUGH records
        while True:
            scan_params = {
                "TableName": table_name,
                "FilterExpression": "begins_with(SK, :sk_prefix)",
                "ExpressionAttributeValues": {":sk_prefix": {"S": "WALKTHROUGH#"}},
            }

            if last_evaluated_key:
                scan_params["ExclusiveStartKey"] = last_evaluated_key

            response = dynamodb.scan(**scan_params)

            # Parse items
            for item in response.get("Items", []):
                pk = item.get("PK", {}).get("S", "")
                sk = item.get("SK", {}).get("S", "")

                # Extract user_id from PK (format: USER#<user_id>)
                if pk.startswith("USER#"):
                    user_id = pk.replace("USER#", "")

                    # Extract walkthrough_id from SK (format: WALKTHROUGH#<walkthrough_id>)
                    if sk.startswith("WALKTHROUGH#"):
                        walkthrough_id = sk.replace("WALKTHROUGH#", "")

                        items.append(
                            {
                                "user_id": user_id,
                                "walkthrough_id": walkthrough_id,
                                "status": item.get("status", {}).get("S", ""),
                                "started_at": item.get("started_at", {}).get("S", ""),
                                "completed_at": item.get("completed_at", {}).get("S"),
                            }
                        )

            # Check if there are more items
            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break

        return items

    except ClientError as e:
        raise Exception(
            f"Failed to scan walkthrough progress from DynamoDB: {e.response['Error']['Code']}"
        )
