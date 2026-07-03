"""DynamoDB operations for progress tracking.

Encapsulates all DynamoDB interactions related to user progress,
capstone submissions, badges, streaks, and last-active state.
Ported from the Lambda-based services (services/dynamo.py, services/progress_service.py,
services/badge_service.py).

Uses the centralized Settings for table names rather than os.environ.
"""

import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings

# Ensure the legacy root is on the path so existing Lambda services can be imported
_legacy_root = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "legacy",
)
if _legacy_root not in sys.path:
    sys.path.insert(0, _legacy_root)

logger = logging.getLogger(__name__)


class ProgressDB:
    """DynamoDB progress operations.

    Accepts a Settings instance to resolve table names and configuration.
    Creates its own boto3 client per instance — for long-lived ECS tasks
    this avoids stale credentials issues since boto3 handles credential
    refresh under the hood.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = boto3.client("dynamodb")

    @property
    def _progress_table(self) -> str:
        return self._settings.progress_table

    @property
    def _user_state_table(self) -> str:
        return self._settings.user_state_table

    # ------------------------------------------------------------------
    # Save progress
    # ------------------------------------------------------------------

    def save_progress(self, user_id: str, content_id: str) -> None:
        """Save user progress (mark content as complete).

        Args:
            user_id: User identifier from JWT sub claim.
            content_id: Content identifier.

        Raises:
            Exception: On DynamoDB failure.
        """
        completed_at = datetime.now(timezone.utc).isoformat()

        item = {
            "PK": {"S": f"USER#{user_id}"},
            "SK": {"S": f"CONTENT#{content_id}"},
            "status": {"S": "complete"},
            "completed_at": {"S": completed_at},
        }

        try:
            self._client.put_item(TableName=self._progress_table, Item=item)
        except ClientError as e:
            raise Exception(f"Failed to save progress: {e.response['Error']['Code']}")

    # ------------------------------------------------------------------
    # Get user progress
    # ------------------------------------------------------------------

    def get_user_progress(self, user_id: str) -> list[dict[str, Any]]:
        """Get all completed content for a user.

        Returns:
            List of dicts with content_id, status, and completed_at.
        """
        try:
            response = self._client.query(
                TableName=self._progress_table,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk_prefix": {"S": "CONTENT#"},
                },
            )

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
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return []
            raise Exception(f"Failed to query progress: {e.response['Error']['Code']}")

    # ------------------------------------------------------------------
    # User stats
    # ------------------------------------------------------------------

    def get_user_stats(self, user_id: str) -> dict[str, Any]:
        """Get aggregated statistics for a user.

        Returns a dict with current_streak, longest_streak, overall_completion,
        completed_count, quizzes_passed, walkthroughs_completed,
        perfect_quiz_achieved, and capstone_submissions.
        """
        progress_items = self.get_user_progress(user_id)

        streaks = self._calculate_streaks(progress_items)
        completed_count = len(progress_items)
        completion_percentage = self._calculate_completion_percentage(completed_count)

        quizzes_passed = self._count_quizzes_passed(user_id)
        walkthroughs_completed = self._count_walkthroughs_completed(user_id)
        perfect_quiz_achieved = self._check_perfect_quiz(user_id)
        capstone_submissions = self._count_capstone_submissions(user_id)

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

    # ------------------------------------------------------------------
    # Recent activities
    # ------------------------------------------------------------------

    def get_recent_activities(
        self, user_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get most recently completed activities sorted by completed_at."""
        progress_items = self.get_user_progress(user_id)
        if not progress_items:
            return []

        sorted_items = sorted(
            progress_items,
            key=lambda x: x.get("completed_at", ""),
            reverse=True,
        )
        return sorted_items[:limit]

    # ------------------------------------------------------------------
    # Capstone submissions
    # ------------------------------------------------------------------

    def save_capstone_submission(
        self,
        user_id: str,
        content_id: str,
        repo_url: str,
        github_username: str,
        repo_name: str,
        provider: str = "github",
        bitbucket_username: str = "",
    ) -> None:
        """Save capstone submission to DynamoDB."""
        timestamp = datetime.now(timezone.utc).isoformat()

        item = {
            "PK": {"S": f"USER#{user_id}"},
            "SK": {"S": f"CAPSTONE_SUBMISSION#{content_id}"},
            "repo_url": {"S": repo_url},
            "github_username": {"S": github_username},
            "repo_name": {"S": repo_name},
            "provider": {"S": provider},
            "status": {"S": "pending_review"},
            "submitted_at": {"S": timestamp},
            "updated_at": {"S": timestamp},
        }

        if bitbucket_username:
            item["bitbucket_username"] = {"S": bitbucket_username}

        try:
            self._client.put_item(TableName=self._progress_table, Item=item)
        except ClientError as e:
            raise Exception(
                f"Failed to save capstone submission: {e.response['Error']['Code']}"
            )

    def get_capstone_submission(
        self, user_id: str, content_id: str
    ) -> dict[str, Any] | None:
        """Retrieve capstone submission for a user/content pair."""
        try:
            response = self._client.get_item(
                TableName=self._progress_table,
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
                "status": item.get("status", {}).get("S", ""),
                "submitted_at": item.get("submitted_at", {}).get("S", ""),
                "updated_at": item.get("updated_at", {}).get("S", ""),
            }

        except ClientError as e:
            raise Exception(
                f"Failed to get capstone submission: {e.response['Error']['Code']}"
            )

    # ------------------------------------------------------------------
    # Capstone reviews
    # ------------------------------------------------------------------

    def get_capstone_review(
        self, user_id: str, content_id: str
    ) -> dict[str, Any] | None:
        """Retrieve a capstone review record."""
        try:
            response = self._client.get_item(
                TableName=self._progress_table,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": f"CAPSTONE_REVIEW#{content_id}"},
                },
            )

            item = response.get("Item")
            if not item:
                return None

            return {
                "feedback": item.get("feedback", {}).get("S", ""),
                "reviewed_by": item.get("reviewed_by", {}).get("S", ""),
                "reviewed_at": item.get("reviewed_at", {}).get("S", ""),
                "updated_at": item.get("updated_at", {}).get("S", ""),
            }

        except ClientError as e:
            raise Exception(
                f"Failed to get capstone review: {e.response['Error']['Code']}"
            )

    # ------------------------------------------------------------------
    # Last active
    # ------------------------------------------------------------------

    def save_last_active(self, user_id: str, page_id: str, page_slug: str) -> None:
        """Save the user's last active lesson."""
        updated_at = datetime.now(timezone.utc).isoformat()

        item = {
            "PK": {"S": f"USER#{user_id}"},
            "SK": {"S": "LAST_ACTIVE"},
            "page_id": {"S": page_id},
            "page_slug": {"S": page_slug},
            "updated_at": {"S": updated_at},
        }

        try:
            self._client.put_item(TableName=self._user_state_table, Item=item)
        except ClientError as e:
            raise Exception(
                f"Failed to save last active: {e.response['Error']['Code']}"
            )

    def get_last_active(self, user_id: str) -> dict[str, Any]:
        """Retrieve the user's last active lesson.

        Returns:
            Dict with page_id and page_slug, or both None if no record.
        """
        try:
            response = self._client.get_item(
                TableName=self._user_state_table,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": "LAST_ACTIVE"},
                },
            )

            item = response.get("Item")
            if not item:
                return {"page_id": None, "page_slug": None}

            return {
                "page_id": item.get("page_id", {}).get("S"),
                "page_slug": item.get("page_slug", {}).get("S"),
            }

        except ClientError as e:
            raise Exception(f"Failed to get last active: {e.response['Error']['Code']}")

    # ------------------------------------------------------------------
    # Delete all progress (admin reset)
    # ------------------------------------------------------------------

    def delete_all_user_progress(self, user_id: str) -> None:
        """Delete all progress data for a user."""
        try:
            response = self._client.query(
                TableName=self._progress_table,
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={":pk": {"S": f"USER#{user_id}"}},
            )

            for item in response.get("Items", []):
                self._client.delete_item(
                    TableName=self._progress_table,
                    Key={"PK": item["PK"], "SK": item["SK"]},
                )

        except ClientError as e:
            raise Exception(f"Failed to delete progress: {e.response['Error']['Code']}")

    # ------------------------------------------------------------------
    # Badges (delegates to badge_service logic)
    # ------------------------------------------------------------------

    def get_user_badges(self, user_id: str) -> list[dict[str, Any]]:
        """Calculate badges for a user.

        Imports and delegates to the existing badge_service module
        which has all the badge logic (including walkthrough difficulty
        checks via S3 content registry).
        """
        # Import here to avoid circular dependency at module level
        from services.badge_service import calculate_user_badges

        progress_items = self.get_user_progress(user_id)
        stats = self.get_user_stats(user_id)
        stats["user_id"] = user_id

        return calculate_user_badges(stats, progress_items)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _calculate_streaks(
        self, progress_items: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Calculate current and longest streaks."""
        if not progress_items:
            return {"current_streak": 0, "longest_streak": 0}

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

        unique_dates = sorted(set(dates), reverse=True)

        # Current streak
        current_streak = 0
        today = datetime.now(timezone.utc).date()
        expected_date = today

        for date in unique_dates:
            if date == expected_date or date == expected_date - timedelta(days=1):
                current_streak += 1
                expected_date = date - timedelta(days=1)
            else:
                break

        # Longest streak
        longest_streak = 1
        current_run = 1

        for i in range(1, len(unique_dates)):
            if unique_dates[i - 1] - unique_dates[i] == timedelta(days=1):
                current_run += 1
                longest_streak = max(longest_streak, current_run)
            else:
                current_run = 1

        return {"current_streak": current_streak, "longest_streak": longest_streak}

    def _calculate_completion_percentage(self, completed_count: int) -> int:
        """Calculate overall completion percentage."""
        total_count = self._settings.total_module_pages
        if total_count == 0:
            return 0
        return min(100, int((completed_count / total_count) * 100))

    def _count_quizzes_passed(self, user_id: str) -> int:
        """Count MODULE# records for a user (quiz completions)."""
        try:
            response = self._client.query(
                TableName=self._progress_table,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk_prefix": {"S": "MODULE#"},
                },
                Select="COUNT",
            )
            return response.get("Count", 0)
        except ClientError:
            return 0

    def _count_walkthroughs_completed(self, user_id: str) -> int:
        """Count completed walkthroughs for a user."""
        try:
            response = self._client.query(
                TableName=self._progress_table,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk_prefix": {"S": "WALKTHROUGH#"},
                },
            )
            count = 0
            for item in response.get("Items", []):
                status = item.get("status", {}).get("S", "")
                if status == "completed":
                    count += 1
            return count
        except ClientError:
            return 0

    def _check_perfect_quiz(self, user_id: str) -> bool:
        """Check if user achieved a perfect score on any quiz."""
        try:
            response = self._client.query(
                TableName=self._progress_table,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk_prefix": {"S": "MODULE#"},
                },
            )
            for item in response.get("Items", []):
                score = int(item.get("score", {}).get("N", "0"))
                if score >= 100:
                    return True
            return False
        except ClientError:
            return False

    def _count_capstone_submissions(self, user_id: str) -> int:
        """Count CAPSTONE_SUBMISSION# records for a user."""
        try:
            response = self._client.query(
                TableName=self._progress_table,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk_prefix": {"S": "CAPSTONE_SUBMISSION#"},
                },
                Select="COUNT",
            )
            return response.get("Count", 0)
        except ClientError:
            return 0
