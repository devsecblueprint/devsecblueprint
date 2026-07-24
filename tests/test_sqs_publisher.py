"""
Tests for SQS Publisher Service.
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

from backend.membership.services.sqs_publisher import publish_sync_event


class TestPublishSyncEvent:
    """Test the publish_sync_event function."""

    @patch.dict(
        os.environ,
        {
            "DISCORD_SYNC_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123456789/dsb-discord-sync.fifo"
        },
    )
    @patch("backend.membership.services.sqs_publisher.boto3")
    def test_publish_success(self, mock_boto3):
        """Test successful message publish to SQS FIFO queue."""
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}

        result = publish_sync_event("user-abc", "tier_change", "BUILDER")

        assert result is True
        mock_boto3.client.assert_called_once_with("sqs")
        mock_sqs.send_message.assert_called_once()

        call_kwargs = mock_sqs.send_message.call_args[1]
        assert (
            call_kwargs["QueueUrl"]
            == "https://sqs.us-east-1.amazonaws.com/123456789/dsb-discord-sync.fifo"
        )
        assert call_kwargs["MessageGroupId"] == "user-abc"

        body = json.loads(call_kwargs["MessageBody"])
        assert body["user_id"] == "user-abc"
        assert body["event_type"] == "tier_change"
        assert body["new_membership_tier"] == "BUILDER"
        assert "timestamp" in body

    @patch.dict(
        os.environ,
        {
            "DISCORD_SYNC_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123456789/dsb-discord-sync.fifo"
        },
    )
    @patch("backend.membership.services.sqs_publisher.boto3")
    def test_publish_with_none_tier(self, mock_boto3):
        """Test publish when new_tier is None (e.g., discord_connected event)."""
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs
        mock_sqs.send_message.return_value = {"MessageId": "msg-456"}

        result = publish_sync_event("user-xyz", "discord_connected")

        assert result is True
        call_kwargs = mock_sqs.send_message.call_args[1]
        body = json.loads(call_kwargs["MessageBody"])
        assert body["new_membership_tier"] is None

    @patch.dict(
        os.environ,
        {
            "DISCORD_SYNC_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123456789/dsb-discord-sync.fifo"
        },
    )
    @patch("backend.membership.services.sqs_publisher.boto3")
    def test_message_group_id_set_to_user_id(self, mock_boto3):
        """Test that MessageGroupId is set to user_id for per-user ordering."""
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs
        mock_sqs.send_message.return_value = {"MessageId": "msg-789"}

        publish_sync_event("user-ordering-test", "admin_sync", "EXPLORER")

        call_kwargs = mock_sqs.send_message.call_args[1]
        assert call_kwargs["MessageGroupId"] == "user-ordering-test"

    @patch.dict(
        os.environ,
        {
            "DISCORD_SYNC_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123456789/dsb-discord-sync.fifo"
        },
    )
    @patch("backend.membership.services.sqs_publisher.boto3")
    def test_message_body_json_format(self, mock_boto3):
        """Test that the message body contains required fields as JSON."""
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs
        mock_sqs.send_message.return_value = {"MessageId": "msg-001"}

        publish_sync_event("user-format", "tier_change", "FREE")

        call_kwargs = mock_sqs.send_message.call_args[1]
        body = json.loads(call_kwargs["MessageBody"])

        assert "user_id" in body
        assert "event_type" in body
        assert "timestamp" in body
        assert "new_membership_tier" in body

    @patch.dict(
        os.environ,
        {
            "DISCORD_SYNC_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123456789/dsb-discord-sync.fifo"
        },
    )
    @patch("backend.membership.services.sqs_publisher.boto3")
    def test_timestamp_is_iso8601_utc(self, mock_boto3):
        """Test that the timestamp is ISO 8601 format in UTC."""
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs
        mock_sqs.send_message.return_value = {"MessageId": "msg-002"}

        publish_sync_event("user-ts", "tier_change", "BUILDER")

        call_kwargs = mock_sqs.send_message.call_args[1]
        body = json.loads(call_kwargs["MessageBody"])
        timestamp = body["timestamp"]
        # ISO 8601 UTC timestamps end with +00:00
        assert "+00:00" in timestamp or "Z" in timestamp

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_queue_url_returns_false(self):
        """Test that missing DISCORD_SYNC_QUEUE_URL returns False without crashing."""
        # Ensure the env var is not set
        os.environ.pop("DISCORD_SYNC_QUEUE_URL", None)

        result = publish_sync_event("user-no-url", "tier_change", "BUILDER")

        assert result is False

    @patch.dict(
        os.environ,
        {
            "DISCORD_SYNC_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123456789/dsb-discord-sync.fifo"
        },
    )
    @patch("backend.membership.services.sqs_publisher.boto3")
    def test_client_error_returns_false(self, mock_boto3):
        """Test that SQS ClientError is handled gracefully (returns False, no crash)."""
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs
        mock_sqs.send_message.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service unavailable"}},
            "SendMessage",
        )

        result = publish_sync_event("user-err", "tier_change", "EXPLORER")

        assert result is False

    @patch.dict(
        os.environ,
        {
            "DISCORD_SYNC_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123456789/dsb-discord-sync.fifo"
        },
    )
    @patch("backend.membership.services.sqs_publisher.boto3")
    def test_unexpected_exception_returns_false(self, mock_boto3):
        """Test that unexpected exceptions are handled gracefully."""
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs
        mock_sqs.send_message.side_effect = RuntimeError("Unexpected failure")

        result = publish_sync_event("user-unexpected", "tier_change", "BUILDER")

        assert result is False

    @patch.dict(
        os.environ,
        {
            "DISCORD_SYNC_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123456789/dsb-discord-sync.fifo"
        },
    )
    @patch("backend.membership.services.sqs_publisher.boto3")
    def test_no_message_deduplication_id_set(self, mock_boto3):
        """Test that MessageDeduplicationId is NOT explicitly set (content-based deduplication)."""
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs
        mock_sqs.send_message.return_value = {"MessageId": "msg-dedup"}

        publish_sync_event("user-dedup", "tier_change", "BUILDER")

        call_kwargs = mock_sqs.send_message.call_args[1]
        assert "MessageDeduplicationId" not in call_kwargs
