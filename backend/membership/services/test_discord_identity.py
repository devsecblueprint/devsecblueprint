"""Unit tests for discord_identity.py service (OAuth, confirm, disconnect, status)."""

import os
from unittest.mock import MagicMock, patch

import pytest

os.environ["MEMBERSHIP_TABLE"] = "test-membership-table"
os.environ["DISCORD_BOT_SECRET_NAME"] = "test-bot-secret"
os.environ["DISCORD_GUILD_ID"] = "12345678901234567"
os.environ["DISCORD_SECRET_NAME"] = "test-discord-secret"
os.environ["FRONTEND_URL"] = "https://test.devsecblueprint.com"
os.environ["DISCORD_CALLBACK_URL"] = (
    "https://api.test.devsecblueprint.com/auth/discord/callback"
)


from services import discord_identity
from services.discord_identity import (
    _exchange_code_for_token,
    _fetch_discord_profile,
    handle_callback,
    start_oauth,
    DISCORD_OAUTH_AUTHORIZE_URL,
)


@pytest.fixture
def mock_get_discord_history():
    with patch.object(discord_identity, "get_discord_history") as mock:
        yield mock


@pytest.fixture
def mock_membership_db():
    with patch("services.discord_identity.membership_db") as mock:
        yield mock


@pytest.fixture
def mock_get_secret_oauth():
    with patch("services.discord_identity.get_secret") as mock:
        mock.return_value = {
            "client_id": "test_client_id_12345",
            "client_secret": "test_client_secret_67890",
        }
        yield mock


# ---------------------------------------------------------------------------
# Tests for start_oauth (Task 17)
# ---------------------------------------------------------------------------


class TestStartOAuth:
    """Tests for the start_oauth function."""

    @patch("services.discord_identity.get_secret")
    @patch("services.discord_identity.membership_db")
    def test_happy_path_returns_authorization_url(self, mock_db, mock_secret):
        """Start OAuth returns a valid Discord authorization URL."""
        mock_db.get_discord_active.return_value = None
        mock_secret.return_value = {
            "client_id": "test_client_id_12345",
            "client_secret": "test_secret",
        }

        result = start_oauth("user-123")

        assert DISCORD_OAUTH_AUTHORIZE_URL in result
        assert "client_id=test_client_id_12345" in result
        assert "response_type=code" in result
        assert "state=" in result

    @patch("services.discord_identity.get_secret")
    @patch("services.discord_identity.membership_db")
    def test_includes_correct_scopes(self, mock_db, mock_secret):
        """Authorization URL includes identify, guilds, and guilds.join scopes."""
        mock_db.get_discord_active.return_value = None
        mock_secret.return_value = {"client_id": "abc123", "client_secret": "sec"}

        result = start_oauth("user-456")

        assert "identify" in result
        assert "guilds" in result
        assert "guilds.join" in result

    @patch("services.discord_identity.get_secret")
    @patch("services.discord_identity.membership_db")
    def test_stores_state_in_dynamodb(self, mock_db, mock_secret):
        """State parameter is stored in DynamoDB for later validation."""
        mock_db.get_discord_active.return_value = None
        mock_secret.return_value = {"client_id": "abc", "client_secret": "sec"}

        start_oauth("user-789")

        mock_db.store_oauth_state.assert_called_once()
        call_args = mock_db.store_oauth_state.call_args[0]
        state = call_args[0]
        user_id = call_args[1]
        assert user_id == "user-789"
        assert len(state) > 20  # token_urlsafe(32) produces ~43 chars

    @patch("services.discord_identity.membership_db")
    def test_raises_if_already_connected(self, mock_db):
        """Raises ValueError if user already has an active Discord connection."""
        mock_db.get_discord_active.return_value = {
            "PK": {"S": "USER#user-existing"},
            "SK": {"S": "DISCORD_ACTIVE"},
        }

        with pytest.raises(ValueError, match="already connected"):
            start_oauth("user-existing")

    @patch("services.discord_identity.get_secret")
    @patch("services.discord_identity.membership_db")
    def test_includes_callback_url(self, mock_db, mock_secret):
        """Authorization URL includes the redirect_uri parameter."""
        mock_db.get_discord_active.return_value = None
        mock_secret.return_value = {"client_id": "cid", "client_secret": "sec"}

        result = start_oauth("user-100")

        assert "redirect_uri=" in result

    @patch("services.discord_identity.get_secret")
    @patch("services.discord_identity.membership_db")
    def test_raises_if_client_id_missing(self, mock_db, mock_secret):
        """Raises Exception if client_id not found in secrets."""
        mock_db.get_discord_active.return_value = None
        mock_secret.return_value = {"client_secret": "sec"}

        with pytest.raises(Exception, match="client_id not found"):
            start_oauth("user-200")


