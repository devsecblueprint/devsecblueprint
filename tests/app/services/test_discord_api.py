"""Unit tests for app.services.discord_api.DiscordClient.

Covers the Discord REST API client: fetching/adding/removing roles, adding
members (OAuth + bot), fetching guild roles, and the merged
get_member_roles_with_details view. httpx is patched at the module level since
the client calls httpx.get/put/delete/post directly.
"""

from unittest.mock import MagicMock, patch

import httpx

from app.services import discord_api as mod
from app.services.discord_api import DiscordClient


def _resp(status_code=200, json_data=None, text=""):
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data if json_data is not None else {}
    r.text = text
    r.raise_for_status = MagicMock()
    return r


def _client():
    return DiscordClient(bot_token="tok", guild_id="g1")


class TestConstructor:
    def test_sets_headers_and_guild(self):
        c = DiscordClient("mytoken", "99")
        assert c.headers == {"Authorization": "Bot mytoken"}
        assert c.guild_id == "99"


class TestGetMemberRoles:
    def test_returns_roles_on_success(self):
        c = _client()
        resp = _resp(200, {"roles": ["r1", "r2"]})
        with patch.object(mod.httpx, "get", return_value=resp) as get:
            result = c.get_member_roles("u1")
        assert result == ["r1", "r2"]
        url, = get.call_args.args
        assert url == "https://discord.com/api/v10/guilds/g1/members/u1"
        assert get.call_args.kwargs["headers"] == {"Authorization": "Bot tok"}
        resp.raise_for_status.assert_called_once()

    def test_missing_roles_key_returns_empty_list(self):
        c = _client()
        with patch.object(mod.httpx, "get", return_value=_resp(200, {})):
            assert c.get_member_roles("u1") == []

    def test_404_returns_none(self):
        c = _client()
        resp = _resp(404)
        with patch.object(mod.httpx, "get", return_value=resp):
            assert c.get_member_roles("u1") is None
        resp.raise_for_status.assert_not_called()

    def test_http_error_returns_none(self):
        c = _client()
        with patch.object(mod.httpx, "get", side_effect=httpx.HTTPError("boom")):
            assert c.get_member_roles("u1") is None

    def test_raise_for_status_error_returns_none(self):
        c = _client()
        resp = _resp(500)
        resp.raise_for_status.side_effect = httpx.HTTPError("500")
        with patch.object(mod.httpx, "get", return_value=resp):
            assert c.get_member_roles("u1") is None


class TestAddRole:
    def test_success_statuses(self):
        c = _client()
        for status in (200, 204):
            with patch.object(mod.httpx, "put", return_value=_resp(status)) as put:
                assert c.add_role("u1", "r1") is True
            url, = put.call_args.args
            assert url == (
                "https://discord.com/api/v10/guilds/g1/members/u1/roles/r1"
            )

    def test_non_success_status_returns_false(self):
        c = _client()
        with patch.object(mod.httpx, "put", return_value=_resp(403)):
            assert c.add_role("u1", "r1") is False

    def test_http_error_returns_false(self):
        c = _client()
        with patch.object(mod.httpx, "put", side_effect=httpx.HTTPError("x")):
            assert c.add_role("u1", "r1") is False


class TestRemoveRole:
    def test_success_statuses_include_404(self):
        c = _client()
        for status in (200, 204, 404):
            with patch.object(mod.httpx, "delete", return_value=_resp(status)) as d:
                assert c.remove_role("u1", "r1") is True
            url, = d.call_args.args
            assert url == (
                "https://discord.com/api/v10/guilds/g1/members/u1/roles/r1"
            )

    def test_non_success_returns_false(self):
        c = _client()
        with patch.object(mod.httpx, "delete", return_value=_resp(500)):
            assert c.remove_role("u1", "r1") is False

    def test_http_error_returns_false(self):
        c = _client()
        with patch.object(mod.httpx, "delete", side_effect=httpx.HTTPError("x")):
            assert c.remove_role("u1", "r1") is False


