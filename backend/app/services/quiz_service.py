"""Quiz service — score quizzes and manage completions/streaks.

Ported from backend/services/quiz_service.py. Self-contained.
Uses the content registry for quiz definitions and DynamoDB for persistence.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings
from app.dependencies import get_settings
from app.services.content_registry import (
    ContentRegistryService,
    SchemaVersionError,
    get_registry_service,
)

logger = logging.getLogger(__name__)


class QuizNotFoundError(Exception):
    """Raised when a quiz is not found in the registry (404)."""

    pass


class RegistryUnavailableError(Exception):
    """Raised when the content registry cannot be accessed (503)."""

    pass


def submit_quiz(
    user_id: str, module_id: str, answers: dict[str, str]
) -> dict[str, Any]:
    """Process a quiz submission: validate, score, persist completion, update streak.

    Args:
        user_id: Authenticated user ID from JWT.
        module_id: Module/quiz identifier.
        answers: Dict mapping question_id to submitted answer choice.

    Returns:
        dict with passed, score, passing_score, already_completed, results, current_streak.

    Raises:
        QuizNotFoundError: If quiz not found.
        RegistryUnavailableError: If content registry is unreachable.
        ValueError: If answers don't match expected question IDs.
    """
    settings = get_settings()
    s3_bucket = settings.content_registry_bucket
    table_name = settings.progress_table

    # Load quiz definition from content registry
    quiz_definition = None
    if s3_bucket:
        try:
            registry = get_registry_service(s3_bucket)
            quiz_definition = registry.get_quiz(module_id)
        except SchemaVersionError as e:
            raise RegistryUnavailableError(f"Schema version incompatible: {e}")
        except Exception as e:
            raise RegistryUnavailableError(f"Content registry unavailable: {e}")

    if quiz_definition is None:
        raise QuizNotFoundError(f"Quiz not found: {module_id}")

    passing_score = quiz_definition["passing_score"]
    questions = quiz_definition["questions"]

    # Validate question IDs
    required_ids = {q["id"] for q in questions}
    submitted_ids = set(answers.keys())

    if required_ids != submitted_ids:
        missing = required_ids - submitted_ids
        extra = submitted_ids - required_ids
        if missing:
            raise ValueError(f"Missing required question IDs: {missing}")
        if extra:
            raise ValueError(f"Extra question IDs not in quiz: {extra}")

    # Score the quiz
    correct_count = 0
    results = []

    for question in questions:
        qid = question["id"]
        correct_answer = question["correct_answer"]
        submitted = answers.get(qid)
        is_correct = submitted == correct_answer
        if is_correct:
            correct_count += 1
        results.append(
            {
                "question_id": qid,
                "correct": is_correct,
                "correct_answer": correct_answer,
                "explanation": question.get("explanation", ""),
            }
        )

    total_count = len(questions)
    score = int((correct_count / total_count) * 100)
    passed = score >= passing_score

    # Check existing completion
    dynamodb = boto3.client("dynamodb")
    existing_completion = _get_module_completion(
        dynamodb, table_name, user_id, module_id
    )
    already_completed = existing_completion is not None

    current_streak = 0

    if passed:
        _save_module_completion(
            dynamodb, table_name, user_id, module_id, score, not already_completed
        )
        if not already_completed:
            current_streak = _update_streak(dynamodb, table_name, user_id)
        else:
            streak_data = _get_streak_data(dynamodb, table_name, user_id)
            current_streak = streak_data["current_streak"]
    else:
        streak_data = _get_streak_data(dynamodb, table_name, user_id)
        current_streak = streak_data["current_streak"]

    return {
        "passed": passed,
        "score": score,
        "passing_score": passing_score,
        "already_completed": already_completed,
        "results": results,
        "current_streak": current_streak,
    }


# ---------------------------------------------------------------------------
# DynamoDB helpers
# ---------------------------------------------------------------------------


def _get_module_completion(
    dynamodb, table_name: str, user_id: str, module_id: str
) -> dict[str, Any] | None:
    """Get MODULE# record for a user."""
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
    except ClientError:
        return None


def _save_module_completion(
    dynamodb, table_name: str, user_id: str, module_id: str, score: int, is_first: bool
) -> None:
    """Save or update MODULE# completion record."""
    completed_at = datetime.now(timezone.utc).isoformat()

    try:
        if is_first:
            item = {
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": f"MODULE#{module_id}"},
                "score": {"N": str(score)},
                "first_completed_at": {"S": completed_at},
                "completed_at": {"S": completed_at},
            }
            dynamodb.put_item(TableName=table_name, Item=item)
        else:
            existing = _get_module_completion(dynamodb, table_name, user_id, module_id)
            if existing and score > existing["score"]:
                dynamodb.update_item(
                    TableName=table_name,
                    Key={
                        "PK": {"S": f"USER#{user_id}"},
                        "SK": {"S": f"MODULE#{module_id}"},
                    },
                    UpdateExpression="SET score = :score, completed_at = :ca",
                    ExpressionAttributeValues={
                        ":score": {"N": str(score)},
                        ":ca": {"S": completed_at},
                    },
                )
            else:
                dynamodb.update_item(
                    TableName=table_name,
                    Key={
                        "PK": {"S": f"USER#{user_id}"},
                        "SK": {"S": f"MODULE#{module_id}"},
                    },
                    UpdateExpression="SET completed_at = :ca",
                    ExpressionAttributeValues={":ca": {"S": completed_at}},
                )
    except ClientError as e:
        raise Exception(
            f"Failed to save module completion: {e.response['Error']['Code']}"
        )


def _get_streak_data(dynamodb, table_name: str, user_id: str) -> dict[str, Any]:
    """Get STREAK record."""
    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "STREAK"}},
        )
        item = response.get("Item")
        if not item:
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
    except ClientError:
        return {"current_streak": 0, "longest_streak": 0, "last_activity_date": None}


def _update_streak(dynamodb, table_name: str, user_id: str) -> int:
    """Update streak on first completion of a quiz for the day."""
    streak_data = _get_streak_data(dynamodb, table_name, user_id)
    current_streak = streak_data["current_streak"]
    longest_streak = streak_data["longest_streak"]
    last_activity_date = streak_data["last_activity_date"]

    today = datetime.now(timezone.utc).date()
    today_str = today.isoformat()

    if last_activity_date:
        last_date = datetime.fromisoformat(last_activity_date).date()
        if last_date == today:
            pass  # Same day, no change
        elif last_date == today - timedelta(days=1):
            current_streak += 1
        else:
            current_streak = 1
    else:
        current_streak = 1

    if current_streak > longest_streak:
        longest_streak = current_streak

    # Persist
    try:
        item = {
            "PK": {"S": f"USER#{user_id}"},
            "SK": {"S": "STREAK"},
            "current_streak": {"N": str(current_streak)},
            "longest_streak": {"N": str(longest_streak)},
            "last_activity_date": {"S": today_str},
        }
        dynamodb.put_item(TableName=table_name, Item=item)
    except ClientError as e:
        logger.error("Failed to update streak: %s", e)

    return current_streak
