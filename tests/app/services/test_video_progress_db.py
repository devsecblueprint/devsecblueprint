"""Unit tests for app.services.video_progress_db.VideoProgressDB.

The service constructs a boto3 DynamoDB client in __init__. Tests patch the
module's boto3.client so no real AWS calls happen, then reassign svc._client
to the mock for direct call assertions.
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import video_progress_db as mod
from app.services.video_progress_db import VideoProgressDB


def _client_error(code: str = "InternalServerError") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


@pytest.fixture
def service():
    client = MagicMock()
    settings = MagicMock(progress_table="test-progress")
    with patch.object(mod.boto3, "client", return_value=client):
        svc = VideoProgressDB(settings)
    svc._client = client
    return svc


class TestGetProgress:
    def test_returns_item(self, service):
        service._client.get_item.return_value = {"Item": {"PK": {"S": "USER#u"}}}
        result = service.get_progress("u", "v")
        assert result == {"PK": {"S": "USER#u"}}
        service._client.get_item.assert_called_once_with(
            TableName="test-progress",
            Key={
                "PK": {"S": "USER#u"},
                "SK": {"S": "VIDEO#v"},
            },
        )

    def test_returns_none_when_absent(self, service):
        service._client.get_item.return_value = {}
        assert service.get_progress("u", "v") is None

    def test_client_error_raises(self, service):
        service._client.get_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_progress("u", "v")


class TestSaveProgress:
    def test_puts_item_with_mapped_fields(self, service):
        data = {
            "position_seconds": 120.5,
            "duration_seconds": 600,
            "percent_complete": 20,
            "completed": False,
            "last_watched_at": "2026-01-03",
            "updated_at": "2026-01-04",
        }
        service.save_progress("u", "v", data)
        service._client.put_item.assert_called_once()
        kwargs = service._client.put_item.call_args.kwargs
        assert kwargs["TableName"] == "test-progress"
        item = kwargs["Item"]
        assert item["PK"] == {"S": "USER#u"}
        assert item["SK"] == {"S": "VIDEO#v"}
        assert item["positionSeconds"] == {"N": "120.5"}
        assert item["durationSeconds"] == {"N": "600"}
        assert item["percentComplete"] == {"N": "20"}
        assert item["completed"] == {"BOOL": False}
        assert item["lastWatchedAt"] == {"S": "2026-01-03"}
        assert item["updatedAt"] == {"S": "2026-01-04"}

    def test_client_error_raises(self, service):
        service._client.put_item.side_effect = _client_error()
        data = {
            "position_seconds": 1,
            "duration_seconds": 2,
            "percent_complete": 50,
            "completed": True,
            "last_watched_at": "x",
            "updated_at": "y",
        }
        with pytest.raises(ClientError):
            service.save_progress("u", "v", data)


class TestGetUserVideoProgress:
    def test_returns_items(self, service):
        items = [{"SK": {"S": "VIDEO#a"}}, {"SK": {"S": "VIDEO#b"}}]
        service._client.query.return_value = {"Items": items}
        result = service.get_user_video_progress("u")
        assert result == items
        kwargs = service._client.query.call_args.kwargs
        assert kwargs["TableName"] == "test-progress"
        assert kwargs["ExpressionAttributeValues"][":pk"] == {"S": "USER#u"}
        assert kwargs["ExpressionAttributeValues"][":sk_prefix"] == {"S": "VIDEO#"}

    def test_returns_empty_when_no_items(self, service):
        service._client.query.return_value = {}
        assert service.get_user_video_progress("u") == []

    def test_client_error_raises(self, service):
        service._client.query.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_user_video_progress("u")
