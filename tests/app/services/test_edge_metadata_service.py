"""Tests for app.services.edge_metadata_service (CloudFront KVS link previews)."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from hypothesis import given, settings as hyp_settings, strategies as st

from app.services import edge_metadata_service as mod
from app.services.edge_metadata_service import (
    MAX_VALUE_BYTES,
    EdgeMetadataService,
    build_value,
)

ARN = "arn:aws:cloudfront::123456789012:key-value-store/abc"


def _error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


def published(**overrides) -> dict:
    data = {
        "slug": "intro",
        "title": "Intro to DevSecOps",
        "description": "A talk about shifting left.",
        "thumbnail_url": "https://cdn.example/thumb.jpg",
        "status": "PUBLISHED",
    }
    data.update(overrides)
    return data


@pytest.fixture
def client():
    c = MagicMock()
    c.describe_key_value_store.return_value = {"ETag": "etag-1"}
    return c


@pytest.fixture
def service(client):
    return EdgeMetadataService(SimpleNamespace(video_edge_kvs_arn=ARN), client=client)


class TestBuildValue:
    def test_compact_json_with_expected_keys(self):
        value = json.loads(build_value(published()))
        assert value == {
            "t": "Intro to DevSecOps",
            "d": "A talk about shifting left.",
            "i": "https://cdn.example/thumb.jpg",
        }

    def test_collapses_whitespace(self):
        value = json.loads(build_value(published(description="a\n\n  b\t c")))
        assert value["d"] == "a b c"

    def test_missing_fields_become_empty_strings(self):
        value = json.loads(build_value({"slug": "x"}))
        assert value == {"t": "", "d": "", "i": ""}

    def test_long_thumbnail_is_dropped(self):
        value = json.loads(
            build_value(published(thumbnail_url="https://x/" + "a" * 400))
        )
        assert value["i"] == ""

    def test_huge_description_still_fits(self):
        raw = build_value(published(description="word " * 5000))
        assert len(raw) <= MAX_VALUE_BYTES
        assert json.loads(raw)["d"]  # some of the description survives

    def test_non_ascii_content_fits_by_bytes(self):
        raw = build_value(published(title="é" * 200, description="日本語" * 300))
        assert len(raw.encode("utf-8")) <= MAX_VALUE_BYTES
        parsed = json.loads(raw)
        assert parsed["t"].startswith("é")

    def test_value_is_ascii_only(self):
        assert build_value(published(title="café")).isascii()

    @hyp_settings(max_examples=60, deadline=None)
    @given(
        title=st.text(max_size=400),
        description=st.text(max_size=2000),
        thumb=st.text(max_size=500),
    )
    def test_never_exceeds_limit(self, title, description, thumb):
        raw = build_value(
            {"title": title, "description": description, "thumbnail_url": thumb}
        )
        assert len(raw.encode("utf-8")) <= MAX_VALUE_BYTES
        json.loads(raw)  # always valid JSON


class TestUpsert:
    def test_writes_with_current_etag(self, service, client):
        assert service.upsert_video(published()) is True
        kwargs = client.put_key.call_args.kwargs
        assert kwargs["KvsARN"] == ARN
        assert kwargs["Key"] == "intro"
        assert kwargs["IfMatch"] == "etag-1"
        assert json.loads(kwargs["Value"])["t"] == "Intro to DevSecOps"

    def test_disabled_without_arn_is_a_no_op(self, client):
        svc = EdgeMetadataService(SimpleNamespace(video_edge_kvs_arn=""), client=client)
        assert svc.enabled is False
        assert svc.upsert_video(published()) is False
        client.put_key.assert_not_called()
        client.describe_key_value_store.assert_not_called()

    @pytest.mark.parametrize("status", ["DRAFT", "READY", "ARCHIVED", ""])
    def test_only_published_videos_are_written(self, service, client, status):
        assert service.upsert_video(published(status=status)) is False
        client.put_key.assert_not_called()

    def test_missing_slug_is_skipped(self, service, client):
        assert service.upsert_video(published(slug="")) is False
        client.put_key.assert_not_called()

    def test_retries_on_conflict_with_fresh_etag(self, service, client):
        client.describe_key_value_store.side_effect = [{"ETag": "e1"}, {"ETag": "e2"}]
        client.put_key.side_effect = [_error("ConflictException"), {"ETag": "e3"}]
        assert service.upsert_video(published()) is True
        assert client.put_key.call_args_list[0].kwargs["IfMatch"] == "e1"
        assert client.put_key.call_args_list[1].kwargs["IfMatch"] == "e2"

    def test_gives_up_after_repeated_conflicts_without_raising(self, service, client):
        client.put_key.side_effect = _error("ConflictException")
        assert service.upsert_video(published()) is False
        assert client.put_key.call_count == mod.MAX_CONFLICT_RETRIES

    def test_other_errors_are_swallowed(self, service, client):
        client.put_key.side_effect = _error("AccessDeniedException")
        assert service.upsert_video(published()) is False

    def test_describe_failure_is_swallowed(self, service, client):
        client.describe_key_value_store.side_effect = RuntimeError("no network")
        assert service.upsert_video(published()) is False


class TestRemove:
    def test_deletes_with_etag(self, service, client):
        assert service.remove_video("intro") is True
        kwargs = client.delete_key.call_args.kwargs
        assert kwargs == {"KvsARN": ARN, "Key": "intro", "IfMatch": "etag-1"}

    @pytest.mark.parametrize(
        "code", ["ResourceNotFoundException", "ValidationException"]
    )
    def test_missing_key_counts_as_success(self, service, client, code):
        client.delete_key.side_effect = _error(code)
        assert service.remove_video("gone") is True

    def test_other_errors_return_false(self, service, client):
        client.delete_key.side_effect = _error("InternalServerException")
        assert service.remove_video("x") is False

    def test_disabled_or_blank_slug_is_noop(self, client):
        off = EdgeMetadataService(SimpleNamespace(video_edge_kvs_arn=""), client=client)
        assert off.remove_video("x") is False
        on = EdgeMetadataService(SimpleNamespace(video_edge_kvs_arn=ARN), client=client)
        assert on.remove_video("") is False
        client.delete_key.assert_not_called()


class TestBackfill:
    def _item(self, slug, status="PUBLISHED"):
        return {
            "slug": {"S": slug},
            "title": {"S": f"Title {slug}"},
            "description": {"S": "d"},
            "thumbnailUrl": {"S": ""},
            "status": {"S": status},
        }

    def test_requires_configuration(self, client):
        svc = EdgeMetadataService(SimpleNamespace(video_edge_kvs_arn=""), client=client)
        with pytest.raises(RuntimeError):
            svc.backfill()

    def test_writes_all_published_videos(self, service, client):
        db = MagicMock()
        db.query_published.return_value = ([self._item("a"), self._item("b")], 2)
        with patch.object(mod, "VideoMetadataDB", return_value=db):
            assert service.backfill() == 2
        keys = [c.kwargs["Key"] for c in client.put_key.call_args_list]
        assert keys == ["a", "b"]

    def test_pages_through_results(self, service, client, monkeypatch):
        monkeypatch.setattr(mod, "BACKFILL_PAGE_SIZE", 2)
        db = MagicMock()
        db.query_published.side_effect = [
            ([self._item("a"), self._item("b")], 3),
            ([self._item("c")], 3),
        ]
        with patch.object(mod, "VideoMetadataDB", return_value=db):
            assert service.backfill() == 3
        assert [c.args for c in db.query_published.call_args_list] == [(1, 2), (2, 2)]

    def test_skips_items_that_fail_to_write(self, service, client):
        client.put_key.side_effect = [_error("AccessDeniedException"), {"ETag": "x"}]
        db = MagicMock()
        db.query_published.return_value = ([self._item("a"), self._item("b")], 2)
        with patch.object(mod, "VideoMetadataDB", return_value=db):
            assert service.backfill() == 1

    def test_empty_catalog(self, service, client):
        db = MagicMock()
        db.query_published.return_value = ([], 0)
        with patch.object(mod, "VideoMetadataDB", return_value=db):
            assert service.backfill() == 0
        client.put_key.assert_not_called()
