"""Unit tests for app.services.video_metadata_db.VideoMetadataDB.

Covers put_video (field mapping + published_at branch), get_video,
get_video_by_slug, query_by_status/query_published pagination, query_all
scan + sort + pagination, slug_exists, and ClientError paths.
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import video_metadata_db as mod
from app.services.video_metadata_db import VideoMetadataDB


def _client_error(code: str = "InternalServerError") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


@pytest.fixture
def service():
    client = MagicMock()
    settings = MagicMock(videos_table="test-videos")
    with patch.object(mod.boto3, "client", return_value=client):
        svc = VideoMetadataDB(settings)
    svc._client = client
    return svc


def _video(**overrides):
    base = {
        "id": "rec-1",
        "title": "Secure APIs",
        "slug": "secure-apis",
        "cloudflare_stream_id": "cf-abc",
        "instructor": "Damien",
        "recorded_at": "2026-01-01",
        "status": "PUBLISHED",
        "created_at": "2026-01-01",
        "updated_at": "2026-01-02",
    }
    base.update(overrides)
    return base


class TestPutVideo:
    def test_maps_fields_and_published_at(self, service):
        video = _video(
            description="d",
            thumbnail_url="http://t",
            duration_seconds=3600,
            tags=["security", "api"],
            resources=[{"title": "r", "url": "http://r"}],
            instructors=[{"name": "A", "linkedin_url": "http://li"}],
            published_at="2026-01-03",
        )
        service.put_video(video)
        kwargs = service._client.put_item.call_args.kwargs
        assert kwargs["TableName"] == "test-videos"
        item = kwargs["Item"]
        assert item["PK"] == {"S": "VIDEO#rec-1"}
        assert item["SK"] == {"S": "METADATA"}
        assert item["durationSeconds"] == {"N": "3600"}
        assert item["tags"] == {"L": [{"S": "security"}, {"S": "api"}]}
        assert item["GSI1PK"] == {"S": "STATUS#PUBLISHED"}
        assert item["GSI1SK"] == {"S": "2026-01-03"}
        assert item["GSI2PK"] == {"S": "secure-apis"}
        assert item["publishedAt"] == {"S": "2026-01-03"}
        assert item["resources"]["L"][0]["M"]["title"] == {"S": "r"}
        assert item["instructors"]["L"][0]["M"]["linkedin_url"] == {"S": "http://li"}

    def test_defaults_without_published_at(self, service):
        service.put_video(_video())
        item = service._client.put_item.call_args.kwargs["Item"]
        # GSI1SK falls back to created_at when no published_at
        assert item["GSI1SK"] == {"S": "2026-01-01"}
        assert "publishedAt" not in item
        assert item["description"] == {"S": ""}
        assert item["durationSeconds"] == {"N": "0"}
        assert item["tags"] == {"L": []}

    def test_instructor_null_linkedin(self, service):
        service.put_video(_video(instructors=[{"name": "A", "linkedin_url": None}]))
        item = service._client.put_item.call_args.kwargs["Item"]
        assert item["instructors"]["L"][0]["M"]["linkedin_url"] == {"S": ""}

    def test_client_error_raises(self, service):
        service._client.put_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.put_video(_video())


class TestGetVideo:
    def test_returns_item(self, service):
        service._client.get_item.return_value = {"Item": {"id": {"S": "rec-1"}}}
        assert service.get_video("rec-1") == {"id": {"S": "rec-1"}}
        service._client.get_item.assert_called_once_with(
            TableName="test-videos",
            Key={"PK": {"S": "VIDEO#rec-1"}, "SK": {"S": "METADATA"}},
        )

    def test_returns_none(self, service):
        service._client.get_item.return_value = {}
        assert service.get_video("rec-1") is None

    def test_client_error_raises(self, service):
        service._client.get_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_video("rec-1")


class TestGetVideoBySlug:
    def test_returns_first_item(self, service):
        service._client.query.return_value = {"Items": [{"slug": {"S": "s"}}]}
        assert service.get_video_by_slug("s") == {"slug": {"S": "s"}}
        kwargs = service._client.query.call_args.kwargs
        assert kwargs["IndexName"] == "slug-index"
        assert kwargs["Limit"] == 1

    def test_returns_none_when_empty(self, service):
        service._client.query.return_value = {"Items": []}
        assert service.get_video_by_slug("s") is None

    def test_client_error_raises(self, service):
        service._client.query.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_video_by_slug("s")


class TestQueryByStatus:
    def test_counts_and_paginates(self, service):
        items = [{"id": {"S": f"v{i}"}} for i in range(5)]
        service._client.query.side_effect = [
            {"Count": 5},
            {"Items": items},
        ]
        paged, total = service.query_by_status("PUBLISHED", page=2, page_size=2)
        assert total == 5
        # page 2, size 2 -> items[2:4]
        assert paged == items[2:4]
        count_call = service._client.query.call_args_list[0].kwargs
        assert count_call["Select"] == "COUNT"
        page_call = service._client.query.call_args_list[1].kwargs
        assert page_call["ScanIndexForward"] is False
        assert page_call["Limit"] == 4  # page_size * page

    def test_query_published_delegates(self, service):
        service._client.query.side_effect = [{"Count": 1}, {"Items": [{"id": {"S": "a"}}]}]
        paged, total = service.query_published(page=1, page_size=10)
        assert total == 1
        assert len(paged) == 1

    def test_client_error_raises(self, service):
        service._client.query.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.query_by_status("PUBLISHED", 1, 10)


class TestQueryAll:
    def test_scans_sorts_and_paginates(self, service):
        items = [
            {"id": {"S": "a"}, "createdAt": {"S": "2026-01-01"}},
            {"id": {"S": "b"}, "createdAt": {"S": "2026-03-01"}},
            {"id": {"S": "c"}, "createdAt": {"S": "2026-02-01"}},
        ]
        service._client.scan.side_effect = [
            {"Count": 3},
            {"Items": items},
        ]
        paged, total = service.query_all(page=1, page_size=2)
        assert total == 3
        # sorted desc by createdAt -> b, c, a; page 1 size 2 -> b, c
        assert [i["id"]["S"] for i in paged] == ["b", "c"]

    def test_handles_missing_created_at(self, service):
        items = [{"id": {"S": "a"}}, {"id": {"S": "b"}, "createdAt": {"S": "2026-01-01"}}]
        service._client.scan.side_effect = [{"Count": 2}, {"Items": items}]
        paged, total = service.query_all(page=1, page_size=10)
        assert total == 2
        assert [i["id"]["S"] for i in paged] == ["b", "a"]

    def test_client_error_raises(self, service):
        service._client.scan.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.query_all(1, 10)


class TestSlugExists:
    def test_true_when_found(self, service):
        service._client.query.return_value = {"Items": [{"slug": {"S": "s"}}]}
        assert service.slug_exists("s") is True

    def test_false_when_absent(self, service):
        service._client.query.return_value = {"Items": []}
        assert service.slug_exists("s") is False
