"""Unit tests for the audit logging service."""

import os
from unittest.mock import patch, MagicMock

import pytest

# Set required env vars before importing the module
os.environ.setdefault("MEMBERSHIP_TABLE", "test-membership-table")

from services.audit import generate_ulid_suffix, write_audit_log
from models.audit_event import AuditEvent, AuditEventType


class TestGenerateUlidSuffix:
    def test_returns_string(self):
        result = generate_ulid_suffix()
        assert isinstance(result, str)

    def test_returns_lowercase(self):
        result = generate_ulid_suffix()
        assert result == result.lower()

    def test_no_padding(self):
        result = generate_ulid_suffix()
        assert "=" not in result

    def test_unique_values(self):
        """Multiple calls should produce different values (collision avoidance)."""
        results = {generate_ulid_suffix() for _ in range(100)}
        # With 6 random bytes, collisions in 100 attempts are astronomically unlikely
        assert len(results) == 100


class TestWriteAuditLog:
    @patch("services.audit._dynamodb_client")
    def test_writes_to_dynamodb(self, mock_client):
        event = AuditEvent.build(
            AuditEventType.CONNECTED,
            dsb_user_id="user123",
            actor="user:user123",
            timestamp="2024-01-15T10:30:00.123Z",
        ).with_discord("123456789012345678")

        write_audit_log(event)

        mock_client.put_item.assert_called_once()
        call_kwargs = mock_client.put_item.call_args[1]
        assert call_kwargs["TableName"] == "test-membership-table"

        item = call_kwargs["Item"]
        assert item["PK"] == {"S": "USER#user123"}
        assert item["SK"]["S"].startswith("AUDIT#2024-01-15T10:30:00.123Z#")
        assert item["event_type"] == {"S": "Connected"}
        assert item["dsb_user_id"] == {"S": "user123"}
        assert item["actor"] == {"S": "user:user123"}
        assert item["timestamp"] == {"S": "2024-01-15T10:30:00.123Z"}
        assert item["discord_user_id"] == {"S": "123456789012345678"}

    @patch("services.audit._dynamodb_client")
    def test_null_for_unset_conditional_fields(self, mock_client):
        """Conditional fields not set should be stored as NULL in DynamoDB."""
        event = AuditEvent.build(
            AuditEventType.SUBSCRIPTION_CREATED,
            dsb_user_id="user1",
            actor="stripe",
            timestamp="2024-01-15T10:30:00.123Z",
        )

        write_audit_log(event)

        item = mock_client.put_item.call_args[1]["Item"]
        # GSI key attributes (discord_user_id) must NOT be present as NULL —
        # DynamoDB rejects NULL for index key attributes. Omission is correct.
        assert "discord_user_id" not in item
        # Non-GSI conditional fields should be stored as NULL
        assert item["previous_state"] == {"NULL": True}
        assert item["new_state"] == {"NULL": True}
        assert item["roles_added"] == {"NULL": True}
        assert item["roles_removed"] == {"NULL": True}
        assert item["stripe_subscription_id"] == {"NULL": True}
        assert item["stripe_event_id"] == {"NULL": True}
        assert item["reason"] == {"NULL": True}
        assert item["error_message"] == {"NULL": True}

    @patch("services.audit._dynamodb_client")
    def test_list_fields_as_dynamodb_list(self, mock_client):
        """roles_added and roles_removed should be stored as DynamoDB List type."""
        event = AuditEvent.build(
            AuditEventType.ROLES_ADDED,
            dsb_user_id="user1",
            actor="system",
            timestamp="2024-01-15T10:30:00.123Z",
        ).with_roles(added=["role_a", "role_b"], removed=["role_c"])

        write_audit_log(event)

        item = mock_client.put_item.call_args[1]["Item"]
        assert item["roles_added"] == {"L": [{"S": "role_a"}, {"S": "role_b"}]}
        assert item["roles_removed"] == {"L": [{"S": "role_c"}]}

    @patch("services.audit._dynamodb_client")
    def test_never_raises_on_dynamodb_failure(self, mock_client):
        """DynamoDB failures should be logged, never raised."""
        mock_client.put_item.side_effect = Exception("DynamoDB unavailable")

        event = AuditEvent.build(
            AuditEventType.SYNC_FAILED,
            dsb_user_id="user1",
            actor="system",
        )

        # Should not raise
        write_audit_log(event)

    @patch("services.audit._dynamodb_client")
    @patch("services.audit.logger")
    def test_logs_error_on_failure(self, mock_logger, mock_client):
        """On failure, logs to CloudWatch via logger.error."""
        mock_client.put_item.side_effect = Exception("Connection timeout")

        event = AuditEvent.build(
            AuditEventType.SYNC_FAILED,
            dsb_user_id="user1",
            actor="system",
        )

        write_audit_log(event)

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0]
        assert "Failed to write audit log" in call_args[0]
        assert "Sync_Failed" in call_args[1]

    @patch("services.audit._dynamodb_client")
    def test_truncates_reason_and_error_message(self, mock_client):
        """Reason (max 500) and error_message (max 1000) should be truncated."""
        event = (
            AuditEvent.build(
                AuditEventType.ADMIN_OVERRIDE,
                dsb_user_id="user1",
                actor="admin:admin1",
                timestamp="2024-01-15T10:30:00.123Z",
            )
            .with_reason("x" * 600)
            .with_error("e" * 1200)
        )

        write_audit_log(event)

        item = mock_client.put_item.call_args[1]["Item"]
        assert len(item["reason"]["S"]) == 500
        assert len(item["error_message"]["S"]) == 1000

    @patch("services.audit._dynamodb_client")
    @patch("services.audit.logger")
    def test_logs_success_info(self, mock_logger, mock_client):
        """Successful writes log an info message."""
        event = AuditEvent.build(
            AuditEventType.VERIFIED,
            dsb_user_id="user1",
            actor="user:user1",
            timestamp="2024-01-15T10:30:00.123Z",
        )

        write_audit_log(event)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0]
        assert "Audit log written" in call_args[0]
