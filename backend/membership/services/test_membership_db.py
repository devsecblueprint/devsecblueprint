"""Unit tests for the DynamoDB service layer (membership_db.py)."""

import os
import time
from unittest.mock import MagicMock, patch

import pytest

# Set env var before import
os.environ["MEMBERSHIP_TABLE"] = "test-membership-table"

from . import membership_db


@pytest.fixture
def mock_dynamodb():
    """Create a mock DynamoDB client."""
    with patch.object(membership_db, "_get_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


class TestGetMembership:
    def test_returns_item_when_found(self, mock_dynamodb):
        expected_item = {
            "PK": {"S": "USER#user1"},
            "SK": {"S": "MEMBERSHIP"},
            "membership_tier": {"S": "BUILDER"},
        }
        mock_dynamodb.get_item.return_value = {"Item": expected_item}

        result = membership_db.get_membership("user1")

        assert result == expected_item
        mock_dynamodb.get_item.assert_called_once_with(
            TableName="test-membership-table",
            Key={"PK": {"S": "USER#user1"}, "SK": {"S": "MEMBERSHIP"}},
        )

    def test_returns_none_when_not_found(self, mock_dynamodb):
        mock_dynamodb.get_item.return_value = {}

        result = membership_db.get_membership("nonexistent")

        assert result is None

    def test_raises_on_client_error(self, mock_dynamodb):
        from botocore.exceptions import ClientError

        mock_dynamodb.get_item.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError"}}, "GetItem"
        )

        with pytest.raises(Exception, match="Failed to get membership"):
            membership_db.get_membership("user1")


class TestPutMembership:
    def test_puts_item_successfully(self, mock_dynamodb):
        record = {
            "PK": {"S": "USER#user1"},
            "SK": {"S": "MEMBERSHIP"},
            "membership_tier": {"S": "FREE"},
        }

        membership_db.put_membership(record)

        mock_dynamodb.put_item.assert_called_once_with(
            TableName="test-membership-table", Item=record
        )

    def test_raises_on_client_error(self, mock_dynamodb):
        from botocore.exceptions import ClientError

        mock_dynamodb.put_item.side_effect = ClientError(
            {"Error": {"Code": "ProvisionedThroughputExceededException"}}, "PutItem"
        )

        with pytest.raises(Exception, match="Failed to put membership"):
            membership_db.put_membership(
                {"PK": {"S": "USER#x"}, "SK": {"S": "MEMBERSHIP"}}
            )


class TestGetDiscordActive:
    def test_returns_item_when_found(self, mock_dynamodb):
        expected_item = {
            "PK": {"S": "USER#user1"},
            "SK": {"S": "DISCORD_ACTIVE"},
            "discord_user_id": {"S": "123456789012345678"},
        }
        mock_dynamodb.get_item.return_value = {"Item": expected_item}

        result = membership_db.get_discord_active("user1")

        assert result == expected_item

    def test_returns_none_when_not_found(self, mock_dynamodb):
        mock_dynamodb.get_item.return_value = {}

        result = membership_db.get_discord_active("user1")

        assert result is None


class TestPutDiscordIdentity:
    def test_puts_record_successfully(self, mock_dynamodb):
        record = {
            "PK": {"S": "USER#user1"},
            "SK": {"S": "DISCORD#123456789012345678"},
            "discord_user_id": {"S": "123456789012345678"},
            "username": {"S": "testuser"},
            "active": {"BOOL": False},
        }

        membership_db.put_discord_identity(record)

        mock_dynamodb.put_item.assert_called_once_with(
            TableName="test-membership-table", Item=record
        )


class TestActivateDiscordConnection:
    def test_creates_transact_write(self, mock_dynamodb):
        record = {
            "discord_user_id": "123456789012345678",
            "username": "testuser",
            "display_name": "Test User",
            "avatar_url": "https://example.com/avatar.png",
        }

        membership_db.activate_discord_connection("user1", record)

        mock_dynamodb.transact_write_items.assert_called_once()
        call_args = mock_dynamodb.transact_write_items.call_args
        items = call_args[1]["TransactItems"]

        # First operation: Update DISCORD# record
        assert items[0]["Update"]["Key"] == {
            "PK": {"S": "USER#user1"},
            "SK": {"S": "DISCORD#123456789012345678"},
        }
        assert ":active" in items[0]["Update"]["ExpressionAttributeValues"]
        assert items[0]["Update"]["ExpressionAttributeValues"][":active"] == {
            "BOOL": True
        }

        # Second operation: Put DISCORD_ACTIVE
        put_item = items[1]["Put"]["Item"]
        assert put_item["PK"] == {"S": "USER#user1"}
        assert put_item["SK"] == {"S": "DISCORD_ACTIVE"}
        assert put_item["discord_user_id"] == {"S": "123456789012345678"}
        assert put_item["active"] == {"BOOL": True}


