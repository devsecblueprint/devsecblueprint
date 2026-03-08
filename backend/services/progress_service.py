"""
Progress service for retrieving and calculating user progress data.

This module provides functions to query DynamoDB for user progress,
calculate statistics like streaks and completion percentages, and
format data for API responses.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import boto3
from botocore.exceptions import ClientError
from services import dynamo
from services.content_registry import get_registry_service

logger = logging.getLogger()


def get_user_progress(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all completed content for a user.

    Args:
        user_id: GitHub user ID

    Returns:
        List of progress items with content_id, status, and completed_at.
        Returns empty list for new users with no progress data.

    Raises:
        Exception: If DynamoDB operation fails
    """
    table_name = os.environ.get("PROGRESS_TABLE")
    if not table_name:
        raise Exception("PROGRESS_TABLE environment variable not set")

    dynamodb = boto3.client("dynamodb")

    try:
        response = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"USER#{user_id}"},
                ":sk_prefix": {"S": "CONTENT#"},
            },
        )

        # Handle new users with no data - return empty list
        items = []
        for item in response.get("Items", []):
            items.append(
                {
                    "content_id": item["SK"]["S"].replace("CONTENT#", ""),
                    "status": item.get("status", {}).get("S", "complete"),
                    "completed_at": item.get("completed_at", {}).get("S", ""),
                }
            )

        return items

    except ClientError as e:
        # If the error is ResourceNotFoundException, return empty list (table doesn't exist yet)
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return []
        raise Exception(
            f"Failed to query progress from DynamoDB: {e.response['Error']['Code']}"
        )


def calculate_streaks(progress_items: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate current and longest streaks from progress data.

    A streak is consecutive days with at least one completed item.
    For new users with no data, returns zeros.

    Args:
        progress_items: List of progress items with completed_at timestamps

    Returns:
        Dict with current_streak and longest_streak (in days).
        Returns {current_streak: 0, longest_streak: 0} for new users.
    """
    # Handle new users with no progress
    if not progress_items:
        return {"current_streak": 0, "longest_streak": 0}

    # Parse and sort dates
    dates = []
    for item in progress_items:
        try:
            completed_at = datetime.fromisoformat(
                item["completed_at"].replace("Z", "+00:00")
            )
            dates.append(completed_at.date())
        except (ValueError, KeyError):
            continue

    if not dates:
        return {"current_streak": 0, "longest_streak": 0}

    # Remove duplicates and sort
    unique_dates = sorted(set(dates), reverse=True)

    # Calculate current streak
    current_streak = 0
    today = datetime.now(timezone.utc).date()
    expected_date = today

    for date in unique_dates:
        if date == expected_date or date == expected_date - timedelta(days=1):
            current_streak += 1
            expected_date = date - timedelta(days=1)
        else:
            break

    # Calculate longest streak
    longest_streak = 1
    current_run = 1

    for i in range(1, len(unique_dates)):
        if unique_dates[i - 1] - unique_dates[i] == timedelta(days=1):
            current_run += 1
            longest_streak = max(longest_streak, current_run)
        else:
            current_run = 1

    return {"current_streak": current_streak, "longest_streak": longest_streak}


def calculate_completion_percentage(completed_count: int) -> int:
    """
    Calculate overall completion percentage.

    Args:
        completed_count: Number of completed items

    Returns:
        Completion percentage (0-100)

    Note: Total count is read from TOTAL_MODULE_PAGES environment variable,
    which is set by Terraform during deployment based on the content registry.
    """
    total_count = int(os.environ.get("TOTAL_MODULE_PAGES", "96"))

    if total_count == 0:
        return 0
    return min(100, int((completed_count / total_count) * 100))


def get_recent_activities(
    progress_items: List[Dict[str, Any]], limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get most recently completed activities.

    Args:
        progress_items: List of progress items
        limit: Maximum number of activities to return

    Returns:
        List of recent activities sorted by completed_at (newest first).
        Returns empty list for new users with no progress.
    """
    # Handle new users with no progress
    if not progress_items:
        return []

    # Sort by completed_at descending
    sorted_items = sorted(
        progress_items,
        key=lambda x: x.get("completed_at", ""),
        reverse=True,
    )

    return sorted_items[:limit]


def get_user_stats(user_id: str) -> Dict[str, Any]:
    """
    Get aggregated statistics for a user.

    Args:
        user_id: GitHub user ID

    Returns:
        Dict with current_streak, longest_streak, overall_completion, completed_count,
        quizzes_passed, walkthroughs_completed, and perfect_quiz_achieved.
        For new users with no data, returns all zeros.

    Raises:
        Exception: If DynamoDB operation fails
    """
    progress_items = get_user_progress(user_id)

    # Get table name for additional queries
    table_name = os.environ.get("PROGRESS_TABLE")

    # Handle new users gracefully - all stats will be 0
    streaks = calculate_streaks(progress_items)
    completed_count = len(progress_items)
    completion_percentage = calculate_completion_percentage(completed_count)

    # Count quizzes passed (from CONTENT# items)
    quizzes_passed = sum(
        1 for item in progress_items if item.get("content_type") == "quiz"
    )

    # Count walkthroughs completed by querying for WALKTHROUGH# items with status="completed"
    walkthroughs_completed = 0
    if table_name:
        try:
            dynamodb = boto3.client("dynamodb")
            response = dynamodb.query(
                TableName=table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk_prefix": {"S": "WALKTHROUGH#"},
                },
            )
            # Count walkthroughs with status="completed"
            for item in response.get("Items", []):
                status = item.get("status", {}).get("S", "")
                if status == "completed":
                    walkthroughs_completed += 1
        except ClientError:
            # If query fails, default to 0
            walkthroughs_completed = 0

    # Check if user has achieved a perfect score (100) on any quiz
    # Quiz scores are stored in MODULE# records, not CONTENT# records
    perfect_quiz_achieved = False
    table_name = os.environ.get("PROGRESS_TABLE")
    if table_name:
        try:
            dynamodb = boto3.client("dynamodb")
            response = dynamodb.query(
                TableName=table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk_prefix": {"S": "MODULE#"},
                },
            )
            # Check if any module has a score of 100
            for item in response.get("Items", []):
                score = int(item.get("score", {}).get("N", "0"))
                if score >= 100:
                    perfect_quiz_achieved = True
                    break
        except ClientError:
            # If query fails, default to False
            perfect_quiz_achieved = False

    # Count capstone submissions by querying for CAPSTONE_SUBMISSION# items
    capstone_submissions = 0
    if table_name:
        try:
            dynamodb = boto3.client("dynamodb")
            response = dynamodb.query(
                TableName=table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk_prefix": {"S": "CAPSTONE_SUBMISSION#"},
                },
            )
            capstone_submissions = len(response.get("Items", []))
        except ClientError:
            # If query fails, default to 0
            capstone_submissions = 0

    return {
        "user_id": user_id,
        "current_streak": streaks["current_streak"],
        "longest_streak": streaks["longest_streak"],
        "overall_completion": completion_percentage,
        "completed_count": completed_count,
        "quizzes_passed": quizzes_passed,
        "walkthroughs_completed": walkthroughs_completed,
        "perfect_quiz_achieved": perfect_quiz_achieved,
        "capstone_submissions": capstone_submissions,
    }


