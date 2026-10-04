"""Unit tests for app.services.notification_service."""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import notification_service as svc


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


@pytest.fixture
def mock_dynamodb():
    client = MagicMock()
    with (
        patch.object(svc, "get_settings") as get_settings,
        patch.object(svc.boto3, "client", return_value=client),
    ):
        get_settings.return_value = MagicMock(notifications_table="test-notifications")
        yield client


class TestCreate:
    def test_create_returns_record_and_sets_ttl(self, mock_dynamodb):
        result = svc.create_notification("user-1", "Hello", "/dashboard")
        assert result["message"] == "Hello"
        assert result["link"] == "/dashboard"
        assert result["notification_id"]
        assert result["created_at"]

        item = mock_dynamodb.put_item.call_args.kwargs["Item"]
        assert item["PK"]["S"] == "USER#user-1"
        assert item["SK"]["S"].startswith("NOTIFICATION#")
        assert int(item["ttl"]["N"]) > 0

    def test_create_raises_on_client_error(self, mock_dynamodb):
        mock_dynamodb.put_item.side_effect = _client_error("ValidationException")
        with pytest.raises(Exception, match="Failed to create notification"):
            svc.create_notification("u", "m", "/l")


class TestGet:
    def test_get_sorts_descending_by_created_at(self, mock_dynamodb):
        mock_dynamodb.query.return_value = {
            "Items": [
                {
                    "SK": {"S": "NOTIFICATION#older"},
                    "message": {"S": "m1"},
                    "link": {"S": "/a"},
                    "created_at": {"S": "2026-01-01"},
                },
                {
                    "SK": {"S": "NOTIFICATION#newer"},
                    "message": {"S": "m2"},
                    "link": {"S": "/b"},
                    "created_at": {"S": "2026-02-01"},
                },
            ]
        }
        result = svc.get_notifications("user-2")
        assert [n["notification_id"] for n in result] == ["newer", "older"]
        assert result[0]["created_at"] == "2026-02-01"

    def test_get_empty_returns_empty_list(self, mock_dynamodb):
        mock_dynamodb.query.return_value = {"Items": []}
        assert svc.get_notifications("u") == []

    def test_get_raises_on_client_error(self, mock_dynamodb):
        mock_dynamodb.query.side_effect = _client_error("InternalServerError")
        with pytest.raises(Exception, match="Failed to get notifications"):
            svc.get_notifications("u")


class TestDelete:
    def test_delete_returns_true(self, mock_dynamodb):
        assert svc.delete_notification("user-3", "notif-123") is True
        key = mock_dynamodb.delete_item.call_args.kwargs["Key"]
        assert key["PK"]["S"] == "USER#user-3"
        assert key["SK"]["S"] == "NOTIFICATION#notif-123"

    def test_delete_raises_on_client_error(self, mock_dynamodb):
        mock_dynamodb.delete_item.side_effect = _client_error(
            "ResourceNotFoundException"
        )
        with pytest.raises(Exception, match="Failed to delete notification"):
            svc.delete_notification("u", "n")
