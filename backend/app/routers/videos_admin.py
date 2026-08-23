"""Admin videos router — CRUD and lifecycle management.

Exposes endpoints for admin users to create, update, list, and
manage the lifecycle of videos.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9
"""

import json
import logging
from typing import Any

import boto3
from fastapi import APIRouter, Depends, Query

from app.auth.jwt import require_admin
from app.config import Settings
from app.dependencies import get_settings
from app.models.videos import (
    CreateVideoRequest,
    VideoResponse,
    StatusTransitionRequest,
    UpdateVideoRequest,
)
from app.services.cloudflare_stream_service import CloudflareStreamService
from app.services.video_service import VideoService
from app.services.video_sync_service import VideoSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/videos", tags=["videos-admin"])


# ------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------


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


@router.get("")
async def list_videos(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_admin),
    video_svc: VideoService = Depends(get_video_service),
) -> dict[str, Any]:
    """List all videos with optional status filter.

    Returns paginated list of videos with total count.
    Admin can filter by status (DRAFT, PROCESSING, READY,
    PUBLISHED, ARCHIVED).
    """
    videos, total = await video_svc.list_videos_admin(
        status=status, page=page, page_size=page_size
    )
    return {
        "recordings": [r.model_dump() for r in videos],
        "total_count": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=VideoResponse, status_code=201)
async def create_video(
    body: CreateVideoRequest,
    user: dict = Depends(require_admin),
    video_svc: VideoService = Depends(get_video_service),
) -> VideoResponse:
    """Create a new video in DRAFT status.

    Generates a unique slug from the title and sets initial
    metadata. The video starts in DRAFT status.
    """
    return await video_svc.create_video(body)


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: str,
    user: dict = Depends(require_admin),
    video_svc: VideoService = Depends(get_video_service),
) -> VideoResponse:
    """Get a single video's details (any status).

    Admin can view videos in any lifecycle status.
    """
    return await video_svc.get_video_admin(video_id)


@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: str,
    body: UpdateVideoRequest,
    user: dict = Depends(require_admin),
    video_svc: VideoService = Depends(get_video_service),
) -> VideoResponse:
    """Update video metadata (partial update).

    Only provided fields are updated. If title changes, a new
    slug is generated.
    """
    return await video_svc.update_video(video_id, body)


@router.post("/{video_id}/status", response_model=VideoResponse)
async def transition_status(
    video_id: str,
    body: StatusTransitionRequest,
    user: dict = Depends(require_admin),
    video_svc: VideoService = Depends(get_video_service),
) -> VideoResponse:
    """Transition a video's lifecycle status.

    Validates the transition against the allowed state machine.
    Returns 400 if the transition is not permitted.
    """
    return await video_svc.transition_status(video_id, body.target_status)


@router.get("/{video_id}/stream-status")
async def check_stream_status(
    video_id: str,
    user: dict = Depends(require_admin),
    video_svc: VideoService = Depends(get_video_service),
) -> VideoResponse:
    """Check Cloudflare Stream processing status.

    Queries Cloudflare for the current processing state of the
    associated video and updates the video if ready.
    """
    return await video_svc.check_processing_status(video_id)


@router.post("/sync")
async def sync_videos(
    user: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
    cf_service: CloudflareStreamService = Depends(get_cloudflare_service),
) -> dict[str, Any]:
    """Manually trigger sync of Cloudflare Stream videos.

    Lists all ready videos in the Cloudflare account and creates
    videos for any that don't already exist in the database.
    New videos are auto-published immediately.
    """
    sync_service = VideoSyncService(settings, cf_service)
    created = await sync_service.sync_all()
    return {"synced": created, "message": f"Synced {created} new videos"}
