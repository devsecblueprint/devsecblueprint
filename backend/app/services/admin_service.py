"""Admin service — DynamoDB queries for admin analytics, submissions, etc.

Self-contained replacement for legacy handlers/admin_submissions.py,
services/dynamo.py admin queries, and services/progress_service.py admin calls.
"""

import logging
import math
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings

logger = logging.getLogger(__name__)


class AdminService:
    """Admin-level DynamoDB operations for analytics, submissions, user search."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = boto3.client("dynamodb")

    @property
    def _progress_table(self) -> str:
        return self._settings.progress_table

    # ------------------------------------------------------------------
    # Registered users
    # ------------------------------------------------------------------

    def get_all_registered_users(self) -> list[dict[str, Any]]:
        """Scan all PROFILE records from the progress table."""
        users: list[dict[str, Any]] = []
        last_key = None

        while True:
            params: dict[str, Any] = {
                "TableName": self._progress_table,
                "FilterExpression": "SK = :sk",
                "ExpressionAttributeValues": {":sk": {"S": "PROFILE"}},
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key

            response = self._client.scan(**params)
            for item in response.get("Items", []):
                pk = item.get("PK", {}).get("S", "")
                if pk.startswith("USER#"):
                    user_id = pk[5:]
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
                            "bitbucket_username": item.get(
                                "bitbucket_username", {}
                            ).get("S", ""),
                            "provider": item.get("provider", {}).get("S", "github"),
                            "avatar_url": item.get("avatar_url", {}).get("S", ""),
                            "registered_at": item.get("registered_at", {}).get("S", ""),
                            "last_login": item.get("last_login", {}).get("S", ""),
                            "email": item.get("email", {}).get("S", ""),
                        }
                    )

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

        return users

    # ------------------------------------------------------------------
    # All progress
    # ------------------------------------------------------------------

    def get_all_users_progress(self) -> list[dict[str, Any]]:
        """Scan all CONTENT# records from the progress table."""
        items: list[dict[str, Any]] = []
        last_key = None

        while True:
            params: dict[str, Any] = {"TableName": self._progress_table}
            if last_key:
                params["ExclusiveStartKey"] = last_key

            response = self._client.scan(**params)
            for item in response.get("Items", []):
                pk = item.get("PK", {}).get("S", "")
                sk = item.get("SK", {}).get("S", "")
                if pk.startswith("USER#") and sk.startswith("CONTENT#"):
                    items.append(
                        {
                            "user_id": pk[5:],
                            "content_id": sk[8:],
                            "status": item.get("status", {}).get("S", ""),
                            "completed_at": item.get("completed_at", {}).get("S", ""),
                        }
                    )

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

        return items

    # ------------------------------------------------------------------
    # Capstone submissions count
    # ------------------------------------------------------------------

    def get_total_capstone_submissions_count(self) -> int:
        """Count all CAPSTONE_SUBMISSION# records."""
        count = 0
        last_key = None

        while True:
            params: dict[str, Any] = {
                "TableName": self._progress_table,
                "FilterExpression": "begins_with(SK, :prefix)",
                "ExpressionAttributeValues": {":prefix": {"S": "CAPSTONE_SUBMISSION#"}},
                "Select": "COUNT",
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key

            response = self._client.scan(**params)
            count += response.get("Count", 0)

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

        return count

    # ------------------------------------------------------------------
    # Badge stats
    # ------------------------------------------------------------------

    def get_all_badge_stats(self) -> dict[str, int]:
        """Placeholder for badge stats — computed client-side in analytics."""
        return {}

    # ------------------------------------------------------------------
    # Quiz stats
    # ------------------------------------------------------------------

    def get_all_quiz_stats(self) -> dict[str, Any]:
        """Count MODULE# records and compute aggregate quiz metrics."""
        total_quizzes = 0
        perfect_scores = 0
        last_key = None

        while True:
            params: dict[str, Any] = {
                "TableName": self._progress_table,
                "FilterExpression": "begins_with(SK, :prefix)",
                "ExpressionAttributeValues": {":prefix": {"S": "MODULE#"}},
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key

            response = self._client.scan(**params)
            for item in response.get("Items", []):
                total_quizzes += 1
                score = int(item.get("score", {}).get("N", "0"))
                if score >= 100:
                    perfect_scores += 1

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

        return {
            "total_quizzes_completed": total_quizzes,
            "perfect_scores": perfect_scores,
        }

    # ------------------------------------------------------------------
    # Capstone submissions (paginated)
    # ------------------------------------------------------------------

    def get_capstone_submissions(
        self, page: int = 1, page_size: int = 50
    ) -> tuple[list[dict[str, Any]], int]:
        """Get all capstone submissions with pagination.

        Returns:
            Tuple of (submissions_page, total_count).
        """
        all_submissions: list[dict[str, Any]] = []
        last_key = None

        while True:
            params: dict[str, Any] = {
                "TableName": self._progress_table,
                "FilterExpression": "begins_with(SK, :prefix)",
                "ExpressionAttributeValues": {":prefix": {"S": "CAPSTONE_SUBMISSION#"}},
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key

            response = self._client.scan(**params)
            for item in response.get("Items", []):
                pk = item.get("PK", {}).get("S", "")
                sk = item.get("SK", {}).get("S", "")
                all_submissions.append(
                    {
                        "user_id": pk[5:] if pk.startswith("USER#") else pk,
                        "content_id": sk.replace("CAPSTONE_SUBMISSION#", ""),
                        "repo_url": item.get("repo_url", {}).get("S", ""),
                        "github_username": item.get("github_username", {}).get("S", ""),
                        "repo_name": item.get("repo_name", {}).get("S", ""),
                        "provider": item.get("provider", {}).get("S", "github"),
                        "status": item.get("status", {}).get("S", ""),
                        "submitted_at": item.get("submitted_at", {}).get("S", ""),
                        "updated_at": item.get("updated_at", {}).get("S", ""),
                    }
                )

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

        # Sort by submitted_at descending
        all_submissions.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)

        total_count = len(all_submissions)
        start = (page - 1) * page_size
        end = start + page_size

        return all_submissions[start:end], total_count

    # ------------------------------------------------------------------
    # User stats (for admin user search / profile)
    # ------------------------------------------------------------------

    def get_user_stats(self, user_id: str) -> dict[str, Any]:
        """Get aggregated stats for a single user."""
        # Count CONTENT# records
        try:
            response = self._client.query(
                TableName=self._progress_table,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk": {"S": "CONTENT#"},
                },
                Select="COUNT",
            )
            completed_count = response.get("Count", 0)
        except ClientError:
            completed_count = 0

        total_pages = self._settings.total_module_pages or 96
        overall_completion = (
            min(100, int((completed_count / total_pages) * 100))
            if total_pages > 0
            else 0
        )

        # Count MODULE# (quizzes)
        quizzes_passed = 0
        perfect_quiz = False
        try:
            response = self._client.query(
                TableName=self._progress_table,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk": {"S": "MODULE#"},
                },
            )
            for item in response.get("Items", []):
                quizzes_passed += 1
                score = int(item.get("score", {}).get("N", "0"))
                if score >= 100:
                    perfect_quiz = True
        except ClientError:
            pass

        # Count walkthroughs completed
        walkthroughs_completed = 0
        try:
            response = self._client.query(
                TableName=self._progress_table,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk": {"S": "WALKTHROUGH#"},
                },
            )
            for item in response.get("Items", []):
                if item.get("status", {}).get("S") == "completed":
                    walkthroughs_completed += 1
        except ClientError:
            pass

        # Count capstone submissions
        capstone_submissions = 0
        try:
            response = self._client.query(
                TableName=self._progress_table,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk": {"S": "CAPSTONE_SUBMISSION#"},
                },
                Select="COUNT",
            )
            capstone_submissions = response.get("Count", 0)
        except ClientError:
            pass

        return {
            "completed_count": completed_count,
            "overall_completion": overall_completion,
            "quizzes_passed": quizzes_passed,
            "walkthroughs_completed": walkthroughs_completed,
            "capstone_submissions": capstone_submissions,
            "perfect_quiz_achieved": perfect_quiz,
        }

    def get_user_progress(self, user_id: str) -> list[dict[str, Any]]:
        """Get all CONTENT# items for a user (for badge calculation)."""
        items: list[dict[str, Any]] = []
        try:
            response = self._client.query(
                TableName=self._progress_table,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk": {"S": "CONTENT#"},
                },
            )
            for item in response.get("Items", []):
                items.append(
                    {
                        "content_id": item["SK"]["S"].replace("CONTENT#", ""),
                        "status": item.get("status", {}).get("S", "complete"),
                        "completed_at": item.get("completed_at", {}).get("S", ""),
                    }
                )
        except ClientError:
            pass
        return items

    # ------------------------------------------------------------------
    # User profile (admin view)
    # ------------------------------------------------------------------

    def get_user_profile(self, user_id: str) -> dict[str, Any] | None:
        """Get a user's PROFILE record."""
        try:
            response = self._client.get_item(
                TableName=self._progress_table,
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
                "gitlab_username": item.get("gitlab_username", {}).get("S", ""),
                "bitbucket_username": item.get("bitbucket_username", {}).get("S", ""),
                "provider": item.get("provider", {}).get("S", "github"),
                "email": item.get("email", {}).get("S", ""),
            }
        except ClientError:
            return None

    # ------------------------------------------------------------------
    # Walkthrough progress (for admin user profile view)
    # ------------------------------------------------------------------

    def get_user_walkthrough_progress(self, user_id: str) -> list[dict[str, Any]]:
        """Get all WALKTHROUGH# records for a user."""
        items: list[dict[str, Any]] = []
        try:
            response = self._client.query(
                TableName=self._progress_table,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk": {"S": "WALKTHROUGH#"},
                },
            )
            for item in response.get("Items", []):
                sk = item.get("SK", {}).get("S", "")
                items.append(
                    {
                        "walkthrough_id": sk.replace("WALKTHROUGH#", ""),
                        "status": item.get("status", {}).get("S", ""),
                        "started_at": item.get("started_at", {}).get("S", ""),
                        "completed_at": item.get("completed_at", {}).get("S"),
                    }
                )
        except ClientError:
            pass
        return items

    # ------------------------------------------------------------------
    # Walkthrough statistics (aggregate)
    # ------------------------------------------------------------------

    def get_walkthrough_statistics(self) -> dict[str, Any]:
        """Get aggregate walkthrough statistics across all users."""
        completed_count = 0
        in_progress_count = 0
        popularity: dict[str, int] = {}
        last_key = None

        while True:
            params: dict[str, Any] = {
                "TableName": self._progress_table,
                "FilterExpression": "begins_with(SK, :prefix)",
                "ExpressionAttributeValues": {":prefix": {"S": "WALKTHROUGH#"}},
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key

            response = self._client.scan(**params)
            for item in response.get("Items", []):
                status = item.get("status", {}).get("S", "")
                sk = item.get("SK", {}).get("S", "")
                wt_id = sk.replace("WALKTHROUGH#", "")

                if status == "completed":
                    completed_count += 1
                elif status == "in_progress":
                    in_progress_count += 1

                if wt_id:
                    popularity[wt_id] = popularity.get(wt_id, 0) + 1

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

        most_popular = None
        if popularity:
            max_count = max(popularity.values())
            top = [k for k, v in popularity.items() if v == max_count]
            most_popular = min(top)

        return {
            "completed_count": completed_count,
            "in_progress_count": in_progress_count,
            "most_popular_walkthrough": most_popular,
        }

    # ------------------------------------------------------------------
    # Capstone reviews (for admin router)
    # ------------------------------------------------------------------

    def get_capstone_submission(
        self, user_id: str, content_id: str
    ) -> dict[str, Any] | None:
        """Get a single capstone submission."""
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
        except ClientError:
            return None

    def save_capstone_review(
        self, user_id: str, content_id: str, feedback: str, reviewed_by: str
    ) -> None:
        """Create a capstone review record."""
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "PK": {"S": f"USER#{user_id}"},
            "SK": {"S": f"CAPSTONE_REVIEW#{content_id}"},
            "feedback": {"S": feedback},
            "reviewed_by": {"S": reviewed_by},
            "reviewed_at": {"S": now},
            "updated_at": {"S": now},
        }
        try:
            self._client.put_item(TableName=self._progress_table, Item=item)
        except ClientError as e:
            raise Exception(f"Failed to save review: {e.response['Error']['Code']}")

    def update_capstone_submission_status(
        self, user_id: str, content_id: str, status: str
    ) -> None:
        """Update the status of a capstone submission."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            self._client.update_item(
                TableName=self._progress_table,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": f"CAPSTONE_SUBMISSION#{content_id}"},
                },
                UpdateExpression="SET #s = :status, updated_at = :ts",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":status": {"S": status},
                    ":ts": {"S": now},
                },
            )
        except ClientError as e:
            raise Exception(
                f"Failed to update submission status: {e.response['Error']['Code']}"
            )

    def get_capstone_review(
        self, user_id: str, content_id: str
    ) -> dict[str, Any] | None:
        """Get a capstone review record."""
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
        except ClientError:
            return None
