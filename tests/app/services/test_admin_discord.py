"""Unit tests for app.services.admin_discord.AdminDiscordService.

Covers get_user_detail (membership + discord views, platform roles, contributor
and activation lookups, guild membership state), trigger_sync, disconnect
(validation + role cleanup), get_audit_log formatting, and the private
_get_bot_token / _remove_discord_roles helpers. MembershipDB is replaced with a
MagicMock after construction; boto3 and httpx are patched where used.
"""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
from botocore.exceptions import ClientError

from app.services import admin_discord as mod
from app.services.admin_discord import AdminDiscordService


def _client_error(code="InternalServerError") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


def _settings(**over):
    base = dict(
        membership_table="test-membership",
        discord_bot_secret_name="test-discord-bot",
        discord_guild_id="123456",
        discord_role_free_id="111",
        discord_role_explorer_id="222",
        discord_role_builder_id="333",
        discord_role_builder_academy_id="444",
    )
    base.update(over)
    return MagicMock(**base)


@pytest.fixture
def service():
    with patch.object(mod.boto3, "client", return_value=MagicMock()):
        svc = AdminDiscordService(_settings())
    # Replace the DB with a controllable mock
    svc._db = MagicMock()
    svc._db._client = MagicMock()
    svc._db._table_name = "test-membership"
    # Default: contributor/activation lookups return nothing
    svc._db._client.get_item.return_value = {}
    return svc


class TestGetUserDetail:
    def test_returns_none_when_no_records(self, service):
        service._db.get_membership.return_value = None
        service._db.get_discord_active.return_value = None
        assert service.get_user_detail("u1") is None

    def test_membership_only_free_tier(self, service):
        service._db.get_membership.return_value = {
            "membership_tier": {"S": "FREE"},
            "subscription_status": {"S": "active"},
            "stripe_customer_id": {"S": "cus_1"},
        }
        service._db.get_discord_active.return_value = None
        result = service.get_user_detail("u1")
        assert result["membership_tier"] == "FREE"
        assert result["stripe_subscription_status"] == "active"
        assert result["stripe_customer_id"] == "cus_1"
        assert result["discord_connected"] is False
        assert result["platform_roles"] == ["Free"]
        assert result["guild_membership_state"] == "not_connected"
        assert result["builderActivatedAt"] is None

    def test_builder_tier_platform_role(self, service):
        service._db.get_membership.return_value = {"membership_tier": {"S": "BUILDER"}}
        service._db.get_discord_active.return_value = None
        result = service.get_user_detail("u1")
        assert result["platform_roles"] == ["Builder"]

    def test_other_tier_titlecased(self, service):
        service._db.get_membership.return_value = {
            "membership_tier": {"S": "BUILDER_ACADEMY"}
        }
        service._db.get_discord_active.return_value = None
        result = service.get_user_detail("u1")
        assert result["platform_roles"] == ["Builder Academy"]

    def test_contributor_role_appended(self, service):
        service._db.get_membership.return_value = {"membership_tier": {"S": "FREE"}}
        service._db.get_discord_active.return_value = None

        def _get_item(TableName, Key):
            if Key["SK"]["S"] == "CONTRIBUTOR_ROLE":
                return {"Item": {"x": {"S": "y"}}}
            return {}

        service._db._client.get_item.side_effect = _get_item
        result = service.get_user_detail("u1")
        assert "Contributor" in result["platform_roles"]

    def test_activation_event_populates_fields(self, service):
        service._db.get_membership.return_value = {"membership_tier": {"S": "BUILDER"}}
        service._db.get_discord_active.return_value = None

        def _get_item(TableName, Key):
            if Key["SK"]["S"] == "BUILDER_ACTIVATED":
                return {
                    "Item": {
                        "activated_at": {"S": "2026-01-01"},
                        "activation_source": {"S": "stripe"},
                    }
                }
            return {}

        service._db._client.get_item.side_effect = _get_item
        result = service.get_user_detail("u1")
        assert result["builderActivatedAt"] == "2026-01-01"
        assert result["activation_source"] == "stripe"

    def test_activation_lookup_exception_sets_none(self, service):
        service._db.get_membership.return_value = {"membership_tier": {"S": "FREE"}}
        service._db.get_discord_active.return_value = None
        service._db._client.get_item.side_effect = RuntimeError("boom")
        result = service.get_user_detail("u1")
        assert result["builderActivatedAt"] is None
        assert result["activation_source"] is None

    def test_discord_active_in_guild(self, service):
        service._db.get_membership.return_value = {"membership_tier": {"S": "FREE"}}
        service._db.get_discord_active.return_value = {
            "username": {"S": "cool"},
            "discord_user_id": {"S": "duid"},
            "platform_state": {"S": "Server_Joined"},
            "last_synced_at": {"S": "2026-01-01"},
            "last_sync_status": {"S": "success"},
        }
        fake_client = MagicMock()
        fake_client.get_member_roles.return_value = ["r1"]
        with patch(
            "app.services.discord_sync._get_discord_client", return_value=fake_client
        ):
            result = service.get_user_detail("u1")
        assert result["discord_connected"] is True
        assert result["discord_username"] == "cool"
        assert result["guild_membership_state"] == "in_guild"

    def test_discord_active_not_in_guild(self, service):
        service._db.get_membership.return_value = None
        service._db.get_discord_active.return_value = {
            "discord_user_id": {"S": "duid"},
        }
        fake_client = MagicMock()
        fake_client.get_member_roles.return_value = None
        with patch(
            "app.services.discord_sync._get_discord_client", return_value=fake_client
        ):
            result = service.get_user_detail("u1")
        assert result["guild_membership_state"] == "not_in_guild"

    def test_discord_active_guild_check_exception_unknown(self, service):
        service._db.get_membership.return_value = None
        service._db.get_discord_active.return_value = {
            "discord_user_id": {"S": "duid"},
        }
        with patch(
            "app.services.discord_sync._get_discord_client",
            side_effect=RuntimeError("down"),
        ):
            result = service.get_user_detail("u1")
        assert result["guild_membership_state"] == "unknown"

    def test_discord_active_no_discord_user_id_unknown(self, service):
        service._db.get_membership.return_value = None
        service._db.get_discord_active.return_value = {"username": {"S": "x"}}
        result = service.get_user_detail("u1")
        assert result["guild_membership_state"] == "unknown"


