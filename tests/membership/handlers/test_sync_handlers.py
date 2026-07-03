"""Unit tests for sync_handlers.py — SQS event handler and reconciliation handler."""

import json
import os
import time
from unittest.mock import patch, MagicMock, call

import pytest

# Set required env vars before importing the module
os.environ.setdefault("MEMBERSHIP_TABLE", "test-membership-table")

from handlers.sync_handlers import (
    handle_sqs_event,
    handle_reconciliation,
    _acquire_reconciliation_lock,
    _release_reconciliation_lock,
    _scan_active_discord_users,
    RECONCILIATION_TIMEOUT_SECONDS,
)


class TestHandleSqsEvent:
    """Tests for handle_sqs_event handler."""

    @patch("services.discord_sync.sync_discord_roles")
    def test_processes_single_record_successfully(self, mock_sync):
        """Single valid SQS record triggers sync and returns 200."""
        event = {
            "Records": [
                {
                    "messageId": "msg-001",
                    "body": json.dumps(
                        {
                            "user_id": "user123",
                            "event_type": "tier_change",
                            "timestamp": "2024-01-15T10:00:00Z",
                        }
                    ),
                }
            ]
        }

        result = handle_sqs_event(event)

        assert result["statusCode"] == 200
        assert "1" in result["body"]
        mock_sync.assert_called_once_with("user123")

    @patch("services.discord_sync.sync_discord_roles")
    def test_processes_multiple_records(self, mock_sync):
        """Multiple SQS records each trigger sync."""
        event = {
            "Records": [
                {
                    "messageId": "msg-001",
                    "body": json.dumps(
                        {"user_id": "user1", "event_type": "tier_change"}
                    ),
                },
                {
                    "messageId": "msg-002",
                    "body": json.dumps(
                        {"user_id": "user2", "event_type": "discord_connected"}
                    ),
                },
            ]
        }

        result = handle_sqs_event(event)

        assert result["statusCode"] == 200
        assert mock_sync.call_count == 2
        mock_sync.assert_any_call("user1")
        mock_sync.assert_any_call("user2")

    @patch("services.discord_sync.sync_discord_roles")
    def test_skips_record_without_user_id(self, mock_sync):
        """Records missing user_id are skipped without raising."""
        event = {
            "Records": [
                {
                    "messageId": "msg-001",
                    "body": json.dumps({"event_type": "tier_change"}),
                }
            ]
        }

        result = handle_sqs_event(event)

        assert result["statusCode"] == 200
        mock_sync.assert_not_called()

    @patch("services.discord_sync.sync_discord_roles")
    def test_raises_on_sync_failure(self, mock_sync):
        """Sync failure raises exception for SQS retry."""
        mock_sync.side_effect = RuntimeError("Discord API timeout")

        event = {
            "Records": [
                {
                    "messageId": "msg-001",
                    "body": json.dumps(
                        {"user_id": "user123", "event_type": "tier_change"}
                    ),
                }
            ]
        }

        with pytest.raises(RuntimeError, match="Discord API timeout"):
            handle_sqs_event(event)

    def test_raises_on_invalid_json(self):
        """Invalid JSON in message body raises ValueError for retry."""
        event = {
            "Records": [
                {
                    "messageId": "msg-001",
                    "body": "not valid json {{{",
                }
            ]
        }

        with pytest.raises(ValueError, match="Invalid JSON"):
            handle_sqs_event(event)

    @patch("services.discord_sync.sync_discord_roles")
    def test_handles_empty_records(self, mock_sync):
        """Event with empty Records list returns 200."""
        event = {"Records": []}

        result = handle_sqs_event(event)

        assert result["statusCode"] == 200
        mock_sync.assert_not_called()

    @patch("services.discord_sync.sync_discord_roles")
    def test_handles_no_records_key(self, mock_sync):
        """Event without Records key returns 200."""
        event = {}

        result = handle_sqs_event(event)

        assert result["statusCode"] == 200
        mock_sync.assert_not_called()