# ---------------------------------------------------------------------------
# Tests for handle_callback (Task 18)
# ---------------------------------------------------------------------------


class TestHandleCallback:
    """Tests for the handle_callback function."""

    @patch("services.discord_identity.membership_db")
    def test_invalid_state_raises_value_error(self, mock_db):
        """Raises ValueError when state parameter is invalid or expired."""
        mock_db.validate_oauth_state.return_value = None

        with pytest.raises(ValueError, match="Invalid or expired state"):
            handle_callback("some_code", "invalid_state")

    @patch("services.discord_identity._fetch_discord_profile")
    @patch("services.discord_identity._exchange_code_for_token")
    @patch("services.discord_identity.get_secret")
    @patch("services.discord_identity.membership_db")
    def test_happy_path_returns_user_id(
        self, mock_db, mock_secret, mock_exchange, mock_fetch
    ):
        """Successful callback returns the user_id."""
        mock_db.validate_oauth_state.return_value = "user-happy"
        mock_secret.return_value = {
            "client_id": "cid",
            "client_secret": "csecret",
        }
        mock_exchange.return_value = "fake_access_token"
        mock_fetch.return_value = {
            "id": "12345678901234567",
            "username": "testuser",
            "global_name": "Test User",
            "avatar": "abc123hash",
        }
        mock_db.check_discord_duplicate.return_value = None

        result = handle_callback("auth_code_123", "valid_state")

        assert result == "user-happy"

    @patch("services.discord_identity._fetch_discord_profile")
    @patch("services.discord_identity._exchange_code_for_token")
    @patch("services.discord_identity.get_secret")
    @patch("services.discord_identity.membership_db")
    def test_stores_unverified_record_with_ttl(
        self, mock_db, mock_secret, mock_exchange, mock_fetch
    ):
        """Stores a Discord identity record with 15-minute TTL."""
        mock_db.validate_oauth_state.return_value = "user-ttl"
        mock_secret.return_value = {
            "client_id": "cid",
            "client_secret": "csecret",
        }
        mock_exchange.return_value = "token123"
        mock_fetch.return_value = {
            "id": "98765432109876543",
            "username": "anotheruser",
            "global_name": "Another User",
            "avatar": None,
        }
        mock_db.check_discord_duplicate.return_value = None

        handle_callback("code", "state")

        mock_db.put_discord_identity.assert_called_once()
        item = mock_db.put_discord_identity.call_args[0][0]

        assert item["PK"] == {"S": "USER#user-ttl"}
        assert item["SK"] == {"S": "DISCORD#98765432109876543"}
        assert item["active"] == {"BOOL": False}
        assert item["platform_state"] == {"S": "Discord_Connected"}
        assert "expires_at" in item
        assert item["expires_at"]["N"]  # Should be a numeric TTL string

    @patch("services.discord_identity._fetch_discord_profile")
    @patch("services.discord_identity._exchange_code_for_token")
    @patch("services.discord_identity.get_secret")
    @patch("services.discord_identity.membership_db")
    def test_duplicate_discord_id_raises(
        self, mock_db, mock_secret, mock_exchange, mock_fetch
    ):
        """Raises ValueError when Discord ID is already linked to another user."""
        mock_db.validate_oauth_state.return_value = "user-dup"
        mock_secret.return_value = {
            "client_id": "cid",
            "client_secret": "csecret",
        }
        mock_exchange.return_value = "token"
        mock_fetch.return_value = {
            "id": "11111111111111111",
            "username": "dupuser",
            "global_name": "Dup",
            "avatar": None,
        }
        mock_db.check_discord_duplicate.return_value = {
            "PK": {"S": "USER#other-user"},
            "active": {"BOOL": True},
        }

        with pytest.raises(ValueError, match="already linked"):
            handle_callback("code", "state")

    @patch("services.discord_identity._fetch_discord_profile")
    @patch("services.discord_identity._exchange_code_for_token")
    @patch("services.discord_identity.get_secret")
    @patch("services.discord_identity.membership_db")
    def test_invalid_discord_id_format_raises(
        self, mock_db, mock_secret, mock_exchange, mock_fetch
    ):
        """Raises ValueError when Discord user ID has invalid format."""
        mock_db.validate_oauth_state.return_value = "user-bad-id"
        mock_secret.return_value = {
            "client_id": "cid",
            "client_secret": "csecret",
        }
        mock_exchange.return_value = "token"
        mock_fetch.return_value = {
            "id": "short",  # Not a valid snowflake
            "username": "baduser",
            "global_name": "Bad",
            "avatar": None,
        }
        mock_db.check_discord_duplicate.return_value = None

        with pytest.raises(ValueError, match="Invalid Discord user ID"):
            handle_callback("code", "state")

    @patch("services.discord_identity._fetch_discord_profile")
    @patch("services.discord_identity._exchange_code_for_token")
    @patch("services.discord_identity.get_secret")
    @patch("services.discord_identity.membership_db")
    def test_username_too_long_raises(
        self, mock_db, mock_secret, mock_exchange, mock_fetch
    ):
        """Raises ValueError when username exceeds 100 characters."""
        mock_db.validate_oauth_state.return_value = "user-longname"
        mock_secret.return_value = {
            "client_id": "cid",
            "client_secret": "csecret",
        }
        mock_exchange.return_value = "token"
        mock_fetch.return_value = {
            "id": "12345678901234567",
            "username": "x" * 101,
            "global_name": "Long",
            "avatar": None,
        }
        mock_db.check_discord_duplicate.return_value = None

        with pytest.raises(ValueError, match="exceeds maximum length"):
            handle_callback("code", "state")

    @patch("services.discord_identity._fetch_discord_profile")
    @patch("services.discord_identity._exchange_code_for_token")
    @patch("services.discord_identity.get_secret")
    @patch("services.discord_identity.membership_db")
    def test_control_characters_in_username_raises(
        self, mock_db, mock_secret, mock_exchange, mock_fetch
    ):
        """Raises ValueError when username contains control characters."""
        mock_db.validate_oauth_state.return_value = "user-ctrl"
        mock_secret.return_value = {
            "client_id": "cid",
            "client_secret": "csecret",
        }
        mock_exchange.return_value = "token"
        mock_fetch.return_value = {
            "id": "12345678901234567",
            "username": "bad\x00user",
            "global_name": "Normal",
            "avatar": None,
        }
        mock_db.check_discord_duplicate.return_value = None

        with pytest.raises(ValueError, match="control characters"):
            handle_callback("code", "state")

    @patch("services.discord_identity._fetch_discord_profile")
    @patch("services.discord_identity._exchange_code_for_token")
    @patch("services.discord_identity.get_secret")
    @patch("services.discord_identity.membership_db")
    def test_avatar_url_constructed_when_hash_present(
        self, mock_db, mock_secret, mock_exchange, mock_fetch
    ):
        """Avatar URL is correctly constructed from hash when present."""
        mock_db.validate_oauth_state.return_value = "user-avatar"
        mock_secret.return_value = {
            "client_id": "cid",
            "client_secret": "csecret",
        }
        mock_exchange.return_value = "token"
        mock_fetch.return_value = {
            "id": "12345678901234567",
            "username": "avataruser",
            "global_name": "Avatar User",
            "avatar": "abc123def",
        }
        mock_db.check_discord_duplicate.return_value = None

        handle_callback("code", "state")

        item = mock_db.put_discord_identity.call_args[0][0]
        assert item["avatar_url"] == {
            "S": "https://cdn.discordapp.com/avatars/12345678901234567/abc123def.png"
        }

    @patch("services.discord_identity._fetch_discord_profile")
    @patch("services.discord_identity._exchange_code_for_token")
    @patch("services.discord_identity.get_secret")
    @patch("services.discord_identity.membership_db")
    def test_no_avatar_when_hash_is_none(
        self, mock_db, mock_secret, mock_exchange, mock_fetch
    ):
        """Avatar URL is not stored when avatar hash is None."""
        mock_db.validate_oauth_state.return_value = "user-noavatar"
        mock_secret.return_value = {
            "client_id": "cid",
            "client_secret": "csecret",
        }
        mock_exchange.return_value = "token"
        mock_fetch.return_value = {
            "id": "12345678901234567",
            "username": "noavataruser",
            "global_name": "No Avatar",
            "avatar": None,
        }
        mock_db.check_discord_duplicate.return_value = None

        handle_callback("code", "state")

        item = mock_db.put_discord_identity.call_args[0][0]
        assert "avatar_url" not in item

    @patch("services.discord_identity.get_secret")
    @patch("services.discord_identity.membership_db")
    def test_incomplete_secrets_raises(self, mock_db, mock_secret):
        """Raises Exception when client_id or client_secret missing from secrets."""
        mock_db.validate_oauth_state.return_value = "user-nosecret"
        mock_secret.return_value = {"client_id": "cid"}  # Missing client_secret

        with pytest.raises(Exception, match="credentials incomplete"):
            handle_callback("code", "state")


