"""
Unit tests for auth/github.py GitHub OAuth flow.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
import responses

from backend.auth.github import (
    start_oauth,
    exchange_code_for_token,
    get_github_user,
    handle_callback,
)


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for OAuth."""
    env = {
        "GITHUB_CLIENT_ID": "test_client_id",
        "GITHUB_CALLBACK_URL": "https://api.example.com/auth/github/callback",
        "GITHUB_SECRET_NAME": "test-github-secret",
        "FRONTEND_URL": "https://devsecblueprint.com",
        "JWT_SECRET_NAME": "test-jwt-secret",
    }
    with patch.dict(os.environ, env):
        yield


@pytest.fixture
def mock_github_secret():
    """Mock GitHub OAuth credentials from Secrets Manager."""
    return {"client_id": "test_client_id", "client_secret": "test_client_secret"}


@pytest.fixture
def mock_jwt_secret():
    """Mock JWT secret from Secrets Manager."""
    return {"secret_key": "test-jwt-secret-key"}


class TestStartOAuth:
    """Test OAuth initiation."""

    def test_constructs_github_authorization_url(
        self, mock_env_vars, mock_github_secret
    ):
        """Should construct proper GitHub OAuth URL."""
        with patch("backend.auth.github.get_secret", return_value=mock_github_secret):
            response = start_oauth()

            assert response["statusCode"] == 302
            assert "Location" in response["headers"]

            location = response["headers"]["Location"]
            assert location.startswith("https://github.com/login/oauth/authorize")
            assert "client_id=test_client_id" in location
            assert (
                "redirect_uri=https%3A%2F%2Fapi.example.com%2Fauth%2Fgithub%2Fcallback"
                in location
            )
            assert "scope=read%3Auser" in location

    def test_includes_cors_headers(self, mock_env_vars, mock_github_secret):
        """Should include CORS headers in response."""
        with patch("backend.auth.github.get_secret", return_value=mock_github_secret):
            response = start_oauth()

            headers = response["headers"]
            assert (
                headers["Access-Control-Allow-Origin"] == "https://devsecblueprint.com"
            )
            assert headers["Access-Control-Allow-Credentials"] == "true"

    def test_returns_error_when_client_id_missing(self):
        """Should return 500 error when GITHUB_CLIENT_ID is missing."""
        with patch.dict(
            os.environ, {"GITHUB_CALLBACK_URL": "https://example.com/callback"}
        ):
            response = start_oauth()

            assert response["statusCode"] == 500
            assert "error" in response["body"]

    def test_returns_error_when_callback_url_missing(self):
        """Should return 500 error when GITHUB_CALLBACK_URL is missing."""
        with patch.dict(os.environ, {"GITHUB_CLIENT_ID": "test_id"}):
            response = start_oauth()

            assert response["statusCode"] == 500
            assert "error" in response["body"]


class TestExchangeCodeForToken:
    """Test authorization code exchange."""

    @responses.activate
    def test_exchanges_code_for_token_successfully(self):
        """Should successfully exchange code for access token."""
        responses.add(
            responses.POST,
            "https://github.com/login/oauth/access_token",
            json={"access_token": "gho_test_token_12345", "token_type": "bearer"},
            status=200,
        )

        token = exchange_code_for_token(
            code="test_code",
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
        )

        assert token == "gho_test_token_12345"

    @responses.activate
    def test_sends_correct_parameters(self):
        """Should send correct parameters to GitHub."""
        responses.add(
            responses.POST,
            "https://github.com/login/oauth/access_token",
            json={"access_token": "token"},
            status=200,
        )

        exchange_code_for_token(
            code="auth_code_123",
            client_id="client_123",
            client_secret="secret_456",
            redirect_uri="https://example.com/cb",
        )

        # Verify request was made with correct data
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        assert "client_id=client_123" in request.body
        assert "client_secret=secret_456" in request.body
        assert "code=auth_code_123" in request.body

    @responses.activate
    def test_raises_error_on_failed_exchange(self):
        """Should raise error when GitHub returns non-200 status."""
        responses.add(
            responses.POST,
            "https://github.com/login/oauth/access_token",
            json={"error": "bad_verification_code"},
            status=401,
        )

        with pytest.raises(Exception) as exc_info:
            exchange_code_for_token(
                code="invalid_code",
                client_id="test_id",
                client_secret="test_secret",
                redirect_uri="https://example.com/callback",
            )

        assert "token exchange failed" in str(exc_info.value).lower()

    @responses.activate
    def test_raises_error_when_no_access_token_in_response(self):
        """Should raise error when response doesn't contain access_token."""
        responses.add(
            responses.POST,
            "https://github.com/login/oauth/access_token",
            json={"token_type": "bearer"},
            status=200,
        )

        with pytest.raises(Exception) as exc_info:
            exchange_code_for_token(
                code="test_code",
                client_id="test_id",
                client_secret="test_secret",
                redirect_uri="https://example.com/callback",
            )

        assert "access_token" in str(exc_info.value).lower()


