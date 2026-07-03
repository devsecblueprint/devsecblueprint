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

All routes require JWT authentication. Reset requires admin.

Requirements: 4.2
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

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

    # Save progress
    try:
        db.save_progress(user_id, body.content_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")

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
