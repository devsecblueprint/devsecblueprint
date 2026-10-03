"""Unit tests for app.services.thumbnail_service.ThumbnailService.

sync_thumbnail is async; a _run helper drives it (no pytest-asyncio).
The Cloudflare service is mocked (AsyncMock methods), and the S3 client is
patched at construction time then reassigned for assertions.

Covered: no-bucket short-circuit, no-metadata / no-thumbnail-url, successful
upload + public URL, S3 ClientError returns "", key derivation with/without
tags (incl. sanitization), and public URL region fallback.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import thumbnail_service as mod
from app.services.thumbnail_service import ThumbnailService


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _make_service(bucket="imgs", region="us-east-2"):
    cf = MagicMock()
    cf.get_video_metadata = AsyncMock()
    cf.download_thumbnail = AsyncMock()
    s3 = MagicMock()
    s3.meta.region_name = region
    settings = MagicMock(public_images_bucket=bucket)
    with patch.object(mod.boto3, "client", return_value=s3):
        svc = ThumbnailService(settings, cf)
    svc._s3 = s3
    return svc, cf, s3


def _metadata(thumbnail_url="https://cf/thumb.jpg", tags=None):
    md = MagicMock()
    md.thumbnail_url = thumbnail_url
    md.tags = tags if tags is not None else []
    return md


class TestSyncThumbnail:
    def test_no_bucket_returns_empty(self):
        svc, cf, s3 = _make_service(bucket="")
        result = _run(svc.sync_thumbnail("vid", "rec-1"))
        assert result == ""
        cf.get_video_metadata.assert_not_called()

    def test_no_metadata_returns_empty(self):
        svc, cf, s3 = _make_service()
        cf.get_video_metadata.return_value = None
        result = _run(svc.sync_thumbnail("vid", "rec-1"))
        assert result == ""
        s3.put_object.assert_not_called()

    def test_no_thumbnail_url_returns_empty(self):
        svc, cf, s3 = _make_service()
        cf.get_video_metadata.return_value = _metadata(thumbnail_url="")
        result = _run(svc.sync_thumbnail("vid", "rec-1"))
        assert result == ""
        s3.put_object.assert_not_called()

    def test_success_without_tags(self):
        svc, cf, s3 = _make_service(bucket="imgs", region="us-west-1")
        cf.get_video_metadata.return_value = _metadata(tags=[])
        cf.download_thumbnail.return_value = b"bytes"
        result = _run(svc.sync_thumbnail("vid", "rec-1"))
        s3.put_object.assert_called_once()
        kwargs = s3.put_object.call_args.kwargs
        assert kwargs["Bucket"] == "imgs"
        assert kwargs["Key"] == "Recording_Thumbnails/rec-1.jpg"
        assert kwargs["Body"] == b"bytes"
        assert kwargs["ContentType"] == "image/jpeg"
        assert result == (
            "https://imgs.s3.us-west-1.amazonaws.com/Recording_Thumbnails/rec-1.jpg"
        )

    def test_success_with_tags_sanitized(self):
        svc, cf, s3 = _make_service()
        cf.get_video_metadata.return_value = _metadata(tags=["Cloud Security/AWS"])
        cf.download_thumbnail.return_value = b"bytes"
        result = _run(svc.sync_thumbnail("vid", "rec-1"))
        key = s3.put_object.call_args.kwargs["Key"]
        assert key == "Recording_Thumbnails/cloud-security-aws/rec-1.jpg"
        assert result.endswith("/Recording_Thumbnails/cloud-security-aws/rec-1.jpg")

    def test_s3_client_error_returns_empty(self):
        svc, cf, s3 = _make_service()
        cf.get_video_metadata.return_value = _metadata(tags=[])
        cf.download_thumbnail.return_value = b"bytes"
        s3.put_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "no"}}, "PutObject"
        )
        result = _run(svc.sync_thumbnail("vid", "rec-1"))
        assert result == ""


class TestDeriveS3Key:
    def test_without_tags(self):
        svc, _, _ = _make_service()
        assert svc._derive_s3_key("rec-1", []) == "Recording_Thumbnails/rec-1.jpg"

    def test_with_tags(self):
        svc, _, _ = _make_service()
        assert (
            svc._derive_s3_key("rec-1", ["Security"])
            == "Recording_Thumbnails/security/rec-1.jpg"
        )


class TestBuildPublicUrl:
    def test_region_fallback(self):
        svc, _, s3 = _make_service()
        s3.meta.region_name = None
        url = svc._build_public_url("Recording_Thumbnails/rec-1.jpg")
        assert url == (
            "https://imgs.s3.us-east-2.amazonaws.com/Recording_Thumbnails/rec-1.jpg"
        )
