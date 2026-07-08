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

    def get_all_badge_stats(self) -> dict[str, Any]:
        """Compute approximate badge statistics using aggregate DynamoDB scans.

        Uses fast aggregate queries instead of per-user badge computation
        to avoid timeouts with large user counts.
        """
        from app.services.badge_service import BADGE_DEFINITIONS, PATH_PAGE_IDS

        # Fast approach: count users who meet simple badge criteria using scans
        # we already have from get_all_users_progress

        # Count users with at least 1 completion (b1: First Steps)
        users_with_any_progress = set()
        # Count users who completed each path
        path_completions: dict[str, set[str]] = {path: set() for path in PATH_PAGE_IDS}

        # Single scan of all CONTENT# records (we already do this for analytics)
        last_key = None
        while True:
            params: dict[str, Any] = {
                "TableName": self._progress_table,
                "FilterExpression": "begins_with(SK, :prefix)",
                "ExpressionAttributeValues": {":prefix": {"S": "CONTENT#"}},
                "ProjectionExpression": "PK, SK",
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key

            response = self._client.scan(**params)
            for item in response.get("Items", []):
                pk = item.get("PK", {}).get("S", "")
                sk = item.get("SK", {}).get("S", "")
                if not pk.startswith("USER#"):
                    continue
                user_id = pk[5:]
                content_id = sk.replace("CONTENT#", "")

                users_with_any_progress.add(user_id)

                # Check path completions
                for path_name, page_ids in PATH_PAGE_IDS.items():
                    if content_id in page_ids:
                        path_completions[path_name].add(f"{user_id}:{content_id}")

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

        # Count MODULE# records for quiz badges
        users_with_perfect_quiz: set[str] = set()
        last_key = None
        while True:
            params = {
                "TableName": self._progress_table,
                "FilterExpression": "begins_with(SK, :prefix)",
                "ExpressionAttributeValues": {":prefix": {"S": "MODULE#"}},
                "ProjectionExpression": "PK, score",
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key

            response = self._client.scan(**params)
            for item in response.get("Items", []):
                pk = item.get("PK", {}).get("S", "")
                score = int(item.get("score", {}).get("N", "0"))
                if pk.startswith("USER#") and score >= 100:
                    users_with_perfect_quiz.add(pk[5:])

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

        # Count capstone submissions
        users_with_capstone: set[str] = set()
        last_key = None
        while True:
            params = {
                "TableName": self._progress_table,
                "FilterExpression": "begins_with(SK, :prefix)",
                "ExpressionAttributeValues": {":prefix": {"S": "CAPSTONE_SUBMISSION#"}},
                "ProjectionExpression": "PK",
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key

            response = self._client.scan(**params)
            for item in response.get("Items", []):
                pk = item.get("PK", {}).get("S", "")
                if pk.startswith("USER#"):
                    users_with_capstone.add(pk[5:])

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

        # Calculate path completion counts (users who completed ALL pages in a path)
        path_completion_users: dict[str, int] = {}
        for path_name, page_ids in PATH_PAGE_IDS.items():
            required = len(page_ids)
            # Count completions per user for this path
            user_path_counts: dict[str, int] = {}
            for entry in path_completions[path_name]:
                uid = entry.split(":")[0]
                user_path_counts[uid] = user_path_counts.get(uid, 0) + 1
            path_completion_users[path_name] = sum(
                1 for count in user_path_counts.values() if count >= required
            )

        # Build badge distribution
        badge_distribution = []
        badge_counts: dict[str, int] = {}

        # b1: First Steps (at least 1 completion)
        badge_counts["b1"] = len(users_with_any_progress)
        # b2: DevSecOps Guru (completed devsecops path)
        badge_counts["b2"] = path_completion_users.get("devsecops", 0)
        # b3: Cloud Security Developer
        badge_counts["b3"] = path_completion_users.get("cloud_security_development", 0)
        # b7: Foundation Builder (know_before_you_go)
        badge_counts["b7"] = path_completion_users.get("know_before_you_go", 0)
        # b8: Perfect Score
        badge_counts["b8"] = len(users_with_perfect_quiz)
        # b9: Capstone Champion
        badge_counts["b9"] = len(users_with_capstone)
        # b4, b5, b6: Walkthrough difficulty badges (skip for now — requires S3 registry)
        badge_counts["b4"] = 0
        badge_counts["b5"] = 0
        badge_counts["b6"] = 0

        total_badges_earned = sum(badge_counts.values())
        all_badge_users = (
            users_with_any_progress  # At minimum, anyone with progress has b1
        )

        badge_title_map = {b["id"]: b["title"] for b in BADGE_DEFINITIONS}
        for badge_id, count in sorted(
            badge_counts.items(), key=lambda x: x[1], reverse=True
        ):
            if count > 0:
                badge_distribution.append(
                    {
                        "badge_id": badge_id,
                        "badge_title": badge_title_map.get(badge_id, badge_id),
                        "count": count,
                    }
                )

        return {
            "total_badges_earned": total_badges_earned,
            "unique_users_with_badges": len(all_badge_users),
            "badge_distribution": badge_distribution,
        }

    # ------------------------------------------------------------------
    # Quiz stats
    # ------------------------------------------------------------------

    def get_all_quiz_stats(self) -> dict[str, Any]:
        """Count MODULE# records and compute aggregate quiz metrics."""
        total_attempts = 0
        perfect_scores = 0
        total_score_sum = 0
        module_stats: dict[str, dict] = {}  # module_id -> {attempts, total_score}
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
                total_attempts += 1
                score = int(item.get("score", {}).get("N", "0"))
                total_score_sum += score
                if score >= 100:
                    perfect_scores += 1

                # Track per-module stats
                sk = item.get("SK", {}).get("S", "")
                module_id = (
                    sk.replace("MODULE#", "") if sk.startswith("MODULE#") else ""
                )
                if module_id:
                    if module_id not in module_stats:
                        module_stats[module_id] = {"attempts": 0, "total_score": 0}
                    module_stats[module_id]["attempts"] += 1
                    module_stats[module_id]["total_score"] += score

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

        average_score = (
            round(total_score_sum / total_attempts) if total_attempts > 0 else 0
        )

        # Build quiz_performance list sorted by lowest avg score (most challenging)
        quiz_performance = []
        for module_id, stats in module_stats.items():
            avg = (
                round(stats["total_score"] / stats["attempts"])
                if stats["attempts"] > 0
                else 0
            )
            quiz_performance.append(
                {
                    "module_id": module_id,
                    "attempts": stats["attempts"],
                    "avg_score": avg,
                }
            )
        quiz_performance.sort(key=lambda x: x["avg_score"])

        return {
            "total_quiz_attempts": total_attempts,
            "average_score": average_score,
            "perfect_scores": perfect_scores,
            "quiz_performance": quiz_performance[:10],  # Top 10 most challenging
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

    # ------------------------------------------------------------------
    # Contributor role mapping
    # ------------------------------------------------------------------

    # Valid contributor roles
    VALID_ROLES = {"contributor"}

    def get_contributor_role(self, user_id: str) -> dict[str, Any] | None:
        """Get a user's contributor role record.

        Returns:
            Dict with role, assigned_by, assigned_at, note or None if not set.
        """
        try:
            response = self._client.get_item(
                TableName=self._progress_table,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": "CONTRIBUTOR_ROLE"},
                },
            )
            item = response.get("Item")
            if not item:
                return None
            return {
                "role": item.get("role", {}).get("S", ""),
                "assigned_by": item.get("assigned_by", {}).get("S", ""),
                "assigned_at": item.get("assigned_at", {}).get("S", ""),
                "note": item.get("note", {}).get("S", ""),
            }
        except ClientError as e:
            logger.error("Failed to get contributor role for %s: %s", user_id, e)
            return None

    def set_contributor_role(
        self,
        user_id: str,
        role: str,
        assigned_by: str,
        note: str = "",
    ) -> dict[str, Any]:
        """Assign or update a contributor role for a user.

        Args:
            user_id: Target user ID.
            role: One of VALID_ROLES.
            assigned_by: Admin user ID performing the assignment.
            note: Optional note about the assignment.

        Returns:
            The saved role record.

        Raises:
            ValueError: If role is not in VALID_ROLES.
        """
        if role not in self.VALID_ROLES:
            raise ValueError(
                f"Invalid role '{role}'. Must be one of: {', '.join(sorted(self.VALID_ROLES))}"
            )

        now = datetime.now(timezone.utc).isoformat()

        item: dict[str, Any] = {
            "PK": {"S": f"USER#{user_id}"},
            "SK": {"S": "CONTRIBUTOR_ROLE"},
            "role": {"S": role},
            "assigned_by": {"S": assigned_by},
            "assigned_at": {"S": now},
        }
        if note:
            item["note"] = {"S": note}

        self._client.put_item(TableName=self._progress_table, Item=item)

        return {
            "role": role,
            "assigned_by": assigned_by,
            "assigned_at": now,
            "note": note,
        }

    def delete_contributor_role(self, user_id: str) -> bool:
        """Remove a user's contributor role.

        Returns:
            True if deleted successfully, False on error.
        """
        try:
            self._client.delete_item(
                TableName=self._progress_table,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": "CONTRIBUTOR_ROLE"},
                },
            )
            return True
        except ClientError as e:
            logger.error("Failed to delete contributor role for %s: %s", user_id, e)
            return False
