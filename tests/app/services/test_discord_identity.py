"""Unit tests for app.services.discord_identity.

Covers the module-level OAuth link/unlink/status functions. These create
boto3 DynamoDB and Secrets Manager clients inside each call and make Discord
HTTP calls via httpx, so we patch mod.boto3.client (routing by service name)
and mod.httpx.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import discord_identity as mod


def _client_error(code="InternalServerError") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


def _settings(**over):
    base = dict(
        membership_table="test-membership",
        discord_secret_name="test-discord",
        discord_bot_secret_name="test-discord-bot",
        discord_callback_url="https://example.com/callback",
        discord_guild_id="123456",
        discord_role_free_id="111",
        discord_role_explorer_id="222",
        discord_role_builder_id="333",
        discord_role_builder_academy_id="444",
    )
    base.update(over)
    return MagicMock(**base)


def _secret_client(secret: dict):
    c = MagicMock()
    c.get_secret_value.return_value = {"SecretString": json.dumps(secret)}
    return c


def _route(dynamodb=None, secrets=None):
    """Build a boto3.client side_effect routing by service name."""
    dynamodb = dynamodb or MagicMock()
    secrets = secrets or MagicMock()

    def _factory(service_name, *a, **k):
        if service_name == "dynamodb":
            return dynamodb
        if service_name == "secretsmanager":
            return secrets
        raise AssertionError(f"unexpected client {service_name}")

    return _factory, dynamodb, secrets


def _resp(status_code=200, json_data=None):
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data if json_data is not None else {}
    return r


class TestSecretHelpers:
    def test_get_discord_secret(self):
        sc = _secret_client({"client_id": "cid", "client_secret": "csec"})
        factory, _, _ = _route(secrets=sc)
        with patch.object(mod.boto3, "client", side_effect=factory):
            result = mod._get_discord_secret(_settings())
        assert result == {"client_id": "cid", "client_secret": "csec"}
        sc.get_secret_value.assert_called_once_with(SecretId="test-discord")

    def test_get_bot_token(self):
        sc = _secret_client({"secret_key": "botkey"})
        factory, _, _ = _route(secrets=sc)
        with patch.object(mod.boto3, "client", side_effect=factory):
            assert mod._get_bot_token(_settings()) == "botkey"
        sc.get_secret_value.assert_called_once_with(SecretId="test-discord-bot")

    def test_get_bot_token_missing_key_returns_empty(self):
        sc = _secret_client({"other": "x"})
        factory, _, _ = _route(secrets=sc)
        with patch.object(mod.boto3, "client", side_effect=factory):
            assert mod._get_bot_token(_settings()) == ""


class TestStartOauth:
    def test_raises_when_already_connected(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {"Item": {"PK": {"S": "x"}}}
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            with pytest.raises(ValueError, match="already connected"):
                mod.start_oauth("u1", _settings())

    def test_client_error_on_check_propagates(self):
        ddb = MagicMock()
        ddb.get_item.side_effect = _client_error()
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            with pytest.raises(ClientError):
                mod.start_oauth("u1", _settings())

    def test_builds_url_and_stores_pending(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {}
        sc = _secret_client({"client_id": "my-client-id"})
        factory, _, _ = _route(dynamodb=ddb, secrets=sc)
        with patch.object(mod.boto3, "client", side_effect=factory):
            url = mod.start_oauth("u1", _settings())
        assert url.startswith("https://discord.com/api/oauth2/authorize")
        assert "client_id=my-client-id" in url
        assert "redirect_uri=https://example.com/callback" in url
        assert "scope=identify+guilds.join" in url
        assert "state=u1:" in url
        # Pending state stored
        put = ddb.put_item.call_args.kwargs
        assert put["Item"]["SK"] == {"S": "DISCORD_PENDING"}
        assert put["Item"]["state"]["S"].startswith("u1:")

    def test_put_item_client_error_propagates(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {}
        ddb.put_item.side_effect = _client_error()
        sc = _secret_client({"client_id": "cid"})
        factory, _, _ = _route(dynamodb=ddb, secrets=sc)
        with patch.object(mod.boto3, "client", side_effect=factory):
            with pytest.raises(ClientError):
                mod.start_oauth("u1", _settings())


class TestHandleCallback:
    def test_invalid_state_too_few_parts(self):
        with patch.object(mod.boto3, "client", return_value=MagicMock()):
            with pytest.raises(ValueError, match="Invalid state parameter"):
                mod.handle_callback("code", "nocolon", _settings())

    def test_state_mismatch_raises(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {"Item": {"state": {"S": "different"}}}
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            with pytest.raises(ValueError, match="Invalid or expired state"):
                mod.handle_callback("code", "u1:123", _settings())

    def test_missing_pending_raises(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {}
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            with pytest.raises(ValueError, match="Invalid or expired state"):
                mod.handle_callback("code", "u1:123", _settings())

    def test_client_error_verifying_state_raises(self):
        ddb = MagicMock()
        ddb.get_item.side_effect = _client_error()
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            with pytest.raises(ValueError, match="Failed to verify state"):
                mod.handle_callback("code", "u1:123", _settings())

    def test_token_exchange_failure_raises(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {"Item": {"state": {"S": "u1:123"}}}
        sc = _secret_client({"client_id": "cid", "client_secret": "csec"})
        factory, _, _ = _route(dynamodb=ddb, secrets=sc)
        with (
            patch.object(mod.boto3, "client", side_effect=factory),
            patch.object(mod.httpx, "post", return_value=_resp(400)),
        ):
            with pytest.raises(ValueError, match="exchange Discord code"):
                mod.handle_callback("code", "u1:123", _settings())

    def test_user_info_failure_raises(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {"Item": {"state": {"S": "u1:123"}}}
        sc = _secret_client({"client_id": "cid", "client_secret": "csec"})
        factory, _, _ = _route(dynamodb=ddb, secrets=sc)
        with (
            patch.object(mod.boto3, "client", side_effect=factory),
            patch.object(
                mod.httpx, "post", return_value=_resp(200, {"access_token": "at"})
            ),
            patch.object(mod.httpx, "get", return_value=_resp(401)),
        ):
            with pytest.raises(ValueError, match="fetch Discord user info"):
                mod.handle_callback("code", "u1:123", _settings())

    def test_success_updates_pending_record(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {"Item": {"state": {"S": "u1:123"}}}
        sc = _secret_client({"client_id": "cid", "client_secret": "csec"})
        factory, _, _ = _route(dynamodb=ddb, secrets=sc)
        user_info = {
            "id": "duid",
            "username": "cooluser",
            "global_name": "Cool User",
            "avatar": "abc",
        }
        with (
            patch.object(mod.boto3, "client", side_effect=factory),
            patch.object(
                mod.httpx, "post", return_value=_resp(200, {"access_token": "at"})
            ) as post,
            patch.object(mod.httpx, "get", return_value=_resp(200, user_info)),
        ):
            mod.handle_callback("thecode", "u1:123", _settings())
        # token exchange used the code
        assert post.call_args.kwargs["data"]["code"] == "thecode"
        vals = ddb.update_item.call_args.kwargs["ExpressionAttributeValues"]
        assert vals[":duid"] == {"S": "duid"}
        assert vals[":uname"] == {"S": "cooluser"}
        assert vals[":dname"] == {"S": "Cool User"}
        assert vals[":avatar"] == {
            "S": "https://cdn.discordapp.com/avatars/duid/abc.png"
        }
        assert vals[":token"] == {"S": "at"}

    def test_success_no_avatar_and_no_global_name(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {"Item": {"state": {"S": "u1:123"}}}
        sc = _secret_client({"client_id": "cid", "client_secret": "csec"})
        factory, _, _ = _route(dynamodb=ddb, secrets=sc)
        user_info = {"id": "duid", "username": "plainuser"}
        with (
            patch.object(mod.boto3, "client", side_effect=factory),
            patch.object(
                mod.httpx, "post", return_value=_resp(200, {"access_token": "at"})
            ),
            patch.object(mod.httpx, "get", return_value=_resp(200, user_info)),
        ):
            mod.handle_callback("code", "u1:123", _settings())
        vals = ddb.update_item.call_args.kwargs["ExpressionAttributeValues"]
        assert vals[":dname"] == {"S": "plainuser"}  # falls back to username
        assert vals[":avatar"] == {"S": ""}  # no avatar

    def test_update_item_client_error_raises(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {"Item": {"state": {"S": "u1:123"}}}
        ddb.update_item.side_effect = _client_error()
        sc = _secret_client({"client_id": "cid", "client_secret": "csec"})
        factory, _, _ = _route(dynamodb=ddb, secrets=sc)
        with (
            patch.object(mod.boto3, "client", side_effect=factory),
            patch.object(
                mod.httpx, "post", return_value=_resp(200, {"access_token": "at"})
            ),
            patch.object(
                mod.httpx, "get", return_value=_resp(200, {"id": "d", "username": "u"})
            ),
        ):
            with pytest.raises(ValueError, match="store Discord identity"):
                mod.handle_callback("code", "u1:123", _settings())


class TestConfirmIdentity:
    def test_no_pending_raises(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {}
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            with pytest.raises(ValueError, match="No pending Discord connection"):
                mod.confirm_identity("u1", _settings())

    def test_fetch_client_error_raises(self):
        ddb = MagicMock()
        ddb.get_item.side_effect = _client_error()
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            with pytest.raises(ValueError, match="fetch pending connection"):
                mod.confirm_identity("u1", _settings())

    def test_incomplete_pending_no_discord_id_raises(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {"Item": {"username": {"S": "u"}}}
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            with pytest.raises(ValueError, match="no Discord user ID"):
                mod.confirm_identity("u1", _settings())

    def test_success_activates_and_returns_detail(self):
        pending = {
            "Item": {
                "discord_user_id": {"S": "duid"},
                "username": {"S": "cool"},
                "display_name": {"S": "Cool"},
                "avatar_url": {"S": "https://a/b.png"},
                "access_token": {"S": "at"},
            }
        }
        ddb = MagicMock()
        ddb.get_item.return_value = pending
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            result = mod.confirm_identity("u1", _settings())
        assert result == {
            "discord_user_id": "duid",
            "username": "cool",
            "display_name": "Cool",
            "avatar_url": "https://a/b.png",
            "platform_state": "Server_Joined",
        }
        ddb.transact_write_items.assert_called_once()

    def test_transact_client_error_raises(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {
            "Item": {"discord_user_id": {"S": "duid"}, "username": {"S": "u"}}
        }
        ddb.transact_write_items.side_effect = _client_error()
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            with pytest.raises(ValueError, match="activate Discord connection"):
                mod.confirm_identity("u1", _settings())


class TestDisconnect:
    def test_no_active_raises(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {}
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            with pytest.raises(ValueError, match="No active Discord connection"):
                mod.disconnect("u1", _settings())

    def test_fetch_client_error_raises(self):
        ddb = MagicMock()
        ddb.get_item.side_effect = _client_error()
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            with pytest.raises(ValueError, match="fetch Discord connection"):
                mod.disconnect("u1", _settings())

    def test_transact_client_error_raises(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {"Item": {"discord_user_id": {"S": "duid"}}}
        ddb.transact_write_items.side_effect = _client_error()
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            with pytest.raises(ValueError, match="disconnect Discord"):
                mod.disconnect("u1", _settings())

    def test_success_removes_roles_and_completed(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {"Item": {"discord_user_id": {"S": "duid"}}}
        sc = _secret_client({"secret_key": "botkey"})
        factory, _, _ = _route(dynamodb=ddb, secrets=sc)
        fake_client = MagicMock()
        with (
            patch.object(mod.boto3, "client", side_effect=factory),
            patch(
                "app.services.discord_api.DiscordClient", return_value=fake_client
            ) as DC,
        ):
            result = mod.disconnect("u1", _settings())
        assert result == {"cleanup_status": "completed"}
        DC.assert_called_once_with("botkey", "123456")
        # All 4 non-empty managed roles removed
        assert fake_client.remove_role.call_count == 4
        fake_client.remove_role.assert_any_call("duid", "111")

    def test_role_removal_exception_sets_failed(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {"Item": {"discord_user_id": {"S": "duid"}}}
        sc = _secret_client({"secret_key": "botkey"})
        factory, _, _ = _route(dynamodb=ddb, secrets=sc)
        fake_client = MagicMock()
        fake_client.remove_role.side_effect = RuntimeError("down")
        with (
            patch.object(mod.boto3, "client", side_effect=factory),
            patch("app.services.discord_api.DiscordClient", return_value=fake_client),
        ):
            result = mod.disconnect("u1", _settings())
        assert result == {"cleanup_status": "failed"}

    def test_no_bot_token_skips_role_removal(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {"Item": {"discord_user_id": {"S": "duid"}}}
        sc = _secret_client({})  # no secret_key -> empty token
        factory, _, _ = _route(dynamodb=ddb, secrets=sc)
        with (
            patch.object(mod.boto3, "client", side_effect=factory),
            patch("app.services.discord_api.DiscordClient") as DC,
        ):
            result = mod.disconnect("u1", _settings())
        assert result == {"cleanup_status": "completed"}
        DC.assert_not_called()


class TestGetStatus:
    def test_active_connection_with_roles(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {
            "Item": {
                "username": {"S": "cool"},
                "avatar_url": {"S": "https://a/b.png"},
                "platform_state": {"S": "Server_Joined"},
                "last_synced_at": {"S": "2026-01-01"},
                "last_sync_status": {"S": "success"},
                "discord_user_id": {"S": "duid"},
            }
        }
        factory, _, _ = _route(dynamodb=ddb)
        fake_client = MagicMock()
        fake_client.get_member_roles_with_details.return_value = [
            {"name": "Builder", "color": "#0000ff"}
        ]
        with (
            patch.object(mod.boto3, "client", side_effect=factory),
            patch(
                "app.services.discord_sync._get_discord_client",
                return_value=fake_client,
            ),
        ):
            result = mod.get_status("u1", _settings())
        assert result["connected"] is True
        assert result["discord_username"] == "cool"
        assert result["platform_state"] == "Server_Joined"
        assert result["discord_roles"] == [{"name": "Builder", "color": "#0000ff"}]

    def test_active_connection_role_fetch_failure_empty_roles(self):
        ddb = MagicMock()
        ddb.get_item.return_value = {
            "Item": {
                "username": {"S": "cool"},
                "last_synced_at": {"S": ""},
                "last_sync_status": {"S": ""},
                "discord_user_id": {"S": "duid"},
            }
        }
        factory, _, _ = _route(dynamodb=ddb)
        with (
            patch.object(mod.boto3, "client", side_effect=factory),
            patch(
                "app.services.discord_sync._get_discord_client",
                side_effect=RuntimeError("down"),
            ),
        ):
            result = mod.get_status("u1", _settings())
        assert result["connected"] is True
        assert result["discord_roles"] == []
        # empty strings normalized to None
        assert result["last_synced_at"] is None
        assert result["last_sync_status"] is None

    def test_pending_connection(self):
        ddb = MagicMock()
        # First get_item (active) returns nothing, second (pending) returns item
        ddb.get_item.side_effect = [
            {},
            {"Item": {"username": {"S": "pend"}, "avatar_url": {"S": "https://x"}}},
        ]
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            result = mod.get_status("u1", _settings())
        assert result["connected"] is False
        assert result["pending"] is True
        assert result["discord_username"] == "pend"

    def test_no_connection_returns_defaults(self):
        ddb = MagicMock()
        ddb.get_item.side_effect = [{}, {}]
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            result = mod.get_status("u1", _settings())
        assert result["connected"] is False
        assert result["pending"] is False

    def test_active_client_error_falls_through_to_pending(self):
        ddb = MagicMock()
        ddb.get_item.side_effect = [_client_error(), {}]
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            result = mod.get_status("u1", _settings())
        assert result["connected"] is False
        assert result["pending"] is False

    def test_pending_client_error_handled(self):
        ddb = MagicMock()
        ddb.get_item.side_effect = [{}, _client_error()]
        factory, _, _ = _route(dynamodb=ddb)
        with patch.object(mod.boto3, "client", side_effect=factory):
            result = mod.get_status("u1", _settings())
        assert result["connected"] is False
        assert result["pending"] is False
