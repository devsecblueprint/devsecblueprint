"""Tests for the discord identity router — /api/discord/*.

- POST   /api/discord/confirm     (auth) — confirms pending link + enqueues sync
- DELETE /api/discord/disconnect  (auth) — unlinks account
- GET    /api/discord/status      (auth) — returns link status

The service functions (confirm_identity, disconnect, get_status) are patched
at the router import site. enqueue_discord_sync is also patched so the
background task is not actually scheduled.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

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


def _make_token(sub: str = "user-123") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "avatar": "https://avatar.url",
        "name": "Test User",
        "provider": "github",
        "github_login": "testuser",
        "is_admin": False,
        "iat": now,
        "exp": now + timedelta(hours=8),
    }
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")


@pytest.fixture
def client():
    from app.dependencies import get_settings as dep_get_settings

    app.dependency_overrides[dep_get_settings] = lambda: TEST_SETTINGS
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def mock_auth():
    from app.auth.jwt import _jwt_secret_cache

    _jwt_secret_cache["secret_key"] = TEST_SECRET_KEY
    _jwt_secret_cache["fetched_at"] = 9999999999.0
    yield
    _jwt_secret_cache["secret_key"] = None
    _jwt_secret_cache["fetched_at"] = 0.0


def _auth_header():
    return {"Authorization": f"Bearer {_make_token()}"}


# ---------------------------------------------------------------------------
# POST /api/discord/confirm
# ---------------------------------------------------------------------------


class TestConfirm:
    def test_requires_auth(self, client, mock_auth):
        assert client.post("/api/discord/confirm").status_code == 401

    def test_success_and_enqueues_sync(self, client, mock_auth):
        with (
            patch("app.routers.discord.confirm_identity") as mock_confirm,
            patch("app.routers.discord.enqueue_discord_sync") as mock_enqueue,
        ):
            mock_confirm.return_value = {
                "discord_user_id": "d-1",
                "username": "disc",
                "display_name": "Disc User",
                "avatar_url": "https://cdn/avatar.png",
                "platform_state": "ACTIVE",
            }
            response = client.post("/api/discord/confirm", headers=_auth_header())

        assert response.status_code == 200
        data = response.json()
        assert data["discord_user_id"] == "d-1"
        assert data["platform_state"] == "ACTIVE"
        mock_confirm.assert_called_once_with("user-123", TEST_SETTINGS)
        mock_enqueue.assert_called_once()
        _, kwargs = mock_enqueue.call_args
        assert kwargs["user_id"] == "user-123"
        assert kwargs["operation"] == "discord_connected"

    def test_value_error_returns_400(self, client, mock_auth):
        with (
            patch("app.routers.discord.confirm_identity") as mock_confirm,
            patch("app.routers.discord.enqueue_discord_sync") as mock_enqueue,
        ):
            mock_confirm.side_effect = ValueError("no pending link")
            response = client.post("/api/discord/confirm", headers=_auth_header())

        assert response.status_code == 400
        assert response.json()["detail"] == "no pending link"
        mock_enqueue.assert_not_called()


# ---------------------------------------------------------------------------
# DELETE /api/discord/disconnect
# ---------------------------------------------------------------------------


class TestDisconnect:
    def test_requires_auth(self, client, mock_auth):
        assert client.delete("/api/discord/disconnect").status_code == 401

    def test_success(self, client, mock_auth):
        with patch("app.routers.discord.disconnect") as mock_disc:
            mock_disc.return_value = {"cleanup_status": "completed"}
            response = client.delete("/api/discord/disconnect", headers=_auth_header())

        assert response.status_code == 200
        assert response.json() == {"cleanup_status": "completed"}
        mock_disc.assert_called_once_with("user-123", TEST_SETTINGS)

    def test_value_error_returns_400(self, client, mock_auth):
        with patch("app.routers.discord.disconnect") as mock_disc:
            mock_disc.side_effect = ValueError("not connected")
            response = client.delete("/api/discord/disconnect", headers=_auth_header())

        assert response.status_code == 400
        assert response.json()["detail"] == "not connected"


# ---------------------------------------------------------------------------
# GET /api/discord/status
# ---------------------------------------------------------------------------


class TestStatus:
    def test_requires_auth(self, client, mock_auth):
        assert client.get("/api/discord/status").status_code == 401

    def test_success(self, client, mock_auth):
        with patch("app.routers.discord.get_status") as mock_status:
            mock_status.return_value = {
                "connected": True,
                "pending": False,
                "discord_username": "disc",
                "discord_avatar_url": "https://cdn/avatar.png",
                "platform_state": "ACTIVE",
                "last_synced_at": "2024-06-01T00:00:00Z",
                "last_sync_status": "success",
            }
            response = client.get("/api/discord/status", headers=_auth_header())

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["discord_username"] == "disc"
        mock_status.assert_called_once_with("user-123", TEST_SETTINGS)

    def test_not_connected_status(self, client, mock_auth):
        with patch("app.routers.discord.get_status") as mock_status:
            mock_status.return_value = {
                "connected": False,
                "pending": False,
                "discord_username": None,
                "discord_avatar_url": None,
                "platform_state": None,
                "last_synced_at": None,
                "last_sync_status": None,
            }
            response = client.get("/api/discord/status", headers=_auth_header())

        assert response.status_code == 200
        assert response.json()["connected"] is False
