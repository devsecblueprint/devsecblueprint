"""
Quiz Service Module

Business logic for quiz validation, scoring, completion tracking, and streak management.
This module orchestrates the quiz submission workflow and delegates to other services.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 4.3, 4.5, 5.2, 8.2, 10.6, 10.7
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from services.quiz_registry import get_quiz
from services.dynamo import (
    get_module_completion,
    save_module_completion,
    get_streak_data,
    update_streak_data,
)

# Import content registry service for parallel operation
try:
    from services.content_registry import get_registry_service, SchemaVersionError

    CONTENT_REGISTRY_AVAILABLE = True
except ImportError:
    CONTENT_REGISTRY_AVAILABLE = False

    # Define a dummy SchemaVersionError so we can still catch it
    class SchemaVersionError(Exception):
        pass


logger = logging.getLogger(__name__)


# Custom exceptions for error handling (Requirements 4.3, 4.5, 5.2)
class QuizNotFoundError(Exception):
    """Raised when a quiz is not found in the registry (404)."""

    pass


class RegistryUnavailableError(Exception):
    """Raised when the content registry cannot be accessed (503)."""

    pass


# Feature flag for parallel operation mode
PARALLEL_MODE_ENABLED = (
    os.environ.get("ENABLE_PARALLEL_REGISTRY_MODE", "false").lower() == "true"
)

# Feature flag to control which registry is primary (default: new registry)
USE_NEW_REGISTRY_AS_PRIMARY = (
    os.environ.get("USE_NEW_REGISTRY_AS_PRIMARY", "true").lower() == "true"
)


def _compare_quiz_definitions(old_quiz: dict, new_quiz: dict, module_id: str) -> None:
    """
    Compare quiz definitions from old and new registries and log discrepancies.

    This function is used during parallel operation mode to validate that the
    new content registry produces the same quiz definitions as the old hardcoded registry.

    Args:
        old_quiz: Quiz definition from quiz_registry.py
        new_quiz: Quiz definition from content_registry
        module_id: Module identifier for logging

    Requirements: 10.6, 10.7
    """
    discrepancies = []

    # Compare passing scores
    old_passing = old_quiz.get("passing_score")
    new_passing = new_quiz.get("passing_score")
    if old_passing != new_passing:
        discrepancies.append(
            f"passing_score mismatch: old={old_passing}, new={new_passing}"
        )

    # Compare question counts
    old_questions = old_quiz.get("questions", [])
    new_questions = new_quiz.get("questions", [])
    if len(old_questions) != len(new_questions):
        discrepancies.append(
            f"question_count mismatch: old={len(old_questions)}, new={len(new_questions)}"
        )

    # Compare individual questions
    old_q_map = {q["id"]: q for q in old_questions}
    new_q_map = {q["id"]: q for q in new_questions}

    # Check for missing questions
    old_ids = set(old_q_map.keys())
    new_ids = set(new_q_map.keys())

    if old_ids != new_ids:
        missing_in_new = old_ids - new_ids
        extra_in_new = new_ids - old_ids
        if missing_in_new:
            discrepancies.append(f"questions missing in new registry: {missing_in_new}")
        if extra_in_new:
            discrepancies.append(f"extra questions in new registry: {extra_in_new}")

    # Compare correct answers for matching questions
    for q_id in old_ids & new_ids:
        old_answer = old_q_map[q_id].get("correct_answer")
        new_answer = new_q_map[q_id].get("correct_answer")
        if old_answer != new_answer:
            discrepancies.append(
                f"question {q_id} correct_answer mismatch: old={old_answer}, new={new_answer}"
            )

    # Log results
    if discrepancies:
        logger.error(
            "Quiz definition discrepancies detected between old and new registries",
            extra={
                "module_id": module_id,
                "discrepancies": discrepancies,
                "discrepancy_count": len(discrepancies),
            },
        )
    else:
        logger.info(
            "Quiz definitions match between old and new registries",
            extra={"module_id": module_id, "question_count": len(old_questions)},
        )


def _compare_validation_results(
    old_results: dict, new_results: dict, module_id: str, answers: dict
) -> None:
    """
    Compare validation results from old and new registries and log discrepancies.

    This function validates that both registries produce identical validation results
    for the same quiz submission.

    Args:
        old_results: Validation results from old registry
        new_results: Validation results from new registry
        module_id: Module identifier for logging
        answers: Submitted answers for context

    Requirements: 10.6, 10.7
    """
    discrepancies = []

    # Compare scores
    old_score = old_results.get("score")
    new_score = new_results.get("score")
    if old_score != new_score:
        discrepancies.append(f"score mismatch: old={old_score}, new={new_score}")

    # Compare passed status
    old_passed = old_results.get("passed")
    new_passed = new_results.get("passed")
    if old_passed != new_passed:
        discrepancies.append(f"passed mismatch: old={old_passed}, new={new_passed}")

    # Compare per-question correctness
    old_per_q = {r["question_id"]: r["correct"] for r in old_results.get("results", [])}
    new_per_q = {r["question_id"]: r["correct"] for r in new_results.get("results", [])}

    for q_id in set(old_per_q.keys()) | set(new_per_q.keys()):
        old_correct = old_per_q.get(q_id)
        new_correct = new_per_q.get(q_id)
        if old_correct != new_correct:
            discrepancies.append(
                f"question {q_id} correctness mismatch: old={old_correct}, new={new_correct}"
            )

    # Log results
    if discrepancies:
        logger.error(
            "Validation result discrepancies detected between old and new registries",
            extra={
                "module_id": module_id,
                "discrepancies": discrepancies,
                "discrepancy_count": len(discrepancies),
                "submitted_answers": answers,
            },
        )
    else:
        logger.info(
            "Validation results match between old and new registries",
            extra={"module_id": module_id, "score": old_score, "passed": old_passed},
        )


def _validate_with_old_registry(quiz_definition: dict, answers: dict) -> dict:
    """
    Validate quiz submission using the old registry format.

    This helper function performs validation using the hardcoded registry format
    for comparison purposes in parallel mode.

    Args:
        quiz_definition: Quiz definition from old registry
        answers: Submitted answers

    Returns:
        dict with score, passed, and results
    """
    passing_score = quiz_definition["passing_score"]
    questions = quiz_definition["questions"]

    # Score the quiz
    correct_count = 0
    results = []

    for question in questions:
        question_id = question["id"]
        correct_answer = question["correct_answer"]
        submitted_answer = answers.get(question_id)

        is_correct = submitted_answer == correct_answer
        if is_correct:
            correct_count += 1

        results.append({"question_id": question_id, "correct": is_correct})

    # Calculate score as percentage
    total_count = len(questions)
    score = int((correct_count / total_count) * 100)

    # Determine pass/fail
    passed = score >= passing_score

    return {"score": score, "passed": passed, "results": results}


def submit_quiz(user_id: str, module_id: str, answers: dict) -> dict:
    """
    Process quiz submission with validation, scoring, and streak updates.

    This function:
    1. Validates module_id exists in quiz registry
    2. Validates all required question IDs are present
    3. Scores the quiz by comparing answers to correct answers
    4. Determines pass/fail status
    5. Updates completion records if quiz passes
    6. Updates streak data for first completions
    7. Returns detailed results with feedback

    Registry Source Selection (controlled by USE_NEW_REGISTRY_AS_PRIMARY):
    - When USE_NEW_REGISTRY_AS_PRIMARY=true (default):
      * Uses ContentRegistryService as primary source
      * Falls back to hardcoded quiz_registry if new registry fails
    - When USE_NEW_REGISTRY_AS_PRIMARY=false:
      * Uses hardcoded quiz_registry as primary source
      * Falls back to ContentRegistryService if old registry fails

    In parallel operation mode (when ENABLE_PARALLEL_REGISTRY_MODE=true):
    - Reads from both old (quiz_registry) and new (content_registry) sources
    - Compares quiz definitions and validation results
    - Logs any discrepancies for investigation

    Args:
        user_id: Authenticated user ID from JWT
        module_id: Module identifier (e.g., "secure-sdlc")
        answers: Dict mapping question_id to answer choice (e.g., {"q1": "B", "q2": "C"})

    Returns:
        dict: {
            "passed": bool,
            "score": int,
            "passing_score": int,
            "already_completed": bool,
            "results": [
                {
                    "question_id": str,
                    "correct": bool,
                    "correct_answer": str,
                    "explanation": str
                }
            ],
            "current_streak": int
        }

    Raises:
        QuizNotFoundError: If quiz not found in any registry (404)
        RegistryUnavailableError: If registry unavailable and no fallback (503)
        ValueError: If validation fails (missing/extra question IDs)
        Exception: If DynamoDB operation fails

    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 4.3, 4.5, 5.2, 6.1, 6.8, 6.9, 10.5, 10.6, 10.7
    """
    # Determine which registry to use as primary source (Requirement 10.5)
    quiz_definition = None
    primary_source = None
    fallback_source = None

    # Get S3 bucket from environment
    s3_bucket = os.environ.get("CONTENT_REGISTRY_BUCKET")

    if USE_NEW_REGISTRY_AS_PRIMARY and CONTENT_REGISTRY_AVAILABLE and s3_bucket:
        # Try new registry first (primary)
        try:
            registry_service = get_registry_service(s3_bucket)
            quiz_definition = registry_service.get_quiz(module_id)

            if quiz_definition:
                primary_source = "content_registry"
                logger.info(
                    "Using ContentRegistryService as primary source",
                    extra={
                        "module_id": module_id,
                        "primary_source": "content_registry",
                    },
                )
            else:
                # Quiz not found in registry - this is a 404 case
                logger.warning(
                    "Quiz not found in ContentRegistryService, falling back to hardcoded registry",
                    extra={
                        "module_id": module_id,
                        "primary_source": "content_registry",
                        "fallback_source": "quiz_registry",
                    },
                )
        except SchemaVersionError as e:
            # Schema version incompatible - this is a 503 case (Requirement 4.5)
            logger.error(
                f"Schema version error in ContentRegistryService: {str(e)}",
                extra={
                    "module_id": module_id,
                    "error": str(e),
                    "error_type": "schema_version",
                },
            )
            # If no fallback available, raise RegistryUnavailableError
            if not get_quiz(module_id):
                raise RegistryUnavailableError(
                    f"Content registry schema version incompatible: {str(e)}"
                )
            # Otherwise, fall back to hardcoded registry
            logger.warning(
                "Falling back to hardcoded registry due to schema version error",
                extra={"module_id": module_id, "fallback_source": "quiz_registry"},
            )
        except Exception as e:
            # S3 fetch failure or other registry errors - this is a 503 case (Requirement 4.3)
            logger.error(
                f"Error fetching from ContentRegistryService: {str(e)}",
                extra={
                    "module_id": module_id,
                    "error": str(e),
                    "error_type": "registry_fetch_failure",
                    "primary_source": "content_registry",
                    "fallback_source": "quiz_registry",
                },
            )
            # If no fallback available, raise RegistryUnavailableError
            if not get_quiz(module_id):
                raise RegistryUnavailableError(
                    f"Content registry unavailable: {str(e)}"
                )
            # Otherwise, fall back to hardcoded registry
            logger.warning(
                "Falling back to hardcoded registry due to registry fetch failure",
                extra={"module_id": module_id, "fallback_source": "quiz_registry"},
            )

        # Fallback to old registry if new registry failed
        if quiz_definition is None:
            quiz_definition = get_quiz(module_id)
            if quiz_definition:
                fallback_source = "quiz_registry"
    else:
        # Use old registry as primary (original behavior)
        quiz_definition = get_quiz(module_id)
        if quiz_definition:
            primary_source = "quiz_registry"
            logger.info(
                "Using hardcoded quiz_registry as primary source",
                extra={"module_id": module_id, "primary_source": "quiz_registry"},
            )

        # Fallback to new registry if old registry failed and new registry is available
        if quiz_definition is None and CONTENT_REGISTRY_AVAILABLE and s3_bucket:
            try:
                registry_service = get_registry_service(s3_bucket)
                quiz_definition = registry_service.get_quiz(module_id)

                if quiz_definition:
                    fallback_source = "content_registry"
                    logger.warning(
                        "Quiz not found in hardcoded registry, falling back to ContentRegistryService",
                        extra={
                            "module_id": module_id,
                            "primary_source": "quiz_registry",
                            "fallback_source": "content_registry",
                        },
                    )
            except SchemaVersionError as e:
                # Schema version incompatible - log but don't fail since primary already failed
                logger.error(
                    f"Schema version error in ContentRegistryService fallback: {str(e)}",
                    extra={
                        "module_id": module_id,
                        "error": str(e),
                        "error_type": "schema_version",
                    },
                )
            except Exception as e:
                # S3 fetch failure - log but don't fail since primary already failed
                logger.error(
                    f"Error fetching from ContentRegistryService fallback: {str(e)}",
                    extra={
                        "module_id": module_id,
                        "error": str(e),
                        "error_type": "registry_fetch_failure",
                    },
                )

    # Validate module_id exists (Requirement 3.1, 5.2)
    if quiz_definition is None:
        # Quiz not found in any registry - this is a 404 case
        raise QuizNotFoundError(f"Quiz not found: {module_id}")

    # Log which source was used
    source_used = primary_source if primary_source else fallback_source
    logger.info(
        "Quiz definition loaded",
        extra={
            "module_id": module_id,
            "source": source_used,
            "is_fallback": fallback_source is not None,
        },
    )

    # Parallel operation mode: compare both registries (Requirements 10.6, 10.7)
    if PARALLEL_MODE_ENABLED and CONTENT_REGISTRY_AVAILABLE and s3_bucket:
        try:
            registry_service = get_registry_service(s3_bucket)

            # Fetch from both sources
            old_quiz = get_quiz(module_id)
            new_quiz = registry_service.get_quiz(module_id)

            if old_quiz and new_quiz:
                # Compare quiz definitions
                _compare_quiz_definitions(old_quiz, new_quiz, module_id)

                logger.info(
                    "Parallel mode: fetched quiz from both registries",
                    extra={
                        "module_id": module_id,
                        "old_registry_found": True,
                        "new_registry_found": True,
                    },
                )
            elif old_quiz and not new_quiz:
                logger.warning(
                    "Parallel mode: quiz only found in old registry",
                    extra={
                        "module_id": module_id,
                        "old_registry_found": True,
                        "new_registry_found": False,
                    },
                )
            elif not old_quiz and new_quiz:
                logger.warning(
                    "Parallel mode: quiz only found in new registry",
                    extra={
                        "module_id": module_id,
                        "old_registry_found": False,
                        "new_registry_found": True,
                    },
                )
        except Exception as e:
            logger.error(
                f"Parallel mode: error during comparison: {str(e)}",
                extra={"module_id": module_id, "error": str(e)},
            )

    # Extract quiz data from old registry (primary source)
    passing_score = quiz_definition["passing_score"]
    questions = quiz_definition["questions"]

    # Validate all required question IDs are present (Requirement 3.3)
    required_question_ids = {q["id"] for q in questions}
    submitted_question_ids = set(answers.keys())

    if required_question_ids != submitted_question_ids:
        missing = required_question_ids - submitted_question_ids
        extra = submitted_question_ids - required_question_ids
        if missing:
            raise ValueError(f"Missing required question IDs: {missing}")
        if extra:
            raise ValueError(f"Extra question IDs not in quiz: {extra}")

    # Score the quiz (Requirements 3.5, 3.6, 3.7)
    correct_count = 0
    results = []

    for question in questions:
        question_id = question["id"]
        correct_answer = question["correct_answer"]
        submitted_answer = answers.get(question_id)

        is_correct = submitted_answer == correct_answer
        if is_correct:
            correct_count += 1

        results.append(
            {
                "question_id": question_id,
                "correct": is_correct,
                "correct_answer": correct_answer,
                "explanation": question["explanation"],
            }
        )

    # Calculate score as percentage (Requirement 3.6)
    total_count = len(questions)
    score = int((correct_count / total_count) * 100)

    # Determine pass/fail (Requirement 3.7)
    passed = score >= passing_score

    # Parallel operation mode: validate with both registries and compare results (Requirements 10.6, 10.7)
    if PARALLEL_MODE_ENABLED and CONTENT_REGISTRY_AVAILABLE and s3_bucket:
        try:
            registry_service = get_registry_service(s3_bucket)

            # Get quiz definitions from both sources
            old_quiz = get_quiz(module_id)
            new_quiz = registry_service.get_quiz(module_id)

            if old_quiz and new_quiz:
                # Validate submission with old registry
                old_results = _validate_with_old_registry(old_quiz, answers)

                # Validate submission with new registry
                validation_result = registry_service.validate_quiz_submission(
                    module_id, answers
                )

                if validation_result:
                    # Build comparable results structure from new registry
                    new_results = {
                        "score": int(validation_result.score),
                        "passed": validation_result.passed,
                        "results": [
                            {"question_id": q_id, "correct": is_correct}
                            for q_id, is_correct in validation_result.per_question.items()
                        ],
                    }

                    # Compare validation results
                    _compare_validation_results(
                        old_results, new_results, module_id, answers
                    )
                else:
                    logger.warning(
                        "Parallel mode: validation failed with new registry",
                        extra={"module_id": module_id},
                    )
        except Exception as e:
            # Log error but don't fail the request
            logger.error(
                f"Parallel mode: error during validation comparison: {str(e)}",
                extra={"module_id": module_id, "error": str(e)},
            )

    # Check if module was previously completed (Requirements 4.1, 6.6, 6.7)
    existing_completion = get_module_completion(user_id, module_id)
    already_completed = existing_completion is not None

    # Initialize current_streak
    current_streak = 0

    # Handle completion tracking and streak updates (Requirements 4.1, 4.6, 5.1-5.7)
    if passed:
        # Save completion record
        save_module_completion(user_id, module_id, score, not already_completed)

        # Update streak only for first completions (Requirement 5.7)
        if not already_completed:
            current_streak = _update_streak(user_id)
        else:
            # For re-completions, just return existing streak
            streak_data = get_streak_data(user_id)
            current_streak = streak_data["current_streak"]
    else:
        # Quiz failed, no completion record created (Requirement 4.6)
        # Return existing streak if any
        streak_data = get_streak_data(user_id)
        current_streak = streak_data["current_streak"]

    return {
        "passed": passed,
        "score": score,
        "passing_score": passing_score,
        "already_completed": already_completed,
        "results": results,
        "current_streak": current_streak,
    }


def _update_streak(user_id: str) -> int:
    """
    Update user streak for a first completion.

    Implements streak calculation logic:
    - If last_activity_date == today: no change to current_streak
    - If last_activity_date == yesterday: increment current_streak by 1
    - Otherwise: reset current_streak to 1
    - Update longest_streak if current_streak exceeds it
    - Update last_activity_date to today

    Args:
        user_id: User identifier

    Returns:
        int: Updated current_streak value

    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
    """
    # Retrieve existing streak data (Requirement 5.1)
    streak_data = get_streak_data(user_id)
    current_streak = streak_data["current_streak"]
    longest_streak = streak_data["longest_streak"]
    last_activity_date = streak_data["last_activity_date"]

    # Get today's date in YYYY-MM-DD format
    today = datetime.now(timezone.utc).date()
    today_str = today.isoformat()

    # Calculate new streak (Requirements 5.2, 5.3, 5.4)
    if last_activity_date:
        last_date = datetime.fromisoformat(last_activity_date).date()

        if last_date == today:
            # Same day, no change (Requirement 5.2)
            pass
        elif last_date == today - timedelta(days=1):
            # Yesterday, increment streak (Requirement 5.3)
            current_streak += 1
        else:
            # Gap in completions, reset to 1 (Requirement 5.4)
            current_streak = 1
    else:
        # First ever completion
        current_streak = 1

    # Update longest_streak if needed (Requirement 5.5)
    if current_streak > longest_streak:
        longest_streak = current_streak

    # Update streak data in DynamoDB (Requirement 5.6)
    update_streak_data(user_id, current_streak, longest_streak, today_str)

    return current_streak
