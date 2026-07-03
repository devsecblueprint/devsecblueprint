"""Unit tests for the authentication middleware."""

import os
from unittest.mock import patch, MagicMock

import pytest

os.environ.setdefault("JWT_SECRET_NAME", "test-jwt-secret")
os.environ.setdefault("ADMIN_USERS", "github:admin_user,gitlab:gl_admin")

from auth.auth_middleware import (
    _extract_token,
    _parse_admin_users,
    authenticate,
    require_auth,
    require_admin,
)


class TestExtractToken:
    def test_extracts_from_bearer_header(self):
        headers = {"Authorization": "Bearer my-jwt-token"}
        assert _extract_token(headers) == "my-jwt-token"

    def test_extracts_from_dsb_session_cookie(self):
        headers = {"cookie": "dsb_session=session-token-123; other=val"}
        assert _extract_token(headers) == "session-token-123"

    def test_extracts_from_dsb_token_cookie_fallback(self):
        headers = {"cookie": "dsb_token=legacy-token-456"}
        assert _extract_token(headers) == "legacy-token-456"

    def test_prefers_bearer_over_cookie(self):
        headers = {
            "Authorization": "Bearer bearer-token",
            "cookie": "dsb_session=cookie-token",
        }
        assert _extract_token(headers) == "bearer-token"

    def test_prefers_dsb_session_over_dsb_token(self):
        headers = {"cookie": "dsb_session=session; dsb_token=legacy"}
        assert _extract_token(headers) == "session"

    def test_returns_none_for_empty_headers(self):
        assert _extract_token({}) is None
        assert _extract_token(None) is None

    def test_returns_none_for_missing_token(self):
        headers = {"content-type": "application/json"}
        assert _extract_token(headers) is None

    def test_returns_none_for_bearer_without_token(self):
        headers = {"Authorization": "Bearer "}
        assert _extract_token(headers) is None

    def test_handles_case_insensitive_headers(self):
        headers = {"authorization": "Bearer lower-case-token"}
        assert _extract_token(headers) == "lower-case-token"


class TestParseAdminUsers:
    @patch.dict(os.environ, {"ADMIN_USERS": "github:admin1,gitlab:admin2"})
    def test_parses_provider_username_pairs(self):
        result = _parse_admin_users()
        assert ("github", "admin1") in result
        assert ("gitlab", "admin2") in result

    @patch.dict(os.environ, {"ADMIN_USERS": "bare_user"})
    def test_bare_username_defaults_to_github(self):
        result = _parse_admin_users()
        assert ("github", "bare_user") in result

    @patch.dict(os.environ, {"ADMIN_USERS": ""})
    def test_empty_string_returns_empty_list(self):
        result = _parse_admin_users()
        assert result == []

    @patch.dict(os.environ, {"ADMIN_USERS": "github:user1,,gitlab:user2"})
    def test_ignores_empty_entries(self):
        result = _parse_admin_users()
        assert len(result) == 2


