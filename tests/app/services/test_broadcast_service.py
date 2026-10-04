"""Unit tests for app.services.broadcast_service.BroadcastService.

Covers broadcast CRUD, unread filtering by dismissals, pagination, single and
batch dismissal (including the BatchWriteItem UnprocessedItems retry path).
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import broadcast_service as mod
from app.services.broadcast_service import BroadcastService


def _client_error(code: str = "InternalServerError") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


@pytest.fixture
def service():
    client = MagicMock()
    with patch.object(mod.boto3, "client", return_value=client):
        settings = MagicMock(broadcasts_table="test-broadcasts")
        svc = BroadcastService(settings)
    # Attach the mock for assertions.
    svc._client = client
    return svc


class TestCreate:
    def test_create_writes_item_and_returns_record(self, service):
        result = service.create_broadcast("Title", "Body", "admin", "/go")
        assert result["title"] == "Title"
        assert result["message"] == "Body"
        assert result["created_by"] == "admin"
        assert result["link"] == "/go"
        assert result["broadcast_id"]

        item = service._client.put_item.call_args.kwargs["Item"]
        assert item["PK"]["S"] == "BROADCAST"
        assert item["SK"]["S"].startswith("MSG#")
        assert int(item["ttl"]["N"]) > 0

    def test_create_defaults_empty_link(self, service):
        result = service.create_broadcast("T", "M", "admin")
        assert result["link"] == ""


class TestGetAll:
    def test_sorts_descending(self, service):
        service._client.query.return_value = {
            "Items": [
                {"broadcast_id": {"S": "old"}, "created_at": {"S": "2026-01-01"}},
                {"broadcast_id": {"S": "new"}, "created_at": {"S": "2026-03-01"}},
            ]
        }
        result = service.get_all_broadcasts()
        assert [b["broadcast_id"] for b in result] == ["new", "old"]

    def test_paginates(self, service):
        service._client.query.side_effect = [
            {
                "Items": [
                    {"broadcast_id": {"S": "a"}, "created_at": {"S": "2026-01-01"}}
                ],
                "LastEvaluatedKey": {"PK": {"S": "BROADCAST"}},
            },
            {
                "Items": [
                    {"broadcast_id": {"S": "b"}, "created_at": {"S": "2026-02-01"}}
                ]
            },
        ]
        result = service.get_all_broadcasts()
        assert len(result) == 2
        assert service._client.query.call_count == 2


class TestDelete:
    def test_delete_returns_true(self, service):
        assert service.delete_broadcast("bid-1") is True
        key = service._client.delete_item.call_args.kwargs["Key"]
        assert key["SK"]["S"] == "MSG#bid-1"

    def test_delete_returns_false_on_error(self, service):
        service._client.delete_item.side_effect = _client_error()
        assert service.delete_broadcast("bid-1") is False


class TestUnread:
    def test_filters_out_dismissed_and_sorts_oldest_first(self, service):
        def query(**kwargs):
            pk = kwargs["ExpressionAttributeValues"][":pk"]["S"]
            if pk == "BROADCAST":
                return {
                    "Items": [
                        {
                            "broadcast_id": {"S": "b1"},
                            "created_at": {"S": "2026-01-01"},
                        },
                        {
                            "broadcast_id": {"S": "b2"},
                            "created_at": {"S": "2026-02-01"},
                        },
                        {
                            "broadcast_id": {"S": "b3"},
                            "created_at": {"S": "2026-03-01"},
                        },
                    ]
                }
            # dismissed query for the user
            return {"Items": [{"SK": {"S": "DISMISSED#b2"}}]}

        service._client.query.side_effect = query
        result = service.get_unread_broadcasts("user-1")
        # b2 dismissed; remaining sorted oldest first
        assert [b["broadcast_id"] for b in result] == ["b1", "b3"]

    def test_no_broadcasts_returns_empty(self, service):
        service._client.query.return_value = {"Items": []}
        assert service.get_unread_broadcasts("user-1") == []


class TestDismiss:
    def test_dismiss_single_returns_true(self, service):
        assert service.dismiss_broadcast("user-1", "b1") is True
        item = service._client.put_item.call_args.kwargs["Item"]
        assert item["PK"]["S"] == "USER#user-1"
        assert item["SK"]["S"] == "DISMISSED#b1"

    def test_dismiss_single_returns_false_on_error(self, service):
        service._client.put_item.side_effect = _client_error()
        assert service.dismiss_broadcast("user-1", "b1") is False

    def test_dismiss_all_empty_is_noop_true(self, service):
        assert service.dismiss_all_broadcasts("user-1", []) is True
        service._client.batch_write_item.assert_not_called()

    def test_dismiss_all_single_batch(self, service):
        service._client.batch_write_item.return_value = {"UnprocessedItems": {}}
        assert service.dismiss_all_broadcasts("user-1", ["b1", "b2"]) is True
        assert service._client.batch_write_item.call_count == 1

    def test_dismiss_all_retries_unprocessed(self, service):
        # First call returns unprocessed, second clears them.
        service._client.batch_write_item.side_effect = [
            {"UnprocessedItems": {"test-broadcasts": [{"PutRequest": {"Item": {}}}]}},
            {"UnprocessedItems": {}},
        ]
        with patch.object(mod.time, "sleep"):
            assert service.dismiss_all_broadcasts("user-1", ["b1"]) is True
        assert service._client.batch_write_item.call_count == 2

    def test_dismiss_all_exhausts_retries_returns_false(self, service):
        service._client.batch_write_item.return_value = {
            "UnprocessedItems": {"test-broadcasts": [{"PutRequest": {"Item": {}}}]}
        }
        with patch.object(mod.time, "sleep"):
            assert service.dismiss_all_broadcasts("user-1", ["b1"]) is False

    def test_dismiss_all_client_error_returns_false(self, service):
        service._client.batch_write_item.side_effect = _client_error()
        assert service.dismiss_all_broadcasts("user-1", ["b1"]) is False

    def test_dismiss_all_chunks_over_25(self, service):
        service._client.batch_write_item.return_value = {"UnprocessedItems": {}}
        ids = [f"b{i}" for i in range(30)]
        assert service.dismiss_all_broadcasts("user-1", ids) is True
        # 30 ids -> 2 batches (25 + 5)
        assert service._client.batch_write_item.call_count == 2


class TestDismissedIds:
    def test_paginates_dismissed(self, service):
        service._client.query.side_effect = [
            {"Items": [{"SK": {"S": "DISMISSED#b1"}}], "LastEvaluatedKey": {"x": 1}},
            {"Items": [{"SK": {"S": "DISMISSED#b2"}}]},
        ]
        result = service._get_dismissed_ids("user-1")
        assert result == {"b1", "b2"}
