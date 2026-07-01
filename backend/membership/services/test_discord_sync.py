"""Unit tests for the Discord role synchronization service."""

import os
from unittest.mock import patch, MagicMock

import pytest

# Set required env vars before importing the module
os.environ.setdefault("MEMBERSHIP_TABLE", "test-membership-table")
os.environ.setdefault("DISCORD_GUILD_ID", "12345678901234567")
os.environ.setdefault("DISCORD_BOT_SECRET_NAME", "test-bot-secret")
os.environ.setdefault("DISCORD_ROLE_FREE_ID", "11111111111111111")
os.environ.setdefault("DISCORD_ROLE_EXPLORER_ID", "22222222222222222")
os.environ.setdefault("DISCORD_ROLE_BUILDER_ID", "33333333333333333")
os.environ.setdefault("DISCORD_ROLE_BUILDER_ACADEMY_ID", "44444444444444444")

from services.discord_sync import sync_discord_roles, DiscordSyncError

# --- Fixtures ---

ROLE_FREE = "11111111111111111"
ROLE_EXPLORER = "22222222222222222"
ROLE_BUILDER = "33333333333333333"
ROLE_BUILDER_ACADEMY = "44444444444444444"


def _make_discord_active(
    discord_user_id="99999999999999999",
    active=True,
    platform_state="Server_Joined",
):
    """Build a minimal DISCORD_ACTIVE DynamoDB item."""
    return {
        "PK": {"S": "USER#user1"},
        "SK": {"S": "DISCORD_ACTIVE"},
        "discord_user_id": {"S": discord_user_id},
        "active": {"BOOL": active},
        "platform_state": {"S": platform_state},
        "username": {"S": "testuser"},
    }


def _make_membership(tier="EXPLORER"):
    """Build a minimal MEMBERSHIP DynamoDB item."""
    return {
        "PK": {"S": "USER#user1"},
        "SK": {"S": "MEMBERSHIP"},
        "membership_tier": {"S": tier},
    }


# --- Tests: Precondition failures (sync should be skipped) ---


class TestSyncPreconditions:
    @patch("services.discord_sync.membership_db")
    def test_skips_when_no_discord_active_record(self, mock_db):
        """Sync is skipped silently if no DISCORD_ACTIVE record exists."""
        mock_db.get_membership.return_value = _make_membership("FREE")
        mock_db.get_discord_active.return_value = None

        # Should not raise
        sync_discord_roles("user1")

    @patch("services.discord_sync.boto3")
    @patch("services.discord_sync.membership_db")
    def test_skips_when_connection_not_active(self, mock_db, mock_boto):
        """Sync is skipped and status set to SKIPPED if active=False."""
        mock_db.get_membership.return_value = _make_membership("FREE")
        mock_db.get_discord_active.return_value = _make_discord_active(active=False)

        mock_dynamo_client = MagicMock()
        mock_boto.client.return_value = mock_dynamo_client

        sync_discord_roles("user1")

        # Should update last_sync_status=SKIPPED
        mock_dynamo_client.update_item.assert_called()
        call_kwargs = mock_dynamo_client.update_item.call_args[1]
        assert call_kwargs["ExpressionAttributeValues"][":st"] == {"S": "SKIPPED"}

    @patch("services.discord_sync.boto3")
    @patch("services.discord_sync.membership_db")
    def test_skips_when_platform_state_not_server_joined(self, mock_db, mock_boto):
        """Sync skipped if platform_state is not Server_Joined or Roles_Synced."""
        mock_db.get_membership.return_value = _make_membership("EXPLORER")
        mock_db.get_discord_active.return_value = _make_discord_active(
            platform_state="Discord_Verified"
        )

        mock_dynamo_client = MagicMock()
        mock_boto.client.return_value = mock_dynamo_client

        sync_discord_roles("user1")

        mock_dynamo_client.update_item.assert_called()
        call_kwargs = mock_dynamo_client.update_item.call_args[1]
        assert call_kwargs["ExpressionAttributeValues"][":st"] == {"S": "SKIPPED"}

    @patch("services.discord_sync.boto3")
    @patch("services.discord_sync.membership_db")
    def test_skips_when_missing_discord_user_id(self, mock_db, mock_boto):
        """Sync skipped if discord_user_id is empty."""
        mock_db.get_membership.return_value = _make_membership("FREE")
        record = _make_discord_active()
        record["discord_user_id"] = {"S": ""}
        mock_db.get_discord_active.return_value = record

        mock_dynamo_client = MagicMock()
        mock_boto.client.return_value = mock_dynamo_client

        sync_discord_roles("user1")

        mock_dynamo_client.update_item.assert_called()

    @patch("services.discord_sync.membership_db")
    def test_defaults_to_free_tier_when_no_membership(self, mock_db):
        """If no MEMBERSHIP record exists, tier defaults to FREE."""
        mock_db.get_membership.return_value = None
        mock_db.get_discord_active.return_value = None

        # Should not raise — just skips due to no discord_active
        sync_discord_roles("user1")
        mock_db.get_membership.assert_called_once_with("user1")