class TestHandleReconciliation:
    """Tests for handle_reconciliation handler."""

    @patch("handlers.sync_handlers._release_reconciliation_lock")
    @patch("handlers.sync_handlers._write_reconciliation_audit")
    @patch("handlers.sync_handlers.time.sleep")
    @patch("services.discord_sync.sync_discord_roles")
    @patch("handlers.sync_handlers._scan_active_discord_users")
    @patch("handlers.sync_handlers._acquire_reconciliation_lock")
    @patch("handlers.sync_handlers.boto3.client")
    def test_successful_reconciliation(
        self,
        mock_boto,
        mock_lock,
        mock_scan,
        mock_sync,
        mock_sleep,
        mock_audit,
        mock_release,
    ):
        """Successful reconciliation processes all users and returns metrics."""
        mock_lock.return_value = True
        mock_scan.return_value = [
            {"PK": {"S": "USER#user1"}, "SK": {"S": "DISCORD_ACTIVE"}},
            {"PK": {"S": "USER#user2"}, "SK": {"S": "DISCORD_ACTIVE"}},
        ]
        mock_sync.return_value = None

        result = handle_reconciliation({"source": "aws.scheduler"})

        assert result["statusCode"] == 200
        body = result["body"]
        assert body["total_processed"] == 2
        assert body["successful"] == 2
        assert body["failed"] == 0
        assert body["timed_out"] is False
        assert mock_sync.call_count == 2
        assert mock_sleep.call_count == 2
        mock_release.assert_called_once()

    @patch("handlers.sync_handlers._release_reconciliation_lock")
    @patch("handlers.sync_handlers._write_reconciliation_audit")
    @patch("handlers.sync_handlers.time.sleep")
    @patch("services.discord_sync.sync_discord_roles")
    @patch("handlers.sync_handlers._scan_active_discord_users")
    @patch("handlers.sync_handlers._acquire_reconciliation_lock")
    @patch("handlers.sync_handlers.boto3.client")
    def test_skips_if_lock_not_acquired(
        self,
        mock_boto,
        mock_lock,
        mock_scan,
        mock_sync,
        mock_sleep,
        mock_audit,
        mock_release,
    ):
        """Reconciliation skips if another instance holds the lock."""
        mock_lock.return_value = False

        result = handle_reconciliation({"source": "aws.scheduler"})

        assert result["statusCode"] == 200
        assert "skipped" in result["body"]
        mock_scan.assert_not_called()
        mock_sync.assert_not_called()

    @patch("handlers.sync_handlers._release_reconciliation_lock")
    @patch("handlers.sync_handlers._write_reconciliation_audit")
    @patch("handlers.sync_handlers.time.sleep")
    @patch("services.discord_sync.sync_discord_roles")
    @patch("handlers.sync_handlers._scan_active_discord_users")
    @patch("handlers.sync_handlers._acquire_reconciliation_lock")
    @patch("handlers.sync_handlers.boto3.client")
    def test_continues_on_per_user_failure(
        self,
        mock_boto,
        mock_lock,
        mock_scan,
        mock_sync,
        mock_sleep,
        mock_audit,
        mock_release,
    ):
        """Per-user sync failure is logged but doesn't stop processing."""
        mock_lock.return_value = True
        mock_scan.return_value = [
            {"PK": {"S": "USER#user1"}, "SK": {"S": "DISCORD_ACTIVE"}},
            {"PK": {"S": "USER#user2"}, "SK": {"S": "DISCORD_ACTIVE"}},
            {"PK": {"S": "USER#user3"}, "SK": {"S": "DISCORD_ACTIVE"}},
        ]
        # Second user fails
        mock_sync.side_effect = [None, RuntimeError("API error"), None]

        result = handle_reconciliation({"source": "aws.scheduler"})

        body = result["body"]
        assert body["total_processed"] == 3
        assert body["successful"] == 2
        assert body["failed"] == 1
        assert body["timed_out"] is False
        mock_release.assert_called_once()

    @patch("handlers.sync_handlers._release_reconciliation_lock")
    @patch("handlers.sync_handlers._write_reconciliation_audit")
    @patch("handlers.sync_handlers.time.sleep")
    @patch("services.discord_sync.sync_discord_roles")
    @patch("handlers.sync_handlers._scan_active_discord_users")
    @patch("handlers.sync_handlers._acquire_reconciliation_lock")
    @patch("handlers.sync_handlers.boto3.client")
    @patch("handlers.sync_handlers.time.time")
    def test_enforces_timeout(
        self,
        mock_time,
        mock_boto,
        mock_lock,
        mock_scan,
        mock_sync,
        mock_sleep,
        mock_audit,
        mock_release,
    ):
        """Reconciliation terminates when 4-hour timeout is exceeded."""
        mock_lock.return_value = True
        mock_scan.return_value = [
            {"PK": {"S": "USER#user1"}, "SK": {"S": "DISCORD_ACTIVE"}},
            {"PK": {"S": "USER#user2"}, "SK": {"S": "DISCORD_ACTIVE"}},
            {"PK": {"S": "USER#user3"}, "SK": {"S": "DISCORD_ACTIVE"}},
        ]
        # time.time() calls in handle_reconciliation:
        # 1. start_time = time.time()
        # 2. elapsed = time.time() - start_time (user1 check, 0s elapsed - proceed)
        # 3. elapsed = time.time() - start_time (user2 check, >14400s - timeout)
        # 4. metrics["elapsed_seconds"] = int(time.time() - start_time)
        mock_time.side_effect = [
            1000.0,  # start_time
            1000.0,  # elapsed check for user1 (0s elapsed, proceed)
            15400.0,  # elapsed check for user2 (14400s exceeded, break)
            15400.0,  # elapsed_seconds calculation
        ]
        mock_sync.return_value = None

        result = handle_reconciliation({"source": "aws.scheduler"})

        body = result["body"]
        assert body["total_processed"] == 1
        assert body["timed_out"] is True
        mock_release.assert_called_once()

    @patch("handlers.sync_handlers._release_reconciliation_lock")
    @patch("handlers.sync_handlers._write_reconciliation_audit")
    @patch("handlers.sync_handlers.time.sleep")
    @patch("services.discord_sync.sync_discord_roles")
    @patch("handlers.sync_handlers._scan_active_discord_users")
    @patch("handlers.sync_handlers._acquire_reconciliation_lock")
    @patch("handlers.sync_handlers.boto3.client")
    def test_releases_lock_on_exception(
        self,
        mock_boto,
        mock_lock,
        mock_scan,
        mock_sync,
        mock_sleep,
        mock_audit,
        mock_release,
    ):
        """Lock is released even if an unexpected exception occurs."""
        mock_lock.return_value = True
        mock_scan.side_effect = RuntimeError("DynamoDB scan failed")

        with pytest.raises(RuntimeError):
            handle_reconciliation({"source": "aws.scheduler"})

        mock_release.assert_called_once()

    @patch("handlers.sync_handlers._release_reconciliation_lock")
    @patch("handlers.sync_handlers._write_reconciliation_audit")
    @patch("handlers.sync_handlers.time.sleep")
    @patch("services.discord_sync.sync_discord_roles")
    @patch("handlers.sync_handlers._scan_active_discord_users")
    @patch("handlers.sync_handlers._acquire_reconciliation_lock")
    @patch("handlers.sync_handlers.boto3.client")
    def test_writes_audit_entries(
        self,
        mock_boto,
        mock_lock,
        mock_scan,
        mock_sync,
        mock_sleep,
        mock_audit,
        mock_release,
    ):
        """Reconciliation writes Started and Completed audit entries."""
        mock_lock.return_value = True
        mock_scan.return_value = []
        mock_sync.return_value = None

        handle_reconciliation({"source": "aws.scheduler"})

        assert mock_audit.call_count == 2
        # First call is Reconciliation_Started
        first_call_args = mock_audit.call_args_list[0]
        from models.audit_event import AuditEventType

        assert first_call_args[0][0] == AuditEventType.RECONCILIATION_STARTED
        # Second call is Reconciliation_Completed
        second_call_args = mock_audit.call_args_list[1]
        assert second_call_args[0][0] == AuditEventType.RECONCILIATION_COMPLETED

    @patch("handlers.sync_handlers._release_reconciliation_lock")
    @patch("handlers.sync_handlers._write_reconciliation_audit")
    @patch("handlers.sync_handlers.time.sleep")
    @patch("services.discord_sync.sync_discord_roles")
    @patch("handlers.sync_handlers._scan_active_discord_users")
    @patch("handlers.sync_handlers._acquire_reconciliation_lock")
    @patch("handlers.sync_handlers.boto3.client")
    def test_handles_empty_scan(
        self,
        mock_boto,
        mock_lock,
        mock_scan,
        mock_sync,
        mock_sleep,
        mock_audit,
        mock_release,
    ):
        """Empty scan (no active users) still succeeds."""
        mock_lock.return_value = True
        mock_scan.return_value = []

        result = handle_reconciliation({"source": "aws.scheduler"})

        body = result["body"]
        assert body["total_processed"] == 0
        assert body["successful"] == 0
        assert body["failed"] == 0