# ---------------------------------------------------------------------------
# Tests for _exchange_code_for_token helper
# ---------------------------------------------------------------------------


class TestExchangeCodeForToken:
    """Tests for the _exchange_code_for_token helper."""

    @patch("services.discord_identity.requests.post")
    def test_successful_exchange(self, mock_post):
        """Returns access token on successful exchange."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "my_token_123"}
        mock_post.return_value = mock_response

        result = _exchange_code_for_token("code", "cid", "csec", "http://callback")

        assert result == "my_token_123"

    @patch("services.discord_identity.requests.post")
    def test_non_200_raises_value_error(self, mock_post):
        """Raises ValueError when Discord returns non-200 status."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to exchange"):
            _exchange_code_for_token("code", "cid", "csec", "http://callback")

    @patch("services.discord_identity.requests.post")
    def test_network_error_raises_value_error(self, mock_post):
        """Raises ValueError on network errors."""
        import requests as req

        mock_post.side_effect = req.exceptions.ConnectionError("Connection refused")

        with pytest.raises(ValueError, match="Failed to exchange"):
            _exchange_code_for_token("code", "cid", "csec", "http://callback")

    @patch("services.discord_identity.requests.post")
    def test_missing_access_token_in_response(self, mock_post):
        """Raises ValueError when access_token not in response body."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token_type": "Bearer"}
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to exchange"):
            _exchange_code_for_token("code", "cid", "csec", "http://callback")


# ---------------------------------------------------------------------------
# Tests for _fetch_discord_profile helper
# ---------------------------------------------------------------------------


class TestFetchDiscordProfile:
    """Tests for the _fetch_discord_profile helper."""

    @patch("services.discord_identity.requests.get")
    def test_successful_fetch(self, mock_get):
        """Returns profile dict on success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "12345678901234567",
            "username": "testuser",
        }
        mock_get.return_value = mock_response

        result = _fetch_discord_profile("access_token")

        assert result["id"] == "12345678901234567"
        mock_get.assert_called_once()

    @patch("services.discord_identity.requests.get")
    def test_non_200_raises_value_error(self, mock_get):
        """Raises ValueError on non-200 response."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to fetch Discord profile"):
            _fetch_discord_profile("bad_token")

    @patch("services.discord_identity.requests.get")
    def test_network_error_raises_value_error(self, mock_get):
        """Raises ValueError on network errors."""
        import requests as req

        mock_get.side_effect = req.exceptions.Timeout("Timeout")

        with pytest.raises(ValueError, match="Failed to fetch Discord profile"):
            _fetch_discord_profile("token")

    @patch("services.discord_identity.requests.get")
    def test_uses_bearer_auth_header(self, mock_get):
        """Sends Bearer token in Authorization header."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", "username": "u"}
        mock_get.return_value = mock_response

        _fetch_discord_profile("my_access_token")

        call_kwargs = mock_get.call_args
        assert call_kwargs[1]["headers"]["Authorization"] == "Bearer my_access_token"