# --- Tests: Happy path — role add/remove ---


class TestSyncRoleChanges:
    @patch("services.discord_sync.write_audit_log")
    @patch("services.discord_sync.boto3")
    @patch("services.discord_sync.get_secret")
    @patch("services.discord_sync.DiscordClient")
    @patch("services.discord_sync.membership_db")
    def test_adds_expected_role_when_missing(
        self, mock_db, mock_discord_class, mock_secret, mock_boto, mock_audit
    ):
        """Adds the expected tier role when the user doesn't have it."""
        mock_db.get_membership.return_value = _make_membership("EXPLORER")
        mock_db.get_discord_active.return_value = _make_discord_active()
        mock_secret.return_value = {"secret_key": "bot-token-123"}

        mock_client = MagicMock()
        mock_discord_class.return_value = mock_client
        # User currently has no managed roles
        mock_client.get_member_roles.return_value = ["unmanaged_role_111"]
        mock_client.add_role.return_value = True

        mock_dynamo_client = MagicMock()
        mock_boto.client.return_value = mock_dynamo_client

        sync_discord_roles("user1")

        mock_client.add_role.assert_called_once_with("99999999999999999", ROLE_EXPLORER)
        mock_client.remove_role.assert_not_called()

        # Audit should record Roles_Added
        audit_calls = [call[0][0] for call in mock_audit.call_args_list]
        event_types = [e.event_type.value for e in audit_calls]
        assert "Roles_Added" in event_types
        assert "Sync_Successful" in event_types

    @patch("services.discord_sync.write_audit_log")
    @patch("services.discord_sync.boto3")
    @patch("services.discord_sync.get_secret")
    @patch("services.discord_sync.DiscordClient")
    @patch("services.discord_sync.membership_db")
    def test_removes_old_managed_roles(
        self, mock_db, mock_discord_class, mock_secret, mock_boto, mock_audit
    ):
        """Removes other managed roles that shouldn't be present."""
        mock_db.get_membership.return_value = _make_membership("BUILDER")
        mock_db.get_discord_active.return_value = _make_discord_active()
        mock_secret.return_value = {"secret_key": "bot-token-123"}

        mock_client = MagicMock()
        mock_discord_class.return_value = mock_client
        # User has BUILDER role (correct) plus EXPLORER role (incorrect)
        mock_client.get_member_roles.return_value = [
            ROLE_BUILDER,
            ROLE_EXPLORER,
            "unmanaged_role_111",
        ]
        mock_client.remove_role.return_value = True

        mock_dynamo_client = MagicMock()
        mock_boto.client.return_value = mock_dynamo_client

        sync_discord_roles("user1")

        mock_client.add_role.assert_not_called()
        mock_client.remove_role.assert_called_once_with(
            "99999999999999999", ROLE_EXPLORER
        )

        audit_calls = [call[0][0] for call in mock_audit.call_args_list]
        event_types = [e.event_type.value for e in audit_calls]
        assert "Roles_Removed" in event_types

    @patch("services.discord_sync.write_audit_log")
    @patch("services.discord_sync.boto3")
    @patch("services.discord_sync.get_secret")
    @patch("services.discord_sync.DiscordClient")
    @patch("services.discord_sync.membership_db")
    def test_adds_and_removes_in_single_sync(
        self, mock_db, mock_discord_class, mock_secret, mock_boto, mock_audit
    ):
        """Adds expected role and removes old managed roles in one operation."""
        mock_db.get_membership.return_value = _make_membership("BUILDER_ACADEMY")
        mock_db.get_discord_active.return_value = _make_discord_active()
        mock_secret.return_value = {"secret_key": "bot-token-123"}

        mock_client = MagicMock()
        mock_discord_class.return_value = mock_client
        # User has FREE and EXPLORER roles, needs BUILDER_ACADEMY
        mock_client.get_member_roles.return_value = [
            ROLE_FREE,
            ROLE_EXPLORER,
            "unmanaged_role_111",
        ]
        mock_client.add_role.return_value = True
        mock_client.remove_role.return_value = True

        mock_dynamo_client = MagicMock()
        mock_boto.client.return_value = mock_dynamo_client

        sync_discord_roles("user1")

        mock_client.add_role.assert_called_once_with(
            "99999999999999999", ROLE_BUILDER_ACADEMY
        )
        # Should remove both FREE and EXPLORER
        remove_calls = mock_client.remove_role.call_args_list
        removed_role_ids = {call[0][1] for call in remove_calls}
        assert ROLE_FREE in removed_role_ids
        assert ROLE_EXPLORER in removed_role_ids


