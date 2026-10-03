"""Unit tests for app.services.user_registration.register_user.

Covered: new-user path (returns True, includes registered_at and all optional
fields in the UpdateExpression), existing-user path (returns False, no
registered_at), ClientError on get_item wrapped, ClientError on update_item
wrapped.
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import user_registration as mod


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


class TestRegisterUser:
    def test_new_user_sets_registered_at_and_optionals(self):
        client = MagicMock()
        client.get_item.return_value = {}  # no "Item" -> new user
        with patch.object(mod.boto3, "client", return_value=client):
            is_new = mod.register_user(
                "tbl",
                "123",
                "Alice",
                avatar_url="http://a",
                github_username="alice",
                provider="github",
                gitlab_username="alice-gl",
                bitbucket_username="alice-bb",
                email="a@example.com",
            )
        assert is_new is True
        kwargs = client.update_item.call_args.kwargs
        assert kwargs["TableName"] == "tbl"
        assert kwargs["Key"] == {
            "PK": {"S": "USER#123"},
            "SK": {"S": "PROFILE"},
        }
        expr = kwargs["UpdateExpression"]
        assert expr.startswith("SET ")
        assert "registered_at = :registered_at" in expr
        assert "avatar_url = :avatar_url" in expr
        assert "github_username = :github_username" in expr
        assert "gitlab_username = :gitlab_username" in expr
        assert "bitbucket_username = :bitbucket_username" in expr
        assert "email = :email" in expr
        vals = kwargs["ExpressionAttributeValues"]
        assert vals[":username"] == {"S": "Alice"}
        assert vals[":provider"] == {"S": "github"}
        assert ":registered_at" in vals
        assert vals[":email"] == {"S": "a@example.com"}

    def test_existing_user_no_registered_at(self):
        client = MagicMock()
        client.get_item.return_value = {"Item": {"PK": {"S": "USER#123"}}}
        with patch.object(mod.boto3, "client", return_value=client):
            is_new = mod.register_user("tbl", "123", "Alice")
        assert is_new is False
        kwargs = client.update_item.call_args.kwargs
        expr = kwargs["UpdateExpression"]
        assert "registered_at" not in expr
        vals = kwargs["ExpressionAttributeValues"]
        # Only required fields present (no optionals supplied)
        assert set(vals.keys()) == {":username", ":last_login", ":provider"}

    def test_get_item_error_wrapped(self):
        client = MagicMock()
        client.get_item.side_effect = _client_error("GetFail")
        with patch.object(mod.boto3, "client", return_value=client):
            with pytest.raises(Exception) as exc:
                mod.register_user("tbl", "123", "Alice")
        assert "Failed to check user existence" in str(exc.value)
        assert "GetFail" in str(exc.value)

    def test_update_item_error_wrapped(self):
        client = MagicMock()
        client.get_item.return_value = {}
        client.update_item.side_effect = _client_error("UpdateFail")
        with patch.object(mod.boto3, "client", return_value=client):
            with pytest.raises(Exception) as exc:
                mod.register_user("tbl", "123", "Alice")
        assert "Failed to register user" in str(exc.value)
        assert "UpdateFail" in str(exc.value)