# ---------------------------------------------------------------------------
# Tests for confirm_identity (Task 19), disconnect (Task 20), get_status (Task 21)
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_activate_discord_connection():
    with patch.object(discord_identity, "activate_discord_connection") as mock:
        yield mock


@pytest.fixture
def mock_get_discord_active():
    with patch.object(discord_identity, "get_discord_active") as mock:
        yield mock


@pytest.fixture
def mock_deactivate_discord_connection():
    with patch.object(discord_identity, "deactivate_discord_connection") as mock:
        yield mock


@pytest.fixture
def mock_get_secret():
    with patch.object(discord_identity, "get_secret") as mock:
        mock.return_value = {"secret_key": "bot-token-123"}
        yield mock


@pytest.fixture
def mock_discord_client():
    with patch.object(discord_identity, "DiscordClient") as mock:
        yield mock


@pytest.fixture
def mock_publish_sync_event():
    with patch.object(discord_identity, "publish_sync_event") as mock:
        yield mock


@pytest.fixture
def mock_write_audit_log():
    with patch.object(discord_identity, "write_audit_log") as mock:
        yield mock


@pytest.fixture
def mock_update_platform_state():
    with patch.object(discord_identity, "_update_platform_state") as mock:
        yield mock


class TestConfirmIdentity:
    """Tests for confirm_identity function."""

    def _pending_record(self):
        return {
            "PK": {"S": "USER#user1"},
            "SK": {"S": "DISCORD#111222333444555666"},
            "discord_user_id": {"S": "111222333444555666"},
            "username": {"S": "testuser"},
            "display_name": {"S": "Test User"},
            "avatar_url": {"S": "https://cdn.discordapp.com/avatars/111/abc.png"},
            "active": {"BOOL": False},
        }

    def test_confirm_happy_path_user_in_guild(
        self,
        mock_get_discord_history,
        mock_activate_discord_connection,
        mock_get_secret,
        mock_discord_client,
        mock_publish_sync_event,
        mock_write_audit_log,
        mock_update_platform_state,
    ):
        mock_get_discord_history.return_value = [self._pending_record()]
        client_instance = MagicMock()
        client_instance.get_member.return_value = {"user": {"id": "111222333444555666"}}
        mock_discord_client.return_value = client_instance

        result = discord_identity.confirm_identity("user1")

        assert result["discord_user_id"] == "111222333444555666"
        assert result["username"] == "testuser"
        assert result["display_name"] == "Test User"
        assert result["platform_state"] == "Server_Joined"

        mock_activate_discord_connection.assert_called_once_with(
            "user1",
            {
                "discord_user_id": "111222333444555666",
                "username": "testuser",
                "display_name": "Test User",
                "avatar_url": "https://cdn.discordapp.com/avatars/111/abc.png",
            },
        )
        mock_publish_sync_event.assert_called_once_with(
            "user1", "discord_connected", None
        )
        mock_update_platform_state.assert_called_once_with("user1", "Server_Joined")
        # Connected + Verified + Guild_Joined = 3 audit calls
        assert mock_write_audit_log.call_count == 3

    def test_confirm_user_not_in_guild(
        self,
        mock_get_discord_history,
        mock_activate_discord_connection,
        mock_get_secret,
        mock_discord_client,
        mock_publish_sync_event,
        mock_write_audit_log,
        mock_update_platform_state,
    ):
        mock_get_discord_history.return_value = [self._pending_record()]
        client_instance = MagicMock()
        client_instance.get_member.return_value = None
        mock_discord_client.return_value = client_instance

        result = discord_identity.confirm_identity("user1")

        assert result["platform_state"] == "Discord_Verified"
        mock_update_platform_state.assert_not_called()
        # Connected + Verified = 2 audit calls (no Guild_Joined)
        assert mock_write_audit_log.call_count == 2

    def test_confirm_no_pending_record_raises_value_error(
        self,
        mock_get_discord_history,
    ):
        mock_get_discord_history.return_value = []

        with pytest.raises(ValueError, match="No pending Discord connection found"):
            discord_identity.confirm_identity("user1")

    def test_confirm_already_verified_skips(
        self,
        mock_get_discord_history,
    ):
        # Record with verified_at set (already verified)
        record = self._pending_record()
        record["verified_at"] = {"S": "2024-01-01T00:00:00Z"}
        mock_get_discord_history.return_value = [record]

        with pytest.raises(ValueError, match="No pending Discord connection found"):
            discord_identity.confirm_identity("user1")

    def test_confirm_already_active_skips(
        self,
        mock_get_discord_history,
    ):
        record = self._pending_record()
        record["active"] = {"BOOL": True}
        mock_get_discord_history.return_value = [record]

        with pytest.raises(ValueError, match="No pending Discord connection found"):
            discord_identity.confirm_identity("user1")

    def test_confirm_guild_check_failure_defaults_to_verified(
        self,
        mock_get_discord_history,
        mock_activate_discord_connection,
        mock_get_secret,
        mock_discord_client,
        mock_publish_sync_event,
        mock_write_audit_log,
        mock_update_platform_state,
    ):
        mock_get_discord_history.return_value = [self._pending_record()]
        mock_get_secret.side_effect = Exception("Secret not found")

        result = discord_identity.confirm_identity("user1")

        assert result["platform_state"] == "Discord_Verified"
        mock_update_platform_state.assert_not_called()