# --- Tests: No-op when roles already correct ---


class TestSyncNoOp:
    @patch("services.discord_sync.write_audit_log")
    @patch("services.discord_sync.boto3")
    @patch("services.discord_sync.get_secret")
    @patch("services.discord_sync.DiscordClient")
    @patch("services.discord_sync.membership_db")
    def test_no_api_calls_when_roles_correct(
        self, mock_db, mock_discord_class, mock_secret, mock_boto, mock_audit
    ):
        """No Discord API add/remove calls when roles are already correct."""
        mock_db.get_membership.return_value = _make_membership("EXPLORER")
        mock_db.get_discord_active.return_value = _make_discord_active()
        mock_secret.return_value = {"secret_key": "bot-token-123"}

        mock_client = MagicMock()
        mock_discord_class.return_value = mock_client
        # User already has exactly the expected role and no other managed roles
        mock_client.get_member_roles.return_value = [
            ROLE_EXPLORER,
            "unmanaged_role_111",
        ]

        mock_dynamo_client = MagicMock()
        mock_boto.client.return_value = mock_dynamo_client

        sync_discord_roles("user1")

        mock_client.add_role.assert_not_called()
        mock_client.remove_role.assert_not_called()

        # Should still update last_synced_at with SUCCESS
        update_calls = mock_dynamo_client.update_item.call_args_list
        assert any(
            call[1]["ExpressionAttributeValues"].get(":st") == {"S": "SUCCESS"}
            for call in update_calls
        )

        # No audit log should be written for role changes
        mock_audit.assert_not_called()


# --- Tests: Discord API failure ---


class TestSyncDiscordFailure:
    @patch("services.discord_sync.write_audit_log")
    @patch("services.discord_sync.boto3")
    @patch("services.discord_sync.get_secret")
    @patch("services.discord_sync.DiscordClient")
    @patch("services.discord_sync.membership_db")
    def test_raises_on_get_roles_failure(
        self, mock_db, mock_discord_class, mock_secret, mock_boto, mock_audit
    ):
        """Raises DiscordSyncError when fetching roles fails."""
        mock_db.get_membership.return_value = _make_membership("EXPLORER")
        mock_db.get_discord_active.return_value = _make_discord_active()
        mock_secret.return_value = {"secret_key": "bot-token-123"}

        mock_client = MagicMock()
        mock_discord_class.return_value = mock_client
        mock_client.get_member_roles.side_effect = Exception("Connection timeout")

        mock_dynamo_client = MagicMock()
        mock_boto.client.return_value = mock_dynamo_client

        with pytest.raises(DiscordSyncError):
            sync_discord_roles("user1")

        # Should have set FAILED status
        update_calls = mock_dynamo_client.update_item.call_args_list
        assert any(
            call[1]["ExpressionAttributeValues"].get(":st") == {"S": "FAILED"}
            for call in update_calls
        )

        # Should have written Sync_Failed audit
        audit_calls = [call[0][0] for call in mock_audit.call_args_list]
        event_types = [e.event_type.value for e in audit_calls]
        assert "Sync_Failed" in event_types

    @patch("services.discord_sync.write_audit_log")
    @patch("services.discord_sync.boto3")
    @patch("services.discord_sync.get_secret")
    @patch("services.discord_sync.DiscordClient")
    @patch("services.discord_sync.membership_db")
    def test_raises_on_add_role_failure(
        self, mock_db, mock_discord_class, mock_secret, mock_boto, mock_audit
    ):
        """Raises DiscordSyncError when adding a role fails."""
        mock_db.get_membership.return_value = _make_membership("EXPLORER")
        mock_db.get_discord_active.return_value = _make_discord_active()
        mock_secret.return_value = {"secret_key": "bot-token-123"}

        mock_client = MagicMock()
        mock_discord_class.return_value = mock_client
        mock_client.get_member_roles.return_value = ["unmanaged_role_111"]
        mock_client.add_role.return_value = False  # API failure

        mock_dynamo_client = MagicMock()
        mock_boto.client.return_value = mock_dynamo_client

        with pytest.raises(DiscordSyncError):
            sync_discord_roles("user1")

        # Should have set FAILED status and Sync_Failed audit
        audit_calls = [call[0][0] for call in mock_audit.call_args_list]
        event_types = [e.event_type.value for e in audit_calls]
        assert "Sync_Failed" in event_types

    @patch("services.discord_sync.write_audit_log")
    @patch("services.discord_sync.boto3")
    @patch("services.discord_sync.get_secret")
    @patch("services.discord_sync.DiscordClient")
    @patch("services.discord_sync.membership_db")
    def test_raises_on_remove_role_failure(
        self, mock_db, mock_discord_class, mock_secret, mock_boto, mock_audit
    ):
        """Raises DiscordSyncError when removing a role fails."""
        mock_db.get_membership.return_value = _make_membership("BUILDER")
        mock_db.get_discord_active.return_value = _make_discord_active()
        mock_secret.return_value = {"secret_key": "bot-token-123"}

        mock_client = MagicMock()
        mock_discord_class.return_value = mock_client
        mock_client.get_member_roles.return_value = [
            ROLE_BUILDER,
            ROLE_FREE,
        ]
        mock_client.remove_role.return_value = False  # API failure

        mock_dynamo_client = MagicMock()
        mock_boto.client.return_value = mock_dynamo_client

        with pytest.raises(DiscordSyncError):
            sync_discord_roles("user1")