class TestAuthenticate:
    @patch("auth.auth_middleware.get_secret")
    def test_valid_jwt_returns_payload(self, mock_get_secret):
        from jose import jwt as jose_jwt

        mock_get_secret.return_value = {"secret_key": "test-secret"}
        token = jose_jwt.encode(
            {"sub": "user123", "provider": "github", "github_login": "testuser"},
            "test-secret",
            algorithm="HS256",
        )
        event = {"headers": {"Authorization": f"Bearer {token}"}}

        result = authenticate(event)

        assert result is not None
        assert result["sub"] == "user123"
        assert "is_admin" in result

    @patch("auth.auth_middleware.get_secret")
    def test_expired_jwt_returns_none(self, mock_get_secret):
        from jose import jwt as jose_jwt
        import time

        mock_get_secret.return_value = {"secret_key": "test-secret"}
        token = jose_jwt.encode(
            {"sub": "user123", "exp": int(time.time()) - 3600},
            "test-secret",
            algorithm="HS256",
        )
        event = {"headers": {"Authorization": f"Bearer {token}"}}

        result = authenticate(event)
        assert result is None

    def test_missing_jwt_returns_none(self):
        event = {"headers": {}}
        result = authenticate(event)
        assert result is None

    @patch("auth.auth_middleware.get_secret")
    @patch.dict(os.environ, {"ADMIN_USERS": "github:admin_user"})
    def test_admin_check_sets_is_admin_true(self, mock_get_secret):
        from jose import jwt as jose_jwt

        mock_get_secret.return_value = {"secret_key": "test-secret"}
        token = jose_jwt.encode(
            {"sub": "admin1", "provider": "github", "github_login": "admin_user"},
            "test-secret",
            algorithm="HS256",
        )
        event = {"headers": {"Authorization": f"Bearer {token}"}}

        result = authenticate(event)

        assert result is not None
        assert result["is_admin"] is True

    @patch("auth.auth_middleware.get_secret")
    @patch.dict(os.environ, {"ADMIN_USERS": "github:admin_user"})
    def test_non_admin_sets_is_admin_false(self, mock_get_secret):
        from jose import jwt as jose_jwt

        mock_get_secret.return_value = {"secret_key": "test-secret"}
        token = jose_jwt.encode(
            {"sub": "user1", "provider": "github", "github_login": "regular_user"},
            "test-secret",
            algorithm="HS256",
        )
        event = {"headers": {"Authorization": f"Bearer {token}"}}

        result = authenticate(event)

        assert result is not None
        assert result["is_admin"] is False


class TestRequireAuth:
    @patch("auth.auth_middleware.get_secret")
    def test_returns_user_on_valid_auth(self, mock_get_secret):
        from jose import jwt as jose_jwt

        mock_get_secret.return_value = {"secret_key": "test-secret"}
        token = jose_jwt.encode(
            {"sub": "user1", "provider": "github", "github_login": "u1"},
            "test-secret",
            algorithm="HS256",
        )
        event = {"headers": {"Authorization": f"Bearer {token}"}}

        user, err = require_auth(event)

        assert user is not None
        assert err is None
        assert user["sub"] == "user1"

    def test_returns_401_on_missing_auth(self):
        event = {"headers": {}}

        user, err = require_auth(event)

        assert user is None
        assert err is not None
        assert err["statusCode"] == 401


class TestRequireAdmin:
    @patch("auth.auth_middleware.get_secret")
    @patch.dict(os.environ, {"ADMIN_USERS": "github:admin_user"})
    def test_returns_user_for_admin(self, mock_get_secret):
        from jose import jwt as jose_jwt

        mock_get_secret.return_value = {"secret_key": "test-secret"}
        token = jose_jwt.encode(
            {"sub": "a1", "provider": "github", "github_login": "admin_user"},
            "test-secret",
            algorithm="HS256",
        )
        event = {"headers": {"Authorization": f"Bearer {token}"}}

        user, err = require_admin(event)

        assert user is not None
        assert err is None
        assert user["is_admin"] is True

    @patch("auth.auth_middleware.get_secret")
    @patch.dict(os.environ, {"ADMIN_USERS": "github:admin_user"})
    def test_returns_403_for_non_admin(self, mock_get_secret):
        from jose import jwt as jose_jwt

        mock_get_secret.return_value = {"secret_key": "test-secret"}
        token = jose_jwt.encode(
            {"sub": "u1", "provider": "github", "github_login": "regular_user"},
            "test-secret",
            algorithm="HS256",
        )
        event = {"headers": {"Authorization": f"Bearer {token}"}}

        user, err = require_admin(event)

        assert user is None
        assert err is not None
        assert err["statusCode"] == 403

    def test_returns_401_for_unauthenticated(self):
        event = {"headers": {}}

        user, err = require_admin(event)

        assert user is None
        assert err is not None
        assert err["statusCode"] == 401
