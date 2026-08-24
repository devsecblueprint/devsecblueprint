"""Progress router — learning progress tracking.

Ports all /progress/* routes from the Lambda handler:
- PUT /progress — Save progress (mark content complete, optional capstone submission)
- GET /progress — Get all completed content for a user
- GET /progress/stats — Get aggregated statistics
- GET /progress/recent — Get recently completed activities
- GET /progress/badges — Get user badges with earned status
- PUT /progress/last-active — Save the learner's last active lesson
- GET /progress/last-active — Retrieve the learner's last active lesson
- DELETE /progress/reset — Reset all progress (admin only)
- GET /progress/capstone/{content_id} — Get capstone submission
- GET /progress/capstone/{content_id}/review — Get capstone review
- GET /progress/journey — Get Builder Journey progress
- PUT /progress/journey — Mark a journey task as complete

All routes require JWT authentication. Reset requires admin.
Journey endpoints require authentication.

Requirements: 4.2, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import boto3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.jwt import get_current_user, require_admin
from app.config import Settings
from app.dependencies import get_settings
from app.services.progress_db import ProgressDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/progress", tags=["progress"])


# ------------------------------------------------------------------
# Request models
# ------------------------------------------------------------------


class SaveProgressRequest(BaseModel):
    """Request body for PUT /progress."""

    content_id: str = Field(..., min_length=1)
    repo_url: str | None = None


class SaveLastActiveRequest(BaseModel):
    """Request body for PUT /progress/last-active."""

    page_id: str = Field(..., min_length=1)
    page_slug: str = Field(..., min_length=1)


# ------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------


def get_progress_db(settings: Settings = Depends(get_settings)) -> ProgressDB:
    """Provide a ProgressDB instance."""
    return ProgressDB(settings)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _validate_repo_url(
    url: str, expected_username: str, provider: str = "github"
) -> dict[str, Any]:
    """Validate a repository URL for the given provider.

    Ported from handlers/progress.py — same validation logic.
    """
    patterns = {
        "github": {
            "regex": r"^https?://(www\.)?github\.com/([^/]+)/([^/]+)/?$",
            "domain": "GitHub",
        },
        "gitlab": {
            "regex": r"^https?://(www\.)?gitlab\.com/([^/]+)/([^/]+)/?$",
            "domain": "GitLab",
        },
        "bitbucket": {
            "regex": r"^https?://(www\.)?bitbucket\.org/([^/]+)/([^/]+)/?$",
            "domain": "Bitbucket Cloud",
        },
    }

    config = patterns.get(provider, patterns["github"])
    match = re.match(config["regex"], url)

    if not match:
        return {"valid": False, "error": f"Invalid {config['domain']} URL format"}

    username = match.group(2)
    repo_name = match.group(3)

    # Bitbucket repos live under workspaces — skip ownership check
    if provider == "bitbucket":
        return {"valid": True, "username": username, "repo_name": repo_name}

    if username.lower() != expected_username.lower():
        return {
            "valid": False,
            "error": f"Repository must be under your {config['domain']} account ({expected_username})",
        }

    return {"valid": True, "username": username, "repo_name": repo_name}


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------


@router.put("")
async def save_progress(
    body: SaveProgressRequest,
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    db: ProgressDB = Depends(get_progress_db),
) -> dict[str, Any]:
    """Save user progress (mark content as complete).

    Optionally accepts repo_url for capstone submissions. If provided,
    validates the repository URL against the user's provider and saves
    the capstone submission metadata.
    """
    user_id = user["sub"]
    provider = user.get("provider", "github")
    github_username = user.get("github_login")
    gitlab_username = user.get("gitlab_login")
    bitbucket_username = user.get("bitbucket_login")

    if provider == "bitbucket":
        provider_username = bitbucket_username
    elif provider == "gitlab":
        provider_username = gitlab_username
    else:
        provider_username = github_username

    # Handle capstone submission if repo_url is provided
    submission_metadata = None
    if body.repo_url:
        # Capstone submissions require BUILDER tier
        try:
            dynamodb = boto3.client("dynamodb")
            membership_response = dynamodb.get_item(
                TableName=settings.membership_table,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": "MEMBERSHIP"},
                },
                ProjectionExpression="membership_tier, subscription_status",
            )
            membership_item = membership_response.get("Item")
            user_tier = (
                membership_item.get("membership_tier", {}).get("S", "FREE")
                if membership_item
                else "FREE"
            )
            sub_status = (
                membership_item.get("subscription_status", {}).get("S")
                if membership_item
                else None
            )
        except Exception:
            user_tier = "FREE"
            sub_status = None

        # Check if user has Builder-equivalent access
        has_builder_access = user_tier == "BUILDER" and sub_status in (
            "active",
            "past_due",
        )

        # Also check for contributor role (Builder-equivalent access)
        if not has_builder_access:
            try:
                contributor_response = dynamodb.get_item(
                    TableName=settings.membership_table,
                    Key={
                        "PK": {"S": f"USER#{user_id}"},
                        "SK": {"S": "CONTRIBUTOR_ROLE"},
                    },
                )
                if contributor_response.get("Item"):
                    has_builder_access = True
            except Exception:
                pass  # Non-critical, default to no access

        # Admins always have Builder-equivalent access
        if user.get("is_admin", False):
            has_builder_access = True

        if not has_builder_access:
            raise HTTPException(
                status_code=403,
                detail="Capstone submissions require a Builder subscription.",
            )

        validation_result = _validate_repo_url(
            body.repo_url, provider_username or "", provider
        )

        if not validation_result["valid"]:
            raise HTTPException(status_code=400, detail=validation_result["error"])

        try:
            # Check for existing submission and handle locking
            existing_submission = None
            try:
                existing_submission = db.get_capstone_submission(
                    user_id, body.content_id
                )
            except Exception:
                pass

            if existing_submission:
                existing_status = existing_submission.get("status", "")
                if existing_status == "pending_review":
                    raise HTTPException(
                        status_code=409, detail="Submission is locked for review"
                    )

            # Save (new or resubmission)
            db.save_capstone_submission(
                user_id=user_id,
                content_id=body.content_id,
                repo_url=body.repo_url,
                github_username=(
                    validation_result["username"] if provider != "bitbucket" else ""
                ),
                repo_name=validation_result["repo_name"],
                provider=provider,
                bitbucket_username=bitbucket_username or "",
            )

            submitted_at = datetime.now(timezone.utc).isoformat()

            # Format timestamp in US Eastern for email display
            eastern = ZoneInfo("America/New_York")
            submitted_at_eastern = datetime.now(timezone.utc).astimezone(eastern)
            submitted_at_display = submitted_at_eastern.strftime(
                "%B %d, %Y at %I:%M %p %Z"
            )

            submission_metadata = {
                "repo_url": body.repo_url,
                "github_username": (
                    validation_result["username"] if provider != "bitbucket" else ""
                ),
                "repo_name": validation_result["repo_name"],
                "submitted_at": submitted_at,
            }

            # Send email notification (fire-and-forget)
            try:
                from app.services.email import send_capstone_notification

                send_capstone_notification(
                    username=provider_username or "",
                    repo_url=body.repo_url,
                    content_id=body.content_id,
                    submitted_at=submitted_at_display,
                )
            except Exception as e:
                logger.error(f"Failed to send capstone notification email: {e}")

        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=500, detail="Service temporarily unavailable"
            )

    # Save progress — but NOT for capstone submissions.
    # Capstones are only marked complete when an admin passes them.
    if body.repo_url:
        # Capstone submission/resubmission: remove any existing completion
        # so it doesn't show as "done" while under review
        try:
            db.delete_progress(user_id, body.content_id)
        except Exception:
            pass  # Non-critical — may not exist yet
    else:
        try:
            db.save_progress(user_id, body.content_id)
        except Exception:
            raise HTTPException(
                status_code=500, detail="Service temporarily unavailable"
            )

    response_data: dict[str, Any] = {"message": "Progress saved successfully"}
    if submission_metadata:
        response_data["submission"] = submission_metadata

    return response_data


@router.get("")
async def get_progress(
    user: dict = Depends(get_current_user),
    db: ProgressDB = Depends(get_progress_db),
) -> dict[str, Any]:
    """Get all completed content for the authenticated user."""
    user_id = user["sub"]

    try:
        progress_items = db.get_user_progress(user_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")

    return {"progress": progress_items}


@router.get("/stats")
async def get_stats(
    user: dict = Depends(get_current_user),
    db: ProgressDB = Depends(get_progress_db),
) -> dict[str, Any]:
    """Get aggregated statistics for the authenticated user."""
    user_id = user["sub"]

    try:
        stats = db.get_user_stats(user_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")

    return stats


@router.get("/recent")
async def get_recent(
    user: dict = Depends(get_current_user),
    db: ProgressDB = Depends(get_progress_db),
) -> dict[str, Any]:
    """Get recently completed activities for the authenticated user."""
    user_id = user["sub"]

    try:
        recent = db.get_recent_activities(user_id, limit=10)
    except Exception:
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")

    return {"recent": recent}


@router.get("/badges")
async def get_badges(
    user: dict = Depends(get_current_user),
    db: ProgressDB = Depends(get_progress_db),
) -> dict[str, Any]:
    """Get user badges with earned status."""
    user_id = user["sub"]

    try:
        badges = db.get_user_badges(user_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")

    return {"badges": badges}


@router.put("/last-active")
async def save_last_active(
    body: SaveLastActiveRequest,
    user: dict = Depends(get_current_user),
    db: ProgressDB = Depends(get_progress_db),
) -> dict[str, str]:
    """Save the learner's last active lesson."""
    user_id = user["sub"]

    try:
        db.save_last_active(user_id, body.page_id, body.page_slug)
    except Exception:
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")

    return {"message": "Last active lesson saved"}