class TestDeactivateDiscordConnection:
    def test_creates_transact_write(self, mock_dynamodb):
        membership_db.deactivate_discord_connection(
            "user1", "123456789012345678", "User requested"
        )

        mock_dynamodb.transact_write_items.assert_called_once()
        call_args = mock_dynamodb.transact_write_items.call_args
        items = call_args[1]["TransactItems"]

        # First operation: Update DISCORD# record
        assert items[0]["Update"]["Key"] == {
            "PK": {"S": "USER#user1"},
            "SK": {"S": "DISCORD#123456789012345678"},
        }
        expr_values = items[0]["Update"]["ExpressionAttributeValues"]
        assert expr_values[":active"] == {"BOOL": False}
        assert expr_values[":reason"] == {"S": "User requested"}

        # Second operation: Delete DISCORD_ACTIVE
        assert items[1]["Delete"]["Key"] == {
            "PK": {"S": "USER#user1"},
            "SK": {"S": "DISCORD_ACTIVE"},
        }


class TestCheckDiscordDuplicate:
    def test_returns_active_item(self, mock_dynamodb):
        active_item = {
            "discord_user_id": {"S": "123456789012345678"},
            "user_id": {"S": "other_user"},
            "active": {"BOOL": True},
        }
        mock_dynamodb.query.return_value = {"Items": [active_item]}

        result = membership_db.check_discord_duplicate("123456789012345678")

        assert result == active_item
        mock_dynamodb.query.assert_called_once_with(
            TableName="test-membership-table",
            IndexName="GSI1",
            KeyConditionExpression="discord_user_id = :discord_id",
            ExpressionAttributeValues={":discord_id": {"S": "123456789012345678"}},
        )

    def test_returns_none_when_no_active_items(self, mock_dynamodb):
        inactive_item = {
            "discord_user_id": {"S": "123456789012345678"},
            "active": {"BOOL": False},
        }
        mock_dynamodb.query.return_value = {"Items": [inactive_item]}

        result = membership_db.check_discord_duplicate("123456789012345678")

        assert result is None

    def test_returns_none_when_empty(self, mock_dynamodb):
        mock_dynamodb.query.return_value = {"Items": []}

        result = membership_db.check_discord_duplicate("999999999999999999")

        assert result is None


class TestResolveStripeCustomer:
    def test_returns_item_when_found(self, mock_dynamodb):
        expected_item = {
            "stripe_customer_id": {"S": "cus_abc123"},
            "user_id": {"S": "user1"},
        }
        mock_dynamodb.query.return_value = {"Items": [expected_item]}

        result = membership_db.resolve_stripe_customer("cus_abc123")

        assert result == expected_item
        mock_dynamodb.query.assert_called_once_with(
            TableName="test-membership-table",
            IndexName="GSI2",
            KeyConditionExpression="stripe_customer_id = :stripe_id",
            ExpressionAttributeValues={":stripe_id": {"S": "cus_abc123"}},
        )

    def test_returns_none_when_not_found(self, mock_dynamodb):
        mock_dynamodb.query.return_value = {"Items": []}

        result = membership_db.resolve_stripe_customer("cus_nonexistent")

        assert result is None


class TestGetRoleMapping:
    def test_returns_mapping_when_found(self, mock_dynamodb):
        expected_item = {
            "PK": {"S": "CONFIG"},
            "SK": {"S": "ROLE_MAP#BUILDER"},
            "discord_role_id": {"S": "987654321012345678"},
            "tier_name": {"S": "BUILDER"},
        }
        mock_dynamodb.get_item.return_value = {"Item": expected_item}

        result = membership_db.get_role_mapping("BUILDER")

        assert result == expected_item
        mock_dynamodb.get_item.assert_called_once_with(
            TableName="test-membership-table",
            Key={"PK": {"S": "CONFIG"}, "SK": {"S": "ROLE_MAP#BUILDER"}},
        )

    def test_returns_none_when_not_configured(self, mock_dynamodb):
        mock_dynamodb.get_item.return_value = {}

        result = membership_db.get_role_mapping("UNKNOWN_TIER")

        assert result is None


class TestStripeEventIdempotency:
    def test_check_returns_true_when_processed(self, mock_dynamodb):
        mock_dynamodb.get_item.return_value = {
            "Item": {
                "PK": {"S": "STRIPE_EVENT#evt_123"},
                "SK": {"S": "PROCESSED"},
            }
        }

        result = membership_db.check_stripe_event_processed("evt_123")

        assert result is True

    def test_check_returns_false_when_not_processed(self, mock_dynamodb):
        mock_dynamodb.get_item.return_value = {}

        result = membership_db.check_stripe_event_processed("evt_new")

        assert result is False

    def test_mark_processed_puts_item_with_ttl(self, mock_dynamodb):
        membership_db.mark_stripe_event_processed("evt_456")

        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args
        item = call_args[1]["Item"]
        assert item["PK"] == {"S": "STRIPE_EVENT#evt_456"}
        assert item["SK"] == {"S": "PROCESSED"}
        # TTL should be approximately 7 days from now
        expires_at = int(item["expires_at"]["N"])
        assert expires_at > int(time.time()) + 604000
        assert expires_at < int(time.time()) + 605000


