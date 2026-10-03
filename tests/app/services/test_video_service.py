"""Unit tests for app.services.video_service.VideoService.

The service is an orchestrator over VideoMetadataDB, VideoProgressDB, and
CloudflareStreamService. Tests build the instance via __new__ and inject
mocked collaborators, so no real AWS/Cloudflare calls occur.

Async methods are driven via a small _run() helper rather than a pytest
plugin, matching the convention in tests/test_reconcile_stripe_sweep.py.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.video_service import VideoService
from app.models.videos import VideoStatus


def _run(coro):
    """Run a coroutine to completion (no pytest-asyncio plugin in this repo)."""
    return asyncio.new_event_loop().run_until_complete(coro)


def _published_item(video_id: str = "rec-1", status: str = "PUBLISHED") -> dict:
    return {
        "id": {"S": video_id},
        "title": {"S": "Secure APIs"},
        "slug": {"S": "secure-apis"},
        "description": {"S": "desc"},
        "cloudflareStreamId": {"S": "cf-abc"},
        "thumbnailUrl": {"S": "https://x/thumb.jpg"},
        "durationSeconds": {"N": "3600"},
        "instructor": {"S": "Damien"},
        "recordedAt": {"S": "2026-01-01"},
        "status": {"S": status},
        "tags": {"L": [{"S": "security"}]},
        "resources": {"L": []},
        "createdAt": {"S": "2026-01-01"},
        "updatedAt": {"S": "2026-01-02"},
        "publishedAt": {"S": "2026-01-02"},
    }


@pytest.fixture
def service():
    svc = VideoService.__new__(VideoService)
    svc._settings = MagicMock(public_images_bucket="imgs")
    svc._meta_db = MagicMock()
    svc._progress_db = MagicMock()
    svc._cf_service = MagicMock()
    return svc


class TestSaveProgress:
    def test_computes_percent_and_completion(self, service):
        resp = service.save_progress("u", "v", position=95.0, duration=100.0)
        assert resp.percent_complete == 95
        assert resp.completed is True
        service._progress_db.save_progress.assert_called_once()

    def test_below_threshold_not_completed(self, service):
        resp = service.save_progress("u", "v", position=50.0, duration=100.0)
        assert resp.percent_complete == 50
        assert resp.completed is False

    def test_exactly_90_percent_is_completed(self, service):
        resp = service.save_progress("u", "v", position=90.0, duration=100.0)
        assert resp.completed is True

    def test_position_exceeds_duration_raises_422(self, service):
        with pytest.raises(HTTPException) as exc:
            service.save_progress("u", "v", position=101.0, duration=100.0)
        assert exc.value.status_code == 422


class TestGetProgress:
    def test_returns_none_when_absent(self, service):
        service._progress_db.get_progress.return_value = None
        assert service.get_progress("u", "v") is None

    def test_parses_progress_item(self, service):
        service._progress_db.get_progress.return_value = {
            "positionSeconds": {"N": "120.5"},
            "durationSeconds": {"N": "600"},
            "percentComplete": {"N": "20"},
            "completed": {"BOOL": False},
            "lastWatchedAt": {"S": "2026-01-03"},
        }
        result = service.get_progress("u", "v")
        assert result["position_seconds"] == 120.5
        assert result["percent_complete"] == 20
        assert result["completed"] is False
        assert result["last_watched_at"] == "2026-01-03"


class TestGetVideoDetail:
    def test_returns_published_video(self, service):
        service._meta_db.get_video.return_value = _published_item()
        resp = _run(service.get_video_detail("rec-1", "u"))
        assert resp.id == "rec-1"
        assert resp.status == VideoStatus.PUBLISHED

    def test_falls_back_to_slug_lookup(self, service):
        service._meta_db.get_video.return_value = None
        service._meta_db.get_video_by_slug.return_value = _published_item()
        resp = _run(service.get_video_detail("secure-apis", "u"))
        assert resp.slug == "secure-apis"

    def test_not_found_raises_404(self, service):
        service._meta_db.get_video.return_value = None
        service._meta_db.get_video_by_slug.return_value = None
        with pytest.raises(HTTPException) as exc:
            _run(service.get_video_detail("nope", "u"))
        assert exc.value.status_code == 404

    def test_draft_video_hidden_from_members(self, service):
        service._meta_db.get_video.return_value = _published_item(status="DRAFT")
        with pytest.raises(HTTPException) as exc:
            _run(service.get_video_detail("rec-1", "u"))
        assert exc.value.status_code == 404


class TestPlaybackToken:
    def test_returns_token_for_published(self, service):
        service._meta_db.get_video.return_value = _published_item()
        service._cf_service.create_signed_token = AsyncMock(return_value="tok-123")
        resp = _run(service.get_playback_token("rec-1", "u"))
        assert resp.token == "tok-123"
        assert resp.expires_in_seconds == 14400

    def test_missing_video_raises_404(self, service):
        service._meta_db.get_video.return_value = None
        with pytest.raises(HTTPException) as exc:
            _run(service.get_playback_token("nope", "u"))
        assert exc.value.status_code == 404

    def test_draft_raises_404(self, service):
        service._meta_db.get_video.return_value = _published_item(status="DRAFT")
        with pytest.raises(HTTPException) as exc:
            _run(service.get_playback_token("rec-1", "u"))
        assert exc.value.status_code == 404


class TestTransitionStatus:
    def test_publish_sets_published_at(self, service):
        service._meta_db.get_video.return_value = _published_item(status="DRAFT")
        with patch("app.services.video_service.validate_transition"):
            resp = _run(service.transition_status("rec-1", VideoStatus.PUBLISHED))
        assert resp.status == VideoStatus.PUBLISHED
        service._meta_db.put_video.assert_called_once()

    def test_not_found_raises_404(self, service):
        service._meta_db.get_video.return_value = None
        with pytest.raises(HTTPException) as exc:
            _run(service.transition_status("nope", VideoStatus.PUBLISHED))
        assert exc.value.status_code == 404


class TestListVideosAdmin:
    def test_with_status_filter(self, service):
        service._meta_db.query_by_status.return_value = ([_published_item()], 1)
        videos, total = _run(service.list_videos_admin(status="PUBLISHED"))
        assert total == 1
        assert len(videos) == 1
        service._meta_db.query_by_status.assert_called_once()

    def test_without_status_filter(self, service):
        service._meta_db.query_all.return_value = ([_published_item()], 1)
        videos, total = _run(service.list_videos_admin())
        assert total == 1
        service._meta_db.query_all.assert_called_once()


class TestGetVideoAdmin:
    def test_returns_any_status(self, service):
        service._meta_db.get_video.return_value = _published_item(status="DRAFT")
        resp = _run(service.get_video_admin("rec-1"))
        assert resp.status == VideoStatus.DRAFT

    def test_not_found_raises_404(self, service):
        service._meta_db.get_video.return_value = None
        with pytest.raises(HTTPException) as exc:
            _run(service.get_video_admin("nope"))
        assert exc.value.status_code == 404


class TestHelpers:
    def test_build_progress_map(self, service):
        items = [
            {
                "SK": {"S": "VIDEO#rec-1"},
                "positionSeconds": {"N": "30"},
                "percentComplete": {"N": "25"},
                "completed": {"BOOL": False},
                "lastWatchedAt": {"S": "2026-01-05"},
            }
        ]
        result = service._build_progress_map(items)
        assert result["rec-1"]["percent_complete"] == 25
        assert result["rec-1"]["position_seconds"] == 30.0

    def test_continue_watching_excludes_completed_and_zero(self, service):
        items = [
            {"id": {"S": "a"}, "title": {"S": "A"}, "slug": {"S": "a"}, "tags": {"L": []}, "durationSeconds": {"N": "10"}},
            {"id": {"S": "b"}, "title": {"S": "B"}, "slug": {"S": "b"}, "tags": {"L": []}, "durationSeconds": {"N": "10"}},
            {"id": {"S": "c"}, "title": {"S": "C"}, "slug": {"S": "c"}, "tags": {"L": []}, "durationSeconds": {"N": "10"}},
        ]
        progress_map = {
            "a": {"percent_complete": 40, "completed": False, "last_watched_at": "2026-01-02"},
            "b": {"percent_complete": 100, "completed": True, "last_watched_at": "2026-01-03"},
            "c": {"percent_complete": 0, "completed": False, "last_watched_at": None},
        }
        result = service._build_continue_watching(progress_map, items)
        ids = [c.id for c in result]
        assert ids == ["a"]  # b completed, c at 0%

    def test_continue_watching_dedupes_and_sorts(self, service):
        items = [
            {"id": {"S": "a"}, "title": {"S": "A"}, "slug": {"S": "a"}, "tags": {"L": []}, "durationSeconds": {"N": "10"}},
            {"id": {"S": "a"}, "title": {"S": "A"}, "slug": {"S": "a"}, "tags": {"L": []}, "durationSeconds": {"N": "10"}},
            {"id": {"S": "d"}, "title": {"S": "D"}, "slug": {"S": "d"}, "tags": {"L": []}, "durationSeconds": {"N": "10"}},
        ]
        progress_map = {
            "a": {"percent_complete": 10, "completed": False, "last_watched_at": "2026-01-01"},
            "d": {"percent_complete": 50, "completed": False, "last_watched_at": "2026-02-01"},
        }
        result = service._build_continue_watching(progress_map, items)
        # Deduped (a once) and sorted by last_watched_at desc -> d, a
        assert [c.id for c in result] == ["d", "a"]


class TestGetCatalog:
    def test_builds_catalog_sections(self, service):
        service._meta_db.query_published.return_value = ([_published_item("rec-1")], 1)
        service._progress_db.get_user_video_progress.return_value = []
        resp = _run(service.get_catalog("u", page=1, page_size=20))
        assert resp.total_count == 1
        assert resp.page == 1
        assert len(resp.all_published) == 1

    def test_page_size_capped_at_100(self, service):
        service._meta_db.query_published.return_value = ([], 0)
        service._progress_db.get_user_video_progress.return_value = []
        resp = _run(service.get_catalog("u", page=1, page_size=500))
        assert resp.page_size == 100
