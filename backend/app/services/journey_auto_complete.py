"""Builder Journey auto-completion logic.

Determines which journey tasks should be automatically marked as complete
based on the user's existing progress, membership state, and submissions.

Auto-completion runs on each GET /progress/journey request so that tasks
completed via normal platform usage (e.g., finishing a walkthrough) are
reflected in the journey without manual action.
"""

from app.config.journey_tasks import (
    AUTO_COMPLETE_MAPPINGS,
    AutoCompleteCondition,
    PREREQUISITE_CONTENT_IDS,
    PREREQUISITE_QUIZ_IDS,
    WALKTHROUGH_CONTENT_IDS,
)


def compute_auto_completions(
    user_id: str,
    existing_progress: list[dict],
    membership: dict | None,
    capstone_count: int,
) -> list[str]:
    """Compute which journey tasks should be auto-completed.

    Checks various platform signals (Discord connection, content progress,
    capstone submissions) and returns task IDs that should be marked complete.

    Args:
        user_id: The user's identifier.
        existing_progress: List of content progress items from the progress
            table (each dict has 'content_id' and 'status' keys).
        membership: The membership DynamoDB item dict (raw DynamoDB format),
            or None if not found.
        capstone_count: Number of capstone submissions the user has.

    Returns:
        List of task IDs that should be auto-completed.
    """
    auto_completed: list[str] = []

    # Build set of completed content IDs for efficient lookup
    user_content_ids: set[str] = {
        item.get("content_id", "") for item in existing_progress
    }

    for task_id, condition in AUTO_COMPLETE_MAPPINGS.items():
        if condition == AutoCompleteCondition.DISCORD_CONNECTED:
            if _check_discord_connected(membership):
                auto_completed.append(task_id)

        elif condition == AutoCompleteCondition.PREREQUISITES_COMPLETE:
            if _check_prerequisites_complete(user_content_ids):
                auto_completed.append(task_id)

        elif condition == AutoCompleteCondition.QUIZZES_COMPLETE:
            if _check_quizzes_complete(user_content_ids):
                auto_completed.append(task_id)

        elif condition == AutoCompleteCondition.CAPSTONE_SUBMITTED:
            if _check_capstone_submitted(capstone_count):
                auto_completed.append(task_id)

        elif condition == AutoCompleteCondition.WALKTHROUGH_STARTED:
            if _check_walkthrough_started(user_content_ids):
                auto_completed.append(task_id)

    return auto_completed


def _check_discord_connected(membership: dict | None) -> bool:
    """Check if user has a discord_id in their membership record."""
    if not membership:
        return False
    discord_id = membership.get("discord_id", {}).get("S", "")
    return bool(discord_id)


def _check_prerequisites_complete(user_content_ids: set[str]) -> bool:
    """Check if all prerequisite content IDs are marked complete."""
    return PREREQUISITE_CONTENT_IDS.issubset(user_content_ids)


def _check_quizzes_complete(user_content_ids: set[str]) -> bool:
    """Check if all prerequisite quiz content IDs are marked complete."""
    return PREREQUISITE_QUIZ_IDS.issubset(user_content_ids)


def _check_capstone_submitted(capstone_count: int) -> bool:
    """Check if at least one capstone submission exists."""
    return capstone_count > 0


def _check_walkthrough_started(user_content_ids: set[str]) -> bool:
    """Check if at least one walkthrough content ID is marked complete."""
    return bool(user_content_ids.intersection(WALKTHROUGH_CONTENT_IDS))
