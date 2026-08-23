"""Thumbnail service for recording thumbnails.

Handles downloading video thumbnails from Cloudflare Stream and
uploading them to the public images S3 bucket under the
recording_thumbnails/ prefix.

The thumbnail filename is derived from the video's tags in Cloudflare,
falling back to the recording ID if no tags are available.
"""

import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings
from app.services.cloudflare_stream_service import CloudflareStreamService

logger = logging.getLogger(__name__)

THUMBNAIL_PREFIX = "Recording_Thumbnails"
THUMBNAIL_CONTENT_TYPE = "image/jpeg"


class ThumbnailService:
    """Manages recording thumbnail upload to S3 public images bucket."""

    def __init__(
        self,
        settings: Settings,
        cf_service: CloudflareStreamService,
    ) -> None:
        self._bucket = settings.public_images_bucket
        self._cf_service = cf_service
        self._s3 = boto3.client("s3")

    async def sync_thumbnail(
        self,
        video_id: str,
        recording_id: str,
    ) -> str:
        """Download thumbnail from Cloudflare and upload to S3.

        The S3 key is derived from the video's tags in Cloudflare.
        If tags exist, the first tag is used as a folder prefix for
        organization (e.g., recording_thumbnails/security/rec-123.jpg).
        Otherwise, it's stored flat (recording_thumbnails/rec-123.jpg).

        Args:
            video_id: The Cloudflare Stream video identifier.
            recording_id: The DSB recording identifier.

        Returns:
            The public URL of the uploaded thumbnail.
        """
        if not self._bucket:
            logger.warning(
                "public_images_bucket not configured, skipping " "thumbnail sync"
            )
            return ""

        # Fetch video metadata to get thumbnail URL and tags
        metadata = await self._cf_service.get_video_metadata(video_id)
        if metadata is None or not metadata.thumbnail_url:
            logger.warning("No thumbnail available for video %s", video_id)
            return ""

        # Download thumbnail bytes from Cloudflare
        thumbnail_bytes = await self._cf_service.download_thumbnail(
            metadata.thumbnail_url
        )

        # Derive S3 key from tags
        s3_key = self._derive_s3_key(recording_id, metadata.tags)

        # Upload to S3
        try:
            self._s3.put_object(
                Bucket=self._bucket,
                Key=s3_key,
                Body=thumbnail_bytes,
                ContentType=THUMBNAIL_CONTENT_TYPE,
                CacheControl="public, max-age=86400",
            )
        except ClientError as e:
            logger.error(
                "Failed to upload thumbnail to S3: %s",
                e.response["Error"]["Code"],
            )
            return ""

        # Return the public URL
        return self._build_public_url(s3_key)

    def _derive_s3_key(self, recording_id: str, tags: list[str]) -> str:
        """Derive the S3 object key from recording ID and tags.

        If tags are present, the first tag is used as a subfolder
        for organizational purposes:
          Recording_Thumbnails/{first_tag}/{recording_id}.jpg

        Otherwise:
          Recording_Thumbnails/{recording_id}.jpg

        Args:
            recording_id: The recording identifier.
            tags: List of tags from the Cloudflare video metadata.

        Returns:
            The S3 object key string.
        """
        filename = f"{recording_id}.jpg"
        if tags:
            # Use first tag as subfolder, sanitized
            folder = tags[0].lower().replace(" ", "-").replace("/", "-")
            return f"{THUMBNAIL_PREFIX}/{folder}/{filename}"
        return f"{THUMBNAIL_PREFIX}/{filename}"

    def _build_public_url(self, s3_key: str) -> str:
        """Build the public URL for the uploaded thumbnail.

        Uses the regional S3 URL format matching the existing pattern:
        https://{bucket}.s3.{region}.amazonaws.com/{key}

        Args:
            s3_key: The S3 object key.

        Returns:
            The HTTPS URL for the thumbnail.
        """
        region = self._s3.meta.region_name or "us-east-2"
        return f"https://{self._bucket}.s3.{region}.amazonaws.com" f"/{s3_key}"