class TestDisconnect:
    """Tests for disconnect function."""

    def _active_record(self):
        return {
            "PK": {"S": "USER#user1"},
            "SK": {"S": "DISCORD_ACTIVE"},
            "discord_user_id": {"S": "111222333444555666"},
            "username": {"S": "testuser"},
            "active": {"BOOL": True},
        }

    def test_disconnect_happy_path(
        self,
        mock_get_discord_active,
        mock_deactivate_discord_connection,
        mock_get_secret,
        mock_discord_client,
        mock_write_audit_log,
    ):
        mock_get_discord_active.return_value = self._active_record()
        client_instance = MagicMock()
        mock_discord_client.return_value = client_instance

        result = discord_identity.disconnect("user1")

        assert result == {"cleanup_status": "completed"}
        mock_deactivate_discord_connection.assert_called_once_with(
            "user1", "111222333444555666", "User requested"
        )
        mock_write_audit_log.assert_called_once()

    def test_disconnect_no_active_connection_raises(
        self,
        mock_get_discord_active,
    ):
        mock_get_discord_active.return_value = None

        with pytest.raises(ValueError, match="No active Discord connection found"):
            discord_identity.disconnect("user1")

    def test_disconnect_role_removal_failure(
        self,
        mock_get_discord_active,
        mock_deactivate_discord_connection,
        mock_get_secret,
        mock_discord_client,
        mock_write_audit_log,
    ):
        mock_get_discord_active.return_value = self._active_record()
        mock_get_secret.side_effect = Exception("Secret retrieval failed")

        result = discord_identity.disconnect("user1")

        assert result == {"cleanup_status": "failed"}
        # Deactivation should still happen
        mock_deactivate_discord_connection.assert_called_once()
        # Audit should still be written
        mock_write_audit_log.assert_called_once()

    def test_disconnect_removes_all_managed_roles(
        self,
        mock_get_discord_active,
        mock_deactivate_discord_connection,
        mock_get_secret,
        mock_discord_client,
        mock_write_audit_log,
    ):
        mock_get_discord_active.return_value = self._active_record()
        client_instance = MagicMock()
        mock_discord_client.return_value = client_instance

        with patch.object(
            discord_identity, "MANAGED_ROLE_IDS", ["role1", "role2", "role3"]
        ):
            discord_identity.disconnect("user1")

        assert client_instance.remove_role.call_count == 3
        client_instance.remove_role.assert_any_call("111222333444555666", "role1")
        client_instance.remove_role.assert_any_call("111222333444555666", "role2")
        client_instance.remove_role.assert_any_call("111222333444555666", "role3")


