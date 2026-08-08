"""Tests for Builder Journey progress endpoints.

Tests GET /progress/journey and PUT /progress/journey endpoints.
"""

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

TEST_SECRET_KEY = "test-secret-key-for-jwt-signing-32chars"


def _make_token(claims: dict | None = None) -> str:
    """Create a valid JWT token for testing."""
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
    """Create a test client with overridden settings."""
    from app.dependencies import get_settings as dep_get_settings

    app.dependency_overrides[dep_get_settings] = lambda: TEST_SETTINGS
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def mock_auth():
    """Mock JWT secret retrieval."""
    with patch("app.auth.jwt.boto3.client") as mock_boto:
        mock_sm = MagicMock()
        mock_boto.return_value = mock_sm
        mock_sm.get_secret_value.return_value = {
            "SecretString": f'{{"secret_key": "{TEST_SECRET_KEY}"}}'
        }
        # Clear caches
        from app.auth.jwt import _jwt_secret_cache

        _jwt_secret_cache["secret_key"] = None
        _jwt_secret_cache["fetched_at"] = 0.0
        yield mock_sm


@pytest.fixture
def mock_dynamodb_builder():
    """Mock DynamoDB for a Builder user with all journey methods."""
    with patch("app.routers.progress.boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client

        # Membership check returns BUILDER with active status
        mock_client.get_item.return_value = {
            "Item": {
                "PK": {"S": "USER#user-123"},
                "SK": {"S": "MEMBERSHIP"},
                "membership_tier": {"S": "BUILDER"},
                "subscription_status": {"S": "active"},
            }
        }
        yield mock_client


@pytest.fixture
def mock_dynamodb_free():
    """Mock DynamoDB for a Free-tier user."""
    with patch("app.routers.progress.boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client

        # Membership check returns FREE
        mock_client.get_item.return_value = {
            "Item": {
                "PK": {"S": "USER#user-123"},
                "SK": {"S": "MEMBERSHIP"},
                "membership_tier": {"S": "FREE"},
                "subscription_status": {"S": None},
            }
        }
        yield mock_client


class TestGetJourneyProgress:
    """Tests for GET /progress/journey."""

    def test_free_tier_returns_403(self, client, mock_auth, mock_dynamodb_free):
        """Free-tier users cannot access journey progress."""
        token = _make_token()
        response = client.get(
            "/progress/journey",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_builder_returns_journey_progress(self, client, mock_auth):
        """Builder users get their journey progress."""
        token = _make_token()

        with patch("app.routers.progress.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            # Builder access check
            mock_client.get_item.return_value = {
                "Item": {
                    "PK": {"S": "USER#user-123"},
                    "SK": {"S": "MEMBERSHIP"},
                    "membership_tier": {"S": "BUILDER"},
                    "subscription_status": {"S": "active"},
                }
            }

            with (
                patch(
                    "app.services.progress_db.ProgressDB.get_journey_progress"
                ) as mock_journey,
                patch(
                    "app.services.progress_db.ProgressDB.save_journey_meta"
                ) as mock_meta,
                patch(
                    "app.services.progress_db.ProgressDB.get_user_progress"
                ) as mock_progress,
                patch(
                    "app.services.progress_db.ProgressDB._count_capstone_submissions"
                ) as mock_capstones,
            ):
                mock_journey.return_value = [
                    {
                        "task_id": "_meta",
                        "status": "completed",
                        "completed_at": "",
                        "phase": 0,
                        "auto_completed": False,
                        "started_at": "2026-08-01T00:00:00Z",
                    },
                    {
                        "task_id": "connect-discord",
                        "status": "completed",
                        "completed_at": "2026-08-01T10:00:00Z",
                        "phase": 1,
                        "auto_completed": True,
                        "started_at": "",
                    },
                ]
                mock_meta.return_value = "2026-08-01T00:00:00Z"
                mock_progress.return_value = []
                mock_capstones.return_value = 0

                response = client.get(
                    "/progress/journey",
                    headers={"Authorization": f"Bearer {token}"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "tasks" in data
                assert "current_phase" in data
                assert "completion_percentage" in data
                assert "is_complete" in data
                assert "journey_started_at" in data
                assert data["current_phase"] == 1
                assert data["is_complete"] is False

    def test_admin_can_access_journey(self, client, mock_auth):
        """Admin users can access journey progress."""
        token = _make_token({"is_admin": True})

        with (
            patch(
                "app.services.progress_db.ProgressDB.get_journey_progress"
            ) as mock_journey,
            patch("app.services.progress_db.ProgressDB.save_journey_meta") as mock_meta,
            patch(
                "app.services.progress_db.ProgressDB.get_user_progress"
            ) as mock_progress,
            patch(
                "app.services.progress_db.ProgressDB._count_capstone_submissions"
            ) as mock_capstones,
            patch("app.routers.progress._get_membership_item") as mock_membership,
        ):
            mock_journey.return_value = []
            mock_meta.return_value = "2026-08-01T00:00:00Z"
            mock_progress.return_value = []
            mock_capstones.return_value = 0
            mock_membership.return_value = None

            response = client.get(
                "/progress/journey",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200


class TestPutJourneyProgress:
    """Tests for PUT /progress/journey."""

    def test_invalid_task_id_returns_400(self, client, mock_auth):
        """Invalid task IDs are rejected."""
        token = _make_token({"is_admin": True})

        response = client.put(
            "/progress/journey",
            headers={"Authorization": f"Bearer {token}"},
            json={"task_id": "invalid-nonexistent-task"},
        )

        assert response.status_code == 400

    def test_complete_valid_task(self, client, mock_auth):
        """Completing a valid task returns success."""
        token = _make_token({"is_admin": True})

        with (
            patch("app.services.progress_db.ProgressDB.save_journey_meta") as mock_meta,
            patch("app.services.progress_db.ProgressDB.save_journey_task") as mock_save,
            patch(
                "app.services.progress_db.ProgressDB.get_journey_progress"
            ) as mock_progress,
        ):
            mock_meta.return_value = "2026-08-01T00:00:00Z"
            mock_save.return_value = None
            mock_progress.return_value = [
                {
                    "task_id": "connect-discord",
                    "status": "completed",
                    "completed_at": "2026-08-01T10:00:00Z",
                    "phase": 1,
                    "auto_completed": False,
                    "started_at": "",
                },
            ]

            response = client.put(
                "/progress/journey",
                headers={"Authorization": f"Bearer {token}"},
                json={"task_id": "connect-discord"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "connect-discord"
            assert data["status"] == "completed"
            assert "completed_at" in data
            assert "phase_completed" in data
            assert "journey_completed" in data

    def test_free_tier_cannot_complete_task(
        self, client, mock_auth, mock_dynamodb_free
    ):
        """Free-tier users cannot complete journey tasks."""
        token = _make_token()

        response = client.put(
            "/progress/journey",
            headers={"Authorization": f"Bearer {token}"},
            json={"task_id": "connect-discord"},
        )

        assert response.status_code == 403