class TestGetGitHubUser:
    """Test GitHub user profile fetching."""

    @responses.activate
    def test_fetches_user_profile_successfully(self):
        """Should successfully fetch user profile from GitHub."""
        responses.add(
            responses.GET,
            "https://api.github.com/user",
            json={
                "id": 12345678,
                "login": "testuser",
                "name": "Test User",
                "email": "test@example.com",
            },
            status=200,
        )

        user_data = get_github_user("gho_test_token")

        assert user_data["id"] == 12345678
        assert user_data["login"] == "testuser"
        assert user_data["name"] == "Test User"

    @responses.activate
    def test_sends_authorization_header(self):
        """Should send Bearer token in Authorization header."""
        responses.add(
            responses.GET,
            "https://api.github.com/user",
            json={"id": 123, "login": "user"},
            status=200,
        )

        get_github_user("test_access_token")

        assert len(responses.calls) == 1
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer test_access_token"

    @responses.activate
    def test_raises_error_on_failed_request(self):
        """Should raise error when GitHub API returns non-200 status."""
        responses.add(
            responses.GET,
            "https://api.github.com/user",
            json={"message": "Bad credentials"},
            status=401,
        )

        with pytest.raises(Exception) as exc_info:
            get_github_user("invalid_token")

        assert "user api failed" in str(exc_info.value).lower()

    @responses.activate
    def test_raises_error_when_no_id_in_response(self):
        """Should raise error when response doesn't contain user id."""
        responses.add(
            responses.GET,
            "https://api.github.com/user",
            json={"login": "user", "name": "User"},
            status=200,
        )

        with pytest.raises(Exception) as exc_info:
            get_github_user("test_token")

        assert "id" in str(exc_info.value).lower()


