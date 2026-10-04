"""Tests for the non-journey progress endpoints.

Covers everything in app.routers.progress EXCEPT the journey endpoints
(which are covered by test_journey_progress.py):

- PUT  /progress                       save_progress (+ capstone submission)
- GET  /progress                       get_progress
- GET  /progress/stats                 get_stats
- GET  /progress/recent                get_recent
- GET  /progress/badges                get_badges
- PUT  /progress/last-active           save_last_active
- GET  /progress/last-active           get_last_active
- DELETE /progress/reset               reset_progress (admin only)
- GET  /progress/capstone/{id}         get_capstone_submission
- GET  /progress/capstone/{id}/review  get_capstone_review
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import Settings
from app.main import app

# Minimal settings for testing. admin_users maps github:adminuser -> admin.
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
    admin_users="github:adminuser",
)

TEST_SECRET_KEY = "test-secret-key-for-jwt-signing-32chars"


def _make_token(claims: dict | None = None) -> str:
    """Create a valid JWT token for testing a regular GitHub user."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "user-123",
        "avatar": "https://avatar.url",
        "name": "Test User",
        "provider": "github",
        "github_login": "testuser",
        "iat": now,
        "exp": now + timedelta(hours=8),
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")


def _make_admin_token() -> str:
    """Create a token whose provider+login matches admin_users."""
    return _make_token({"sub": "admin-1", "github_login": "adminuser"})


@pytest.fixture
def client():
    """Test client with overridden settings."""
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


# ---------------------------------------------------------------------------
# Auth gating (shared behaviour)
# ---------------------------------------------------------------------------


