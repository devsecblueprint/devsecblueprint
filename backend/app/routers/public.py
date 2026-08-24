"""Public credential verification and video preview router.

Provides unauthenticated endpoints for third parties (employers, etc.)
to verify DSB credentials by credential_id, and for unauthenticated
visitors to browse published video previews.

NEVER exposes: email, user_id, review session details, internal identifiers,
Cloudflare Stream IDs, or playback tokens.

Requirements: 10.1, 10.2, 10.3, 10.4
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import Settings
from app.dependencies import get_settings
from app.models.certification import PublicCredentialResponse
from app.services.certification.db import CertificationDB
from app.services.certification.pathway_config import get_pathway as get_pathway_config
from app.services.video_metadata_db import VideoMetadataDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/credentials/{credential_id}", response_model=PublicCredentialResponse)
async def verify_credential(
    credential_id: str, settings: Settings = Depends(get_settings)
) -> PublicCredentialResponse:
    """Verify a credential by its public credential_id.

    No authentication required. Returns only publicly-safe information:
    holder name, pathway name, issuance/expiration dates, and status.

    Returns 404 if the credential does not exist.
    """
    db = CertificationDB(settings)

    # Look up credential via GSI (no user_id needed)
    credential = db.get_credential_by_id(credential_id)
    if credential is None:
        raise HTTPException(status_code=404, detail="Credential not found")

    # Resolve pathway display name from config
    pathway_id = credential["pathway_id"]
    pathway = get_pathway_config(pathway_id)
    pathway_name = (
        pathway["display_name"] if pathway else pathway_id.replace("-", " ").title()
    )

    return PublicCredentialResponse(
        credential_id=credential["credential_id"],
        holder_name=credential["full_name_at_issuance"],
        pathway_name=pathway_name,
        issued_at=credential["issued_at"],
        expires_at=credential["expires_at"],
        credential_status=credential["credential_status"],
    )


# ---------------------------------------------------------------------------
# Public Video Preview Models
# ---------------------------------------------------------------------------


class PublicVideoItem(BaseModel):
    """Public-safe video summary for preview listing."""

    id: str
    title: str
    slug: str
    description: str
    thumbnail_url: str | None
    duration_seconds: int
    tags: list[str]
    instructor: str
    instructors: list[dict[str, str]] = Field(default_factory=list)
    recorded_at: str
    published_at: str | None


class PublicVideosResponse(BaseModel):
    """Response for public video listing endpoint."""

    videos: list[PublicVideoItem]
    total_count: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Public Video Preview Endpoints
# ---------------------------------------------------------------------------


@router.get("/videos", response_model=PublicVideosResponse)
async def list_public_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    settings: Settings = Depends(get_settings),
) -> PublicVideosResponse:
    """List published videos for public preview.

    No authentication required. Returns only publicly-safe metadata
    (title, description, tags, duration, instructors) for published
    videos. Does NOT expose Cloudflare Stream IDs or playback tokens.

    Designed for search engine indexing and unauthenticated browsing.
    """
    db = VideoMetadataDB(settings)
    items, total_count = db.query_published(page, page_size)

    videos: list[PublicVideoItem] = []
    for item in items:
        thumbnail = item.get("thumbnailUrl", {}).get("S", "")
        instructors_raw = item.get("instructors", {}).get("L", [])
        instructors = [
            {
                "name": i.get("M", {}).get("name", {}).get("S", ""),
                "linkedin_url": i.get("M", {}).get("linkedin_url", {}).get("S", ""),
            }
            for i in instructors_raw
        ]

        videos.append(
            PublicVideoItem(
                id=item.get("id", {}).get("S", ""),
                title=item.get("title", {}).get("S", ""),
                slug=item.get("slug", {}).get("S", ""),
                description=item.get("description", {}).get("S", ""),
                thumbnail_url=thumbnail or None,
                duration_seconds=int(item.get("durationSeconds", {}).get("N", "0")),
                tags=[t.get("S", "") for t in item.get("tags", {}).get("L", [])],
                instructor=item.get("instructor", {}).get("S", ""),
                instructors=instructors,
                recorded_at=item.get("recordedAt", {}).get("S", ""),
                published_at=item.get("publishedAt", {}).get("S", None),
            )
        )

    return PublicVideosResponse(
        videos=videos,
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@router.get("/videos/{slug}", response_model=PublicVideoItem)
async def get_public_video(
    slug: str,
    settings: Settings = Depends(get_settings),
) -> PublicVideoItem:
    """Get a single published video's public metadata by slug.

    No authentication required. Returns only publicly-safe metadata.
    Returns 404 if video does not exist or is not PUBLISHED.
    """
    db = VideoMetadataDB(settings)
    item = db.get_video_by_slug(slug)

    if item is None:
        raise HTTPException(status_code=404, detail="Video not found")

    status = item.get("status", {}).get("S", "")
    if status != "PUBLISHED":
        raise HTTPException(status_code=404, detail="Video not found")

    thumbnail = item.get("thumbnailUrl", {}).get("S", "")
    instructors_raw = item.get("instructors", {}).get("L", [])
    instructors = [
        {
            "name": i.get("M", {}).get("name", {}).get("S", ""),
            "linkedin_url": i.get("M", {}).get("linkedin_url", {}).get("S", ""),
        }
        for i in instructors_raw
    ]

    return PublicVideoItem(
        id=item.get("id", {}).get("S", ""),
        title=item.get("title", {}).get("S", ""),
        slug=item.get("slug", {}).get("S", ""),
        description=item.get("description", {}).get("S", ""),
        thumbnail_url=thumbnail or None,
        duration_seconds=int(item.get("durationSeconds", {}).get("N", "0")),
        tags=[t.get("S", "") for t in item.get("tags", {}).get("L", [])],
        instructor=item.get("instructor", {}).get("S", ""),
        instructors=instructors,
        recorded_at=item.get("recordedAt", {}).get("S", ""),
        published_at=item.get("publishedAt", {}).get("S", None),
    )
