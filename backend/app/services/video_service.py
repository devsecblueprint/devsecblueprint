"""Video service - business logic orchestrator.

Coordinates metadata DB, progress DB, and Cloudflare Stream service
to implement video lifecycle, catalog, playback, and progress.

Requirements: 2.4, 2.5, 2.6, 3.3, 3.6, 4.4, 5.7, 5.8, 5.12
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3
from fastapi import HTTPException

from app.config import Settings
from app.models.videos import (
    CatalogVideoItem,
    CatalogResponse,
    CreateVideoRequest,
    InstructorInfo,
    PlaybackTokenResponse,
    ProgressSaveResponse,
    VideoResponse,
    VideoStatus,
    ResourceLink,
    UpdateVideoRequest,
)
from app.services.cloudflare_stream_service import CloudflareStreamService
from app.services.video_metadata_db import VideoMetadataDB
from app.services.video_progress_db import VideoProgressDB
from app.services.slug_utils import ensure_unique_slug, generate_slug
from app.services.transition_utils import validate_transition

logger = logging.getLogger(__name__)


class VideoService:
    """Business logic orchestrator for video operations."""

    def __init__(
        self,
        settings: Settings,
        cf_service: CloudflareStreamService,
    ) -> None:
        self._settings = settings
        self._meta_db = VideoMetadataDB(settings)
        self._progress_db = VideoProgressDB(settings)
        self._cf_service = cf_service

    # ------------------------------------------------------------------
    # Member operations
    # ------------------------------------------------------------------

    async def get_catalog(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> CatalogResponse:
        """Retrieve the member video catalog.

        Args:
            user_id: The authenticated user's ID.
            page: 1-based page number for All Published.
            page_size: Items per page (max 100).

        Returns:
            CatalogResponse with continue_watching, latest,
            and all_published sections.
        """
        page_size = min(page_size, 100)

        # Get all published videos
        all_items, total_count = self._meta_db.query_published(page, page_size)

        # Get latest 10 published videos
        latest_items, _ = self._meta_db.query_published(1, 10)

        # Get user's video progress
        user_progress = self._progress_db.get_user_video_progress(user_id)
        progress_map = self._build_progress_map(user_progress)

        # Build continue watching (in-progress, not completed)
        continue_watching = self._build_continue_watching(
            progress_map, latest_items + all_items
        )

        # Build catalog items with progress
        latest = [self._to_catalog_item(item, progress_map) for item in latest_items]
        all_published = [
            self._to_catalog_item(item, progress_map) for item in all_items
        ]

        return CatalogResponse(
            continue_watching=continue_watching,
            latest=latest,
            all_published=all_published,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    async def get_video_detail(
        self,
        id_or_slug: str,
        user_id: str,
    ) -> VideoResponse:
        """Retrieve a single video's detail.

        Args:
            id_or_slug: Video ID or slug.
            user_id: The authenticated user's ID.

        Returns:
            Full video response.

        Raises:
            HTTPException: With 404 if not found or not PUBLISHED.
        """
        item = self._meta_db.get_video(id_or_slug)
        if item is None:
            item = self._meta_db.get_video_by_slug(id_or_slug)
        if item is None:
            raise HTTPException(
                status_code=404,
                detail="Video not found or unavailable",
            )

        status = item.get("status", {}).get("S", "")
        if status != VideoStatus.PUBLISHED.value:
            raise HTTPException(
                status_code=404,
                detail="Video not found or unavailable",
            )

        return self._to_video_response(item)

    async def get_playback_token(
        self,
        video_id: str,
        user_id: str,
    ) -> PlaybackTokenResponse:
        """Generate a signed Cloudflare playback token.

        Args:
            video_id: The video identifier.
            user_id: The authenticated user's ID.

        Returns:
            PlaybackTokenResponse with token and expiry.

        Raises:
            HTTPException: With 404 if not found/not published,
                502 if Cloudflare is unavailable.
        """
        item = self._meta_db.get_video(video_id)
        if item is None:
            raise HTTPException(
                status_code=404,
                detail="Video not found or unavailable",
            )

        status = item.get("status", {}).get("S", "")
        if status != VideoStatus.PUBLISHED.value:
            raise HTTPException(
                status_code=404,
                detail="Video not found or unavailable",
            )

        cf_video_id = item.get("cloudflareStreamId", {}).get("S", "")
        expiry_seconds = 14400  # 4 hours
        token = await self._cf_service.create_signed_token(cf_video_id, expiry_seconds)

        return PlaybackTokenResponse(token=token, expires_in_seconds=expiry_seconds)

    def get_progress(
        self,
        user_id: str,
        video_id: str,
    ) -> dict[str, Any] | None:
        """Retrieve user's playback progress for a video.

        Args:
            user_id: The user identifier.
            video_id: The video identifier.

        Returns:
            Progress dict or None if no progress exists.
        """
        item = self._progress_db.get_progress(user_id, video_id)
        if item is None:
            return None

        return {
            "position_seconds": float(item.get("positionSeconds", {}).get("N", "0")),
            "duration_seconds": float(item.get("durationSeconds", {}).get("N", "0")),
            "percent_complete": int(item.get("percentComplete", {}).get("N", "0")),
            "completed": item.get("completed", {}).get("BOOL", False),
            "last_watched_at": item.get("lastWatchedAt", {}).get("S", None),
        }

    def save_progress(
        self,
        user_id: str,
        video_id: str,
        position: float,
        duration: float,
    ) -> ProgressSaveResponse:
        """Save playback progress, calculating completion server-side.

        Args:
            user_id: The user identifier.
            video_id: The video identifier.
            position: Current playback position in seconds.
            duration: Total video duration in seconds.

        Returns:
            ProgressSaveResponse with calculated percent and completion.

        Raises:
            HTTPException: With 422 if position > duration.
        """
        if position > duration:
            raise HTTPException(
                status_code=422,
                detail="positionSeconds cannot exceed durationSeconds",
            )

        percent_complete = round(position / duration * 100)
        completed = percent_complete >= 90
        now = datetime.now(timezone.utc).isoformat()

        self._progress_db.save_progress(
            user_id,
            video_id,
            {
                "position_seconds": position,
                "duration_seconds": duration,
                "percent_complete": percent_complete,
                "completed": completed,
                "last_watched_at": now,
                "updated_at": now,
            },
        )

        return ProgressSaveResponse(
            percent_complete=percent_complete, completed=completed
        )

    # ------------------------------------------------------------------
    # Admin operations
    # ------------------------------------------------------------------

    async def create_video(
        self,
        data: CreateVideoRequest,
    ) -> VideoResponse:
        """Create a new video in DRAFT status.

        Performs a dynamic lookup against Cloudflare Stream to fetch
        video metadata (duration, thumbnail, tags). Tags from the
        Cloudflare video are merged with any tags provided in the
        request. The thumbnail is downloaded from Cloudflare and
        uploaded to the public images bucket under recording_thumbnails/.

        Args:
            data: The creation request body.

        Returns:
            Full video response for the created item.
        """
        video_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        slug = generate_slug(data.title)
        slug = ensure_unique_slug(slug, self._meta_db.slug_exists)

        # Dynamic lookup: fetch metadata from Cloudflare Stream
        duration_seconds = 0
        thumbnail_url = data.thumbnail_url or ""
        tags = list(data.tags)

        video_metadata = await self._cf_service.get_video_metadata(
            data.cloudflare_stream_id
        )
        if video_metadata is not None:
            duration_seconds = int(video_metadata.duration_seconds)

            # Merge Cloudflare tags with request tags (deduplicated)
            cf_tags = video_metadata.tags
            if cf_tags:
                existing = set(t.lower() for t in tags)
                for tag in cf_tags:
                    if tag.lower() not in existing:
                        tags.append(tag)
                        existing.add(tag.lower())

            # Use thumbnail_url from Cloudflare video meta (already
            # uploaded to S3 under Recording_Thumbnails/)
            if not thumbnail_url and video_metadata.thumbnail_url:
                thumbnail_url = video_metadata.thumbnail_url

        video: dict[str, Any] = {
            "id": video_id,
            "title": data.title,
            "slug": slug,
            "description": data.description,
            "cloudflare_stream_id": data.cloudflare_stream_id,
            "thumbnail_url": thumbnail_url,
            "duration_seconds": duration_seconds,
            "instructor": data.instructor,
            "recorded_at": data.recorded_at,
            "status": VideoStatus.DRAFT.value,
            "tags": tags,
            "resources": [{"title": r.title, "url": r.url} for r in data.resources],
            "created_at": now,
            "updated_at": now,
            "published_at": None,
        }

        self._meta_db.put_video(video)

        return VideoResponse(
            id=video_id,
            title=data.title,
            slug=slug,
            description=data.description,
            thumbnail_url=thumbnail_url or None,
            duration_seconds=duration_seconds,
            instructor=data.instructor,
            recorded_at=data.recorded_at,
            status=VideoStatus.DRAFT,
            tags=tags,
            resources=data.resources,
            created_at=now,
            updated_at=now,
            published_at=None,
        )

    async def update_video(
        self,
        video_id: str,
        data: UpdateVideoRequest,
    ) -> VideoResponse:
        """Update video metadata (partial update).

        Args:
            video_id: The video identifier.
            data: The update request body with optional fields.

        Returns:
            Full video response with updated fields.

        Raises:
            HTTPException: With 404 if video not found.
        """
        item = self._meta_db.get_video(video_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Video not found")

        # Build updated video dict from existing item
        video = self._item_to_dict(item)
        now = datetime.now(timezone.utc).isoformat()
        video["updated_at"] = now

        if data.title is not None:
            video["title"] = data.title
            slug = generate_slug(data.title)
            slug = ensure_unique_slug(slug, self._meta_db.slug_exists)
            video["slug"] = slug

        if data.description is not None:
            video["description"] = data.description

        if data.instructor is not None:
            video["instructor"] = data.instructor

        if data.tags is not None:
            video["tags"] = data.tags

        if data.resources is not None:
            video["resources"] = [
                {"title": r.title, "url": r.url} for r in data.resources
            ]

        if data.thumbnail_url is not None:
            video["thumbnail_url"] = data.thumbnail_url

        if data.instructors is not None:
            video["instructors"] = [
                {"name": i.name, "linkedin_url": i.linkedin_url}
                for i in data.instructors
            ]

        self._meta_db.put_video(video)
        return self._dict_to_response(video)

    async def transition_status(
        self,
        video_id: str,
        target_status: VideoStatus,
    ) -> VideoResponse:
        """Transition a video's lifecycle status.

        Args:
            video_id: The video identifier.
            target_status: The desired target status.

        Returns:
            Full video response with updated status.

        Raises:
            HTTPException: With 404 if not found, 400 if invalid transition.
        """
        item = self._meta_db.get_video(video_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Video not found")

        current_status = VideoStatus(item.get("status", {}).get("S", ""))
        validate_transition(current_status, target_status)

        video = self._item_to_dict(item)
        now = datetime.now(timezone.utc).isoformat()
        video["status"] = target_status.value
        video["updated_at"] = now

        if target_status == VideoStatus.PUBLISHED:
            video["published_at"] = now

        self._meta_db.put_video(video)
        return self._dict_to_response(video)

    async def check_processing_status(
        self,
        video_id: str,
    ) -> VideoResponse:
        """Check Cloudflare processing status and update if ready.

        When the video is ready, fetches duration and syncs the
        thumbnail from Cloudflare to S3 if not already set.

        Args:
            video_id: The video identifier.

        Returns:
            Full video response with current status.

        Raises:
            HTTPException: With 404 if not found.
        """
        item = self._meta_db.get_video(video_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Video not found")

        cf_video_id = item.get("cloudflareStreamId", {}).get("S", "")
        video = self._item_to_dict(item)

        # Dynamic lookup from Cloudflare
        video_metadata = await self._cf_service.get_video_metadata(cf_video_id)

        if video_metadata is not None and video_metadata.status == "ready":
            video["duration_seconds"] = int(video_metadata.duration_seconds)
            video["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Use thumbnail from Cloudflare meta if not already set
            if not video.get("thumbnail_url"):
                if video_metadata.thumbnail_url:
                    video["thumbnail_url"] = video_metadata.thumbnail_url

        self._meta_db.put_video(video)
        return self._dict_to_response(video)

    async def get_video_admin(
        self,
        video_id: str,
    ) -> VideoResponse:
        """Retrieve a video for admin (any status).

        Args:
            video_id: The video identifier.

        Returns:
            Full video response.

        Raises:
            HTTPException: With 404 if not found.
        """
        item = self._meta_db.get_video(video_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Video not found")
        return self._to_video_response(item)

    async def list_videos_admin(
        self,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[VideoResponse], int]:
        """List videos for admin with optional status filter.

        Args:
            status: Optional status filter.
            page: 1-based page number.
            page_size: Items per page.

        Returns:
            Tuple of (videos list, total count).
        """
        if status:
            items, total = self._meta_db.query_by_status(status, page, page_size)
        else:
            items, total = self._meta_db.query_all(page, page_size)

        videos = [self._to_video_response(item) for item in items]
        return videos, total

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_progress_map(
        self, progress_items: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Build a map of video_id -> progress data."""
        progress_map: dict[str, dict[str, Any]] = {}
        for item in progress_items:
            sk = item.get("SK", {}).get("S", "")
            video_id = sk.replace("VIDEO#", "")
            progress_map[video_id] = {
                "position_seconds": float(
                    item.get("positionSeconds", {}).get("N", "0")
                ),
                "percent_complete": int(item.get("percentComplete", {}).get("N", "0")),
                "completed": item.get("completed", {}).get("BOOL", False),
                "last_watched_at": item.get("lastWatchedAt", {}).get("S", None),
            }
        return progress_map

    def _build_continue_watching(
        self,
        progress_map: dict[str, dict[str, Any]],
        all_items: list[dict[str, Any]],
    ) -> list[CatalogVideoItem]:
        """Build the Continue Watching list from progress data."""
        # Deduplicate items by ID
        seen: set[str] = set()
        unique_items: list[dict[str, Any]] = []
        for item in all_items:
            item_id = item.get("id", {}).get("S", "")
            if item_id not in seen:
                seen.add(item_id)
                unique_items.append(item)

        continue_watching: list[CatalogVideoItem] = []
        for item in unique_items:
            item_id = item.get("id", {}).get("S", "")
            progress = progress_map.get(item_id)
            if progress is None:
                continue
            percent = progress.get("percent_complete", 0)
            completed = progress.get("completed", False)
            if percent > 0 and not completed:
                continue_watching.append(self._to_catalog_item(item, progress_map))

        # Sort by last_watched_at descending
        continue_watching.sort(
            key=lambda x: x.last_watched_at or "",
            reverse=True,
        )
        return continue_watching

    def _to_catalog_item(
        self,
        item: dict[str, Any],
        progress_map: dict[str, dict[str, Any]],
    ) -> CatalogVideoItem:
        """Convert a DynamoDB item to a CatalogVideoItem."""
        item_id = item.get("id", {}).get("S", "")
        progress = progress_map.get(item_id, {})

        tags_list = item.get("tags", {}).get("L", [])
        tags = [t.get("S", "") for t in tags_list]

        return CatalogVideoItem(
            id=item_id,
            title=item.get("title", {}).get("S", ""),
            slug=item.get("slug", {}).get("S", ""),
            thumbnail_url=item.get("thumbnailUrl", {}).get("S", "") or None,
            duration_seconds=int(item.get("durationSeconds", {}).get("N", "0")),
            tags=tags,
            published_at=item.get("publishedAt", {}).get(
                "S",
                item.get("GSI1SK", {}).get("S", ""),
            ),
            progress_percent=progress.get("percent_complete", 0),
            position_seconds=progress.get("position_seconds"),
            last_watched_at=progress.get("last_watched_at"),
        )

    def _to_video_response(self, item: dict[str, Any]) -> VideoResponse:
        """Convert a DynamoDB item to a VideoResponse."""
        tags_list = item.get("tags", {}).get("L", [])
        tags = [t.get("S", "") for t in tags_list]

        resources_list = item.get("resources", {}).get("L", [])
        resources = [
            ResourceLink(
                title=r.get("M", {}).get("title", {}).get("S", ""),
                url=r.get("M", {}).get("url", {}).get("S", ""),
            )
            for r in resources_list
        ]

        instructors_list = item.get("instructors", {}).get("L", [])
        instructors = [
            InstructorInfo(
                name=i.get("M", {}).get("name", {}).get("S", ""),
                linkedin_url=i.get("M", {}).get("linkedin_url", {}).get("S", "")
                or None,
            )
            for i in instructors_list
        ]

        thumbnail = item.get("thumbnailUrl", {}).get("S", "")

        return VideoResponse(
            id=item.get("id", {}).get("S", ""),
            title=item.get("title", {}).get("S", ""),
            slug=item.get("slug", {}).get("S", ""),
            description=item.get("description", {}).get("S", ""),
            thumbnail_url=thumbnail or None,
            duration_seconds=int(item.get("durationSeconds", {}).get("N", "0")),
            instructor=item.get("instructor", {}).get("S", ""),
            instructors=instructors,
            recorded_at=item.get("recordedAt", {}).get("S", ""),
            status=VideoStatus(item.get("status", {}).get("S", "DRAFT")),
            tags=tags,
            resources=resources,
            created_at=item.get("createdAt", {}).get("S", ""),
            updated_at=item.get("updatedAt", {}).get("S", ""),
            published_at=item.get("publishedAt", {}).get("S", None),
        )

    def _item_to_dict(self, item: dict[str, Any]) -> dict[str, Any]:
        """Convert a DynamoDB item to a plain dict for put_video."""
        tags_list = item.get("tags", {}).get("L", [])
        tags = [t.get("S", "") for t in tags_list]

        resources_list = item.get("resources", {}).get("L", [])
        resources = [
            {
                "title": r.get("M", {}).get("title", {}).get("S", ""),
                "url": r.get("M", {}).get("url", {}).get("S", ""),
            }
            for r in resources_list
        ]

        return {
            "id": item.get("id", {}).get("S", ""),
            "title": item.get("title", {}).get("S", ""),
            "slug": item.get("slug", {}).get("S", ""),
            "description": item.get("description", {}).get("S", ""),
            "cloudflare_stream_id": item.get("cloudflareStreamId", {}).get("S", ""),
            "thumbnail_url": item.get("thumbnailUrl", {}).get("S", ""),
            "duration_seconds": int(item.get("durationSeconds", {}).get("N", "0")),
            "instructor": item.get("instructor", {}).get("S", ""),
            "instructors": [
                {
                    "name": i.get("M", {}).get("name", {}).get("S", ""),
                    "linkedin_url": i.get("M", {}).get("linkedin_url", {}).get("S", "")
                    or None,
                }
                for i in item.get("instructors", {}).get("L", [])
            ],
            "recorded_at": item.get("recordedAt", {}).get("S", ""),
            "status": item.get("status", {}).get("S", "DRAFT"),
            "tags": tags,
            "resources": resources,
            "created_at": item.get("createdAt", {}).get("S", ""),
            "updated_at": item.get("updatedAt", {}).get("S", ""),
            "published_at": item.get("publishedAt", {}).get("S", None),
        }

    def _dict_to_response(self, video: dict[str, Any]) -> VideoResponse:
        """Convert a plain dict to a VideoResponse."""
        resources = [
            ResourceLink(title=r["title"], url=r["url"])
            for r in video.get("resources", [])
        ]

        instructors = [
            InstructorInfo(
                name=i.get("name", ""),
                linkedin_url=i.get("linkedin_url") or None,
            )
            for i in video.get("instructors", [])
        ]

        thumbnail = video.get("thumbnail_url", "")

        return VideoResponse(
            id=video["id"],
            title=video["title"],
            slug=video["slug"],
            description=video.get("description", ""),
            thumbnail_url=thumbnail or None,
            duration_seconds=video.get("duration_seconds", 0),
            instructor=video["instructor"],
            instructors=instructors,
            recorded_at=video["recorded_at"],
            status=VideoStatus(video["status"]),
            tags=video.get("tags", []),
            resources=resources,
            created_at=video["created_at"],
            updated_at=video["updated_at"],
            published_at=video.get("published_at"),
        )

    async def _sync_thumbnail(
        self,
        cf_thumbnail_url: str,
        video_id: str,
        tags: list[str],
    ) -> str:
        """Download thumbnail from Cloudflare and upload to S3.

        Stores the thumbnail in the public images bucket under
        recording_thumbnails/, using the video's tags to derive
        the subfolder structure.

        Args:
            cf_thumbnail_url: Cloudflare's auto-generated thumbnail URL.
            video_id: The DSB video identifier.
            tags: Tags from the Cloudflare video metadata.

        Returns:
            The public S3 URL of the uploaded thumbnail, or empty
            string if upload fails.
        """
        bucket = self._settings.public_images_bucket
        if not bucket:
            logger.warning(
                "public_images_bucket not configured, skipping " "thumbnail sync"
            )
            return ""

        if not cf_thumbnail_url:
            return ""

        try:
            # Download thumbnail from Cloudflare
            thumbnail_bytes = await self._cf_service.download_thumbnail(
                cf_thumbnail_url
            )

            # Derive S3 key from tags
            filename = f"{video_id}.jpg"
            if tags:
                folder = tags[0].lower().replace(" ", "-").replace("/", "-")
                s3_key = f"Recording_Thumbnails/{folder}/{filename}"
            else:
                s3_key = f"Recording_Thumbnails/{filename}"

            # Upload to S3
            s3 = boto3.client("s3")
            s3.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=thumbnail_bytes,
                ContentType="image/jpeg",
                CacheControl="public, max-age=86400",
            )

            # Build URL with regional S3 endpoint
            region = s3.meta.region_name or "us-east-2"
            return f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
        except Exception:
            logger.exception(
                "Failed to sync thumbnail for video %s",
                video_id,
            )
            return ""
