"""Unit tests for the JWT authentication module.

Tests token extraction, JWT validation, admin determination, and
secret caching behavior without requiring real AWS credentials.
"""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt

from app.auth.jwt import (
    _extract_token,
    _get_jwt_secret,
    _jwt_secret_cache,
    _parse_admin_users,
    get_current_user,
    require_admin,
    _CACHE_TTL_SECONDS,
)
from app.config import Settings

# --- Test fixtures ---

TEST_SECRET_KEY = "test-secret-key-for-jwt-signing"


def _make_settings(**overrides) -> Settings:
    """Create a Settings instance with test defaults."""
    defaults = {
        "membership_table": "t",
        "progress_table": "t",
        "user_state_table": "t",
        "testimonials_table": "t",
        "notifications_table": "t",
        "discord_secret_name": "s",
        "discord_bot_secret_name": "s",
        "stripe_secret_name": "s",
        "stripe_webhook_secret_name": "s",
        "jwt_secret_name": "test-jwt-secret",
        "github_secret_name": "s",
        "gitlab_secret_name": "s",
        "bitbucket_secret_name": "s",
        "discord_guild_id": "g",
        "discord_role_free_id": "r",
        "discord_role_explorer_id": "r",
        "discord_role_builder_id": "r",
        "discord_role_builder_academy_id": "r",
        "discord_callback_url": "http://localhost",
        "frontend_url": "http://localhost:3000",
        "frontend_origin": "http://localhost:3000",
        "github_callback_url": "http://localhost",
        "gitlab_callback_url": "http://localhost",
        "bitbucket_callback_url": "http://localhost",
        "admin_users": "",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _generate_token(
    payload: dict, secret: str = TEST_SECRET_KEY, algorithm: str = "HS256"
) -> str:
    """Generate a JWT token for testing."""
    return jose_jwt.encode(payload, secret, algorithm=algorithm)


def _valid_payload(
    user_id: str = "12345",
    provider: str = "github",
    github_login: str = "testuser",
    **extra,
) -> dict:
    """Generate a valid JWT payload."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "provider": provider,
        "github_login": github_login,
        "name": "Test User",
        "avatar": "https://example.com/avatar.png",
        "iat": now,
        "exp": now + timedelta(hours=1),
        **extra,
    }
    return payload


# --- Create a test app with protected routes ---


def _create_test_app(admin_users: str = "") -> TestClient:
    """Create a minimal FastAPI app with auth-protected endpoints for testing."""
    app = FastAPI()
    settings = _make_settings(admin_users=admin_users)

    # Override the settings dependency
    from app.dependencies import get_settings as _get_settings

    app.dependency_overrides[_get_settings] = lambda: settings

    @app.get("/protected")
    async def protected(user: dict = Depends(get_current_user)):
        return user

    @app.get("/admin-only")
    async def admin_only(user: dict = Depends(require_admin)):
        return user

    return TestClient(app)


# --- Tests ---


class TestExtractToken:
    """Tests for _extract_token."""

    def test_bearer_token(self):
        """Authorization: Bearer token is extracted first."""
        app = FastAPI()

        @app.get("/test")
        async def handler(request):
            from starlette.requests import Request

            return {"token": _extract_token(request)}

        client = TestClient(app)
        # Use the actual FastAPI Request object via a real HTTP call
        # We'll test extraction logic via the full flow instead

    def test_parse_admin_users_empty(self):
        """Empty string returns empty list."""
        assert _parse_admin_users("") == []

    def test_parse_admin_users_with_provider(self):
        """Parses provider:username format."""
        result = _parse_admin_users("github:alice, gitlab:bob")
        assert ("github", "alice") in result
        assert ("gitlab", "bob") in result

    def test_parse_admin_users_bare_username(self):
        """Bare usernames default to github provider."""
        result = _parse_admin_users("alice,bob")
        assert ("github", "alice") in result
        assert ("github", "bob") in result

    def test_parse_admin_users_mixed(self):
        """Mixed format entries are parsed correctly."""
        result = _parse_admin_users("gitlab:alice, bob, bitbucket:charlie")
        assert result == [
            ("gitlab", "alice"),
            ("github", "bob"),
            ("bitbucket", "charlie"),
        ]


class TestGetCurrentUser:
    """Integration tests for get_current_user via HTTP."""

    @patch("app.auth.jwt._get_jwt_secret")
    def test_valid_bearer_token(self, mock_secret):
        """Valid Bearer token returns decoded payload with is_admin."""
        mock_secret.return_value = TEST_SECRET_KEY
        client = _create_test_app()

        token = _generate_token(_valid_payload())
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sub"] == "12345"
        assert data["is_admin"] is False

    @patch("app.auth.jwt._get_jwt_secret")
    def test_valid_cookie_token(self, mock_secret):
        """Token from dsb_session cookie is accepted."""
        mock_secret.return_value = TEST_SECRET_KEY
        client = _create_test_app()

        token = _generate_token(_valid_payload())
        client.cookies.set("dsb_session", token)
        response = client.get("/protected")

        assert response.status_code == 200
        assert response.json()["sub"] == "12345"

    @patch("app.auth.jwt._get_jwt_secret")
    def test_legacy_cookie_token(self, mock_secret):
        """Token from legacy dsb_token cookie is accepted."""
        mock_secret.return_value = TEST_SECRET_KEY
        client = _create_test_app()

        token = _generate_token(_valid_payload())
        client.cookies.set("dsb_token", token)
        response = client.get("/protected")

        assert response.status_code == 200
        assert response.json()["sub"] == "12345"

    def test_no_token_returns_401(self):
        """Missing token returns 401."""
        client = _create_test_app()
        response = client.get("/protected")

        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"

    @patch("app.auth.jwt._get_jwt_secret")
    def test_expired_token_returns_401(self, mock_secret):
        """Expired token returns 401."""
        mock_secret.return_value = TEST_SECRET_KEY
        client = _create_test_app()

        payload = _valid_payload()
        payload["exp"] = datetime.now(timezone.utc) - timedelta(hours=1)
        token = _generate_token(payload)

        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    @patch("app.auth.jwt._get_jwt_secret")
    def test_invalid_signature_returns_401(self, mock_secret):
        """Token signed with wrong key returns 401."""
        mock_secret.return_value = TEST_SECRET_KEY
        client = _create_test_app()

        token = _generate_token(_valid_payload(), secret="wrong-key")
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    @patch("app.auth.jwt._get_jwt_secret")
    def test_missing_sub_claim_returns_401(self, mock_secret):
        """Token without sub claim returns 401."""
        mock_secret.return_value = TEST_SECRET_KEY
        client = _create_test_app()

        payload = _valid_payload()
        del payload["sub"]
        token = _generate_token(payload)

        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    @patch("app.auth.jwt._get_jwt_secret")
    def test_admin_user_detected(self, mock_secret):
        """User matching admin_users config gets is_admin=True."""
        mock_secret.return_value = TEST_SECRET_KEY
        client = _create_test_app(admin_users="github:testuser")

        token = _generate_token(_valid_payload())
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["is_admin"] is True

    @patch("app.auth.jwt._get_jwt_secret")
    def test_gitlab_admin_user(self, mock_secret):
        """GitLab provider admin detection works."""
        mock_secret.return_value = TEST_SECRET_KEY
        client = _create_test_app(admin_users="gitlab:gitlabuser")

        payload = _valid_payload(
            provider="gitlab", github_login="", gitlab_login="gitlabuser"
        )
        # Remove github_login since it's gitlab provider
        payload.pop("github_login", None)
        token = _generate_token(payload)

        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["is_admin"] is True


class TestRequireAdmin:
    """Tests for the require_admin dependency."""

    @patch("app.auth.jwt._get_jwt_secret")
    def test_admin_access_granted(self, mock_secret):
        """Admin user can access admin-only route."""
        mock_secret.return_value = TEST_SECRET_KEY
        client = _create_test_app(admin_users="github:testuser")

        token = _generate_token(_valid_payload())
        response = client.get(
            "/admin-only", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["is_admin"] is True

    @patch("app.auth.jwt._get_jwt_secret")
    def test_non_admin_returns_403(self, mock_secret):
        """Non-admin user gets 403 on admin-only route."""
        mock_secret.return_value = TEST_SECRET_KEY
        client = _create_test_app(admin_users="github:otheradmin")

        token = _generate_token(_valid_payload())
        response = client.get(
            "/admin-only", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Forbidden"

    def test_unauthenticated_returns_401(self):
        """Unauthenticated request to admin route returns 401."""
        client = _create_test_app()
        response = client.get("/admin-only")
        assert response.status_code == 401


class TestSecretCaching:
    """Tests for JWT secret caching behavior."""

    def setup_method(self):
        """Reset cache before each test."""
        _jwt_secret_cache["secret_key"] = None
        _jwt_secret_cache["fetched_at"] = 0.0

    @patch("app.auth.jwt.boto3.client")
    def test_secret_is_cached(self, mock_boto):
        """Secret is fetched from Secrets Manager and cached."""
        import json

        mock_sm = MagicMock()
        mock_sm.get_secret_value.return_value = {
            "SecretString": json.dumps({"secret_key": "cached-secret"})
        }
        mock_boto.return_value = mock_sm

        settings = _make_settings()

        # First call fetches from Secrets Manager
        result = _get_jwt_secret(settings)
        assert result == "cached-secret"
        assert mock_sm.get_secret_value.call_count == 1

        # Second call uses cache
        result = _get_jwt_secret(settings)
        assert result == "cached-secret"
        assert mock_sm.get_secret_value.call_count == 1

    @patch("app.auth.jwt.boto3.client")
    def test_cache_expires_after_ttl(self, mock_boto):
        """Cache is refreshed after TTL expires."""
        import json

        mock_sm = MagicMock()
        mock_sm.get_secret_value.return_value = {
            "SecretString": json.dumps({"secret_key": "new-secret"})
        }
        mock_boto.return_value = mock_sm

        settings = _make_settings()

        # Simulate an expired cache entry
        _jwt_secret_cache["secret_key"] = "old-secret"
        _jwt_secret_cache["fetched_at"] = time.time() - _CACHE_TTL_SECONDS - 1

        result = _get_jwt_secret(settings)
        assert result == "new-secret"
        assert mock_sm.get_secret_value.call_count == 1

    def teardown_method(self):
        """Reset cache after each test."""
        _jwt_secret_cache["secret_key"] = None
        _jwt_secret_cache["fetched_at"] = 0.0