class TestTriggerSync:
    def test_writes_audit_and_returns_success(self, service):
        result = service.trigger_sync("admin1", "u1", reason="manual")
        assert result == {"success": True, "user_id": "u1"}
        service._db.write_audit_event.assert_called_once()
        item = service._db.write_audit_event.call_args.args[0]
        assert item["event_type"] == {"S": "ADMIN_OVERRIDE"}
        assert item["actor"] == {"S": "admin:admin1"}
        assert "manual" in item["reason"]["S"]


class TestDisconnect:
    def test_reason_too_short_raises(self, service):
        with pytest.raises(ValueError, match="at least 5 characters"):
            service.disconnect("admin1", "u1", "no")

    def test_empty_reason_raises(self, service):
        with pytest.raises(ValueError, match="at least 5 characters"):
            service.disconnect("admin1", "u1", "")

    def test_reason_too_long_raises(self, service):
        with pytest.raises(ValueError, match="not exceed 500"):
            service.disconnect("admin1", "u1", "x" * 501)

    def test_no_active_connection_raises(self, service):
        service._db.get_discord_active.return_value = None
        with pytest.raises(ValueError, match="no active Discord connection"):
            service.disconnect("admin1", "u1", "valid reason")

    def test_success_removes_roles_completed(self, service):
        service._db.get_discord_active.return_value = {"discord_user_id": {"S": "duid"}}
        secret_client = MagicMock()
        secret_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"secret_key": "botkey"})
        }
        with (
            patch.object(mod.boto3, "client", return_value=secret_client),
            patch.object(mod, "AdminDiscordService", wraps=AdminDiscordService),
            patch("httpx.delete", return_value=MagicMock(status_code=204)) as hdel,
        ):
            result = service.disconnect("admin1", "u1", "valid reason")
        assert result == {"cleanup_status": "completed", "user_id": "u1"}
        service._db.deactivate_discord_connection.assert_called_once()
        # 4 managed roles removed
        assert hdel.call_count == 4
        # Two audit entries written (ADMIN_OVERRIDE + DISCONNECTED)
        assert service._db.write_audit_event.call_count == 2

    def test_role_cleanup_failure_sets_failed(self, service):
        service._db.get_discord_active.return_value = {"discord_user_id": {"S": "duid"}}
        # _get_bot_token raises -> cleanup failed
        with patch.object(mod.boto3, "client", side_effect=RuntimeError("down")):
            result = service.disconnect("admin1", "u1", "valid reason")
        assert result["cleanup_status"] == "failed"
        # Audit entries still written
        assert service._db.write_audit_event.call_count == 2