# --- Tests: User not in guild ---


class TestSyncUserNotInGuild:
    @patch("services.discord_sync.write_audit_log")
    @patch("services.discord_sync.boto3")
    @patch("services.discord_sync.get_secret")
    @patch("services.discord_sync.DiscordClient")
    @patch("services.discord_sync.membership_db")
    def test_skips_when_user_not_in_guild(
        self, mock_db, mock_discord_class, mock_secret, mock_boto, mock_audit
    ):
        """Sync skips (no error) when get_member_roles returns None (user left guild)."""
        mock_db.get_membership.return_value = _make_membership("EXPLORER")
        mock_db.get_discord_active.return_value = _make_discord_active()
        mock_secret.return_value = {"secret_key": "bot-token-123"}

        mock_client = MagicMock()
        mock_discord_class.return_value = mock_client
        mock_client.get_member_roles.return_value = None  # Not in guild

        mock_dynamo_client = MagicMock()
        mock_boto.client.return_value = mock_dynamo_client

        # Should not raise
        sync_discord_roles("user1")

        mock_client.add_role.assert_not_called()
        mock_client.remove_role.assert_not_called()

        # Should update status to SKIPPED
        update_calls = mock_dynamo_client.update_item.call_args_list
        assert any(
            call[1]["ExpressionAttributeValues"].get(":st") == {"S": "SKIPPED"}
            for call in update_calls
        )


# --- Tests: Idempotency ---


class TestSyncIdempotency:
    @patch("services.discord_sync.write_audit_log")
    @patch("services.discord_sync.boto3")
    @patch("services.discord_sync.get_secret")
    @patch("services.discord_sync.DiscordClient")
    @patch("services.discord_sync.membership_db")
    def test_idempotent_when_already_synced(
        self, mock_db, mock_discord_class, mock_secret, mock_boto, mock_audit
    ):
        """Calling sync twice when roles are already correct is a no-op."""
        mock_db.get_membership.return_value = _make_membership("FREE")
        mock_db.get_discord_active.return_value = _make_discord_active(
            platform_state="Roles_Synced"
        )
        mock_secret.return_value = {"secret_key": "bot-token-123"}

        mock_client = MagicMock()
        mock_discord_class.return_value = mock_client
        mock_client.get_member_roles.return_value = [ROLE_FREE, "other_role"]

        mock_dynamo_client = MagicMock()
        mock_boto.client.return_value = mock_dynamo_client

        # Call twice
        sync_discord_roles("user1")
        sync_discord_roles("user1")

        # No role modifications should occur
        mock_client.add_role.assert_not_called()
        mock_client.remove_role.assert_not_called()


# --- Tests: Unmanaged roles preserved ---


class TestUnmanagedRolesPreserved:
    @patch("services.discord_sync.write_audit_log")
    @patch("services.discord_sync.boto3")
    @patch("services.discord_sync.get_secret")
    @patch("services.discord_sync.DiscordClient")
    @patch("services.discord_sync.membership_db")
    def test_unmanaged_roles_not_touched(
        self, mock_db, mock_discord_class, mock_secret, mock_boto, mock_audit
    ):
        """Unmanaged Discord roles are never removed."""
        mock_db.get_membership.return_value = _make_membership("EXPLORER")
        mock_db.get_discord_active.return_value = _make_discord_active()
        mock_secret.return_value = {"secret_key": "bot-token-123"}

        mock_client = MagicMock()
        mock_discord_class.return_value = mock_client
        # User has lots of unmanaged roles plus the wrong managed role
        mock_client.get_member_roles.return_value = [
            ROLE_FREE,
            "unmanaged_a",
            "unmanaged_b",
            "unmanaged_c",
        ]
        mock_client.add_role.return_value = True
        mock_client.remove_role.return_value = True

        mock_dynamo_client = MagicMock()
        mock_boto.client.return_value = mock_dynamo_client

        sync_discord_roles("user1")

        # Should only add EXPLORER, remove FREE — never touch unmanaged roles
        mock_client.add_role.assert_called_once_with("99999999999999999", ROLE_EXPLORER)
        mock_client.remove_role.assert_called_once_with("99999999999999999", ROLE_FREE)
