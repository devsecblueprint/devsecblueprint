"""Unit tests for app.services.membership_db.MembershipDB.

Constructs a boto3 DynamoDB client in __init__; tests patch the module's
boto3.client, then reassign svc._client for direct assertions.
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import membership_db as mod
from app.services.membership_db import MembershipDB


def _client_error(code: str = "InternalServerError") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


@pytest.fixture
def service():
    client = MagicMock()
    settings = MagicMock(membership_table="test-membership")
    with patch.object(mod.boto3, "client", return_value=client):
        svc = MembershipDB(settings)
    svc._client = client
    return svc


class TestGetMembership:
    def test_returns_item(self, service):
        service._client.get_item.return_value = {"Item": {"PK": {"S": "USER#u"}}}
        result = service.get_membership("u")
        assert result == {"PK": {"S": "USER#u"}}
        service._client.get_item.assert_called_once_with(
            TableName="test-membership",
            Key={"PK": {"S": "USER#u"}, "SK": {"S": "MEMBERSHIP"}},
        )

    def test_returns_none_when_absent(self, service):
        service._client.get_item.return_value = {}
        assert service.get_membership("u") is None

    def test_client_error_raises(self, service):
        service._client.get_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_membership("u")


class TestGetDiscordActive:
    def test_returns_item(self, service):
        service._client.get_item.return_value = {
            "Item": {"SK": {"S": "DISCORD_ACTIVE"}}
        }
        result = service.get_discord_active("u")
        assert result == {"SK": {"S": "DISCORD_ACTIVE"}}
        service._client.get_item.assert_called_once_with(
            TableName="test-membership",
            Key={"PK": {"S": "USER#u"}, "SK": {"S": "DISCORD_ACTIVE"}},
        )

    def test_returns_none_when_absent(self, service):
        service._client.get_item.return_value = {}
        assert service.get_discord_active("u") is None

    def test_client_error_raises(self, service):
        service._client.get_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_discord_active("u")


class TestDeactivateDiscordConnection:
    def test_transact_write_items_structure(self, service):
        service.deactivate_discord_connection("u", "disc-1", "left guild")
        service._client.transact_write_items.assert_called_once()
        kwargs = service._client.transact_write_items.call_args.kwargs
        items = kwargs["TransactItems"]
        assert len(items) == 2

        update = items[0]["Update"]
        assert update["TableName"] == "test-membership"
        assert update["Key"]["SK"] == {"S": "DISCORD#disc-1"}
        assert update["Key"]["PK"] == {"S": "USER#u"}
        vals = update["ExpressionAttributeValues"]
        assert vals[":active"] == {"BOOL": False}
        assert vals[":reason"] == {"S": "left guild"}
        assert ":disconnected_at" in vals

        delete = items[1]["Delete"]
        assert delete["Key"]["SK"] == {"S": "DISCORD_ACTIVE"}
        assert delete["Key"]["PK"] == {"S": "USER#u"}

    def test_returns_none(self, service):
        assert service.deactivate_discord_connection("u", "d", "r") is None

    def test_client_error_raises(self, service):
        service._client.transact_write_items.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.deactivate_discord_connection("u", "d", "r")


class TestGetUserAuditLog:
    def test_returns_items_with_defaults(self, service):
        items = [{"SK": {"S": "AUDIT#1"}}]
        service._client.query.return_value = {"Items": items}
        result = service.get_user_audit_log("u")
        assert result == items
        kwargs = service._client.query.call_args.kwargs
        assert kwargs["TableName"] == "test-membership"
        assert kwargs["ScanIndexForward"] is False
        assert kwargs["Limit"] == 100
        assert kwargs["ExpressionAttributeValues"][":pk"] == {"S": "USER#u"}
        assert kwargs["ExpressionAttributeValues"][":sk_prefix"] == {"S": "AUDIT#"}

    def test_respects_custom_limit(self, service):
        service._client.query.return_value = {"Items": []}
        result = service.get_user_audit_log("u", limit=5)
        assert result == []
        assert service._client.query.call_args.kwargs["Limit"] == 5

    def test_returns_empty_when_no_items(self, service):
        service._client.query.return_value = {}
        assert service.get_user_audit_log("u") == []

    def test_client_error_raises(self, service):
        service._client.query.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_user_audit_log("u")


class TestWriteAuditEvent:
    def test_put_item_called(self, service):
        event = {"PK": {"S": "USER#u"}, "SK": {"S": "AUDIT#1"}}
        service.write_audit_event(event)
        service._client.put_item.assert_called_once_with(
            TableName="test-membership", Item=event
        )

    def test_client_error_raises(self, service):
        service._client.put_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.write_audit_event({"PK": {"S": "x"}})
