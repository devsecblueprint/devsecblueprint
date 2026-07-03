"""Unit tests for the admin Discord service functions."""

import os
from unittest.mock import patch, MagicMock

import pytest

# Set required env vars before importing
os.environ.setdefault("MEMBERSHIP_TABLE", "test-membership-table")
os.environ.setdefault(
    "DISCORD_SYNC_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123/queue.fifo"
)
os.environ.setdefault("DISCORD_BOT_SECRET_NAME", "test-bot-secret")
os.environ.setdefault("DISCORD_GUILD_ID", "12345678901234567")

from services.admin_discord import (
    get_admin_user_detail,
    admin_trigger_sync,
    admin_disconnect,
    get_admin_audit_log,
)


class TestGetAdminUserDetail:
    """Tests for get_admin_user_detail."""

    @patch("services.admin_discord.get_discord_active")
    @patch("services.admin_discord.get_membership")
    def test_returns_none_when_no_records(self, mock_membership, mock_discord):
        """Returns None (404 indicator) when user has no records."""
        mock_membership.return_value = None
        mock_discord.return_value = None

        result = get_admin_user_detail("user123")

        assert result is None

    @patch("services.admin_discord.get_discord_active")
    @patch("services.admin_discord.get_membership")
    def test_returns_detail_with_membership_only(self, mock_membership, mock_discord):
        """Returns user detail when only membership record exists."""
        mock_membership.return_value = {
            "PK": {"S": "USER#user123"},
            "SK": {"S": "MEMBERSHIP"},
            "membership_tier": {"S": "EXPLORER"},
            "subscription_status": {"S": "active"},
            "stripe_customer_id": {"S": "cus_abc123"},
        }
        mock_discord.return_value = None

        result = get_admin_user_detail("user123")

        assert result is not None
        assert result["user_id"] == "user123"
        assert result["membership_tier"] == "EXPLORER"
        assert result["stripe_subscription_status"] == "active"
        assert result["stripe_customer_id"] == "cus_abc123"
        assert result["discord_connected"] is False
        assert result["discord_username"] is None
        assert result["discord_user_id"] is None

    @patch("services.admin_discord.get_discord_active")
    @patch("services.admin_discord.get_membership")
    def test_returns_detail_with_discord_connected(self, mock_membership, mock_discord):
        """Returns full detail when Discord is connected."""
        mock_membership.return_value = {
            "PK": {"S": "USER#user123"},
            "SK": {"S": "MEMBERSHIP"},
            "membership_tier": {"S": "BUILDER"},
            "subscription_status": {"S": "active"},
            "stripe_customer_id": {"S": "cus_xyz"},
        }
        mock_discord.return_value = {
            "PK": {"S": "USER#user123"},
            "SK": {"S": "DISCORD_ACTIVE"},
            "discord_user_id": {"S": "98765432109876543"},
            "username": {"S": "testuser#1234"},
            "platform_state": {"S": "Discord_Verified"},
            "last_synced_at": {"S": "2024-01-15T10:30:00Z"},
            "last_sync_status": {"S": "success"},
        }

        result = get_admin_user_detail("user123")

        assert result["discord_connected"] is True
        assert result["discord_username"] == "testuser#1234"
        assert result["discord_user_id"] == "98765432109876543"
        assert result["platform_state"] == "Discord_Verified"
        assert result["last_synced_at"] == "2024-01-15T10:30:00Z"
        assert result["last_sync_status"] == "success"
        assert result["membership_tier"] == "BUILDER"

    @patch("services.admin_discord.get_discord_active")
    @patch("services.admin_discord.get_membership")
    def test_returns_detail_with_discord_only(self, mock_membership, mock_discord):
        """Returns detail when only Discord record exists (no membership)."""
        mock_membership.return_value = None
        mock_discord.return_value = {
            "PK": {"S": "USER#user123"},
            "SK": {"S": "DISCORD_ACTIVE"},
            "discord_user_id": {"S": "98765432109876543"},
            "username": {"S": "testuser"},
            "platform_state": {"S": "Discord_Verified"},
        }

        result = get_admin_user_detail("user123")

        assert result is not None
        assert result["discord_connected"] is True
        assert result["membership_tier"] == "FREE"
        assert result["stripe_subscription_status"] is None


