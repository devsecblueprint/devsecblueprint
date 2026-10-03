"""Tests for the user router — /user/profile (GET/PUT) and /user/account (DELETE).

Note on /me: both auth.router and user.router register GET /me. Because
auth.router is included first in app.main, auth's /me handler wins and
user.router's /me is unreachable. The /me behavior is therefore covered in
test_auth.py, and this file focuses on the user-specific routes:
GET /user/profile, PUT /user/profile, and DELETE /user/account.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from botocore.exceptions import ClientError
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
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def mock_auth():
    """Pre-populate the JWT secret cache so no boto3 call is needed."""
    from app.auth.jwt import _jwt_secret_cache

    _jwt_secret_cache["secret_key"] = TEST_SECRET_KEY
    _jwt_secret_cache["fetched_at"] = 9999999999.0
    yield
    _jwt_secret_cache["secret_key"] = None
    _jwt_secret_cache["fetched_at"] = 0.0


def _profile_item() -> dict:
    return {
        "Item": {
            "PK": {"S": "USER#user-123"},
            "SK": {"S": "PROFILE"},
            "username": {"S": "testuser"},
            "avatar_url": {"S": "https://avatar.url"},
            "registered_at": {"S": "2024-01-01T00:00:00Z"},
            "last_login": {"S": "2024-06-01T00:00:00Z"},
            "github_username": {"S": "testuser"},
            "provider": {"S": "github"},
            "email": {"S": "test@example.com"},
            "full_name": {"S": "Test User"},
        }
    }


# ---------------------------------------------------------------------------
# GET /user/profile
# ---------------------------------------------------------------------------


class TestGetUserProfile:
    def test_requires_auth(self, client, mock_auth):
        """No token -> 401."""
        response = client.get("/user/profile")
        assert response.status_code == 401

    def test_success_returns_profile(self, client, mock_auth):
        """Valid profile returns 200 with mapped fields."""
        token = _make_token()
        with patch("app.routers.user.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            def get_item_side_effect(**kwargs):
                sk = kwargs["Key"]["SK"]["S"]
                if sk == "PROFILE":
                    return _profile_item()
                return {}  # no CONTRIBUTOR_ROLE

            mock_client.get_item.side_effect = get_item_side_effect
            mock_client.query.return_value = {"Count": 3}

            response = client.get(
                "/user/profile",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user-123"
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["total_completions"] == 3
        assert data["is_new_user"] is False
        assert data["contributor_role"] is None
        assert data["full_name"] == "Test User"

    def test_new_user_when_no_progress(self, client, mock_auth):
        """is_new_user true when progress count is zero."""
        token = _make_token()
        with patch("app.routers.user.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.get_item.side_effect = lambda **kw: (
                _profile_item() if kw["Key"]["SK"]["S"] == "PROFILE" else {}
            )
            mock_client.query.return_value = {"Count": 0}

            response = client.get(
                "/user/profile",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["is_new_user"] is True
        assert data["total_completions"] == 0

    def test_contributor_role_included(self, client, mock_auth):
        """Contributor role record is surfaced in the response."""
        token = _make_token()
        with patch("app.routers.user.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            def get_item_side_effect(**kwargs):
                sk = kwargs["Key"]["SK"]["S"]
                if sk == "PROFILE":
                    return _profile_item()
                if sk == "CONTRIBUTOR_ROLE":
                    return {
                        "Item": {
                            "role": {"S": "AUTHOR"},
                            "assigned_by": {"S": "admin"},
                            "assigned_at": {"S": "2024-02-01T00:00:00Z"},
                            "note": {"S": "trusted"},
                        }
                    }
                return {}

            mock_client.get_item.side_effect = get_item_side_effect
            mock_client.query.return_value = {"Count": 1}

            response = client.get(
                "/user/profile",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["contributor_role"]["role"] == "AUTHOR"
        assert data["contributor_role"]["assigned_by"] == "admin"

    def test_not_found_returns_404(self, client, mock_auth):
        """Missing profile returns 404."""
        token = _make_token()
        with patch("app.routers.user.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.get_item.return_value = {}  # no Item

            response = client.get(
                "/user/profile",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "User profile not found"

    def test_dynamodb_error_returns_500(self, client, mock_auth):
        """ClientError while fetching profile returns 500."""
        token = _make_token()
        with patch("app.routers.user.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.get_item.side_effect = ClientError(
                {"Error": {"Code": "InternalError", "Message": "boom"}},
                "GetItem",
            )

            response = client.get(
                "/user/profile",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to fetch user profile"


# ---------------------------------------------------------------------------
# PUT /user/profile
# ---------------------------------------------------------------------------


class TestUpdateUserProfile:
    def test_requires_auth(self, client, mock_auth):
        response = client.put("/user/profile", json={"full_name": "New Name"})
        assert response.status_code == 401

    def test_success_updates_full_name(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.user.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.update_item.return_value = {}

            response = client.put(
                "/user/profile",
                headers={"Authorization": f"Bearer {token}"},
                json={"full_name": "Updated Name"},
            )

        assert response.status_code == 200
        assert response.json() == {"full_name": "Updated Name"}
        mock_client.update_item.assert_called_once()

    def test_whitespace_only_returns_400(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.user.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            response = client.put(
                "/user/profile",
                headers={"Authorization": f"Bearer {token}"},
                json={"full_name": "    "},
            )

        assert response.status_code == 400
        assert "whitespace" in response.json()["detail"]

    def test_empty_full_name_returns_422(self, client, mock_auth):
        """Pydantic min_length=1 rejects empty string with 422."""
        token = _make_token()
        response = client.put(
            "/user/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": ""},
        )
        assert response.status_code == 422

    def test_too_long_full_name_returns_422(self, client, mock_auth):
        token = _make_token()
        response = client.put(
            "/user/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "x" * 201},
        )
        assert response.status_code == 422

    def test_profile_missing_returns_404(self, client, mock_auth):
        """ConditionalCheckFailedException -> 404."""
        token = _make_token()
        with patch("app.routers.user.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.update_item.side_effect = ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException", "Message": "no"}},
                "UpdateItem",
            )

            response = client.put(
                "/user/profile",
                headers={"Authorization": f"Bearer {token}"},
                json={"full_name": "Updated Name"},
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "User profile not found"

    def test_update_error_returns_500(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.user.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.update_item.side_effect = ClientError(
                {"Error": {"Code": "InternalError", "Message": "boom"}},
                "UpdateItem",
            )

            response = client.put(
                "/user/profile",
                headers={"Authorization": f"Bearer {token}"},
                json={"full_name": "Updated Name"},
            )

        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to update user profile"


# ---------------------------------------------------------------------------
# DELETE /user/account
# ---------------------------------------------------------------------------


class TestDeleteAccount:
    def test_requires_auth(self, client, mock_auth):
        response = client.delete("/user/account")
        assert response.status_code == 401

    def test_success_deletes_account(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.user.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            # First query (delete items) returns some items, then stops.
            mock_client.query.side_effect = [
                {
                    "Items": [
                        {"PK": {"S": "USER#user-123"}, "SK": {"S": "PROFILE"}},
                        {"PK": {"S": "USER#user-123"}, "SK": {"S": "CONTENT#1"}},
                    ]
                },
                {"Items": []},  # session revocation query
            ]
            mock_client.delete_item.return_value = {}

            response = client.delete(
                "/user/account",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json() == {"message": "Account successfully deleted"}
        # Session cookies cleared
        set_cookie = response.headers.get("set-cookie", "")
        assert "dsb_session" in set_cookie

    def test_paginated_deletion(self, client, mock_auth):
        """Deletion follows LastEvaluatedKey pagination."""
        token = _make_token()
        with patch("app.routers.user.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.query.side_effect = [
                {
                    "Items": [{"PK": {"S": "USER#user-123"}, "SK": {"S": "A"}}],
                    "LastEvaluatedKey": {"PK": {"S": "USER#user-123"}, "SK": {"S": "A"}},
                },
                {"Items": [{"PK": {"S": "USER#user-123"}, "SK": {"S": "B"}}]},
                {"Items": []},  # session revocation
            ]
            mock_client.delete_item.return_value = {}

            response = client.delete(
                "/user/account",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert mock_client.delete_item.call_count == 2

    def test_delete_error_returns_500(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.user.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.query.side_effect = ClientError(
                {"Error": {"Code": "InternalError", "Message": "boom"}},
                "Query",
            )

            response = client.delete(
                "/user/account",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to delete account"


# ---------------------------------------------------------------------------
# Additional branch coverage
# ---------------------------------------------------------------------------


class TestProfileBranches:
    def test_progress_count_error_returns_500(self, client, mock_auth):
        """ClientError while counting progress returns 500."""
        token = _make_token()
        with patch("app.routers.user.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.get_item.side_effect = lambda **kw: (
                _profile_item() if kw["Key"]["SK"]["S"] == "PROFILE" else {}
            )
            mock_client.query.side_effect = ClientError(
                {"Error": {"Code": "InternalError", "Message": "boom"}},
                "Query",
            )

            response = client.get(
                "/user/profile",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to fetch user profile"

    def test_contributor_role_lookup_error_is_swallowed(self, client, mock_auth):
        """A failure fetching the contributor role is logged, not fatal."""
        token = _make_token()
        with patch("app.routers.user.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            def get_item_side_effect(**kwargs):
                sk = kwargs["Key"]["SK"]["S"]
                if sk == "PROFILE":
                    return _profile_item()
                raise RuntimeError("contributor lookup failed")

            mock_client.get_item.side_effect = get_item_side_effect
            mock_client.query.return_value = {"Count": 2}

            response = client.get(
                "/user/profile",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["contributor_role"] is None
        assert data["total_completions"] == 2


class TestDeleteAccountBranches:
    def test_session_revocation_error_is_swallowed(self, client, mock_auth):
        """A ClientError during session revocation does not fail the delete."""
        token = _make_token()
        with patch("app.routers.user.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            # First query: items to delete; second query (revoke) raises.
            mock_client.query.side_effect = [
                {"Items": [{"PK": {"S": "USER#user-123"}, "SK": {"S": "PROFILE"}}]},
                ClientError(
                    {"Error": {"Code": "InternalError", "Message": "boom"}},
                    "Query",
                ),
            ]
            mock_client.delete_item.return_value = {}

            response = client.delete(
                "/user/account",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json() == {"message": "Account successfully deleted"}
