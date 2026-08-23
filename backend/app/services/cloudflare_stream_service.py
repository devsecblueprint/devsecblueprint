"""Cloudflare Stream API client service.

Encapsulates all interactions with the Cloudflare Stream API for
video validation, status checks, signed token generation, and
dynamic metadata lookup (duration, thumbnail, tags).

Videos are registered in Cloudflare Stream automatically (external
upload pipeline). This service performs dynamic lookups to retrieve
video metadata at recording creation time. Thumbnails are derived
from Cloudflare's auto-generated thumbnail URL and stored in the
public images S3 bucket under recording_thumbnails/.

Requirements: 7.1, 7.2, 7.3, 7.5, 7.6
"""

import logging
import time
from typing import Any

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class VideoMetadata:
    """Metadata fetched from a Cloudflare Stream video."""

    def __init__(
        self,
        video_id: str,
        duration_seconds: float,
        thumbnail_url: str,
        status: str,
        require_signed_urls: bool,
        tags: list[str],
    ) -> None:
        self.video_id = video_id
        self.duration_seconds = duration_seconds
        self.thumbnail_url = thumbnail_url
        self.status = status
        self.require_signed_urls = require_signed_urls
        self.tags = tags
        self.name: str = ""


class CloudflareStreamService:
    """Encapsulated client for Cloudflare Stream API operations."""

    def __init__(self, account_id: str, api_token: str) -> None:
        self._account_id = account_id
        self._api_token = api_token
        self._base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}"
        self._client = httpx.AsyncClient(
            timeout=10.0,
            headers={"Authorization": f"Bearer {api_token}"},
        )

    async def get_video_metadata(self, video_id: str) -> VideoMetadata | None:
        """Fetch full video metadata from Cloudflare Stream.

        Performs a dynamic lookup to retrieve duration, thumbnail URL,
        processing status, signed URL requirement, and tags.

        Args:
            video_id: The Cloudflare Stream video identifier.

        Returns:
            VideoMetadata object, or None if the video doesn't exist.
        """
        try:
            response = await self._client.get(f"{self._base_url}/stream/{video_id}")
            if response.status_code != 200:
                return None

            data = response.json()
            if not data.get("success"):
                return None

            result = data.get("result", {})
            duration = result.get("duration", 0)
            status_obj = result.get("status", {})
            state = status_obj.get("state", "error")
            require_signed = result.get("requireSignedURLs", False)
            meta = result.get("meta", {})
            tags = self._extract_tags(meta)

            # Prefer thumbnail_url from video meta (S3 URL set by
            # the admin), fall back to Cloudflare's auto-generated one
            thumbnail = meta.get("thumbnail_url", result.get("thumbnail", ""))

            vm = VideoMetadata(
                video_id=video_id,
                duration_seconds=duration,
                thumbnail_url=thumbnail,
                status=state,
                require_signed_urls=require_signed,
                tags=tags,
            )
            vm.name = meta.get("name", result.get("name", ""))
            return vm
        except httpx.HTTPError:
            logger.exception("Failed to fetch video metadata for %s", video_id)
            return None

    async def validate_video(self, video_id: str) -> bool:
        """Check if a video exists in the account.

        Args:
            video_id: The Cloudflare Stream video identifier.

        Returns:
            True if the video exists, False otherwise.
        """
        metadata = await self.get_video_metadata(video_id)
        return metadata is not None

    async def get_video_status(self, video_id: str) -> str:
        """Return processing state of a video.

        Args:
            video_id: The Cloudflare Stream video identifier.

        Returns:
            Status string: queued, inprogress, ready, error.

        Raises:
            HTTPException: With status 502 if Cloudflare is unreachable.
        """
        try:
            response = await self._client.get(f"{self._base_url}/stream/{video_id}")
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                status = result.get("status", {})
                return status.get("state", "error")
            return "error"
        except httpx.HTTPError:
            logger.exception("Failed to get video status for %s", video_id)
            raise HTTPException(
                status_code=502,
                detail="Cloudflare Stream service unavailable",
            )

    async def get_video_duration(self, video_id: str) -> int:
        """Fetch the video duration in seconds from Cloudflare.

        Args:
            video_id: The Cloudflare Stream video identifier.

        Returns:
            Duration in whole seconds, or 0 if unavailable.
        """
        metadata = await self.get_video_metadata(video_id)
        if metadata is None:
            return 0
        return int(metadata.duration_seconds)

    async def get_thumbnail_url(self, video_id: str) -> str:
        """Get the Cloudflare auto-generated thumbnail URL for a video.

        This URL can be downloaded and re-uploaded to S3 for public
        serving from the recording_thumbnails/ folder.

        Args:
            video_id: The Cloudflare Stream video identifier.

        Returns:
            The thumbnail URL string, or empty string if unavailable.
        """
        metadata = await self.get_video_metadata(video_id)
        if metadata is None:
            return ""
        return metadata.thumbnail_url

    async def get_video_tags(self, video_id: str) -> list[str]:
        """Retrieve tags from the video's metadata in Cloudflare.

        Tags are stored in the video's meta object. This is used to
        derive the thumbnail filename and categorization.

        Args:
            video_id: The Cloudflare Stream video identifier.

        Returns:
            List of tag strings from the video metadata.
        """
        metadata = await self.get_video_metadata(video_id)
        if metadata is None:
            return []
        return metadata.tags

    async def create_signed_token(
        self,
        video_id: str,
        expiry_seconds: int = 3600,
    ) -> str:
        """Generate a signed playback token.

        The video must have requireSignedURLs enabled in Cloudflare
        for this token to be the only way to access the stream.

        Args:
            video_id: The Cloudflare Stream video identifier.
            expiry_seconds: Token validity duration in seconds.

        Returns:
            The signed token string for use in playback URLs.

        Raises:
            HTTPException: With status 502 if token generation fails.
        """
        exp = int(time.time()) + expiry_seconds

        try:
            response = await self._client.post(
                f"{self._base_url}/stream/{video_id}/token",
                json={
                    "exp": exp,
                    "accessRules": [
                        {"type": "any", "action": "allow"},
                    ],
                },
            )
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                token = result.get("token", "")
                if token:
                    return token
            logger.error(
                "Token generation failed for video %s: %s",
                video_id,
                response.text,
            )
            raise HTTPException(
                status_code=502,
                detail="Playback temporarily unavailable",
            )
        except httpx.HTTPError:
            logger.exception("Failed to create signed token for %s", video_id)
            raise HTTPException(
                status_code=502,
                detail="Playback temporarily unavailable",
            )

    async def download_thumbnail(self, thumbnail_url: str) -> bytes:
        """Download thumbnail bytes from Cloudflare's thumbnail URL.

        Used to re-upload the thumbnail to the public images S3 bucket.

        Args:
            thumbnail_url: The Cloudflare-generated thumbnail URL.

        Returns:
            Raw image bytes.

        Raises:
            HTTPException: With 502 if download fails.
        """
        try:
            response = await self._client.get(thumbnail_url)
            if response.status_code == 200:
                return response.content
            logger.error("Thumbnail download failed: %s", response.status_code)
            raise HTTPException(
                status_code=502,
                detail="Failed to download video thumbnail",
            )
        except httpx.HTTPError:
            logger.exception("Failed to download thumbnail from %s", thumbnail_url)
            raise HTTPException(
                status_code=502,
                detail="Failed to download video thumbnail",
            )

    def _extract_tags(self, meta: dict[str, Any]) -> list[str]:
        """Extract tags from Cloudflare video meta object.

        Cloudflare stores custom metadata as key-value pairs in the
        meta field. Tags can be stored as a comma-separated string
        under the 'tags' key, or as individual keys prefixed with
        'tag-'.

        Args:
            meta: The meta dict from the Cloudflare API response.

        Returns:
            List of tag strings.
        """
        tags: list[str] = []

        # Check for comma-separated tags field
        tags_str = meta.get("tags", "")
        if tags_str:
            tags.extend(t.strip() for t in tags_str.split(",") if t.strip())

        # Check for tag-prefixed keys
        for key, value in meta.items():
            if key.startswith("tag-") and value:
                tags.append(str(value).strip())

        return tags

    async def list_all_videos(self) -> list[VideoMetadata]:
        """List all videos in the Cloudflare Stream account.

        Paginates through all results to build a complete list.

        Returns:
            List of VideoMetadata objects for all videos in the account.
        """
        all_videos: list[VideoMetadata] = []
        endpoint = f"{self._base_url}/stream"

        try:
            # Cloudflare Stream API paginates; loop until no more
            while endpoint:
                response = await self._client.get(endpoint)
                if response.status_code != 200:
                    break

                data = response.json()
                if not data.get("success"):
                    break

                results = data.get("result", [])
                for item in results:
                    video_id = item.get("uid", "")
                    duration = item.get("duration", 0)
                    status_obj = item.get("status", {})
                    state = status_obj.get("state", "error")
                    require_signed = item.get("requireSignedURLs", False)
                    meta = item.get("meta", {})
                    tags = self._extract_tags(meta)
                    thumbnail = meta.get("thumbnail_url", item.get("thumbnail", ""))
                    # Store the video name in the first tag position
                    # for title derivation if available
                    name = meta.get("name", "")

                    vm = VideoMetadata(
                        video_id=video_id,
                        duration_seconds=duration,
                        thumbnail_url=thumbnail,
                        status=state,
                        require_signed_urls=require_signed,
                        tags=tags,
                    )
                    vm.name = name
                    all_videos.append(vm)

                # Check for next page via range header
                result_info = data.get("result_info", {})
                total = result_info.get("total_count", 0)
                if len(all_videos) >= total:
                    break
                # No cursor-based pagination in Stream API; use
                # the count-based approach
                endpoint = ""

        except httpx.HTTPError:
            logger.exception("Failed to list videos from Cloudflare")

        return all_videos