class TestAdminTriggerSync:
    """Tests for admin_trigger_sync."""

    @patch("services.admin_discord.write_audit_log")
    @patch("services.admin_discord.publish_sync_event")
    def test_publishes_sync_event(self, mock_publish, mock_audit):
        """Publishes sync event to SQS for the target user."""
        result = admin_trigger_sync("admin1", "user123", "Testing sync")

        mock_publish.assert_called_once_with("user123", "admin_sync", None)
        assert result == {"success": True, "user_id": "user123"}

    @patch("services.admin_discord.write_audit_log")
    @patch("services.admin_discord.publish_sync_event")
    def test_writes_admin_override_audit(self, mock_publish, mock_audit):
        """Writes Admin_Override audit entry with reason."""
        admin_trigger_sync("admin1", "user123", "Manual fix")

        mock_audit.assert_called_once()
        event = mock_audit.call_args[0][0]
        assert event.event_type.value == "Admin_Override"
        assert event.dsb_user_id == "user123"
        assert event.actor == "admin:admin1"
        assert "Sync triggered: Manual fix" in event.reason

    @patch("services.admin_discord.write_audit_log")
    @patch("services.admin_discord.publish_sync_event")
    def test_uses_default_reason(self, mock_publish, mock_audit):
        """Uses default reason when none provided."""
        admin_trigger_sync("admin1", "user123")

        event = mock_audit.call_args[0][0]
        assert "Admin triggered" in event.reason


class TestAdminDisconnect:
    """Tests for admin_disconnect."""

    @patch("services.admin_discord.write_audit_log")
    @patch("services.admin_discord.get_secret")
    @patch("services.admin_discord.deactivate_discord_connection")
    @patch("services.admin_discord.get_discord_active")
    def test_validates_reason_too_short(
        self, mock_active, mock_deactivate, mock_secret, mock_audit
    ):
        """Raises ValueError when reason is less than 5 characters."""
        with pytest.raises(ValueError, match="at least 5 characters"):
            admin_disconnect("admin1", "user123", "Hi")

    @patch("services.admin_discord.write_audit_log")
    @patch("services.admin_discord.get_secret")
    @patch("services.admin_discord.deactivate_discord_connection")
    @patch("services.admin_discord.get_discord_active")
    def test_validates_reason_too_long(
        self, mock_active, mock_deactivate, mock_secret, mock_audit
    ):
        """Raises ValueError when reason exceeds 500 characters."""
        with pytest.raises(ValueError, match="must not exceed 500 characters"):
            admin_disconnect("admin1", "user123", "x" * 501)

    @patch("services.admin_discord.write_audit_log")
    @patch("services.admin_discord.get_secret")
    @patch("services.admin_discord.deactivate_discord_connection")
    @patch("services.admin_discord.get_discord_active")
    def test_validates_empty_reason(
        self, mock_active, mock_deactivate, mock_secret, mock_audit
    ):
        """Raises ValueError when reason is empty."""
        with pytest.raises(ValueError, match="at least 5 characters"):
            admin_disconnect("admin1", "user123", "")

    @patch("services.admin_discord.write_audit_log")
    @patch("services.admin_discord.get_secret")
    @patch("services.admin_discord.deactivate_discord_connection")
    @patch("services.admin_discord.get_discord_active")
    def test_raises_when_no_active_connection(
        self, mock_active, mock_deactivate, mock_secret, mock_audit
    ):
        """Raises ValueError when target user has no active Discord connection."""
        mock_active.return_value = None

        with pytest.raises(ValueError, match="no active Discord connection"):
            admin_disconnect("admin1", "user123", "User violated ToS")

    @patch("services.admin_discord.DiscordClient")
    @patch("services.admin_discord.write_audit_log")
    @patch("services.admin_discord.get_secret")
    @patch("services.admin_discord.deactivate_discord_connection")
    @patch("services.admin_discord.get_discord_active")
    def test_successful_disconnect(
        self, mock_active, mock_deactivate, mock_secret, mock_discord_cls, mock_audit
    ):
        """Successfully disconnects user and removes roles."""
        mock_active.return_value = {
            "discord_user_id": {"S": "98765432109876543"},
        }
        mock_secret.return_value = {"secret_key": "bot-token-123"}
        mock_discord_instance = MagicMock()
        mock_discord_cls.return_value = mock_discord_instance

        result = admin_disconnect("admin1", "user123", "Violated community guidelines")

        assert result["cleanup_status"] == "completed"
        assert result["user_id"] == "user123"

        # Verify deactivation was called
        mock_deactivate.assert_called_once_with(
            "user123", "98765432109876543", "Admin: Violated community guidelines"
        )

    @patch("services.admin_discord.DiscordClient")
    @patch("services.admin_discord.write_audit_log")
    @patch("services.admin_discord.get_secret")
    @patch("services.admin_discord.deactivate_discord_connection")
    @patch("services.admin_discord.get_discord_active")
    def test_writes_both_audit_entries(
        self, mock_active, mock_deactivate, mock_secret, mock_discord_cls, mock_audit
    ):
        """Writes both Admin_Override and Disconnected audit entries."""
        mock_active.return_value = {
            "discord_user_id": {"S": "98765432109876543"},
        }
        mock_secret.return_value = {"secret_key": "bot-token-123"}
        mock_discord_cls.return_value = MagicMock()

        admin_disconnect("admin1", "user123", "Testing disconnect")

        assert mock_audit.call_count == 2
        # First call: Admin_Override
        first_event = mock_audit.call_args_list[0][0][0]
        assert first_event.event_type.value == "Admin_Override"
        assert first_event.actor == "admin:admin1"
        assert first_event.discord_user_id == "98765432109876543"
        # Second call: Disconnected
        second_event = mock_audit.call_args_list[1][0][0]
        assert second_event.event_type.value == "Disconnected"
        assert second_event.actor == "admin:admin1"

    @patch("services.admin_discord.DiscordClient")
    @patch("services.admin_discord.write_audit_log")
    @patch("services.admin_discord.get_secret")
    @patch("services.admin_discord.deactivate_discord_connection")
    @patch("services.admin_discord.get_discord_active")
    def test_cleanup_failed_on_role_removal_error(
        self, mock_active, mock_deactivate, mock_secret, mock_discord_cls, mock_audit
    ):
        """Returns cleanup_status='failed' when role removal raises."""
        mock_active.return_value = {
            "discord_user_id": {"S": "98765432109876543"},
        }
        mock_secret.side_effect = Exception("Secrets Manager unavailable")

        result = admin_disconnect("admin1", "user123", "Admin action reason")

        assert result["cleanup_status"] == "failed"
        # Audit entries are still written even when role removal fails
        assert mock_audit.call_count == 2