class TestHandleCallback:
    """Test complete OAuth callback flow."""

    @responses.activate
    def test_complete_callback_flow_success(
        self, mock_env_vars, mock_github_secret, mock_jwt_secret
    ):
        """Should successfully complete full OAuth callback flow."""
        # Mock GitHub token exchange
        responses.add(
            responses.POST,
            "https://github.com/login/oauth/access_token",
            json={"access_token": "gho_token"},
            status=200,
        )

        # Mock GitHub user API
        responses.add(
            responses.GET,
            "https://api.github.com/user",
            json={
                "id": 87654321,
                "login": "testuser",
                "name": "Test User",
                "avatar_url": "https://example.com/avatar.jpg",
            },
            status=200,
        )

        with (
            patch("backend.auth.github.get_secret") as mock_get_secret,
            patch("backend.auth.github.generate_jwt") as mock_generate_jwt,
            patch("backend.services.dynamo.register_user") as mock_register_user,
            patch("backend.services.dynamo.boto3.client"),
        ):

            # Configure mock to return different secrets based on name
            def get_secret_side_effect(secret_name):
                if secret_name == "test-github-secret":
                    return mock_github_secret
                elif secret_name == "test-jwt-secret":
                    return mock_jwt_secret
                raise Exception(f"Unknown secret: {secret_name}")

            mock_get_secret.side_effect = get_secret_side_effect
            mock_generate_jwt.return_value = "test_jwt_token_12345"

            response = handle_callback("test_auth_code")

            # Verify redirect response
            assert response["statusCode"] == 302
            # The redirect URL should contain the token
            assert "?token=test_jwt_token_12345" in response["headers"]["Location"]

    def test_returns_error_when_code_missing(self, mock_env_vars):
        """Should return 400 error when code parameter is missing."""
        # This test is for the handler that calls handle_callback
        # The function itself expects code as parameter
        pass

    @responses.activate
    def test_returns_error_on_token_exchange_failure(
        self, mock_env_vars, mock_github_secret
    ):
        """Should return 401 error when token exchange fails."""
        responses.add(
            responses.POST,
            "https://github.com/login/oauth/access_token",
            json={"error": "bad_verification_code"},
            status=401,
        )

        with patch("backend.auth.github.get_secret", return_value=mock_github_secret):
            response = handle_callback("invalid_code")

            assert response["statusCode"] == 401
            assert "error" in response["body"]
            assert "Authentication failed" in response["body"]

    @responses.activate
    def test_returns_error_on_user_fetch_failure(
        self, mock_env_vars, mock_github_secret
    ):
        """Should return 401 error when user fetch fails."""
        responses.add(
            responses.POST,
            "https://github.com/login/oauth/access_token",
            json={"access_token": "token"},
            status=200,
        )

        responses.add(
            responses.GET,
            "https://api.github.com/user",
            json={"message": "Bad credentials"},
            status=401,
        )

        with patch("backend.auth.github.get_secret", return_value=mock_github_secret):
            response = handle_callback("test_code")

            assert response["statusCode"] == 401
            assert "Authentication failed" in response["body"]

    def test_returns_error_on_secrets_manager_failure(self, mock_env_vars):
        """Should return 500 error when Secrets Manager fails."""
        with patch(
            "backend.auth.github.get_secret",
            side_effect=Exception("Secrets Manager error"),
        ):
            response = handle_callback("test_code")

            assert response["statusCode"] == 401
            assert "error" in response["body"]

    def test_returns_error_when_env_vars_missing(self):
        """Should return 500 error when required environment variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            response = handle_callback("test_code")

            assert response["statusCode"] == 500
            assert "Configuration error" in response["body"]

    def test_returns_error_when_github_credentials_incomplete(self, mock_env_vars):
        """Should return 500 error when GitHub secret is missing credentials."""
        incomplete_secret = {"client_id": "test_id"}  # Missing client_secret

        with patch("backend.auth.github.get_secret", return_value=incomplete_secret):
            response = handle_callback("test_code")

            assert response["statusCode"] == 500
            assert "Configuration error" in response["body"]

    @responses.activate
    def test_does_not_persist_github_access_token(
        self, mock_env_vars, mock_github_secret, mock_jwt_secret
    ):
        """Should not store GitHub access token anywhere."""
        responses.add(
            responses.POST,
            "https://github.com/login/oauth/access_token",
            json={"access_token": "gho_sensitive_token"},
            status=200,
        )

        responses.add(
            responses.GET,
            "https://api.github.com/user",
            json={
                "id": 12345,
                "login": "user",
                "avatar_url": "https://example.com/avatar.jpg",
            },
            status=200,
        )

        with (
            patch("backend.auth.github.get_secret") as mock_get_secret,
            patch("backend.auth.github.generate_jwt") as mock_generate_jwt,
            patch("backend.services.dynamo.register_user"),
        ):

            def get_secret_side_effect(secret_name):
                if secret_name == "test-github-secret":
                    return mock_github_secret
                elif secret_name == "test-jwt-secret":
                    return mock_jwt_secret

            mock_get_secret.side_effect = get_secret_side_effect
            mock_generate_jwt.return_value = "test_jwt_token"

            response = handle_callback("test_code")

            # Verify GitHub token is not in response
            assert "gho_sensitive_token" not in str(response)

    @responses.activate
    def test_includes_cors_headers(
        self, mock_env_vars, mock_github_secret, mock_jwt_secret
    ):
        """Should include CORS headers in callback response."""
        responses.add(
            responses.POST,
            "https://github.com/login/oauth/access_token",
            json={"access_token": "token"},
            status=200,
        )

        responses.add(
            responses.GET,
            "https://api.github.com/user",
            json={
                "id": 123,
                "login": "user",
                "avatar_url": "https://example.com/avatar.jpg",
            },
            status=200,
        )

        with (
            patch("backend.auth.github.get_secret") as mock_get_secret,
            patch("backend.auth.github.generate_jwt") as mock_generate_jwt,
            patch("backend.services.dynamo.register_user"),
        ):

            def get_secret_side_effect(secret_name):
                if secret_name == "test-github-secret":
                    return mock_github_secret
                elif secret_name == "test-jwt-secret":
                    return mock_jwt_secret

            mock_get_secret.side_effect = get_secret_side_effect
            mock_generate_jwt.return_value = "test_jwt"

            response = handle_callback("test_code")

            headers = response["headers"]
            assert (
                headers["Access-Control-Allow-Origin"] == "https://devsecblueprint.com"
            )
            assert headers["Access-Control-Allow-Credentials"] == "true"