@router.get("/last-active")
async def get_last_active(
    user: dict = Depends(get_current_user),
    db: ProgressDB = Depends(get_progress_db),
) -> dict[str, Any]:
    """Retrieve the learner's last active lesson."""
    user_id = user["sub"]

    try:
        last_active = db.get_last_active(user_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")

    return last_active


@router.delete("/reset")
async def reset_progress(
    user: dict = Depends(require_admin),
    db: ProgressDB = Depends(get_progress_db),
) -> dict[str, Any]:
    """Reset all progress for the authenticated admin user."""
    user_id = user["sub"]
    username = user.get("name", "")

    logger.info(f"Reset request from user_id: {user_id}, username: {username}")

    try:
        db.delete_all_user_progress(user_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to reset progress")

    logger.info(f"Reset all progress for admin user: {username} (ID: {user_id})")

    return {"message": "Progress reset successfully", "user_id": user_id}


@router.get("/capstone/{content_id}")
async def get_capstone_submission(
    content_id: str,
    user: dict = Depends(get_current_user),
    db: ProgressDB = Depends(get_progress_db),
) -> dict[str, Any]:
    """Get capstone submission for a specific content_id."""
    user_id = user["sub"]

    try:
        submission = db.get_capstone_submission(user_id, content_id)

        if submission:
            return submission
        else:
            return {"submission": None}

    except Exception:
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")


@router.get("/capstone/{content_id}/review")
async def get_capstone_review(
    content_id: str,
    user: dict = Depends(get_current_user),
    db: ProgressDB = Depends(get_progress_db),
) -> dict[str, Any]:
    """Get the review for a capstone submission."""
    user_id = user["sub"]

    try:
        review = db.get_capstone_review(user_id, content_id)

        if not review:
            return {"review": None}

        return {"review": review}

    except Exception:
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")


# ------------------------------------------------------------------
# Journey request/response models
# ------------------------------------------------------------------


class JourneyTaskCompletion(BaseModel):
    """A single journey task with its completion status."""

    task_id: str
    phase: int
    status: str
    completed_at: str | None = None
    auto_completed: bool = False


class JourneyProgressResponse(BaseModel):
    """Response model for GET /progress/journey."""

    tasks: list[JourneyTaskCompletion]
    current_phase: int
    completion_percentage: int
    is_complete: bool
    journey_started_at: str | None = None
    tier: str | None = None


class CompleteJourneyTaskRequest(BaseModel):
    """Request model for PUT /progress/journey."""

    task_id: str = Field(..., min_length=1)


class CompleteJourneyTaskResponse(BaseModel):
    """Response model for PUT /progress/journey."""

    task_id: str
    status: str
    completed_at: str
    phase_completed: bool
    journey_completed: bool


# ------------------------------------------------------------------
# Journey helpers
# ------------------------------------------------------------------


def _determine_journey_tier(user: dict, settings: Settings) -> str:
    """Determine the journey tier for the authenticated user.

    Classification rules (in priority order):
    1. Admin users → BUILDER
    2. membership_tier=BUILDER + subscription active/past_due → BUILDER
    3. All other authenticated users → FREE

    Gracefully defaults to FREE on DynamoDB failures.
    """
    # Admins always get Builder tier
    if user.get("is_admin", False):
        return "BUILDER"

    user_id = user["sub"]

    dynamodb = boto3.client("dynamodb")

    # Check membership tier and subscription
    try:
        membership_response = dynamodb.get_item(
            TableName=settings.membership_table,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "MEMBERSHIP"},
            },
            ProjectionExpression="membership_tier, subscription_status",
        )
        membership_item = membership_response.get("Item")
        if membership_item:
            user_tier = membership_item.get("membership_tier", {}).get("S", "FREE")
            sub_status = membership_item.get("subscription_status", {}).get("S")
            if user_tier == "BUILDER" and sub_status in ("active", "past_due"):
                return "BUILDER"
    except Exception:
        pass  # Default to FREE on failure

    return "FREE"