class TestAcquireReconciliationLock:
    """Tests for the concurrency lock acquisition."""

    def test_acquires_lock_successfully(self):
        """Lock is acquired when no existing lock exists."""
        mock_dynamodb = MagicMock()
        mock_dynamodb.put_item.return_value = {}

        result = _acquire_reconciliation_lock(mock_dynamodb)

        assert result is True
        mock_dynamodb.put_item.assert_called_once()
        call_kwargs = mock_dynamodb.put_item.call_args[1]
        assert call_kwargs["ConditionExpression"] == "attribute_not_exists(PK)"
        item = call_kwargs["Item"]
        assert item["PK"]["S"] == "RECONCILIATION_LOCK"
        assert item["SK"]["S"] == "ACTIVE"
        assert "expires_at" in item

    def test_returns_false_when_lock_exists(self):
        """Returns False when another reconciliation holds the lock."""
        mock_dynamodb = MagicMock()
        error_response = {
            "Error": {"Code": "ConditionalCheckFailedException", "Message": ""}
        }
        mock_dynamodb.put_item.side_effect = ClientError(error_response, "PutItem")

        result = _acquire_reconciliation_lock(mock_dynamodb)

        assert result is False

    def test_raises_on_unexpected_error(self):
        """Unexpected DynamoDB errors are re-raised."""
        mock_dynamodb = MagicMock()
        error_response = {"Error": {"Code": "InternalServerError", "Message": ""}}
        mock_dynamodb.put_item.side_effect = ClientError(error_response, "PutItem")

        with pytest.raises(ClientError):
            _acquire_reconciliation_lock(mock_dynamodb)


