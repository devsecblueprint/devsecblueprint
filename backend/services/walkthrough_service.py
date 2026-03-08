"""
Walkthrough Service Module

Business logic for walkthrough operations and progress tracking.
Provides functions for retrieving walkthroughs with filtering, loading README content,
and managing user progress.

Requirements: 10.3, 10.4, 8.4, 15.1
"""

from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, timezone
from services.walkthrough_registry import get_registry, WalkthroughMetadata
from services.dynamo import (
    get_walkthrough_progress as get_progress_from_db,
    save_walkthrough_progress,
)


def get_walkthroughs(
    difficulty: Optional[str] = None,
    topics: Optional[List[str]] = None,
    search: Optional[str] = None,
) -> List[Dict]:
    """
    Retrieve walkthroughs with optional filtering.

    Applies filters in sequence: difficulty, topics, then search.
    All filters use AND logic when combined.

    Args:
        difficulty: Filter by difficulty level ("Beginner", "Intermediate", "Advanced")
        topics: Filter by topic tags (matches walkthroughs with at least one topic)
        search: Search query (case-insensitive, partial matching in title/description/topics)

    Returns:
        List of walkthrough metadata dicts with keys:
            - id, title, description, difficulty, topics, estimatedTime, prerequisites, repository

    Requirements: 10.3, 10.4
    """
    registry = get_registry()

    # Start with all walkthroughs
    results = registry.get_all()

    # Apply difficulty filter
    if difficulty:
        results = [wt for wt in results if wt.difficulty == difficulty]

    # Apply topics filter
    if topics:
        results = [wt for wt in results if any(topic in wt.topics for topic in topics)]

    # Apply search filter
    if search:
        search_lower = search.lower()
        results = [
            wt
            for wt in results
            if (
                search_lower in wt.title.lower()
                or search_lower in wt.description.lower()
                or any(search_lower in topic.lower() for topic in wt.topics)
            )
        ]

    # Convert to dict format
    return [_walkthrough_to_dict(wt) for wt in results]


def get_walkthrough_by_id(walkthrough_id: str) -> Optional[Dict]:
    """
    Retrieve a single walkthrough by ID.

    Args:
        walkthrough_id: Unique walkthrough identifier

    Returns:
        Walkthrough metadata dict or None if not found.
        Dict contains keys: id, title, description, difficulty, topics,
        estimatedTime, prerequisites, repository

    Requirements: 10.5
    """
    registry = get_registry()
    walkthrough = registry.get_by_id(walkthrough_id)

    if walkthrough is None:
        return None

    return _walkthrough_to_dict(walkthrough)


def load_readme(walkthrough_id: str) -> str:
    """
    Load README.md content for a walkthrough.

    Args:
        walkthrough_id: Walkthrough identifier

    Returns:
        README markdown content as string

    Raises:
        FileNotFoundError: If README.md does not exist for the walkthrough
        ValueError: If walkthrough_id is not found in registry

    Requirements: 8.4, 15.1
    """
    registry = get_registry()
    walkthrough = registry.get_by_id(walkthrough_id)

    if walkthrough is None:
        raise ValueError(f"Walkthrough not found: {walkthrough_id}")

    # Construct path to README.md
    readme_path = Path(walkthrough.repository) / "README.md"

    if not readme_path.exists():
        raise FileNotFoundError(
            f"README.md not found for walkthrough: {walkthrough_id}"
        )

    # Read and return README content
    with open(readme_path, "r", encoding="utf-8") as f:
        return f.read()


def _walkthrough_to_dict(walkthrough: WalkthroughMetadata) -> Dict:
    """
    Convert WalkthroughMetadata to dictionary format.

    Args:
        walkthrough: WalkthroughMetadata object

    Returns:
        Dictionary with walkthrough data
    """
    return {
        "id": walkthrough.id,
        "title": walkthrough.title,
        "description": walkthrough.description,
        "difficulty": walkthrough.difficulty,
        "topics": walkthrough.topics,
        "estimatedTime": walkthrough.estimated_time,
        "prerequisites": walkthrough.prerequisites,
        "repository": walkthrough.repository,
    }


def get_walkthrough_progress(user_id: str, walkthrough_id: str) -> Dict:
    """
    Retrieve user's progress for a walkthrough.

    If no progress record exists, returns default "not_started" status.

    Args:
        user_id: Authenticated user ID
        walkthrough_id: Walkthrough identifier

    Returns:
        dict: {
            "status": str,  # "not_started", "in_progress", "completed"
            "started_at": str | None,
            "completed_at": str | None
        }

    Requirements: 11.7
    """
    # Get progress from DynamoDB
    progress = get_progress_from_db(user_id, walkthrough_id)

    # If no record exists, return default not_started status
    if progress is None:
        return {"status": "not_started", "started_at": None, "completed_at": None}

    # Return the progress record
    return {
        "status": progress.get("status", "not_started"),
        "started_at": progress.get("started_at") or None,
        "completed_at": progress.get("completed_at") or None,
    }


def update_walkthrough_progress(user_id: str, walkthrough_id: str, status: str) -> None:
    """
    Update user's progress for a walkthrough.

    Handles timestamp logic:
    - When status is "in_progress" and no prior record exists, sets started_at to current time
    - When status is "completed", sets completed_at to current time (preserves started_at)

    Args:
        user_id: Authenticated user ID
        walkthrough_id: Walkthrough identifier
        status: New status ("in_progress" or "completed")

    Raises:
        ValueError: If status is invalid (not "in_progress" or "completed")

    Requirements: 11.7, 11.8
    """
    # Validate status
    valid_statuses = ["in_progress", "completed"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

    # Get current progress to check if record exists
    current_progress = get_progress_from_db(user_id, walkthrough_id)

    # Prepare timestamp values
    started_at = None
    completed_at = None

    if status == "in_progress":
        # If this is the first view (no existing record), set started_at to now
        if current_progress is None:
            started_at = datetime.now(timezone.utc).isoformat()
        else:
            # Preserve existing started_at
            started_at = current_progress.get("started_at")

    elif status == "completed":
        # Set completed_at to now
        completed_at = datetime.now(timezone.utc).isoformat()

        # Preserve or set started_at
        if current_progress and current_progress.get("started_at"):
            started_at = current_progress.get("started_at")
        else:
            # If somehow completing without a started_at, set it to now
            started_at = completed_at

    # Save the progress record
    save_walkthrough_progress(
        user_id=user_id,
        walkthrough_id=walkthrough_id,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
    )