class TestAuthGating:
    def test_get_progress_no_token_401(self, client, mock_auth):
        resp = client.get("/progress")
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Unauthorized"

    def test_get_progress_invalid_signature_401(self, client, mock_auth):
        token = jwt.encode({"sub": "x"}, "wrong-secret", algorithm="HS256")
        resp = client.get("/progress", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_reset_requires_admin_403(self, client, mock_auth):
        """A non-admin user is forbidden from resetting progress."""
        token = _make_token()
        resp = client.delete(
            "/progress/reset", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Forbidden"


# ---------------------------------------------------------------------------
# GET /progress
# ---------------------------------------------------------------------------


class TestGetProgress:
    def test_success(self, client, mock_auth):
        token = _make_token()
        items = [{"content_id": "c1", "completed_at": "2026-01-01T00:00:00Z"}]
        with patch(
            "app.services.progress_db.ProgressDB.get_user_progress",
            return_value=items,
        ):
            resp = client.get(
                "/progress", headers={"Authorization": f"Bearer {token}"}
            )
        assert resp.status_code == 200
        assert resp.json() == {"progress": items}

    def test_db_failure_500(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.services.progress_db.ProgressDB.get_user_progress",
            side_effect=RuntimeError("boom"),
        ):
            resp = client.get(
                "/progress", headers={"Authorization": f"Bearer {token}"}
            )
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Service temporarily unavailable"


# ---------------------------------------------------------------------------
# GET /progress/stats
# ---------------------------------------------------------------------------


class TestGetStats:
    def test_success(self, client, mock_auth):
        token = _make_token()
        stats = {"total_completed": 5, "current_streak": 3}
        with patch(
            "app.services.progress_db.ProgressDB.get_user_stats", return_value=stats
        ):
            resp = client.get(
                "/progress/stats", headers={"Authorization": f"Bearer {token}"}
            )
        assert resp.status_code == 200
        assert resp.json() == stats

    def test_db_failure_500(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.services.progress_db.ProgressDB.get_user_stats",
            side_effect=RuntimeError("boom"),
        ):
            resp = client.get(
                "/progress/stats", headers={"Authorization": f"Bearer {token}"}
            )
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /progress/recent
# ---------------------------------------------------------------------------


class TestGetRecent:
    def test_success(self, client, mock_auth):
        token = _make_token()
        recent = [{"content_id": "c1", "completed_at": "2026-01-01T00:00:00Z"}]
        with patch(
            "app.services.progress_db.ProgressDB.get_recent_activities",
            return_value=recent,
        ) as m:
            resp = client.get(
                "/progress/recent", headers={"Authorization": f"Bearer {token}"}
            )
        assert resp.status_code == 200
        assert resp.json() == {"recent": recent}
        # Router passes limit=10
        _, kwargs = m.call_args
        assert kwargs.get("limit") == 10

    def test_db_failure_500(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.services.progress_db.ProgressDB.get_recent_activities",
            side_effect=RuntimeError("boom"),
        ):
            resp = client.get(
                "/progress/recent", headers={"Authorization": f"Bearer {token}"}
            )
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /progress/badges
# ---------------------------------------------------------------------------


class TestGetBadges:
    def test_success(self, client, mock_auth):
        token = _make_token()
        badges = [{"id": "first-step", "earned": True}]
        with patch(
            "app.services.progress_db.ProgressDB.get_user_badges", return_value=badges
        ):
            resp = client.get(
                "/progress/badges", headers={"Authorization": f"Bearer {token}"}
            )
        assert resp.status_code == 200
        assert resp.json() == {"badges": badges}

    def test_db_failure_500(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.services.progress_db.ProgressDB.get_user_badges",
            side_effect=RuntimeError("boom"),
        ):
            resp = client.get(
                "/progress/badges", headers={"Authorization": f"Bearer {token}"}
            )
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# PUT /progress/last-active  &  GET /progress/last-active
# ---------------------------------------------------------------------------


class TestLastActive:
    def test_put_success(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.services.progress_db.ProgressDB.save_last_active"
        ) as m:
            resp = client.put(
                "/progress/last-active",
                headers={"Authorization": f"Bearer {token}"},
                json={"page_id": "p1", "page_slug": "intro"},
            )
        assert resp.status_code == 200
        assert resp.json() == {"message": "Last active lesson saved"}
        m.assert_called_once_with("user-123", "p1", "intro")

    def test_put_validation_422_missing_fields(self, client, mock_auth):
        token = _make_token()
        resp = client.put(
            "/progress/last-active",
            headers={"Authorization": f"Bearer {token}"},
            json={"page_id": "p1"},
        )
        assert resp.status_code == 422

    def test_put_validation_422_empty_string(self, client, mock_auth):
        token = _make_token()
        resp = client.put(
            "/progress/last-active",
            headers={"Authorization": f"Bearer {token}"},
            json={"page_id": "", "page_slug": "intro"},
        )
        assert resp.status_code == 422

    def test_put_db_failure_500(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.services.progress_db.ProgressDB.save_last_active",
            side_effect=RuntimeError("boom"),
        ):
            resp = client.put(
                "/progress/last-active",
                headers={"Authorization": f"Bearer {token}"},
                json={"page_id": "p1", "page_slug": "intro"},
            )
        assert resp.status_code == 500

    def test_get_success(self, client, mock_auth):
        token = _make_token()
        last = {"page_id": "p1", "page_slug": "intro"}
        with patch(
            "app.services.progress_db.ProgressDB.get_last_active", return_value=last
        ):
            resp = client.get(
                "/progress/last-active",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 200
        assert resp.json() == last

    def test_get_db_failure_500(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.services.progress_db.ProgressDB.get_last_active",
            side_effect=RuntimeError("boom"),
        ):
            resp = client.get(
                "/progress/last-active",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /progress/reset  (admin only)
# ---------------------------------------------------------------------------


class TestResetProgress:
    def test_admin_success(self, client, mock_auth):
        token = _make_admin_token()
        with patch(
            "app.services.progress_db.ProgressDB.delete_all_user_progress"
        ) as m:
            resp = client.delete(
                "/progress/reset", headers={"Authorization": f"Bearer {token}"}
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["message"] == "Progress reset successfully"
        assert body["user_id"] == "admin-1"
        m.assert_called_once_with("admin-1")

    def test_admin_db_failure_500(self, client, mock_auth):
        token = _make_admin_token()
        with patch(
            "app.services.progress_db.ProgressDB.delete_all_user_progress",
            side_effect=RuntimeError("boom"),
        ):
            resp = client.delete(
                "/progress/reset", headers={"Authorization": f"Bearer {token}"}
            )
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to reset progress"


# ---------------------------------------------------------------------------
# GET /progress/capstone/{content_id}
# ---------------------------------------------------------------------------


class TestGetCapstoneSubmission:
    def test_found(self, client, mock_auth):
        token = _make_token()
        submission = {"content_id": "cap-1", "status": "pending_review"}
        with patch(
            "app.services.progress_db.ProgressDB.get_capstone_submission",
            return_value=submission,
        ):
            resp = client.get(
                "/progress/capstone/cap-1",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 200
        assert resp.json() == submission

    def test_not_found_returns_null_submission(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.services.progress_db.ProgressDB.get_capstone_submission",
            return_value=None,
        ):
            resp = client.get(
                "/progress/capstone/cap-1",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 200
        assert resp.json() == {"submission": None}

    def test_db_failure_500(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.services.progress_db.ProgressDB.get_capstone_submission",
            side_effect=RuntimeError("boom"),
        ):
            resp = client.get(
                "/progress/capstone/cap-1",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /progress/capstone/{content_id}/review
# ---------------------------------------------------------------------------


class TestGetCapstoneReview:
    def test_found(self, client, mock_auth):
        token = _make_token()
        review = {"status": "passed", "feedback": "great"}
        with patch(
            "app.services.progress_db.ProgressDB.get_capstone_review",
            return_value=review,
        ):
            resp = client.get(
                "/progress/capstone/cap-1/review",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 200
        assert resp.json() == {"review": review}

    def test_none_returns_null_review(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.services.progress_db.ProgressDB.get_capstone_review",
            return_value=None,
        ):
            resp = client.get(
                "/progress/capstone/cap-1/review",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 200
        assert resp.json() == {"review": None}

    def test_db_failure_500(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.services.progress_db.ProgressDB.get_capstone_review",
            side_effect=RuntimeError("boom"),
        ):
            resp = client.get(
                "/progress/capstone/cap-1/review",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# PUT /progress  (save progress + capstone submission branches)
# ---------------------------------------------------------------------------


class TestSaveProgress:
    def test_validation_422_missing_content_id(self, client, mock_auth):
        token = _make_token()
        resp = client.put(
            "/progress",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert resp.status_code == 422

    def test_validation_422_empty_content_id(self, client, mock_auth):
        token = _make_token()
        resp = client.put(
            "/progress",
            headers={"Authorization": f"Bearer {token}"},
            json={"content_id": ""},
        )
        assert resp.status_code == 422

    def test_simple_save_success(self, client, mock_auth):
        """No repo_url -> plain content completion, saved via save_progress."""
        token = _make_token()
        with patch(
            "app.services.progress_db.ProgressDB.save_progress"
        ) as m:
            resp = client.put(
                "/progress",
                headers={"Authorization": f"Bearer {token}"},
                json={"content_id": "lesson-1"},
            )
        assert resp.status_code == 200
        assert resp.json() == {"message": "Progress saved successfully"}
        m.assert_called_once_with("user-123", "lesson-1")

    def test_simple_save_db_failure_500(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.services.progress_db.ProgressDB.save_progress",
            side_effect=RuntimeError("boom"),
        ):
            resp = client.put(
                "/progress",
                headers={"Authorization": f"Bearer {token}"},
                json={"content_id": "lesson-1"},
            )
        assert resp.status_code == 500

    def test_capstone_free_tier_forbidden_403(self, client, mock_auth):
        """A FREE-tier user cannot submit a capstone (repo_url present)."""
        token = _make_token()
        with patch("app.routers.progress.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            # Membership lookup -> FREE; CONTRIBUTOR_ROLE lookup -> no item
            mock_client.get_item.return_value = {}
            resp = client.put(
                "/progress",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "content_id": "cap-1",
                    "repo_url": "https://github.com/testuser/repo",
                },
            )
        assert resp.status_code == 403
        assert "Builder" in resp.json()["detail"]

    def test_capstone_builder_invalid_repo_url_400(self, client, mock_auth):
        """Builder user, but repo belongs to another account -> 400."""
        token = _make_token()
        with patch("app.routers.progress.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.get_item.return_value = {
                "Item": {
                    "membership_tier": {"S": "BUILDER"},
                    "subscription_status": {"S": "active"},
                }
            }
            resp = client.put(
                "/progress",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "content_id": "cap-1",
                    "repo_url": "https://github.com/someoneelse/repo",
                },
            )
        assert resp.status_code == 400
        assert "under your" in resp.json()["detail"]

    def test_capstone_builder_success(self, client, mock_auth):
        """Builder user submits a valid capstone -> submission metadata returned."""
        token = _make_token()
        with (
            patch("app.routers.progress.boto3.client") as mock_boto,
            patch(
                "app.services.progress_db.ProgressDB.get_capstone_submission",
                return_value=None,
            ),
            patch(
                "app.services.progress_db.ProgressDB.save_capstone_submission"
            ) as mock_save,
            patch("app.services.progress_db.ProgressDB.delete_progress"),
            patch(
                "app.services.email.send_capstone_notification", return_value=True
            ),
        ):
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.get_item.return_value = {
                "Item": {
                    "membership_tier": {"S": "BUILDER"},
                    "subscription_status": {"S": "active"},
                }
            }
            resp = client.put(
                "/progress",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "content_id": "cap-1",
                    "repo_url": "https://github.com/testuser/myrepo",
                },
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["message"] == "Progress saved successfully"
        assert body["submission"]["repo_url"] == "https://github.com/testuser/myrepo"
        assert body["submission"]["repo_name"] == "myrepo"
        assert body["submission"]["github_username"] == "testuser"
        mock_save.assert_called_once()

    def test_capstone_locked_for_review_409(self, client, mock_auth):
        """Resubmitting while a prior submission is pending_review -> 409."""
        token = _make_token()
        with (
            patch("app.routers.progress.boto3.client") as mock_boto,
            patch(
                "app.services.progress_db.ProgressDB.get_capstone_submission",
                return_value={"status": "pending_review"},
            ),
        ):
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.get_item.return_value = {
                "Item": {
                    "membership_tier": {"S": "BUILDER"},
                    "subscription_status": {"S": "active"},
                }
            }
            resp = client.put(
                "/progress",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "content_id": "cap-1",
                    "repo_url": "https://github.com/testuser/myrepo",
                },
            )
        assert resp.status_code == 409
        assert resp.json()["detail"] == "Submission is locked for review"

    def test_capstone_contributor_role_grants_access(self, client, mock_auth):
        """A FREE user with a CONTRIBUTOR_ROLE record gets Builder-equivalent access."""
        token = _make_token()

        def get_item_side_effect(**kwargs):
            sk = kwargs["Key"]["SK"]["S"]
            if sk == "MEMBERSHIP":
                return {}  # FREE
            if sk == "CONTRIBUTOR_ROLE":
                return {"Item": {"PK": {"S": "USER#user-123"}}}
            return {}

        with (
            patch("app.routers.progress.boto3.client") as mock_boto,
            patch(
                "app.services.progress_db.ProgressDB.get_capstone_submission",
                return_value=None,
            ),
            patch("app.services.progress_db.ProgressDB.save_capstone_submission"),
            patch("app.services.progress_db.ProgressDB.delete_progress"),
            patch(
                "app.services.email.send_capstone_notification", return_value=True
            ),
        ):
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.get_item.side_effect = get_item_side_effect
            resp = client.put(
                "/progress",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "content_id": "cap-1",
                    "repo_url": "https://github.com/testuser/myrepo",
                },
            )
        assert resp.status_code == 200
        assert resp.json()["submission"]["repo_name"] == "myrepo"
