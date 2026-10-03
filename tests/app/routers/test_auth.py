"""Tests for the auth router — OAuth flows, /me, and /logout.

Covers:
- GET /auth/{github,gitlab,bitbucket}/start (redirect + config error)
- GET /auth/{github,gitlab,bitbucket}/callback (missing code, success, failure)
- GET /auth/discord/start (auth required, success, ValueError)
- GET /auth/discord/callback (missing params, success, failure)
- GET /me (auth required, provider-specific fields)
- POST /logout (auth required, success, session revocation error)

OAuth provider modules return an OAuthResult-like object with
`redirect_url` and `cookies`; we patch those module functions directly at
the router import site.
"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import Settings
from app.main import app

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

TEST_SECRET_KEY = "test-secret-key-for-jwt-signing-32chars"


def _make_token(claims: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "user-123",
        "avatar": "https://avatar.url",
        "name": "Test User",
        "provider": "github",
        "github_login": "testuser",
        "is_admin": False,
        "iat": now,
        "exp": now + timedelta(hours=8),
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")


@pytest.fixture
def client():
    from app.dependencies import get_settings as dep_get_settings

    app.dependency_overrides[dep_get_settings] = lambda: TEST_SETTINGS
    # TestClient without follow_redirects so we can assert 302 responses.
    yield TestClient(app, follow_redirects=False)
    app.dependency_overrides.clear()


@pytest.fixture
def mock_auth():
    from app.auth.jwt import _jwt_secret_cache

    _jwt_secret_cache["secret_key"] = TEST_SECRET_KEY
    _jwt_secret_cache["fetched_at"] = 9999999999.0
    yield
    _jwt_secret_cache["secret_key"] = None
    _jwt_secret_cache["fetched_at"] = 0.0


# ---------------------------------------------------------------------------
# OAuth start endpoints
# ---------------------------------------------------------------------------


class TestOAuthStart:
    @pytest.mark.parametrize(
        "provider,patch_target",
        [
            ("github", "app.routers.auth.start_github_oauth"),
            ("gitlab", "app.routers.auth.start_gitlab_oauth"),
            ("bitbucket", "app.routers.auth.start_bitbucket_oauth"),
        ],
    )
    def test_start_redirects(self, client, provider, patch_target):
        with patch(patch_target) as mock_start:
            async def _ret(settings):
                return f"https://{provider}.com/authorize?x=1"

            mock_start.side_effect = _ret
            response = client.get(f"/auth/{provider}/start")

        assert response.status_code == 302
        assert response.headers["location"] == f"https://{provider}.com/authorize?x=1"

    @pytest.mark.parametrize(
        "provider,patch_target",
        [
            ("github", "app.routers.auth.start_github_oauth"),
            ("gitlab", "app.routers.auth.start_gitlab_oauth"),
            ("bitbucket", "app.routers.auth.start_bitbucket_oauth"),
        ],
    )
    def test_start_config_error_returns_500(self, client, provider, patch_target):
        with patch(patch_target) as mock_start:
            async def _raise(settings):
                raise RuntimeError("missing config")

            mock_start.side_effect = _raise
            response = client.get(f"/auth/{provider}/start")

        assert response.status_code == 500
        assert response.json() == {"error": "Configuration error"}


# ---------------------------------------------------------------------------
# OAuth callback endpoints
# ---------------------------------------------------------------------------


class TestOAuthCallback:
    @pytest.mark.parametrize(
        "provider",
        ["github", "gitlab", "bitbucket"],
    )
    def test_callback_missing_code_returns_400(self, client, provider):
        response = client.get(f"/auth/{provider}/callback")
        assert response.status_code == 400
        assert response.json() == {"detail": "Invalid request"}

    @pytest.mark.parametrize(
        "provider,patch_target",
        [
            ("github", "app.routers.auth.handle_github_callback"),
            ("gitlab", "app.routers.auth.handle_gitlab_callback"),
            ("bitbucket", "app.routers.auth.handle_bitbucket_callback"),
        ],
    )
    def test_callback_success_redirects_with_cookies(
        self, client, provider, patch_target
    ):
        with patch(patch_target) as mock_handle:
            async def _ret(code, settings):
                return SimpleNamespace(
                    redirect_url="https://example.com/dashboard",
                    cookies=["dsb_session=abc; Path=/"],
                )

            mock_handle.side_effect = _ret
            response = client.get(f"/auth/{provider}/callback?code=valid-code")

        assert response.status_code == 302
        assert response.headers["location"] == "https://example.com/dashboard"
        assert "dsb_session=abc" in response.headers.get("set-cookie", "")

    @pytest.mark.parametrize(
        "provider,patch_target",
        [
            ("github", "app.routers.auth.handle_github_callback"),
            ("gitlab", "app.routers.auth.handle_gitlab_callback"),
            ("bitbucket", "app.routers.auth.handle_bitbucket_callback"),
        ],
    )
    def test_callback_failure_returns_401(self, client, provider, patch_target):
        with patch(patch_target) as mock_handle:
            async def _raise(code, settings):
                raise RuntimeError("bad code")

            mock_handle.side_effect = _raise
            response = client.get(f"/auth/{provider}/callback?code=bad")

        assert response.status_code == 401
        assert response.json() == {"error": "Authentication failed"}


# ---------------------------------------------------------------------------
# Discord OAuth
# ---------------------------------------------------------------------------


class TestDiscordOAuth:
    def test_discord_start_requires_auth(self, client, mock_auth):
        response = client.get("/auth/discord/start")
        assert response.status_code == 401

    def test_discord_start_redirects(self, client, mock_auth):
        token = _make_token()
        with patch("app.services.discord_identity.start_oauth") as mock_start:
            mock_start.return_value = "https://discord.com/oauth2/authorize?x=1"
            response = client.get(
                "/auth/discord/start",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 302
        assert response.headers["location"].startswith("https://discord.com")
        mock_start.assert_called_once()

    def test_discord_start_value_error_returns_400(self, client, mock_auth):
        token = _make_token()
        with patch("app.services.discord_identity.start_oauth") as mock_start:
            mock_start.side_effect = ValueError("already linked")
            response = client.get(
                "/auth/discord/start",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 400
        assert response.json() == {"detail": "already linked"}

    def test_discord_callback_missing_params_redirects_error(self, client):
        response = client.get("/auth/discord/callback")
        assert response.status_code == 302
        assert "discord=error" in response.headers["location"]

    def test_discord_callback_success_redirects_pending(self, client):
        with patch("app.services.discord_identity.handle_callback") as mock_cb:
            mock_cb.return_value = None
            response = client.get(
                "/auth/discord/callback?code=abc&state=xyz",
            )

        assert response.status_code == 302
        assert "discord=pending" in response.headers["location"]

    def test_discord_callback_failure_redirects_error(self, client):
        with patch("app.services.discord_identity.handle_callback") as mock_cb:
            mock_cb.side_effect = ValueError("bad state")
            response = client.get(
                "/auth/discord/callback?code=abc&state=xyz",
            )

        assert response.status_code == 302
        assert "discord=error" in response.headers["location"]


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------


class TestMe:
    def test_requires_auth(self, client, mock_auth):
        response = client.get("/me")
        assert response.status_code == 401

    def test_github_user(self, client, mock_auth):
        token = _make_token()
        response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user-123"
        assert data["authenticated"] is True
        assert data["provider"] == "github"
        assert data["github_username"] == "testuser"
        assert data["avatar_url"] == "https://avatar.url"
        assert data["username"] == "Test User"

    def test_gitlab_user(self, client, mock_auth):
        token = _make_token(
            {"provider": "gitlab", "gitlab_login": "gluser", "github_login": None}
        )
        response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "gitlab"
        assert data["gitlab_username"] == "gluser"

    def test_bitbucket_user(self, client, mock_auth):
        token = _make_token(
            {"provider": "bitbucket", "bitbucket_login": "bbuser", "github_login": None}
        )
        response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "bitbucket"
        assert data["bitbucket_username"] == "bbuser"


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------


class TestLogout:
    def test_requires_auth(self, client, mock_auth):
        response = client.post("/logout")
        assert response.status_code == 401

    def test_logout_success(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.auth.delete_all_user_sessions") as mock_del:
            mock_del.return_value = None
            response = client.post(
                "/logout",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json() == {"message": "Logged out"}
        mock_del.assert_called_once_with(
            table_name=TEST_SETTINGS.progress_table,
            user_id="user-123",
        )

    def test_logout_swallows_revocation_error(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.auth.delete_all_user_sessions") as mock_del:
            mock_del.side_effect = RuntimeError("dynamo down")
            response = client.post(
                "/logout",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json() == {"message": "Logged out"}