class TestOAuthState:
    def test_store_puts_item_with_ttl(self, mock_dynamodb):
        membership_db.store_oauth_state("random_state_abc", "user1")

        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args
        item = call_args[1]["Item"]
        assert item["PK"] == {"S": "OAUTH_STATE#random_state_abc"}
        assert item["SK"] == {"S": "STATE"}
        assert item["user_id"] == {"S": "user1"}
        # TTL should be approximately 10 minutes from now
        expires_at = int(item["expires_at"]["N"])
        assert expires_at > int(time.time()) + 500
        assert expires_at < int(time.time()) + 700

    def test_validate_returns_user_id_and_deletes(self, mock_dynamodb):
        future_time = str(int(time.time()) + 300)
        mock_dynamodb.get_item.return_value = {
            "Item": {
                "PK": {"S": "OAUTH_STATE#state123"},
                "SK": {"S": "STATE"},
                "user_id": {"S": "user42"},
                "expires_at": {"N": future_time},
            }
        }

        result = membership_db.validate_oauth_state("state123")

        assert result == "user42"
        # Should delete the state record after validation
        mock_dynamodb.delete_item.assert_called_once_with(
            TableName="test-membership-table",
            Key={
                "PK": {"S": "OAUTH_STATE#state123"},
                "SK": {"S": "STATE"},
            },
        )

    def test_validate_returns_none_when_not_found(self, mock_dynamodb):
        mock_dynamodb.get_item.return_value = {}

        result = membership_db.validate_oauth_state("invalid_state")

        assert result is None
        mock_dynamodb.delete_item.assert_not_called()

    def test_validate_returns_none_when_expired(self, mock_dynamodb):
        past_time = str(int(time.time()) - 100)
        mock_dynamodb.get_item.return_value = {
            "Item": {
                "PK": {"S": "OAUTH_STATE#old_state"},
                "SK": {"S": "STATE"},
                "user_id": {"S": "user1"},
                "expires_at": {"N": past_time},
            }
        }

        result = membership_db.validate_oauth_state("old_state")

        assert result is None


class TestGetUserAuditLog:
    def test_queries_with_correct_params(self, mock_dynamodb):
        mock_dynamodb.query.return_value = {"Items": []}

        membership_db.get_user_audit_log("user1", limit=50)

        mock_dynamodb.query.assert_called_once_with(
            TableName="test-membership-table",
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": "USER#user1"},
                ":sk_prefix": {"S": "AUDIT#"},
            },
            ScanIndexForward=False,
            Limit=50,
        )

    def test_returns_items(self, mock_dynamodb):
        items = [
            {
                "PK": {"S": "USER#user1"},
                "SK": {"S": "AUDIT#2024-01-02T00:00:00Z#ULID1"},
            },
            {
                "PK": {"S": "USER#user1"},
                "SK": {"S": "AUDIT#2024-01-01T00:00:00Z#ULID2"},
            },
        ]
        mock_dynamodb.query.return_value = {"Items": items}

        result = membership_db.get_user_audit_log("user1")

        assert result == items

    def test_default_limit_is_100(self, mock_dynamodb):
        mock_dynamodb.query.return_value = {"Items": []}

        membership_db.get_user_audit_log("user1")

        call_args = mock_dynamodb.query.call_args
        assert call_args[1]["Limit"] == 100


class TestGetDiscordHistory:
    def test_queries_with_correct_params(self, mock_dynamodb):
        mock_dynamodb.query.return_value = {"Items": []}

        membership_db.get_discord_history("user1")

        mock_dynamodb.query.assert_called_once_with(
            TableName="test-membership-table",
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": "USER#user1"},
                ":sk_prefix": {"S": "DISCORD#"},
            },
            ScanIndexForward=False,
        )

    def test_returns_items(self, mock_dynamodb):
        items = [
            {
                "PK": {"S": "USER#user1"},
                "SK": {"S": "DISCORD#123456789012345678"},
                "active": {"BOOL": True},
            },
            {
                "PK": {"S": "USER#user1"},
                "SK": {"S": "DISCORD#987654321098765432"},
                "active": {"BOOL": False},
            },
        ]
        mock_dynamodb.query.return_value = {"Items": items}

        result = membership_db.get_discord_history("user1")

        assert len(result) == 2


class TestTableNameMissing:
    def test_raises_when_table_name_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove MEMBERSHIP_TABLE from env
            os.environ.pop("MEMBERSHIP_TABLE", None)
            with pytest.raises(
                Exception, match="MEMBERSHIP_TABLE environment variable not set"
            ):
                membership_db.get_membership("user1")