class TestGetAuditLog:
    def test_formats_entries_with_optional_fields(self, service):
        service._db.get_user_audit_log.return_value = [
            {
                "event_type": {"S": "ADMIN_OVERRIDE"},
                "timestamp": {"S": "2026-01-01"},
                "actor": {"S": "admin:a1"},
                "dsb_user_id": {"S": "u1"},
                "discord_user_id": {"S": "duid"},
                "previous_state": {"S": "old"},
                "new_state": {"S": "new"},
                "reason": {"S": "because"},
                "error_message": {"S": "err"},
                "roles_added": {"L": [{"S": "r1"}, {"S": "r2"}]},
                "roles_removed": {"L": [{"S": "r3"}]},
            }
        ]
        result = service.get_audit_log("u1")
        assert len(result) == 1
        entry = result[0]
        assert entry["event_type"] == "ADMIN_OVERRIDE"
        assert entry["discord_user_id"] == "duid"
        assert entry["previous_state"] == "old"
        assert entry["new_state"] == "new"
        assert entry["reason"] == "because"
        assert entry["error_message"] == "err"
        assert entry["roles_added"] == ["r1", "r2"]
        assert entry["roles_removed"] == ["r3"]

    def test_minimal_entry_omits_optional_fields(self, service):
        service._db.get_user_audit_log.return_value = [
            {
                "event_type": {"S": "CONNECTED"},
                "timestamp": {"S": "2026-01-02"},
                "actor": {"S": "user:u1"},
                "dsb_user_id": {"S": "u1"},
            }
        ]
        result = service.get_audit_log("u1")
        entry = result[0]
        assert entry["event_type"] == "CONNECTED"
        assert "discord_user_id" not in entry
        assert "roles_added" not in entry

    def test_empty_audit_log(self, service):
        service._db.get_user_audit_log.return_value = []
        assert service.get_audit_log("u1") == []


class TestGetBotToken:
    def test_returns_secret_key(self, service):
        client = MagicMock()
        client.get_secret_value.return_value = {
            "SecretString": json.dumps({"secret_key": "botkey"})
        }
        with patch.object(mod.boto3, "client", return_value=client):
            assert service._get_bot_token() == "botkey"
        client.get_secret_value.assert_called_once_with(SecretId="test-discord-bot")

    def test_client_error_returns_none(self, service):
        client = MagicMock()
        client.get_secret_value.side_effect = _client_error("AccessDenied")
        with patch.object(mod.boto3, "client", return_value=client):
            assert service._get_bot_token() is None

    def test_bad_json_returns_none(self, service):
        client = MagicMock()
        client.get_secret_value.return_value = {"SecretString": "not-json{"}
        with patch.object(mod.boto3, "client", return_value=client):
            assert service._get_bot_token() is None


class TestRemoveDiscordRoles:
    def test_deletes_each_nonempty_role(self, service):
        with patch("httpx.delete", return_value=MagicMock(status_code=204)) as hdel:
            service._remove_discord_roles("bot", "duid", ["r1", "", "r2"])
        # Empty role skipped -> 2 calls
        assert hdel.call_count == 2
        (url,) = hdel.call_args_list[0].args
        assert url == (
            "https://discord.com/api/v10/guilds/123456/members/duid/roles/r1"
        )
        assert hdel.call_args_list[0].kwargs["headers"] == {"Authorization": "Bot bot"}

    def test_non_success_status_logged_but_no_raise(self, service):
        with patch("httpx.delete", return_value=MagicMock(status_code=500)):
            service._remove_discord_roles("bot", "duid", ["r1"])  # no exception

    def test_http_error_swallowed(self, service):
        with patch("httpx.delete", side_effect=httpx.HTTPError("x")):
            service._remove_discord_roles("bot", "duid", ["r1"])  # no exception


class TestWriteAudit:
    def test_write_audit_failure_swallowed(self, service):
        service._db.write_audit_event.side_effect = RuntimeError("db down")
        # Should not raise
        service._write_audit("u1", "CONNECTED", "actor")