class TestAddMemberToGuild:
    def test_added_201(self):
        c = _client()
        with patch.object(mod.httpx, "put", return_value=_resp(201)) as put:
            assert c.add_member_to_guild("u1", "atoken") is True
        assert put.call_args.kwargs["json"] == {"access_token": "atoken"}
        url, = put.call_args.args
        assert url == "https://discord.com/api/v10/guilds/g1/members/u1"

    def test_already_member_204(self):
        c = _client()
        with patch.object(mod.httpx, "put", return_value=_resp(204)):
            assert c.add_member_to_guild("u1", "atoken") is True

    def test_failure_status_returns_false(self):
        c = _client()
        with patch.object(mod.httpx, "put", return_value=_resp(403, text="forbidden")):
            assert c.add_member_to_guild("u1", "atoken") is False

    def test_http_error_returns_false(self):
        c = _client()
        with patch.object(mod.httpx, "put", side_effect=httpx.HTTPError("x")):
            assert c.add_member_to_guild("u1", "atoken") is False


class TestAddMemberWithBot:
    def test_added_with_access_token_sets_body(self):
        c = _client()
        with patch.object(mod.httpx, "put", return_value=_resp(201)) as put:
            assert c.add_member_with_bot("u1", "atoken") is True
        assert put.call_args.kwargs["json"] == {"access_token": "atoken"}
        assert put.call_args.kwargs["headers"]["Content-Type"] == "application/json"

    def test_added_without_access_token_empty_body(self):
        c = _client()
        with patch.object(mod.httpx, "put", return_value=_resp(204)) as put:
            assert c.add_member_with_bot("u1") is True
        assert put.call_args.kwargs["json"] == {}

    def test_failure_status_returns_false(self):
        c = _client()
        with patch.object(mod.httpx, "put", return_value=_resp(400, text="bad")):
            assert c.add_member_with_bot("u1", "atoken") is False

    def test_http_error_returns_false(self):
        c = _client()
        with patch.object(mod.httpx, "put", side_effect=httpx.HTTPError("x")):
            assert c.add_member_with_bot("u1", "atoken") is False


class TestGetGuildRoles:
    def test_success_returns_json(self):
        c = _client()
        roles = [{"id": "r1", "name": "Builder", "color": 255}]
        resp = _resp(200, roles)
        with patch.object(mod.httpx, "get", return_value=resp) as get:
            assert c.get_guild_roles() == roles
        url, = get.call_args.args
        assert url == "https://discord.com/api/v10/guilds/g1/roles"

    def test_http_error_returns_none(self):
        c = _client()
        with patch.object(mod.httpx, "get", side_effect=httpx.HTTPError("x")):
            assert c.get_guild_roles() is None

    def test_raise_for_status_error_returns_none(self):
        c = _client()
        resp = _resp(500)
        resp.raise_for_status.side_effect = httpx.HTTPError("500")
        with patch.object(mod.httpx, "get", return_value=resp):
            assert c.get_guild_roles() is None


class TestGetMemberRolesWithDetails:
    def test_member_not_in_guild_returns_none(self):
        c = _client()
        with patch.object(c, "get_member_roles", return_value=None):
            assert c.get_member_roles_with_details("u1") is None

    def test_guild_roles_failure_returns_none(self):
        c = _client()
        with patch.object(c, "get_member_roles", return_value=["r1"]), patch.object(
            c, "get_guild_roles", return_value=None
        ):
            assert c.get_member_roles_with_details("u1") is None

    def test_merges_names_and_colors_excludes_everyone(self):
        c = _client()
        member_roles = ["r1", "r2", "r3", "unknown"]
        guild_roles = [
            {"id": "r1", "name": "Builder", "color": 255},  # -> #0000ff
            {"id": "r2", "name": "@everyone", "color": 0},  # excluded
            {"id": "r3", "name": "Explorer", "color": 0},  # color None
        ]
        with patch.object(c, "get_member_roles", return_value=member_roles), patch.object(
            c, "get_guild_roles", return_value=guild_roles
        ):
            result = c.get_member_roles_with_details("u1")
        assert result == [
            {"name": "Builder", "color": "#0000ff"},
            {"name": "Explorer", "color": None},
        ]

    def test_missing_color_defaults_to_zero(self):
        c = _client()
        with patch.object(c, "get_member_roles", return_value=["r1"]), patch.object(
            c, "get_guild_roles", return_value=[{"id": "r1", "name": "NoColor"}]
        ):
            result = c.get_member_roles_with_details("u1")
        assert result == [{"name": "NoColor", "color": None}]
