"""Member videos router — catalog, playback, and progress.

Exposes endpoints for authenticated members with VIDEO_RECORDINGS
entitlement to browse videos, obtain playback tokens, and
manage their watch progress.

Requirements: 3.1, 3.4, 3.5, 3.6, 3.7, 3.8, 4.1, 4.2, 4.3, 4.4,
              4.8, 5.3, 5.11, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7,
              6.8, 11.6
"""

import json
import logging
from typing import Any

import boto3
from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.jwt import get_current_user
from app.config import Settings
from app.dependencies import get_settings
from app.models.videos import (
    CatalogResponse,
    PlaybackTokenResponse,
    ProgressResponse,
    ProgressSaveResponse,
    ProgressUpdateRequest,
    VideoResponse,
)
from app.services.cloudflare_stream_service import CloudflareStreamService
from app.services.entitlement_service import EntitlementService
from app.services.video_service import VideoService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/videos", tags=["videos"])


# ------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------


def get_entitlement_service(
    settings: Settings = Depends(get_settings),
) -> EntitlementService:
    """Provide an EntitlementService instance."""
    return EntitlementService(settings)


def get_cloudflare_service(
    settings: Settings = Depends(get_settings),
) -> CloudflareStreamService:
    """Provide a CloudflareStreamService instance."""
    return CloudflareStreamService(
        account_id=settings.cloudflare_account_id,
        api_token=_get_cloudflare_token(settings),
    )


def get_video_service(
    settings: Settings = Depends(get_settings),
    cf_service: CloudflareStreamService = Depends(get_cloudflare_service),
) -> VideoService:
    """Provide a VideoService instance."""
    return VideoService(settings, cf_service)


def _get_cloudflare_token(settings: Settings) -> str:
    """Retrieve Cloudflare API token from Secrets Manager."""
    if not settings.cloudflare_secret_name:
        return ""
    try:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=settings.cloudflare_secret_name)
        secret_data = json.loads(response["SecretString"])
        return secret_data.get("secret_key", "")
    except Exception:
        logger.exception("Failed to retrieve Cloudflare API token")
        return ""


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------


@router.get("", response_model=CatalogResponse)
async def get_catalog(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    entitlement_svc: EntitlementService = Depends(get_entitlement_service),
    video_svc: VideoService = Depends(get_video_service),
) -> CatalogResponse:
    """Get the member video catalog.

    Returns published videos organized into Continue Watching,
    Latest, and All Published sections with pagination.
    """
    entitlement_svc.require_video_recordings(user)
    user_id = user["sub"]
    return await video_svc.get_catalog(user_id, page, page_size)


@router.get("/{id_or_slug}", response_model=VideoResponse)
async def get_video(
    id_or_slug: str,
    user: dict = Depends(get_current_user),
    entitlement_svc: EntitlementService = Depends(get_entitlement_service),
    video_svc: VideoService = Depends(get_video_service),
) -> VideoResponse:
    """Get a single video's detail by ID or slug.

    Returns full metadata for a PUBLISHED video. Returns 404
    if the video does not exist or is not published.
    """
    entitlement_svc.require_video_recordings(user)
    user_id = user["sub"]
    return await video_svc.get_video_detail(id_or_slug, user_id)


@router.post("/{video_id}/playback", response_model=PlaybackTokenResponse)
async def request_playback(
    video_id: str,
    user: dict = Depends(get_current_user),
    entitlement_svc: EntitlementService = Depends(get_entitlement_service),
    video_svc: VideoService = Depends(get_video_service),
) -> PlaybackTokenResponse:
    """Generate a signed Cloudflare Stream playback token.

    Verifies authentication, entitlement, and video status
    before generating a time-limited signed token (max 4 hours).
    """
    entitlement_svc.require_video_recordings(user)
    user_id = user["sub"]
    return await video_svc.get_playback_token(video_id, user_id)


@router.get("/{video_id}/progress", response_model=ProgressResponse)
async def get_progress(
    video_id: str,
    user: dict = Depends(get_current_user),
    entitlement_svc: EntitlementService = Depends(get_entitlement_service),
    video_svc: VideoService = Depends(get_video_service),
) -> ProgressResponse:
    """Get the user's playback progress for a video.

    Returns position, duration, percent complete, completion flag,
    and last watched timestamp.
    """
    entitlement_svc.require_video_recordings(user)
    user_id = user["sub"]
    progress = video_svc.get_progress(user_id, video_id)

    if progress is None:
        return ProgressResponse(
            position_seconds=None,
            duration_seconds=None,
            percent_complete=None,
            completed=None,
            last_watched_at=None,
        )

    return ProgressResponse(
        position_seconds=progress["position_seconds"],
        duration_seconds=progress["duration_seconds"],
        percent_complete=progress["percent_complete"],
        completed=progress["completed"],
        last_watched_at=progress["last_watched_at"],
    )


@router.put("/{video_id}/progress", response_model=ProgressSaveResponse)
async def save_progress(
    video_id: str,
    body: ProgressUpdateRequest,
    user: dict = Depends(get_current_user),
    entitlement_svc: EntitlementService = Depends(get_entitlement_service),
    video_svc: VideoService = Depends(get_video_service),
) -> ProgressSaveResponse:
    """Save or update playback progress for a video.

    Accepts position and duration; server calculates percent complete
    and marks video as completed when >= 90%.
    Rejects invalid inputs (position > duration).
    """
    entitlement_svc.require_video_recordings(user)
    user_id = user["sub"]

    if body.position_seconds > body.duration_seconds:
        raise HTTPException(
            status_code=422,
            detail="positionSeconds cannot exceed durationSeconds",
        )

    return video_svc.save_progress(
        user_id,
        video_id,
        body.position_seconds,
        body.duration_seconds,
    )
