"""Edge metadata for public video pages (link previews).

Link-preview crawlers (Discord, Slack, LinkedIn, X, ...) don't run JavaScript,
and every ``/videos/preview/<slug>`` URL is served from one static HTML file.
To give crawlers per-video Open Graph tags, the CloudFront viewer-request
function looks the slug up in a CloudFront Key Value Store. This service keeps
that store in sync with published videos.

Store layout:
    key:   video slug
    value: compact JSON ``{"t": title, "d": description, "i": thumbnail_url}``
           (the store limits values to 1 KB)

Only public-safe fields of PUBLISHED videos are ever written.

Note: the KeyValueStore API is signed with SigV4A, which requires the
``awscrt`` package alongside boto3.
"""

import json
import logging
import re
from typing import Any, Callable

import boto3
from botocore.exceptions import ClientError

from app.config import Settings
from app.services.video_metadata_db import VideoMetadataDB

logger = logging.getLogger(__name__)

MAX_VALUE_BYTES = 1024
MAX_TITLE_CHARS = 200
MAX_DESCRIPTION_CHARS = 300
MAX_THUMBNAIL_CHARS = 300
MAX_CONFLICT_RETRIES = 4
BACKFILL_PAGE_SIZE = 100

_WHITESPACE_RE = re.compile(r"\s+")


def _clean(text: str | None) -> str:
    """Collapse whitespace so the description fits as compactly as possible."""
    return _WHITESPACE_RE.sub(" ", text or "").strip()


def build_value(video: dict[str, Any]) -> str:
    """Build the compact JSON value for a video, within the 1 KB store limit.

    The JSON is ASCII-only (non-ASCII is ``\\uXXXX``-escaped) so the character
    count equals the byte count. The description is shortened first, then the
    title, until the value fits.
    """
    title = _clean(video.get("title"))[:MAX_TITLE_CHARS]
    description = _clean(video.get("description"))[:MAX_DESCRIPTION_CHARS]
    thumbnail = (video.get("thumbnail_url") or "").strip()
    if len(thumbnail) > MAX_THUMBNAIL_CHARS:
        thumbnail = ""

    def encode() -> str:
        return json.dumps(
            {"t": title, "d": description, "i": thumbnail},
            separators=(",", ":"),
            ensure_ascii=True,
        )

    value = encode()
    while len(value) > MAX_VALUE_BYTES and description:
        description = description[: int(len(description) * 0.8)].rstrip()
        value = encode()
    while len(value) > MAX_VALUE_BYTES and len(title) > 20:
        title = title[: int(len(title) * 0.8)].rstrip()
        value = encode()
    if len(value) > MAX_VALUE_BYTES:
        thumbnail = ""
        value = encode()
    return value


def _is_conflict(error: ClientError) -> bool:
    return error.response.get("Error", {}).get("Code") == "ConflictException"


class EdgeMetadataService:
    """Keeps the CloudFront Key Value Store in sync with published videos."""

    def __init__(self, settings: Settings, client: Any = None) -> None:
        self._settings = settings
        self._client = client

    @property
    def enabled(self) -> bool:
        return bool(self._settings.video_edge_kvs_arn)

    @property
    def _arn(self) -> str:
        return self._settings.video_edge_kvs_arn

    def _kvs(self) -> Any:
        if self._client is None:
            self._client = boto3.client(
                "cloudfront-keyvaluestore", region_name="us-east-1"
            )
        return self._client

    def _write(self, op: Callable[[str], Any]) -> None:
        """Run a mutating call with a fresh ETag, retrying on write conflicts."""
        client = self._kvs()
        for attempt in range(MAX_CONFLICT_RETRIES):
            etag = client.describe_key_value_store(KvsARN=self._arn)["ETag"]
            try:
                op(etag)
                return
            except ClientError as e:
                if _is_conflict(e) and attempt < MAX_CONFLICT_RETRIES - 1:
                    continue
                raise

    # ------------------------------------------------------------------
    # Per-video operations (never raise; failures are logged)
    # ------------------------------------------------------------------

    def upsert_video(self, video: dict[str, Any]) -> bool:
        """Store a published video's public metadata. Returns True on success."""
        if not self.enabled:
            return False
        slug = video.get("slug", "")
        if not slug or str(video.get("status", "")) != "PUBLISHED":
            return False
        try:
            value = build_value(video)
            self._write(
                lambda etag: self._kvs().put_key(
                    KvsARN=self._arn, Key=slug, Value=value, IfMatch=etag
                )
            )
            return True
        except Exception:
            logger.exception("Edge metadata upsert failed for slug %s", slug)
            return False

    def remove_video(self, slug: str) -> bool:
        """Remove a video's metadata. A missing key counts as success."""
        if not self.enabled or not slug:
            return False
        try:
            self._write(
                lambda etag: self._kvs().delete_key(
                    KvsARN=self._arn, Key=slug, IfMatch=etag
                )
            )
            return True
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            if code in ("ResourceNotFoundException", "ValidationException"):
                return True
            logger.exception("Edge metadata removal failed for slug %s", slug)
            return False
        except Exception:
            logger.exception("Edge metadata removal failed for slug %s", slug)
            return False

    # ------------------------------------------------------------------
    # Backfill
    # ------------------------------------------------------------------

    def backfill(self, settings: Settings | None = None) -> int:
        """Write metadata for every PUBLISHED video. Safe to repeat.

        Raises:
            RuntimeError: If the store is not configured.
        """
        if not self.enabled:
            raise RuntimeError("VIDEO_EDGE_KVS_ARN is not configured")

        db = VideoMetadataDB(settings or self._settings)
        count = 0
        page = 1
        while True:
            items, _total = db.query_published(page, BACKFILL_PAGE_SIZE)
            for item in items:
                video = {
                    "slug": item.get("slug", {}).get("S", ""),
                    "title": item.get("title", {}).get("S", ""),
                    "description": item.get("description", {}).get("S", ""),
                    "thumbnail_url": item.get("thumbnailUrl", {}).get("S", ""),
                    "status": item.get("status", {}).get("S", ""),
                }
                if self.upsert_video(video):
                    count += 1
            if len(items) < BACKFILL_PAGE_SIZE:
                break
            page += 1
        logger.info("Edge metadata backfill complete: %d videos", count)
        return count