class TestReleaseReconciliationLock:
    """Tests for the concurrency lock release."""

    def test_releases_lock_successfully(self):
        """Lock deletion call made with correct key."""
        mock_dynamodb = MagicMock()
        mock_dynamodb.delete_item.return_value = {}

        _release_reconciliation_lock(mock_dynamodb)

        mock_dynamodb.delete_item.assert_called_once()
        call_kwargs = mock_dynamodb.delete_item.call_args[1]
        assert call_kwargs["Key"]["PK"]["S"] == "RECONCILIATION_LOCK"
        assert call_kwargs["Key"]["SK"]["S"] == "ACTIVE"

    def test_does_not_raise_on_error(self):
        """Lock release errors are logged but don't raise."""
        mock_dynamodb = MagicMock()
        error_response = {"Error": {"Code": "InternalServerError", "Message": ""}}
        mock_dynamodb.delete_item.side_effect = ClientError(
            error_response, "DeleteItem"
        )

        # Should not raise
        _release_reconciliation_lock(mock_dynamodb)


class TestScanActiveDiscordUsers:
    """Tests for the DynamoDB scan helper."""

    def test_returns_matching_items(self):
        """Returns items from scan with correct filter."""
        mock_dynamodb = MagicMock()
        mock_dynamodb.scan.return_value = {
            "Items": [
                {"PK": {"S": "USER#user1"}, "SK": {"S": "DISCORD_ACTIVE"}},
                {"PK": {"S": "USER#user2"}, "SK": {"S": "DISCORD_ACTIVE"}},
            ]
        }

        result = _scan_active_discord_users(mock_dynamodb)

        assert len(result) == 2
        mock_dynamodb.scan.assert_called_once()
        call_kwargs = mock_dynamodb.scan.call_args[1]
        assert call_kwargs["FilterExpression"] == "SK = :sk"
        assert call_kwargs["ExpressionAttributeValues"][":sk"]["S"] == "DISCORD_ACTIVE"

    def test_handles_pagination(self):
        """Handles paginated scan results."""
        mock_dynamodb = MagicMock()
        mock_dynamodb.scan.side_effect = [
            {
                "Items": [{"PK": {"S": "USER#user1"}, "SK": {"S": "DISCORD_ACTIVE"}}],
                "LastEvaluatedKey": {
                    "PK": {"S": "USER#user1"},
                    "SK": {"S": "DISCORD_ACTIVE"},
                },
            },
            {
                "Items": [{"PK": {"S": "USER#user2"}, "SK": {"S": "DISCORD_ACTIVE"}}],
            },
        ]

        result = _scan_active_discord_users(mock_dynamodb)

        assert len(result) == 2
        assert mock_dynamodb.scan.call_count == 2

    def test_returns_empty_list_when_no_items(self):
        """Returns empty list when no active Discord users found."""
        mock_dynamodb = MagicMock()
        mock_dynamodb.scan.return_value = {"Items": []}

        result = _scan_active_discord_users(mock_dynamodb)

        assert result == []