def _get_membership_item(user_id: str, settings: Settings) -> dict | None:
    """Fetch the full membership item for auto-completion checks."""
    try:
        dynamodb = boto3.client("dynamodb")
        response = dynamodb.get_item(
            TableName=settings.membership_table,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "MEMBERSHIP"},
            },
        )
        return response.get("Item")
    except Exception:
        return None


# ------------------------------------------------------------------
# Journey routes
# ------------------------------------------------------------------


@router.get("/journey")
async def get_journey_progress(
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    db: ProgressDB = Depends(get_progress_db),
) -> JourneyProgressResponse:
    """Get the member's full journey progress state.

    Requires authentication. Determines the user's tier and returns
    tier-appropriate tasks. Computes auto-completions from existing
    platform progress and persists any newly detected completions.
    """
    from app.config.journey_tasks import (
        FREE_JOURNEY_PHASES,
        FREE_TASK_TO_PHASE,
        FREE_TOTAL_JOURNEY_TASKS,
        FREE_VALID_TASK_IDS,
        BUILDER_JOURNEY_PHASES,
        BUILDER_TASK_TO_PHASE,
        BUILDER_TOTAL_JOURNEY_TASKS,
        BUILDER_VALID_TASK_IDS,
    )
    from app.services.journey_auto_complete import compute_auto_completions

    user_id = user["sub"]

    # Determine the user's journey tier
    tier = _determine_journey_tier(user, settings)

    # Select tier-specific constants
    if tier == "FREE":
        journey_phases = FREE_JOURNEY_PHASES
        task_to_phase = FREE_TASK_TO_PHASE
        total_journey_tasks = FREE_TOTAL_JOURNEY_TASKS
        valid_task_ids = FREE_VALID_TASK_IDS
    else:
        journey_phases = BUILDER_JOURNEY_PHASES
        task_to_phase = BUILDER_TASK_TO_PHASE
        total_journey_tasks = BUILDER_TOTAL_JOURNEY_TASKS
        valid_task_ids = BUILDER_VALID_TASK_IDS

    try:
        # Get existing journey progress
        journey_items = db.get_journey_progress(user_id)

        # Build set of already-completed task IDs
        completed_task_ids: set[str] = set()
        task_map: dict[str, dict] = {}
        journey_started_at: str | None = None

        for item in journey_items:
            tid = item["task_id"]
            if tid == "_meta":
                journey_started_at = item.get("started_at") or item.get(
                    "completed_at", ""
                )
                continue
            completed_task_ids.add(tid)
            task_map[tid] = item

        # Ensure journey meta exists (lazy initialization)
        if not journey_started_at:
            journey_started_at = db.save_journey_meta(user_id)

        # Get user content progress for auto-completion checks
        content_progress = db.get_user_progress(user_id)
        membership_item = _get_membership_item(user_id, settings)
        capstone_count = db._count_capstone_submissions(user_id)

        # Compute auto-completions
        auto_complete_ids = compute_auto_completions(
            user_id=user_id,
            existing_progress=content_progress,
            membership=membership_item,
            capstone_count=capstone_count,
        )

        # Filter auto-completions to only tier-valid tasks
        auto_complete_ids = [tid for tid in auto_complete_ids if tid in valid_task_ids]

        # Persist any new auto-completions
        for task_id in auto_complete_ids:
            if task_id not in completed_task_ids:
                phase = task_to_phase.get(task_id, 1)
                db.save_journey_task(
                    user_id=user_id,
                    task_id=task_id,
                    phase=phase,
                    auto_completed=True,
                )
                completed_task_ids.add(task_id)
                task_map[task_id] = {
                    "task_id": task_id,
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "phase": phase,
                    "auto_completed": True,
                }

        # Build response task list (only tier-appropriate tasks)
        tasks: list[JourneyTaskCompletion] = []
        for phase_num, phase_task_ids in journey_phases.items():
            for task_id in phase_task_ids:
                if task_id in task_map:
                    item = task_map[task_id]
                    tasks.append(
                        JourneyTaskCompletion(
                            task_id=task_id,
                            phase=phase_num,
                            status="completed",
                            completed_at=item.get("completed_at"),
                            auto_completed=item.get("auto_completed", False),
                        )
                    )
                else:
                    tasks.append(
                        JourneyTaskCompletion(
                            task_id=task_id,
                            phase=phase_num,
                            status="not_started",
                            completed_at=None,
                            auto_completed=False,
                        )
                    )

        # Compute current phase (first phase with incomplete tasks)
        current_phase = max(journey_phases.keys())
        for phase_num in sorted(journey_phases.keys()):
            phase_tasks = journey_phases[phase_num]
            if not all(tid in completed_task_ids for tid in phase_tasks):
                current_phase = phase_num
                break

        # Compute completion percentage
        completion_percentage = int(
            (len(completed_task_ids & valid_task_ids) / total_journey_tasks) * 100
        )

        # Is journey fully complete?
        is_complete = completed_task_ids >= valid_task_ids

        return JourneyProgressResponse(
            tasks=tasks,
            current_phase=current_phase,
            completion_percentage=completion_percentage,
            is_complete=is_complete,
            journey_started_at=journey_started_at,
            tier=tier,
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")


@router.put("/journey")
async def complete_journey_task(
    body: CompleteJourneyTaskRequest,
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    db: ProgressDB = Depends(get_progress_db),
) -> CompleteJourneyTaskResponse:
    """Mark a specific journey task as complete.

    Requires authentication. Validates task_id against the user's
    tier-specific allowlist. Idempotent — returns success if the
    task is already complete.
    """
    from app.config.journey_tasks import (
        FREE_JOURNEY_PHASES,
        FREE_TASK_TO_PHASE,
        FREE_VALID_TASK_IDS,
        BUILDER_JOURNEY_PHASES,
        BUILDER_TASK_TO_PHASE,
        BUILDER_VALID_TASK_IDS,
    )

    # Determine the user's journey tier
    tier = _determine_journey_tier(user, settings)

    # Select tier-specific constants
    if tier == "FREE":
        journey_phases = FREE_JOURNEY_PHASES
        task_to_phase = FREE_TASK_TO_PHASE
        valid_task_ids = FREE_VALID_TASK_IDS
    else:
        journey_phases = BUILDER_JOURNEY_PHASES
        task_to_phase = BUILDER_TASK_TO_PHASE
        valid_task_ids = BUILDER_VALID_TASK_IDS

    # Validate task_id against tier-specific valid set
    if body.task_id not in valid_task_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Task '{body.task_id}' is not valid for the {tier} journey.",
        )

    user_id = user["sub"]
    phase = task_to_phase[body.task_id]

    try:
        # Ensure journey meta exists
        db.save_journey_meta(user_id)

        # Save the task (idempotent)
        db.save_journey_task(user_id=user_id, task_id=body.task_id, phase=phase)

        completed_at = datetime.now(timezone.utc).isoformat()

        # Check if all tasks in the phase are now complete
        journey_items = db.get_journey_progress(user_id)
        completed_task_ids: set[str] = {
            item["task_id"] for item in journey_items if item["task_id"] != "_meta"
        }

        phase_tasks = journey_phases[phase]
        phase_completed = all(tid in completed_task_ids for tid in phase_tasks)

        # Check if entire journey is complete
        journey_completed = completed_task_ids >= valid_task_ids

        return CompleteJourneyTaskResponse(
            task_id=body.task_id,
            status="completed",
            completed_at=completed_at,
            phase_completed=phase_completed,
            journey_completed=journey_completed,
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")


@router.delete("/journey/{task_id}")
async def uncomplete_journey_task(
    task_id: str,
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    db: ProgressDB = Depends(get_progress_db),
) -> dict[str, str]:
    """Uncomplete a journey task (remove its completion record).

    Requires authentication. Validates task_id against the user's
    tier-specific allowlist. Cannot uncomplete auto-completed tasks.
    """
    from app.config.journey_tasks import (
        FREE_VALID_TASK_IDS,
        BUILDER_VALID_TASK_IDS,
    )

    # Determine the user's journey tier
    tier = _determine_journey_tier(user, settings)

    # Select tier-specific valid set
    valid_task_ids = FREE_VALID_TASK_IDS if tier == "FREE" else BUILDER_VALID_TASK_IDS

    # Validate task_id against tier-specific valid set
    if task_id not in valid_task_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Task '{task_id}' is not valid for the {tier} journey.",
        )

    user_id = user["sub"]

    try:
        # Check if the task is auto-completed — those can't be unchecked
        journey_items = db.get_journey_progress(user_id)
        for item in journey_items:
            if item.get("task_id") == task_id:
                if item.get("auto_completed", False):
                    raise HTTPException(
                        status_code=400,
                        detail="Auto-completed tasks cannot be unchecked.",
                    )
                break

        db.delete_journey_task(user_id, task_id)

        return {"message": f"Task '{task_id}' uncompleted successfully."}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")