class TestGetStatus:
    """Tests for get_status function."""

    def test_get_status_connected(self, mock_get_discord_active):
        mock_get_discord_active.return_value = {
            "PK": {"S": "USER#user1"},
            "SK": {"S": "DISCORD_ACTIVE"},
            "discord_user_id": {"S": "111222333444555666"},
            "username": {"S": "testuser"},
            "avatar_url": {"S": "https://cdn.discordapp.com/avatars/111/abc.png"},
            "platform_state": {"S": "Server_Joined"},
            "last_synced_at": {"S": "2024-06-01T12:00:00Z"},
            "last_sync_status": {"S": "SUCCESS"},
        }

        result = discord_identity.get_status("user1")

        assert result == {
            "connected": True,
            "discord_username": "testuser",
            "discord_avatar_url": "https://cdn.discordapp.com/avatars/111/abc.png",
            "platform_state": "Server_Joined",
            "last_synced_at": "2024-06-01T12:00:00Z",
            "last_sync_status": "SUCCESS",
        }

    def test_get_status_not_connected(self, mock_get_discord_active):
        mock_get_discord_active.return_value = None

        result = discord_identity.get_status("user1")

        assert result == {
            "connected": False,
            "discord_username": None,
            "discord_avatar_url": None,
            "platform_state": None,
            "last_synced_at": None,
            "last_sync_status": None,
        }

    def test_get_status_missing_optional_fields(self, mock_get_discord_active):
        mock_get_discord_active.return_value = {
            "PK": {"S": "USER#user1"},
            "SK": {"S": "DISCORD_ACTIVE"},
            "discord_user_id": {"S": "111222333444555666"},
            "username": {"S": "testuser"},
            "platform_state": {"S": "Discord_Verified"},
        }

        result = discord_identity.get_status("user1")

        assert result["connected"] is True
        assert result["discord_username"] == "testuser"
        assert result["discord_avatar_url"] is None
        assert result["platform_state"] == "Discord_Verified"
        assert result["last_synced_at"] is None
        assert result["last_sync_status"] is None


