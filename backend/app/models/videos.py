"""Pydantic models for the videos feature.

Defines request/response schemas, the VideoStatus enum,
and the allowed state transition map.

Requirements: 2.1, 2.2, 5.2, 5.11, 6.4
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class VideoStatus(str, Enum):
    """Lifecycle status of a video."""

    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    READY = "READY"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


ALLOWED_TRANSITIONS: dict[VideoStatus, set[VideoStatus]] = {
    VideoStatus.DRAFT: {VideoStatus.PROCESSING},
    VideoStatus.PROCESSING: {VideoStatus.READY},
    VideoStatus.READY: {
        VideoStatus.PUBLISHED,
        VideoStatus.ARCHIVED,
    },
    VideoStatus.PUBLISHED: {VideoStatus.ARCHIVED},
    VideoStatus.ARCHIVED: set(),
}


# ---------------------------------------------------------------------------
# Shared models
# ---------------------------------------------------------------------------


class ResourceLink(BaseModel):
    """A linked resource attached to a video (e.g., slide deck, repo)."""

    title: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., min_length=1)


class InstructorInfo(BaseModel):
    """An instructor/author with optional LinkedIn profile URL."""

    name: str = Field(..., min_length=1, max_length=200)
    linkedin_url: str | None = None


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class CreateVideoRequest(BaseModel):
    """Request body for creating a new video."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=5000)
    cloudflare_stream_id: str = Field(..., min_length=1, max_length=64)
    instructor: str = Field("", max_length=200)
    instructors: list[InstructorInfo] = Field(default_factory=list)
    recorded_at: str  # ISO 8601
    tags: list[str] = Field(default_factory=list, max_length=20)
    resources: list[ResourceLink] = Field(default_factory=list, max_length=30)
    thumbnail_url: str | None = None


class UpdateVideoRequest(BaseModel):
    """Request body for updating video metadata (partial update)."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=5000)
    instructor: str | None = Field(None, max_length=200)
    instructors: list[InstructorInfo] | None = None
    tags: list[str] | None = Field(None, max_length=20)
    resources: list[ResourceLink] | None = Field(None, max_length=30)
    thumbnail_url: str | None = None


class StatusTransitionRequest(BaseModel):
    """Request body for transitioning a video's status."""

    target_status: VideoStatus


class ProgressUpdateRequest(BaseModel):
    """Request body for saving playback progress."""

    position_seconds: float = Field(..., ge=0)
    duration_seconds: float = Field(..., gt=0, le=86400)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class VideoResponse(BaseModel):
    """Full video metadata response."""

    id: str
    title: str
    slug: str
    description: str
    thumbnail_url: str | None
    duration_seconds: int
    instructor: str
    instructors: list[InstructorInfo] = Field(default_factory=list)
    recorded_at: str
    status: VideoStatus
    tags: list[str]
    resources: list[ResourceLink]
    created_at: str
    updated_at: str
    published_at: str | None


class CatalogVideoItem(BaseModel):
    """A single video entry in the catalog response."""

    id: str
    title: str
    slug: str
    thumbnail_url: str | None
    duration_seconds: int
    tags: list[str]
    published_at: str
    progress_percent: int  # 0-100
    position_seconds: float | None  # For continue watching
    last_watched_at: str | None


class CatalogResponse(BaseModel):
    """Response for the member videos catalog endpoint."""

    continue_watching: list[CatalogVideoItem]
    latest: list[CatalogVideoItem]
    all_published: list[CatalogVideoItem]
    total_count: int
    page: int
    page_size: int


class PlaybackTokenResponse(BaseModel):
    """Response containing a signed Cloudflare Stream playback token."""

    token: str
    expires_in_seconds: int


class ProgressResponse(BaseModel):
    """Response for retrieving playback progress."""

    position_seconds: float | None
    duration_seconds: float | None
    percent_complete: int | None
    completed: bool | None
    last_watched_at: str | None


class ProgressSaveResponse(BaseModel):
    """Response after successfully saving playback progress."""

    percent_complete: int
    completed: bool
