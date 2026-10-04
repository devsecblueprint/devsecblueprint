"""Unit tests for app.services.video_sync_service.

VideoSyncService builds a VideoMetadataDB(settings) in __init__, so we patch
mod.VideoMetadataDB at construction and reassign svc._meta_db to a MagicMock for
per-test control. The Cloudflare service is a MagicMock with an AsyncMock
list_all_videos. sync_all is async; a _run helper drives it (no pytest-asyncio).

Covers sync_all (empty, skip non-ready, skip existing, create new, per-video
failure isolation), _get_existing_stream_ids (success + query error),
_create_and_publish (put_video payload + slug uniqueness), _derive_title
(name with extension / tags / fallback), _derive_instructor (tag / default),
run_video_sync (not configured, no token, happy path), and
_get_cloudflare_token (success + error).
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import video_sync_service as mod
from app.services.cloudflare_stream_service import VideoMetadata
from app.models.videos import VideoStatus


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _make_settings():
    s = MagicMock()
    s.videos_table = "test-videos"
    s.cloudflare_account_id = "acct"
    s.cloudflare_secret_name = "cf-secret"
    return s


def _make_service():
    cf = MagicMock()
    cf.list_all_videos = AsyncMock()
    with patch.object(mod, "VideoMetadataDB") as MetaDB:
        svc = mod.VideoSyncService(_make_settings(), cf)
    svc._meta_db = MagicMock()
    return svc, cf


def _vm(video_id="v1", status="ready", name="", tags=None, duration=42.7, thumb=""):
    vm = VideoMetadata(
        video_id=video_id,
        duration_seconds=duration,
        thumbnail_url=thumb,
        status=status,
        require_signed_urls=False,
        tags=tags if tags is not None else [],
    )
    vm.name = name
    return vm


class TestSyncAll:
    def test_no_videos_returns_zero(self):
        svc, cf = _make_service()
        cf.list_all_videos.return_value = []
        assert _run(svc.sync_all()) == 0
        svc._meta_db.put_video.assert_not_called()

    def test_skips_non_ready_and_existing(self):
        svc, cf = _make_service()
        cf.list_all_videos.return_value = [
            _vm(video_id="not-ready", status="inprogress", name="A"),
            _vm(video_id="already", status="ready", name="B"),
        ]
        svc._get_existing_stream_ids = MagicMock(return_value={"already"})
        created = _run(svc.sync_all())
        assert created == 0
        svc._meta_db.put_video.assert_not_called()

    def test_creates_new_ready_video(self):
        svc, cf = _make_service()
        cf.list_all_videos.return_value = [_vm(video_id="new1", name="Fresh Video")]
        svc._get_existing_stream_ids = MagicMock(return_value=set())
        svc._meta_db.slug_exists.return_value = False
        created = _run(svc.sync_all())
        assert created == 1
        svc._meta_db.put_video.assert_called_once()

    def test_failure_on_one_video_is_isolated(self):
        svc, cf = _make_service()
        cf.list_all_videos.return_value = [
            _vm(video_id="good", name="Good"),
            _vm(video_id="bad", name="Bad"),
        ]
        svc._get_existing_stream_ids = MagicMock(return_value=set())
        # First create succeeds, second raises
        svc._create_and_publish = MagicMock(side_effect=[None, RuntimeError("boom")])
        created = _run(svc.sync_all())
        assert created == 1
        assert svc._create_and_publish.call_count == 2


class TestGetExistingStreamIds:
    def test_collects_cloudflare_stream_ids(self):
        svc, _ = _make_service()
        items = [
            {"cloudflareStreamId": {"S": "cf-1"}},
            {"cloudflareStreamId": {"S": "cf-2"}},
            {"cloudflareStreamId": {"S": ""}},  # ignored
            {},  # ignored
        ]
        svc._meta_db.query_all.return_value = (items, 4)
        result = svc._get_existing_stream_ids()
        assert result == {"cf-1", "cf-2"}
        svc._meta_db.query_all.assert_called_once_with(page=1, page_size=1000)

    def test_query_error_returns_empty_set(self):
        svc, _ = _make_service()
        svc._meta_db.query_all.side_effect = RuntimeError("db down")
        assert svc._get_existing_stream_ids() == set()


class TestCreateAndPublish:
    def test_builds_video_entry_and_calls_put(self):
        svc, _ = _make_service()
        svc._meta_db.slug_exists.return_value = False
        video = _vm(
            video_id="cf-xyz",
            name="Intro to AWS",
            tags=["instructor:Jane Doe", "cloud"],
            duration=90.9,
            thumb="https://cf/t.jpg",
        )
        svc._create_and_publish(video)

        svc._meta_db.put_video.assert_called_once()
        entry = svc._meta_db.put_video.call_args.args[0]
        assert entry["title"] == "Intro to AWS"
        assert entry["slug"] == "intro-to-aws"
        assert entry["cloudflare_stream_id"] == "cf-xyz"
        assert entry["thumbnail_url"] == "https://cf/t.jpg"
        assert entry["duration_seconds"] == 90  # int truncation
        assert entry["instructor"] == "Jane Doe"
        assert entry["status"] == VideoStatus.READY.value
        assert entry["tags"] == ["instructor:Jane Doe", "cloud"]
        assert entry["published_at"] is None
        # a UUID id was assigned
        assert isinstance(entry["id"], str) and len(entry["id"]) == 36

    def test_slug_uniqueness_applied(self):
        svc, _ = _make_service()
        # base slug taken once, then free
        svc._meta_db.slug_exists.side_effect = lambda s: s == "intro-to-aws"
        svc._create_and_publish(_vm(name="Intro to AWS"))
        entry = svc._meta_db.put_video.call_args.args[0]
        assert entry["slug"] == "intro-to-aws-1"


class TestDeriveTitle:
    def test_name_with_extension_cleaned(self):
        svc, _ = _make_service()
        assert svc._derive_title(_vm(name="My_Cool-Clip.MP4")) == "My Cool Clip"

    def test_falls_back_to_first_tag(self):
        svc, _ = _make_service()
        assert svc._derive_title(_vm(name="", tags=["cloud-security"])) == (
            "Cloud Security"
        )

    def test_generic_fallback_uses_video_id_prefix(self):
        svc, _ = _make_service()
        title = svc._derive_title(_vm(video_id="abcdef123456", name="", tags=[]))
        assert title == "Builder Session abcdef12"


class TestDeriveInstructor:
    def test_instructor_tag(self):
        svc, _ = _make_service()
        assert svc._derive_instructor(_vm(tags=["instructor:Alice"])) == "Alice"

    def test_default_when_no_tag(self):
        svc, _ = _make_service()
        assert svc._derive_instructor(_vm(tags=["cloud"])) == "DSB Team"


class TestRunVideoSync:
    def test_skips_when_not_configured(self):
        settings = _make_settings()
        settings.cloudflare_account_id = ""
        with patch.object(mod, "get_settings", return_value=settings):
            # Should return without constructing anything
            _run(mod.run_video_sync())

    def test_skips_when_no_token(self):
        settings = _make_settings()
        with (
            patch.object(mod, "get_settings", return_value=settings),
            patch.object(mod, "_get_cloudflare_token", return_value=""),
            patch.object(mod, "CloudflareStreamService") as CF,
        ):
            _run(mod.run_video_sync())
        CF.assert_not_called()

    def test_happy_path_runs_sync(self):
        settings = _make_settings()
        fake_sync = MagicMock()
        fake_sync.sync_all = AsyncMock(return_value=3)
        with (
            patch.object(mod, "get_settings", return_value=settings),
            patch.object(mod, "_get_cloudflare_token", return_value="tok"),
            patch.object(mod, "CloudflareStreamService") as CF,
            patch.object(mod, "VideoSyncService", return_value=fake_sync) as VS,
        ):
            _run(mod.run_video_sync())
        CF.assert_called_once_with(account_id="acct", api_token="tok")
        VS.assert_called_once()
        fake_sync.sync_all.assert_awaited_once()


class TestGetCloudflareToken:
    def test_success_reads_secret_key(self):
        settings = _make_settings()
        client = MagicMock()
        client.get_secret_value.return_value = {
            "SecretString": json.dumps({"secret_key": "tok-123"})
        }
        with patch.object(mod.boto3, "client", return_value=client):
            token = mod._get_cloudflare_token(settings)
        assert token == "tok-123"
        client.get_secret_value.assert_called_once_with(SecretId="cf-secret")

    def test_error_returns_empty(self):
        settings = _make_settings()
        with patch.object(mod.boto3, "client", side_effect=RuntimeError("no aws")):
            assert mod._get_cloudflare_token(settings) == ""