class TestUpdatePlatformState:
    """Tests for _update_platform_state helper."""

    def test_update_platform_state_calls_dynamodb(self):
        with patch("boto3.client") as mock_boto3:
            mock_client = MagicMock()
            mock_boto3.return_value = mock_client

            discord_identity._update_platform_state("user1", "Server_Joined")

            mock_client.update_item.assert_called_once_with(
                TableName="test-membership-table",
                Key={
                    "PK": {"S": "USER#user1"},
                    "SK": {"S": "DISCORD_ACTIVE"},
                },
                UpdateExpression="SET platform_state = :ps",
                ExpressionAttributeValues={
                    ":ps": {"S": "Server_Joined"},
                },
            )

    def test_update_platform_state_handles_error(self):
        with patch("boto3.client") as mock_boto3:
            mock_client = MagicMock()
            mock_client.update_item.side_effect = Exception("DynamoDB error")
            mock_boto3.return_value = mock_client

            # Should not raise
            discord_identity._update_platform_state("user1", "Server_Joined")

    def test_update_platform_state_no_table_name(self):
        with patch.dict(os.environ, {"MEMBERSHIP_TABLE": ""}):
            with patch("boto3.client") as mock_boto3:
                # Should not raise, just log error
                discord_identity._update_platform_state("user1", "Server_Joined")
                mock_boto3.assert_not_called()
