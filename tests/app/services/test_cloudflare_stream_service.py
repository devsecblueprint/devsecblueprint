"""Unit tests for app.services.cloudflare_stream_service.CloudflareStreamService.

All methods are async and drive httpx.AsyncClient. A _run helper executes the
coroutines (no pytest-asyncio). The service builds its own httpx.AsyncClient in
__init__; we construct the service then reassign svc._client to an AsyncMock so
each HTTP call (get/post) is controllable and its arguments assertable.

Covers get_video_metadata (success / non-200 / success=false / HTTPError),
validate_video, get_video_status (ready / error / HTTPError->502),
get_video_duration, get_thumbnail_url, get_video_tags, create_signed_token
(success / no-token / non-200 / HTTPError), download_thumbnail (success /
non-200 / HTTPError), _extract_tags, and list_all_videos (success / non-200 /
success=false / HTTPError).
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import HTTPException

from app.services.cloudflare_stream_service import (
    CloudflareStreamService,
    VideoMetadata,
)

ACCOUNT = "acct123"
BASE = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}"


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _make_service():
    svc = CloudflareStreamService(account_id=ACCOUNT, api_token="tok")
    svc._client = AsyncMock()
    return svc


def _resp(status_code=200, json_data=None, content=b"", text=""):
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data if json_data is not None else {}
    r.content = content
    r.text = text
    return r


def _video_result(**overrides):
    result = {
        "duration": 123.4,
        "status": {"state": "ready"},
        "requireSignedURLs": True,
        "thumbnail": "https://cf/auto-thumb.jpg",
        "meta": {"name": "My Video", "tags": "aws, security"},
    }
    result.update(overrides)
    return result


class TestGetVideoMetadata:
    def test_success_parses_fields(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(
            json_data={"success": True, "result": _video_result()}
        )
        md = _run(svc.get_video_metadata("vid1"))
        assert isinstance(md, VideoMetadata)
        assert md.video_id == "vid1"
        assert md.duration_seconds == 123.4
        assert md.status == "ready"
        assert md.require_signed_urls is True
        assert md.name == "My Video"
        assert md.tags == ["aws", "security"]
        # Prefers meta.thumbnail_url when present; else Cloudflare auto thumb
        assert md.thumbnail_url == "https://cf/auto-thumb.jpg"
        svc._client.get.assert_awaited_once_with(f"{BASE}/stream/vid1")

    def test_prefers_meta_thumbnail_url(self):
        svc = _make_service()
        result = _video_result(
            meta={"thumbnail_url": "https://s3/custom.jpg", "name": "x"}
        )
        svc._client.get.return_value = _resp(
            json_data={"success": True, "result": result}
        )
        md = _run(svc.get_video_metadata("vid1"))
        assert md.thumbnail_url == "https://s3/custom.jpg"

    def test_non_200_returns_none(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(status_code=404)
        assert _run(svc.get_video_metadata("vid1")) is None

    def test_success_false_returns_none(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(json_data={"success": False})
        assert _run(svc.get_video_metadata("vid1")) is None

    def test_http_error_returns_none(self):
        svc = _make_service()
        svc._client.get.side_effect = httpx.HTTPError("boom")
        assert _run(svc.get_video_metadata("vid1")) is None


class TestValidateVideo:
    def test_true_when_metadata_present(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(
            json_data={"success": True, "result": _video_result()}
        )
        assert _run(svc.validate_video("vid1")) is True

    def test_false_when_missing(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(status_code=404)
        assert _run(svc.validate_video("vid1")) is False


class TestGetVideoStatus:
    def test_returns_state(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(
            json_data={"result": {"status": {"state": "inprogress"}}}
        )
        assert _run(svc.get_video_status("vid1")) == "inprogress"

    def test_non_200_returns_error(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(status_code=500)
        assert _run(svc.get_video_status("vid1")) == "error"

    def test_http_error_raises_502(self):
        svc = _make_service()
        svc._client.get.side_effect = httpx.HTTPError("down")
        with pytest.raises(HTTPException) as exc:
            _run(svc.get_video_status("vid1"))
        assert exc.value.status_code == 502


class TestGetVideoDuration:
    def test_returns_int_seconds(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(
            json_data={"success": True, "result": _video_result(duration=99.9)}
        )
        assert _run(svc.get_video_duration("vid1")) == 99

    def test_zero_when_missing(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(status_code=404)
        assert _run(svc.get_video_duration("vid1")) == 0


class TestGetThumbnailUrl:
    def test_returns_url(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(
            json_data={"success": True, "result": _video_result()}
        )
        assert _run(svc.get_thumbnail_url("vid1")) == "https://cf/auto-thumb.jpg"

    def test_empty_when_missing(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(status_code=404)
        assert _run(svc.get_thumbnail_url("vid1")) == ""


class TestGetVideoTags:
    def test_returns_tags(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(
            json_data={"success": True, "result": _video_result()}
        )
        assert _run(svc.get_video_tags("vid1")) == ["aws", "security"]

    def test_empty_when_missing(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(status_code=404)
        assert _run(svc.get_video_tags("vid1")) == []


class TestCreateSignedToken:
    def test_success_returns_token_and_posts_access_rules(self):
        svc = _make_service()
        svc._client.post.return_value = _resp(
            json_data={"result": {"token": "signed-abc"}}
        )
        token = _run(svc.create_signed_token("vid1", expiry_seconds=600))
        assert token == "signed-abc"
        svc._client.post.assert_awaited_once()
        args, kwargs = svc._client.post.call_args
        assert args[0] == f"{BASE}/stream/vid1/token"
        body = kwargs["json"]
        assert body["accessRules"] == [{"type": "any", "action": "allow"}]
        assert isinstance(body["exp"], int)

    def test_no_token_in_result_raises_502(self):
        svc = _make_service()
        svc._client.post.return_value = _resp(json_data={"result": {}}, text="empty")
        with pytest.raises(HTTPException) as exc:
            _run(svc.create_signed_token("vid1"))
        assert exc.value.status_code == 502

    def test_non_200_raises_502(self):
        svc = _make_service()
        svc._client.post.return_value = _resp(status_code=403, text="forbidden")
        with pytest.raises(HTTPException) as exc:
            _run(svc.create_signed_token("vid1"))
        assert exc.value.status_code == 502

    def test_http_error_raises_502(self):
        svc = _make_service()
        svc._client.post.side_effect = httpx.HTTPError("down")
        with pytest.raises(HTTPException) as exc:
            _run(svc.create_signed_token("vid1"))
        assert exc.value.status_code == 502


class TestDownloadThumbnail:
    def test_success_returns_bytes(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(content=b"imgdata")
        assert _run(svc.download_thumbnail("https://cf/t.jpg")) == b"imgdata"
        svc._client.get.assert_awaited_once_with("https://cf/t.jpg")

    def test_non_200_raises_502(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(status_code=404)
        with pytest.raises(HTTPException) as exc:
            _run(svc.download_thumbnail("https://cf/t.jpg"))
        assert exc.value.status_code == 502

    def test_http_error_raises_502(self):
        svc = _make_service()
        svc._client.get.side_effect = httpx.HTTPError("down")
        with pytest.raises(HTTPException) as exc:
            _run(svc.download_thumbnail("https://cf/t.jpg"))
        assert exc.value.status_code == 502


class TestExtractTags:
    def test_comma_separated_and_prefixed(self):
        svc = _make_service()
        meta = {"tags": "one, two ,", "tag-extra": "three", "tag-empty": ""}
        tags = svc._extract_tags(meta)
        assert tags == ["one", "two", "three"]

    def test_empty_meta(self):
        svc = _make_service()
        assert svc._extract_tags({}) == []


class TestListAllVideos:
    def test_success_builds_list(self):
        svc = _make_service()
        results = [
            {
                "uid": "v1",
                "duration": 10,
                "status": {"state": "ready"},
                "requireSignedURLs": False,
                "meta": {"name": "First", "tags": "a,b"},
                "thumbnail": "https://cf/v1.jpg",
            },
            {
                "uid": "v2",
                "duration": 20,
                "status": {"state": "inprogress"},
                "meta": {},
            },
        ]
        svc._client.get.return_value = _resp(
            json_data={
                "success": True,
                "result": results,
                "result_info": {"total_count": 2},
            }
        )
        videos = _run(svc.list_all_videos())
        assert [v.video_id for v in videos] == ["v1", "v2"]
        assert videos[0].name == "First"
        assert videos[0].tags == ["a", "b"]
        assert videos[0].status == "ready"
        assert videos[1].status == "inprogress"
        assert videos[1].require_signed_urls is False

    def test_non_200_returns_empty(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(status_code=500)
        assert _run(svc.list_all_videos()) == []

    def test_success_false_returns_empty(self):
        svc = _make_service()
        svc._client.get.return_value = _resp(json_data={"success": False})
        assert _run(svc.list_all_videos()) == []

    def test_http_error_returns_partial(self):
        svc = _make_service()
        svc._client.get.side_effect = httpx.HTTPError("down")
        assert _run(svc.list_all_videos()) == []