class TestGetAdminAuditLog:
    """Tests for get_admin_audit_log."""

    @patch("services.admin_discord.get_user_audit_log")
    def test_returns_formatted_entries(self, mock_audit_log):
        """Formats raw DynamoDB items into readable audit entries."""
        mock_audit_log.return_value = [
            {
                "PK": {"S": "USER#user123"},
                "SK": {"S": "AUDIT#2024-01-15T10:30:00.123Z#abc"},
                "event_type": {"S": "Connected"},
                "timestamp": {"S": "2024-01-15T10:30:00.123Z"},
                "actor": {"S": "user:user123"},
                "dsb_user_id": {"S": "user123"},
                "discord_user_id": {"S": "98765432109876543"},
                "reason": {"NULL": True},
                "error_message": {"NULL": True},
            },
            {
                "PK": {"S": "USER#user123"},
                "SK": {"S": "AUDIT#2024-01-14T09:00:00.000Z#def"},
                "event_type": {"S": "Admin_Override"},
                "timestamp": {"S": "2024-01-14T09:00:00.000Z"},
                "actor": {"S": "admin:admin1"},
                "dsb_user_id": {"S": "user123"},
                "reason": {"S": "Manual sync requested"},
                "discord_user_id": {"NULL": True},
                "error_message": {"NULL": True},
            },
        ]

        result = get_admin_audit_log("user123")

        assert len(result) == 2
        assert result[0]["event_type"] == "Connected"
        assert result[0]["timestamp"] == "2024-01-15T10:30:00.123Z"
        assert result[0]["actor"] == "user:user123"
        assert result[0]["discord_user_id"] == "98765432109876543"
        assert "reason" not in result[0]  # NULL values excluded

        assert result[1]["event_type"] == "Admin_Override"
        assert result[1]["reason"] == "Manual sync requested"
        assert "discord_user_id" not in result[1]  # NULL values excluded

    @patch("services.admin_discord.get_user_audit_log")
    def test_returns_empty_list_for_no_entries(self, mock_audit_log):
        """Returns empty list when no audit entries exist."""
        mock_audit_log.return_value = []

        result = get_admin_audit_log("user123")

        assert result == []
        mock_audit_log.assert_called_once_with("user123", limit=100)

    @patch("services.admin_discord.get_user_audit_log")
    def test_includes_role_lists(self, mock_audit_log):
        """Includes roles_added and roles_removed when present."""
        mock_audit_log.return_value = [
            {
                "PK": {"S": "USER#user123"},
                "SK": {"S": "AUDIT#2024-01-15T10:30:00.123Z#abc"},
                "event_type": {"S": "Roles_Added"},
                "timestamp": {"S": "2024-01-15T10:30:00.123Z"},
                "actor": {"S": "system"},
                "dsb_user_id": {"S": "user123"},
                "roles_added": {"L": [{"S": "role_a"}, {"S": "role_b"}]},
                "roles_removed": {"L": [{"S": "role_c"}]},
            }
        ]

        result = get_admin_audit_log("user123")

        assert result[0]["roles_added"] == ["role_a", "role_b"]
        assert result[0]["roles_removed"] == ["role_c"]

    @patch("services.admin_discord.get_user_audit_log")
    def test_passes_limit_100(self, mock_audit_log):
        """Passes limit=100 to the DB query."""
        mock_audit_log.return_value = []

        get_admin_audit_log("user123")

        mock_audit_log.assert_called_once_with("user123", limit=100)
