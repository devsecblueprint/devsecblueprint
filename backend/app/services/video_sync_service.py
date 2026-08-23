"""Video sync service — auto-imports videos from Cloudflare Stream.

Periodically lists all videos from the Cloudflare Stream account and
creates/publishes videos for any that are ready but not yet
tracked in DynamoDB. This eliminates the need for manual admin creation.

Videos are matched by their Cloudflare Stream video ID. If a video exists
in Cloudflare but not in the videos table, it gets auto-created and
published. Title and instructor are derived from the video's meta fields.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3

from app.config import Settings
from app.dependencies import get_settings
from app.models.videos import VideoStatus
from app.services.cloudflare_stream_service import (
    CloudflareStreamService,
    VideoMetadata,
)
from app.services.video_metadata_db import VideoMetadataDB
from app.services.slug_utils import ensure_unique_slug, generate_slug

logger = logging.getLogger(__name__)


class VideoSyncService:
    """Auto-syncs Cloudflare Stream videos into the videos catalog."""

    def __init__(
        self,
        settings: Settings,
        cf_service: CloudflareStreamService,
    ) -> None:
        self._settings = settings
        self._meta_db = VideoMetadataDB(settings)
        self._cf_service = cf_service

    async def sync_all(self) -> int:
        """Sync all ready videos from Cloudflare into the catalog.

        For each video in Cloudflare Stream:
        - If it's in 'ready' state and not already in the videos
          table, create a video and auto-publish it.
        - If it already exists, skip it.

        Returns:
            Number of new videos created.
        """
        videos = await self._cf_service.list_all_videos()
        if not videos:
            logger.info("No videos found in Cloudflare Stream")
            return 0

        # Get all existing cloudflare stream IDs in our DB
        existing_ids = self._get_existing_stream_ids()

        created = 0
        for video in videos:
            if video.status != "ready":
                continue
            if video.video_id in existing_ids:
                continue

            try:
                self._create_and_publish(video)
                created += 1
                logger.info(
                    "Auto-synced video for stream ID %s",
                    video.video_id,
                )
            except Exception:
                logger.exception("Failed to sync video %s", video.video_id)

        if created > 0:
            logger.info("Synced %d new videos from Cloudflare", created)
        return created

    def _get_existing_stream_ids(self) -> set[str]:
        """Get all Cloudflare Stream IDs already in the videos table."""
        try:
            items, _ = self._meta_db.query_all(page=1, page_size=1000)
            stream_ids: set[str] = set()
            for item in items:
                cf_id = item.get("cloudflareStreamId", {}).get("S", "")
                if cf_id:
                    stream_ids.add(cf_id)
            return stream_ids
        except Exception:
            logger.exception("Failed to query existing videos")
            return set()

    def _create_and_publish(self, video: VideoMetadata) -> None:
        """Create a video from video metadata and publish it.

        Derives title from the video's meta.name field or tags.
        Sets instructor from meta.instructor or defaults to 'DSB Team'.

        Args:
            video: The VideoMetadata from Cloudflare.
        """
        video_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Derive title from video metadata
        title = self._derive_title(video)
        slug = generate_slug(title)
        slug = ensure_unique_slug(slug, self._meta_db.slug_exists)

        # Derive instructor
        instructor = self._derive_instructor(video)

        video_entry: dict[str, Any] = {
            "id": video_id,
            "title": title,
            "slug": slug,
            "description": "",
            "cloudflare_stream_id": video.video_id,
            "thumbnail_url": video.thumbnail_url or "",
            "duration_seconds": int(video.duration_seconds),
            "instructor": instructor,
            "recorded_at": now,
            "status": VideoStatus.READY.value,
            "tags": video.tags,
            "resources": [],
            "created_at": now,
            "updated_at": now,
            "published_at": None,
        }

        self._meta_db.put_video(video_entry)

    def _derive_title(self, video: VideoMetadata) -> str:
        """Derive a video title from video metadata.

        Checks (in order):
        1. Video name from Cloudflare meta.name field
        2. First tag as a fallback title
        3. Generic title with video ID prefix

        Args:
            video: The VideoMetadata from Cloudflare.

        Returns:
            A human-readable title string.
        """
        if video.name:
            # Clean up file extensions if present
            name = video.name
            for ext in (".mp4", ".mkv", ".mov", ".webm", ".avi"):
                if name.lower().endswith(ext):
                    name = name[: -len(ext)]
            return name.replace("_", " ").replace("-", " ").strip()

        if video.tags:
            return video.tags[0].replace("-", " ").title()

        return f"Builder Session {video.video_id[:8]}"

    def _derive_instructor(self, video: VideoMetadata) -> str:
        """Derive instructor from video metadata.

        Checks for an 'instructor' key in tags, falls back to
        'DSB Team'.

        Args:
            video: The VideoMetadata from Cloudflare.

        Returns:
            Instructor name string.
        """
        # Look for instructor in tags (format: "instructor:Name")
        for tag in video.tags:
            if tag.lower().startswith("instructor:"):
                return tag.split(":", 1)[1].strip()
        return "DSB Team"


async def run_video_sync() -> None:
    """Background job entry point for video sync.

    Called by APScheduler to auto-import Cloudflare videos.
    """
    settings = get_settings()

    if not settings.cloudflare_account_id or not settings.cloudflare_secret_name:
        logger.debug("Cloudflare not configured, skipping video sync")
        return

    # Get API token from secrets manager
    api_token = _get_cloudflare_token(settings)
    if not api_token:
        logger.warning("No Cloudflare API token available, skipping sync")
        return

    cf_service = CloudflareStreamService(
        account_id=settings.cloudflare_account_id,
        api_token=api_token,
    )

    sync_service = VideoSyncService(settings, cf_service)
    await sync_service.sync_all()


def _get_cloudflare_token(settings: Settings) -> str:
    """Retrieve Cloudflare API token from Secrets Manager."""
    try:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=settings.cloudflare_secret_name)
        secret_data = json.loads(response["SecretString"])
        return secret_data.get("secret_key", "")
    except Exception:
        logger.exception("Failed to retrieve Cloudflare API token")
        return ""
