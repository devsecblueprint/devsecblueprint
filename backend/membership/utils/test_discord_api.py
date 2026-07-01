"""Unit tests for the Discord API client."""

from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from utils.discord_api import DiscordClient


@pytest.fixture
def client():
    """Create a DiscordClient instance for testing."""
    return DiscordClient(bot_token="test-bot-token", guild_id="123456789012345678")


@pytest.fixture
def mock_session(client):
    """Mock the internal requests session."""
    with patch.object(client, "_session") as mock:
        yield mock


class TestDiscordClientInit:
    def test_sets_base_url(self):
        assert DiscordClient.BASE_URL == "https://discord.com/api/v10"

    def test_sets_timeout(self):
        assert DiscordClient.TIMEOUT == 10

    def test_sets_max_retries(self):
        assert DiscordClient.MAX_RETRIES == 5

    def test_sets_backoff_params(self):
        assert DiscordClient.BASE_BACKOFF == 1
        assert DiscordClient.MAX_BACKOFF == 60

    def test_stores_bot_token_and_guild_id(self, client):
        assert client.bot_token == "test-bot-token"
        assert client.guild_id == "123456789012345678"

    def test_session_has_authorization_header(self, client):
        assert client._session.headers["Authorization"] == "Bot test-bot-token"

    def test_session_has_content_type_header(self, client):
        assert client._session.headers["Content-Type"] == "application/json"