def get_walkthrough_statistics() -> Dict[str, Any]:
    """
    Calculate aggregate walkthrough statistics across all users.

    Retrieves all walkthrough progress records from DynamoDB and aggregates:
    - Total completed walkthroughs (status="completed")
    - Total in-progress walkthroughs (status="in_progress")
    - Most popular walkthrough (highest combined count)

    Returns:
        dict: {
            "completed_count": int,
            "in_progress_count": int,
            "most_popular_walkthrough": str | None,
            "most_popular_walkthrough_title": str | None
        }

    Raises:
        Exception: If DynamoDB operation fails
    """
    # Retrieve all walkthrough progress records
    all_records = dynamo.get_all_walkthrough_progress()

    # Initialize counters
    completed_count = 0
    in_progress_count = 0
    walkthrough_popularity = {}  # {walkthrough_id: count}

    # Process each record
    for record in all_records:
        status = record.get("status", "")
        walkthrough_id = record.get("walkthrough_id", "")

        # Count by status
        if status == "completed":
            completed_count += 1
        elif status == "in_progress":
            in_progress_count += 1

        # Track popularity (all statuses count)
        if walkthrough_id:
            walkthrough_popularity[walkthrough_id] = (
                walkthrough_popularity.get(walkthrough_id, 0) + 1
            )

    # Find most popular walkthrough
    most_popular_walkthrough = None
    most_popular_walkthrough_title = None

    if walkthrough_popularity:
        # Get the maximum count
        max_count = max(walkthrough_popularity.values())
        # Get all walkthroughs with the maximum count
        top_walkthroughs = [
            wt_id
            for wt_id, count in walkthrough_popularity.items()
            if count == max_count
        ]
        # Apply alphabetical tie-breaking
        most_popular_walkthrough = min(top_walkthroughs)

        # Try to get the title from the content registry
        try:
            s3_bucket = os.environ.get("CONTENT_BUCKET")
            if s3_bucket:
                registry = get_registry_service(s3_bucket)
                walkthrough_data = registry.get_walkthrough(most_popular_walkthrough)
                if walkthrough_data:
                    most_popular_walkthrough_title = walkthrough_data.get(
                        "title", most_popular_walkthrough
                    )
                else:
                    # Fallback to ID if not found in registry
                    most_popular_walkthrough_title = most_popular_walkthrough
            else:
                # Fallback to ID if no bucket configured
                most_popular_walkthrough_title = most_popular_walkthrough
        except Exception as e:
            # If registry lookup fails, fallback to ID
            logger.warning(f"Failed to get walkthrough title: {str(e)}")
            most_popular_walkthrough_title = most_popular_walkthrough

    return {
        "completed_count": completed_count,
        "in_progress_count": in_progress_count,
        "most_popular_walkthrough": most_popular_walkthrough,
        "most_popular_walkthrough_title": most_popular_walkthrough_title,
    }
