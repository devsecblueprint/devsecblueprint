"""Unit tests for app.services.session_store.

These are module-level functions that each call boto3.client("dynamodb").
Tests patch the module's boto3.client to return a mock client and assert on
the DynamoDB calls, success paths, None/empty paths, and ClientError wrapping
(the module re-raises as a plain Exception with the error code).
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import session_store as mod


def _client_error(code: str = "ResourceNotFoundException") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


class TestStoreRefreshToken:
    def test_puts_item(self):
        client = MagicMock()
        with patch.object(mod.boto3, "client", return_value=client):
            mod.store_refresh_token("tbl", "u", "hash", 100, 200)
        kwargs = client.put_item.call_args.kwargs
        assert kwargs["TableName"] == "tbl"
        item = kwargs["Item"]
        assert item["PK"] == {"S": "USER#u"}
        assert item["SK"] == {"S": "SESSION#hash"}
        assert item["created_at"] == {"N": "100"}
        assert item["expires_at"] == {"N": "200"}
        assert item["user_id"] == {"S": "u"}

    def test_client_error_wrapped(self):
        client = MagicMock()
        client.put_item.side_effect = _client_error("Boom")
        with patch.object(mod.boto3, "client", return_value=client):
            with pytest.raises(Exception) as exc:
                mod.store_refresh_token("tbl", "u", "hash", 100, 200)
        assert "Boom" in str(exc.value)


class TestGetRefreshToken:
    def test_returns_parsed_record(self):
        client = MagicMock()
        client.get_item.return_value = {
            "Item": {
                "user_id": {"S": "u"},
                "SK": {"S": "SESSION#hash"},
                "created_at": {"N": "100"},
                "expires_at": {"N": "200"},
            }
        }
        with patch.object(mod.boto3, "client", return_value=client):
            result = mod.get_refresh_token("tbl", "u", "hash")
        assert result == {
            "user_id": "u",
            "token_hash": "hash",
            "created_at": 100,
            "expires_at": 200,
        }
        client.get_item.assert_called_once_with(
            TableName="tbl",
            Key={"PK": {"S": "USER#u"}, "SK": {"S": "SESSION#hash"}},
        )

    def test_returns_none_when_absent(self):
        client = MagicMock()
        client.get_item.return_value = {}
        with patch.object(mod.boto3, "client", return_value=client):
            assert mod.get_refresh_token("tbl", "u", "hash") is None

    def test_client_error_wrapped(self):
        client = MagicMock()
        client.get_item.side_effect = _client_error("GetFail")
        with patch.object(mod.boto3, "client", return_value=client):
            with pytest.raises(Exception) as exc:
                mod.get_refresh_token("tbl", "u", "hash")
        assert "GetFail" in str(exc.value)


class TestDeleteRefreshToken:
    def test_deletes_item(self):
        client = MagicMock()
        with patch.object(mod.boto3, "client", return_value=client):
            mod.delete_refresh_token("tbl", "u", "hash")
        client.delete_item.assert_called_once_with(
            TableName="tbl",
            Key={"PK": {"S": "USER#u"}, "SK": {"S": "SESSION#hash"}},
        )

    def test_client_error_wrapped(self):
        client = MagicMock()
        client.delete_item.side_effect = _client_error("DelFail")
        with patch.object(mod.boto3, "client", return_value=client):
            with pytest.raises(Exception) as exc:
                mod.delete_refresh_token("tbl", "u", "hash")
        assert "DelFail" in str(exc.value)


class TestDeleteAllUserSessions:
    def test_queries_and_deletes_each(self):
        client = MagicMock()
        client.query.return_value = {
            "Items": [
                {"PK": {"S": "USER#u"}, "SK": {"S": "SESSION#a"}},
                {"PK": {"S": "USER#u"}, "SK": {"S": "SESSION#b"}},
            ]
        }
        with patch.object(mod.boto3, "client", return_value=client):
            mod.delete_all_user_sessions("tbl", "u")
        query_kwargs = client.query.call_args.kwargs
        assert query_kwargs["ExpressionAttributeValues"][":pk"] == {"S": "USER#u"}
        assert query_kwargs["ExpressionAttributeValues"][":sk_prefix"] == {
            "S": "SESSION#"
        }
        assert client.delete_item.call_count == 2
        client.delete_item.assert_any_call(
            TableName="tbl",
            Key={"PK": {"S": "USER#u"}, "SK": {"S": "SESSION#a"}},
        )

    def test_no_sessions_no_delete(self):
        client = MagicMock()
        client.query.return_value = {}
        with patch.object(mod.boto3, "client", return_value=client):
            mod.delete_all_user_sessions("tbl", "u")
        client.delete_item.assert_not_called()

    def test_client_error_wrapped(self):
        client = MagicMock()
        client.query.side_effect = _client_error("QueryFail")
        with patch.object(mod.boto3, "client", return_value=client):
            with pytest.raises(Exception) as exc:
                mod.delete_all_user_sessions("tbl", "u")
        assert "QueryFail" in str(exc.value)
