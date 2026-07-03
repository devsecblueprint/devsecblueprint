"""Tests for the refresh router — POST /refresh."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import Settings
from app.main import app

# Minimal settings for testing
TEST_SETTINGS = Settings(
    membership_table="test-membership",
    progress_table="test-progress",
    user_state_table="test-user-state",
    testimonials_table="test-testimonials",
    notifications_table="test-notifications",
    discord_secret_name="test-discord",
    discord_bot_secret_name="test-discord-bot",
    stripe_secret_name="test-stripe",
    stripe_webhook_secret_name="test-stripe-webhook",
    jwt_secret_name="test-jwt-secret",
    github_secret_name="test-github",
    gitlab_secret_name="test-gitlab",
    bitbucket_secret_name="test-bitbucket",
    discord_guild_id="123456",
    discord_role_free_id="111",
    discord_role_explorer_id="222",
    discord_role_builder_id="333",
    discord_role_builder_academy_id="444",
    discord_callback_url="https://example.com/callback",
    frontend_url="https://example.com",
    frontend_origin="https://example.com",
    github_callback_url="https://example.com/auth/github/callback",
    gitlab_callback_url="https://example.com/auth/gitlab/callback",
    bitbucket_callback_url="https://example.com/auth/bitbucket/callback",
    session_token_lifetime_hours=8,
)

TEST_SECRET_KEY = "test-secret-key-for-jwt-signing"


def _make_token(
    claims: dict, secret: str = TEST_SECRET_KEY, expired: bool = False
) -> str:
    """Helper to create a JWT token for testing."""
    now = datetime.now(timezone.utc)
    if expired:
        exp = now - timedelta(hours=1)
        iat = now - timedelta(hours=9)
    else:
        exp = now + timedelta(hours=8)
        iat = now

    payload = {
        "sub": claims.get("sub", "user-123"),
        "avatar": claims.get("avatar", "https://avatar.url"),
        "name": claims.get("name", "Test User"),
        "provider": claims.get("provider", "github"),
        "github_login": claims.get("github_login", "testuser"),
        "is_admin": claims.get("is_admin", False),
        "iat": iat,
        "exp": exp,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def client():
    """Create a test client with overridden settings."""
    from app.dependencies import get_settings as dep_get_settings

    app.dependency_overrides[dep_get_settings] = lambda: TEST_SETTINGS
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def mock_secrets():
    """Mock AWS Secrets Manager to return the test JWT secret."""
    with patch("app.routers.refresh.boto3.client") as mock_boto:
        mock_sm = MagicMock()
        mock_boto.return_value = mock_sm
        mock_sm.get_secret_value.return_value = {
            "SecretString": f'{{"secret_key": "{TEST_SECRET_KEY}"}}'
        }
        # Clear the cache before each test
        from app.routers.refresh import _jwt_secret_cache

        _jwt_secret_cache["secret_key"] = None
        _jwt_secret_cache["fetched_at"] = 0.0
        yield mock_sm


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB put_item for session storage."""
    with patch("app.routers.refresh.boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": f'{{"secret_key": "{TEST_SECRET_KEY}"}}'
        }
        mock_client.put_item.return_value = {}
        # Clear cache
        from app.routers.refresh import _jwt_secret_cache

        _jwt_secret_cache["secret_key"] = None
        _jwt_secret_cache["fetched_at"] = 0.0
        yield mock_client


class TestRefreshEndpoint:
    """Tests for POST /refresh."""

    def test_refresh_with_valid_token_in_auth_header(self, client, mock_dynamodb):
        """Token refresh succeeds with a valid token in Authorization header."""
        token = _make_token(
            {"sub": "user-123", "provider": "github", "github_login": "testuser"}
        )

        response = client.post(
            "/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_token" in data
        # Verify the new token is valid
        decoded = jwt.decode(
            data["session_token"], TEST_SECRET_KEY, algorithms=["HS256"]
        )
        assert decoded["sub"] == "user-123"
        assert decoded["provider"] == "github"

    def test_refresh_with_expired_token(self, client, mock_dynamodb):
        """Token refresh succeeds even with an expired token (signature still valid)."""
        token = _make_token(
            {"sub": "user-456", "provider": "gitlab", "gitlab_login": "gitlabuser"},
            expired=True,
        )

        response = client.post(
            "/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_token" in data
        decoded = jwt.decode(
            data["session_token"], TEST_SECRET_KEY, algorithms=["HS256"]
        )
        assert decoded["sub"] == "user-456"
        assert decoded["provider"] == "gitlab"

    def test_refresh_with_cookie(self, client, mock_dynamodb):
        """Token refresh works when token is in dsb_session cookie."""
        token = _make_token({"sub": "user-789"})

        response = client.post(
            "/refresh",
            cookies={"dsb_session": token},
        )

        assert response.status_code == 200
        assert "session_token" in response.json()

    def test_refresh_with_legacy_cookie(self, client, mock_dynamodb):
        """Token refresh works with the legacy dsb_token cookie."""
        token = _make_token({"sub": "user-legacy"})

        response = client.post(
            "/refresh",
            cookies={"dsb_token": token},
        )

        assert response.status_code == 200
        assert "session_token" in response.json()

    def test_refresh_no_token_returns_401(self, client, mock_dynamodb):
        """Returns 401 when no token is provided."""
        response = client.post("/refresh")

        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication failed"

    def test_refresh_invalid_token_returns_401(self, client, mock_dynamodb):
        """Returns 401 for a token with invalid signature."""
        token = _make_token({"sub": "user-123"}, secret="wrong-secret")

        response = client.post(
            "/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication failed"

    def test_refresh_malformed_token_returns_401(self, client, mock_dynamodb):
        """Returns 401 for a completely malformed token."""
        response = client.post(
            "/refresh",
            headers={"Authorization": "Bearer not.a.valid.token"},
        )

        assert response.status_code == 401

    def test_refresh_stores_session_in_dynamodb(self, client, mock_dynamodb):
        """Verify that a new session record is stored in DynamoDB."""
        token = _make_token({"sub": "user-store"})

        response = client.post(
            "/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        # Verify DynamoDB put_item was called
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args
        item = call_args[1]["Item"] if "Item" in call_args[1] else call_args[0][0]
        assert item["PK"]["S"] == "USER#user-store"
        assert item["SK"]["S"].startswith("SESSION#")

    def test_refresh_preserves_provider_claims(self, client, mock_dynamodb):
        """Refresh preserves provider-specific claims in the new token."""
        token = _make_token(
            {
                "sub": "user-bb",
                "provider": "bitbucket",
                "bitbucket_login": "bbuser",
            }
        )
        # Need to encode with bitbucket_login claim properly
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "user-bb",
            "avatar": "https://avatar.url",
            "name": "BB User",
            "provider": "bitbucket",
            "bitbucket_login": "bbuser",
            "is_admin": False,
            "iat": now,
            "exp": now + timedelta(hours=8),
        }
        token = jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")

        response = client.post(
            "/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        decoded = jwt.decode(
            response.json()["session_token"], TEST_SECRET_KEY, algorithms=["HS256"]
        )
        assert decoded["provider"] == "bitbucket"
        assert decoded["bitbucket_login"] == "bbuser"