class TestGetMember:
    def test_returns_member_dict_on_200(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {
            "user": {"id": "111"},
            "roles": ["role1", "role2"],
        }
        mock_session.request.return_value = mock_response

        result = client.get_member("111")

        assert result == {"user": {"id": "111"}, "roles": ["role1", "role2"]}
        mock_session.request.assert_called_once_with(
            "GET",
            "https://discord.com/api/v10/guilds/123456789012345678/members/111",
            timeout=10,
        )

    def test_returns_none_on_404(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        result = client.get_member("999")
        assert result is None

    def test_returns_none_on_request_failure(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {}
        mock_response.text = "Forbidden"
        mock_session.request.return_value = mock_response

        result = client.get_member("111")
        assert result is None


class TestAddMemberToGuild:
    def test_returns_true_on_201(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        result = client.add_member_to_guild("111", "oauth-token-abc")
        assert result is True
        mock_session.request.assert_called_once_with(
            "PUT",
            "https://discord.com/api/v10/guilds/123456789012345678/members/111",
            json={"access_token": "oauth-token-abc"},
            timeout=10,
        )

    def test_returns_true_on_204_already_member(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        result = client.add_member_to_guild("111", "oauth-token")
        assert result is True

    def test_returns_false_on_failure(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {}
        mock_response.text = "Missing permissions"
        mock_session.request.return_value = mock_response

        result = client.add_member_to_guild("111", "oauth-token")
        assert result is False


class TestGetMemberRoles:
    def test_returns_roles_list(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {
            "user": {"id": "111"},
            "roles": ["role_a", "role_b", "role_c"],
        }
        mock_session.request.return_value = mock_response

        result = client.get_member_roles("111")
        assert result == ["role_a", "role_b", "role_c"]

    def test_returns_none_if_not_in_guild(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        result = client.get_member_roles("999")
        assert result is None

    def test_returns_empty_list_if_no_roles(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {"user": {"id": "111"}, "roles": []}
        mock_session.request.return_value = mock_response

        result = client.get_member_roles("111")
        assert result == []


class TestAddRole:
    def test_returns_true_on_204(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        result = client.add_role("111", "role_abc")
        assert result is True
        mock_session.request.assert_called_once_with(
            "PUT",
            "https://discord.com/api/v10/guilds/123456789012345678/members/111/roles/role_abc",
            timeout=10,
        )

    def test_returns_false_on_404(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        result = client.add_role("111", "role_abc")
        assert result is False

    def test_returns_false_on_other_error(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {}
        mock_response.text = "Missing permissions"
        mock_session.request.return_value = mock_response

        result = client.add_role("111", "role_abc")
        assert result is False


class TestRemoveRole:
    def test_returns_true_on_204(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        result = client.remove_role("111", "role_abc")
        assert result is True
        mock_session.request.assert_called_once_with(
            "DELETE",
            "https://discord.com/api/v10/guilds/123456789012345678/members/111/roles/role_abc",
            timeout=10,
        )

    def test_returns_false_on_404(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        result = client.remove_role("111", "role_abc")
        assert result is False

    def test_returns_false_on_other_error(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {}
        mock_response.text = "Missing permissions"
        mock_session.request.return_value = mock_response

        result = client.remove_role("111", "role_abc")
        assert result is False


class TestRequestRetryLogic:
    @patch("utils.discord_api.time.sleep")
    def test_retries_on_429_with_retry_after_header(
        self, mock_sleep, client, mock_session
    ):
        rate_limited = MagicMock()
        rate_limited.status_code = 429
        rate_limited.headers = {"Retry-After": "2.5"}
        rate_limited.json.return_value = {}

        success = MagicMock()
        success.status_code = 200
        success.headers = {}

        mock_session.request.side_effect = [rate_limited, success]

        result = client._request("GET", "/test")
        assert result.status_code == 200
        mock_sleep.assert_called_with(2.5)

    @patch("utils.discord_api.time.sleep")
    def test_retries_on_429_with_json_retry_after(
        self, mock_sleep, client, mock_session
    ):
        rate_limited = MagicMock()
        rate_limited.status_code = 429
        rate_limited.headers = {}
        rate_limited.json.return_value = {"retry_after": 1.5}

        success = MagicMock()
        success.status_code = 200
        success.headers = {}

        mock_session.request.side_effect = [rate_limited, success]

        result = client._request("GET", "/test")
        assert result.status_code == 200
        mock_sleep.assert_called_with(1.5)

    @patch("utils.discord_api.time.sleep")
    def test_exponential_backoff_on_500(self, mock_sleep, client, mock_session):
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.headers = {}

        success = MagicMock()
        success.status_code = 200
        success.headers = {}

        mock_session.request.side_effect = [
            error_response,
            error_response,
            success,
        ]

        result = client._request("GET", "/test")
        assert result.status_code == 200

        # First backoff: 1s (1 * 2^0), second: 2s (1 * 2^1)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)

    @patch("utils.discord_api.time.sleep")
    def test_returns_none_after_max_retries_on_500(
        self, mock_sleep, client, mock_session
    ):
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.headers = {}

        mock_session.request.return_value = error_response

        result = client._request("GET", "/test")
        assert result is None
        assert mock_session.request.call_count == 5

    @patch("utils.discord_api.time.sleep")
    def test_returns_none_on_non_retryable_4xx(self, mock_sleep, client, mock_session):
        error_response = MagicMock()
        error_response.status_code = 403
        error_response.headers = {}
        error_response.text = "Forbidden"

        mock_session.request.return_value = error_response

        result = client._request("GET", "/test")
        assert result is None
        # Should not retry on 4xx (except 429)
        assert mock_session.request.call_count == 1

    def test_returns_404_response_to_caller(self, client, mock_session):
        not_found = MagicMock()
        not_found.status_code = 404
        not_found.headers = {}

        mock_session.request.return_value = not_found

        result = client._request("GET", "/test")
        assert result is not None
        assert result.status_code == 404

    @patch("utils.discord_api.time.sleep")
    def test_handles_timeout_exception_with_backoff(
        self, mock_sleep, client, mock_session
    ):
        import requests as req

        mock_session.request.side_effect = [
            req.exceptions.Timeout("timed out"),
            MagicMock(status_code=200, headers={}),
        ]

        result = client._request("GET", "/test")
        assert result.status_code == 200
        mock_sleep.assert_called_once_with(1)  # First attempt backoff

    @patch("utils.discord_api.time.sleep")
    def test_handles_request_exception_with_backoff(
        self, mock_sleep, client, mock_session
    ):
        import requests as req

        mock_session.request.side_effect = [
            req.exceptions.ConnectionError("connection refused"),
            MagicMock(status_code=200, headers={}),
        ]

        result = client._request("GET", "/test")
        assert result.status_code == 200
        mock_sleep.assert_called_once_with(1)

    def test_uses_10_second_timeout(self, client, mock_session):
        success = MagicMock()
        success.status_code = 200
        success.headers = {}
        mock_session.request.return_value = success

        client._request("GET", "/test")
        _, kwargs = mock_session.request.call_args
        assert kwargs["timeout"] == 10


class TestHandleRateLimit:
    @patch("utils.discord_api.time.sleep")
    def test_sleeps_when_remaining_is_zero(self, mock_sleep, client):
        response = MagicMock()
        response.headers = {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset-After": "3.5",
        }

        client._handle_rate_limit(response)
        mock_sleep.assert_called_once_with(3.5)

    @patch("utils.discord_api.time.sleep")
    def test_does_not_sleep_when_remaining_nonzero(self, mock_sleep, client):
        response = MagicMock()
        response.headers = {
            "X-RateLimit-Remaining": "5",
            "X-RateLimit-Reset-After": "3.5",
        }

        client._handle_rate_limit(response)
        mock_sleep.assert_not_called()

    @patch("utils.discord_api.time.sleep")
    def test_does_not_sleep_when_headers_missing(self, mock_sleep, client):
        response = MagicMock()
        response.headers = {}

        client._handle_rate_limit(response)
        mock_sleep.assert_not_called()


class TestCalculateBackoff:
    def test_first_attempt_is_1s(self, client):
        assert client._calculate_backoff(0) == 1

    def test_second_attempt_is_2s(self, client):
        assert client._calculate_backoff(1) == 2

    def test_third_attempt_is_4s(self, client):
        assert client._calculate_backoff(2) == 4

    def test_fourth_attempt_is_8s(self, client):
        assert client._calculate_backoff(3) == 8

    def test_fifth_attempt_is_16s(self, client):
        assert client._calculate_backoff(4) == 16

    def test_capped_at_max_backoff(self, client):
        assert client._calculate_backoff(10) == 60


class TestGetRetryAfter:
    def test_from_header(self, client):
        response = MagicMock()
        response.headers = {"Retry-After": "5.0"}
        response.json.return_value = {}

        assert client._get_retry_after(response) == 5.0

    def test_from_json_body(self, client):
        response = MagicMock()
        response.headers = {}
        response.json.return_value = {"retry_after": 2.75}

        assert client._get_retry_after(response) == 2.75

    def test_defaults_to_1_when_missing(self, client):
        response = MagicMock()
        response.headers = {}
        response.json.return_value = {}

        assert client._get_retry_after(response) == 1.0

    def test_header_takes_precedence_over_body(self, client):
        response = MagicMock()
        response.headers = {"Retry-After": "10"}
        response.json.return_value = {"retry_after": 3}

        assert client._get_retry_after(response) == 10.0
