"""Tests for the admin router — /admin/* routes.

The admin router consolidates Discord admin ops, analytics, submissions,
registry/module health, user search/listing/profile, sessions, CSV exports,
capstone review, contributor-role management, walkthrough access-tier
management, broadcasts, and journey analytics.

Every route requires an admin JWT (admin status is derived from the
(provider, login) tuple matching ADMIN_USERS, not from an is_admin claim).
Tests cover: success paths, 401 (unauthenticated), 403 (non-admin),
404 (not found), 400/422 (validation), and major business branches.
"""

from datetime import datetime, timedelta, timezone
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
    broadcasts_table="test-broadcasts",
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
    discord_role_contributor_id="",
    discord_callback_url="https://example.com/callback",
    frontend_url="https://example.com",
    frontend_origin="https://example.com",
    github_callback_url="https://example.com/auth/github/callback",
    gitlab_callback_url="https://example.com/auth/gitlab/callback",
    bitbucket_callback_url="https://example.com/auth/bitbucket/callback",
    session_token_lifetime_hours=8,
    admin_users="github:adminuser",
    reviewer_users="github:revieweruser",
    content_registry_bucket="test-registry-bucket",
    total_module_pages=96,
)

TEST_SECRET_KEY = "test-secret-key-for-jwt-signing-32chars"


def _make_token(github_login: str = "nobody") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": f"user-{github_login}",
        "avatar": "https://avatar.url",
        "name": "Test User",
        "provider": "github",
        "github_login": github_login,
        "iat": now,
        "exp": now + timedelta(hours=8),
    }
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")


def admin_token():
    return _make_token("adminuser")


def plain_token():
    return _make_token("plainuser")


def _h(token):
    return {"Authorization": f"Bearer {token}"}


A = {"headers": None}


@pytest.fixture
def client():
    from app.dependencies import get_settings as dep_get_settings

    app.dependency_overrides[dep_get_settings] = lambda: TEST_SETTINGS
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_auth():
    from app.auth.jwt import _jwt_secret_cache

    _jwt_secret_cache["secret_key"] = TEST_SECRET_KEY
    _jwt_secret_cache["fetched_at"] = 9999999999.0
    yield
    _jwt_secret_cache["secret_key"] = None
    _jwt_secret_cache["fetched_at"] = 0.0


# ===========================================================================
# Discord admin routes
# ===========================================================================


class TestDiscordUserDetail:
    def test_unauthenticated_401(self, client):
        assert client.get("/admin/discord/users/u1").status_code == 401

    def test_non_admin_403(self, client):
        resp = client.get("/admin/discord/users/u1", headers=_h(plain_token()))
        assert resp.status_code == 403

    def test_success(self, client):
        with patch("app.routers.admin.AdminDiscordService") as MockSvc:
            MockSvc.return_value.get_user_detail.return_value = {
                "user_id": "u1",
                "membership_tier": "BUILDER",
            }
            resp = client.get("/admin/discord/users/u1", headers=_h(admin_token()))
            assert resp.status_code == 200
            assert resp.json()["membership_tier"] == "BUILDER"

    def test_not_found_404(self, client):
        with patch("app.routers.admin.AdminDiscordService") as MockSvc:
            MockSvc.return_value.get_user_detail.return_value = None
            resp = client.get("/admin/discord/users/u1", headers=_h(admin_token()))
            assert resp.status_code == 404
            assert resp.json()["detail"] == "User not found"


class TestDiscordSync:
    def test_non_admin_403(self, client):
        resp = client.post(
            "/admin/discord/users/u1/sync", headers=_h(plain_token())
        )
        assert resp.status_code == 403

    def test_success_with_reason(self, client):
        with (
            patch("app.routers.admin.AdminDiscordService") as MockSvc,
            patch("app.routers.admin.enqueue_discord_sync") as mock_enqueue,
        ):
            MockSvc.return_value.trigger_sync.return_value = {"status": "queued"}
            resp = client.post(
                "/admin/discord/users/u1/sync",
                headers=_h(admin_token()),
                json={"reason": "manual check"},
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "queued"
            MockSvc.return_value.trigger_sync.assert_called_once()
            mock_enqueue.assert_called_once()

    def test_success_no_body(self, client):
        with (
            patch("app.routers.admin.AdminDiscordService") as MockSvc,
            patch("app.routers.admin.enqueue_discord_sync"),
        ):
            MockSvc.return_value.trigger_sync.return_value = {"status": "queued"}
            resp = client.post(
                "/admin/discord/users/u1/sync", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            # Default reason should be used
            args = MockSvc.return_value.trigger_sync.call_args[0]
            assert args[2] == "Admin triggered"


class TestDiscordDisconnect:
    def test_non_admin_403(self, client):
        resp = client.request(
            "DELETE",
            "/admin/discord/users/u1/disconnect",
            headers=_h(plain_token()),
            json={"reason": "spam"},
        )
        assert resp.status_code == 403

    def test_missing_reason_400(self, client):
        resp = client.request(
            "DELETE",
            "/admin/discord/users/u1/disconnect",
            headers=_h(admin_token()),
            json={},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Reason is required"

    def test_success(self, client):
        with patch("app.routers.admin.AdminDiscordService") as MockSvc:
            MockSvc.return_value.disconnect.return_value = {"status": "disconnected"}
            resp = client.request(
                "DELETE",
                "/admin/discord/users/u1/disconnect",
                headers=_h(admin_token()),
                json={"reason": "policy violation"},
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "disconnected"

    def test_value_error_400(self, client):
        with patch("app.routers.admin.AdminDiscordService") as MockSvc:
            MockSvc.return_value.disconnect.side_effect = ValueError("not connected")
            resp = client.request(
                "DELETE",
                "/admin/discord/users/u1/disconnect",
                headers=_h(admin_token()),
                json={"reason": "policy violation"},
            )
            assert resp.status_code == 400
            assert resp.json()["detail"] == "not connected"


class TestDiscordAudit:
    def test_non_admin_403(self, client):
        resp = client.get(
            "/admin/discord/users/u1/audit", headers=_h(plain_token())
        )
        assert resp.status_code == 403

    def test_success(self, client):
        with patch("app.routers.admin.AdminDiscordService") as MockSvc:
            MockSvc.return_value.get_audit_log.return_value = [{"action": "sync"}]
            resp = client.get(
                "/admin/discord/users/u1/audit", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            assert resp.json()["entries"] == [{"action": "sync"}]


# ===========================================================================
# Analytics
# ===========================================================================


class TestAnalytics:
    def test_non_admin_403(self, client):
        assert (
            client.get("/admin/analytics", headers=_h(plain_token())).status_code
            == 403
        )

    def test_unauthenticated_401(self, client):
        assert client.get("/admin/analytics").status_code == 401

    def test_success(self, client):
        now = datetime.now(timezone.utc)
        with patch("app.routers.admin.AdminService") as MockSvc:
            svc = MockSvc.return_value
            svc.get_all_users_progress.return_value = [
                {"user_id": "u1", "completed_at": now.isoformat()},
                {"user_id": "u1", "completed_at": now.isoformat()},
                {"user_id": "u2", "completed_at": ""},
            ]
            svc.get_all_registered_users.return_value = [
                {"user_id": "u1", "github_username": "alice", "registered_at": now.isoformat()},
                {"user_id": "u2", "username": "bob", "registered_at": now.isoformat()},
            ]
            svc.get_total_capstone_submissions_count.return_value = 3
            svc.get_all_badge_stats.return_value = {"total": 5}
            svc.get_all_quiz_stats.return_value = {"total": 2}

            resp = client.get("/admin/analytics", headers=_h(admin_token()))
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_registered_users"] == 2
            assert data["users_with_progress"] == 2
            assert data["total_capstone_submissions"] == 3
            assert data["active_learners_7d"] == 1
            assert len(data["registration_timeline"]) == 30
            assert len(data["completion_by_user"]) <= 10

    def test_service_error_500(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_all_users_progress.side_effect = Exception("boom")
            resp = client.get("/admin/analytics", headers=_h(admin_token()))
            assert resp.status_code == 500
            assert resp.json()["detail"] == "Failed to fetch analytics"


# ===========================================================================
# Submissions
# ===========================================================================


class TestSubmissions:
    def test_non_admin_403(self, client):
        assert (
            client.get("/admin/submissions", headers=_h(plain_token())).status_code
            == 403
        )

    def test_success(self, client):
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch("app.services.certification.db.CertificationDB") as MockCertDB,
        ):
            MockSvc.return_value.get_capstone_submissions.return_value = (
                [
                    {
                        "user_id": "u1",
                        "content_id": "devsecops-capstone",
                        "repo_url": "https://github.com/x/y",
                    }
                ],
                1,
            )
            MockCertDB.return_value.list_user_credentials.return_value = [
                {
                    "credential_status": "ACTIVE",
                    "pathway_id": "devsecops-engineering",
                    "credential_id": "cred-1",
                }
            ]
            resp = client.get("/admin/submissions", headers=_h(admin_token()))
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_count"] == 1
            assert data["total_pages"] == 1
            sub = data["submissions"][0]
            assert sub["has_active_credential"] is True
            assert sub["credential_id"] == "cred-1"

    def test_submission_without_matching_credential(self, client):
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch("app.services.certification.db.CertificationDB") as MockCertDB,
        ):
            MockSvc.return_value.get_capstone_submissions.return_value = (
                [{"user_id": "u1", "content_id": "unknown-capstone"}],
                1,
            )
            MockCertDB.return_value.list_user_credentials.return_value = []
            resp = client.get("/admin/submissions", headers=_h(admin_token()))
            assert resp.status_code == 200
            assert resp.json()["submissions"][0]["has_active_credential"] is False

    def test_credential_fetch_failure_is_tolerated(self, client):
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch("app.services.certification.db.CertificationDB") as MockCertDB,
        ):
            MockSvc.return_value.get_capstone_submissions.return_value = (
                [{"user_id": "u1", "content_id": "devsecops-capstone"}],
                1,
            )
            MockCertDB.return_value.list_user_credentials.side_effect = Exception(
                "cred boom"
            )
            resp = client.get("/admin/submissions", headers=_h(admin_token()))
            assert resp.status_code == 200
            assert resp.json()["submissions"][0]["has_active_credential"] is False

    def test_invalid_pagination_400(self, client):
        resp = client.get(
            "/admin/submissions?page=abc", headers=_h(admin_token())
        )
        assert resp.status_code == 400

    def test_page_lt_1_400(self, client):
        resp = client.get("/admin/submissions?page=0", headers=_h(admin_token()))
        assert resp.status_code == 400

    def test_page_size_out_of_range_400(self, client):
        resp = client.get(
            "/admin/submissions?page_size=500", headers=_h(admin_token())
        )
        assert resp.status_code == 400

    def test_service_error_500(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_capstone_submissions.side_effect = Exception(
                "boom"
            )
            resp = client.get("/admin/submissions", headers=_h(admin_token()))
            assert resp.status_code == 500


# ===========================================================================
# Registry status + module health
# ===========================================================================


class TestRegistryStatus:
    def test_non_admin_403(self, client):
        assert (
            client.get(
                "/admin/registry-status", headers=_h(plain_token())
            ).status_code
            == 403
        )

    def test_success(self, client):
        with patch("app.routers.admin.get_registry_service") as mock_get:
            svc = MagicMock()
            svc._registry = {
                "entries": {"a": {}, "b": {}},
                "schema_version": "1.0",
            }
            svc._last_loaded_at = "2026-01-01"
            mock_get.return_value = svc
            resp = client.get("/admin/registry-status", headers=_h(admin_token()))
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "healthy"
            assert data["entry_count"] == 2
            assert data["schema_version"] == "1.0"

    def test_registry_none_503(self, client):
        with patch("app.routers.admin.get_registry_service") as mock_get:
            svc = MagicMock()
            svc._registry = None
            mock_get.return_value = svc
            resp = client.get("/admin/registry-status", headers=_h(admin_token()))
            assert resp.status_code == 503

    def test_registry_value_error_503(self, client):
        with patch("app.routers.admin.get_registry_service") as mock_get:
            mock_get.side_effect = ValueError("bad bucket")
            resp = client.get("/admin/registry-status", headers=_h(admin_token()))
            assert resp.status_code == 503


class TestModuleHealth:
    def test_non_admin_403(self, client):
        assert (
            client.get("/admin/module-health", headers=_h(plain_token())).status_code
            == 403
        )

    def test_success(self, client):
        with patch("app.routers.admin.get_registry_service") as mock_get:
            svc = MagicMock()
            svc._registry = {
                "entries": {
                    "a": {"content_type": "quiz"},
                    "b": {"content_type": "walkthrough"},
                    "c": {"content_type": "walkthrough"},
                }
            }
            mock_get.return_value = svc
            resp = client.get("/admin/module-health", headers=_h(admin_token()))
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_entries"] == 3
            assert data["quizzes"] == 1
            assert data["walkthroughs"] == 2

    def test_registry_none_503(self, client):
        with patch("app.routers.admin.get_registry_service") as mock_get:
            svc = MagicMock()
            svc._registry = None
            mock_get.return_value = svc
            resp = client.get("/admin/module-health", headers=_h(admin_token()))
            assert resp.status_code == 503


class TestWalkthroughStatistics:
    def test_non_admin_403(self, client):
        assert (
            client.get(
                "/admin/walkthrough-statistics", headers=_h(plain_token())
            ).status_code
            == 403
        )

    def test_success(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_walkthrough_statistics.return_value = {
                "total": 10
            }
            resp = client.get(
                "/admin/walkthrough-statistics", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            assert resp.json()["total"] == 10

    def test_service_error_500(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_walkthrough_statistics.side_effect = Exception(
                "x"
            )
            resp = client.get(
                "/admin/walkthrough-statistics", headers=_h(admin_token())
            )
            assert resp.status_code == 500


# ===========================================================================
# User search
# ===========================================================================


class TestUserSearch:
    def test_non_admin_403(self, client):
        assert (
            client.get(
                "/admin/users/search?q=alice", headers=_h(plain_token())
            ).status_code
            == 403
        )

    def test_missing_query_400(self, client):
        resp = client.get("/admin/users/search", headers=_h(admin_token()))
        assert resp.status_code == 400

    def test_success(self, client):
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch("app.routers.admin.calculate_user_badges") as mock_badges,
            patch("app.routers.admin.get_badges_earned_count") as mock_count,
        ):
            svc = MockSvc.return_value
            svc.get_all_registered_users.return_value = [
                {"user_id": "u1", "username": "alice", "github_username": "alice-gh"},
                {"user_id": "u2", "username": "bob", "github_username": "bob-gh"},
            ]
            svc.get_user_stats.return_value = {
                "completed_count": 5,
                "overall_completion": 50,
                "quizzes_passed": 2,
                "walkthroughs_completed": 1,
                "capstone_submissions": 0,
            }
            svc.get_user_progress.return_value = []
            mock_badges.return_value = []
            mock_count.return_value = 3

            resp = client.get(
                "/admin/users/search?q=alice", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_results"] == 1
            assert data["users"][0]["username"] == "alice"
            assert data["users"][0]["stats"]["badges_earned"] == 3

    def test_stats_failure_degrades_gracefully(self, client):
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch("app.routers.admin.calculate_user_badges"),
            patch("app.routers.admin.get_badges_earned_count"),
        ):
            svc = MockSvc.return_value
            svc.get_all_registered_users.return_value = [
                {"user_id": "u1", "username": "alice", "github_username": "alice-gh"},
            ]
            svc.get_user_stats.side_effect = Exception("stats boom")
            resp = client.get(
                "/admin/users/search?q=alice", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["users"][0]["stats"]["completed_count"] == 0

    def test_service_error_500(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_all_registered_users.side_effect = Exception("x")
            resp = client.get(
                "/admin/users/search?q=alice", headers=_h(admin_token())
            )
            assert resp.status_code == 500


# ===========================================================================
# Users list (with membership + credential enrichment via boto3 scans)
# ===========================================================================


class TestListUsers:
    def test_non_admin_403(self, client):
        assert client.get("/admin/users", headers=_h(plain_token())).status_code == 403

    def _boto_scan_empty(self):
        """boto3 client whose scans return no items (both scans end immediately)."""
        mock_client = MagicMock()
        mock_client.scan.return_value = {"Items": []}
        return mock_client

    def test_success_basic(self, client):
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch("app.routers.admin.boto3_mod.client") as mock_boto,
        ):
            MockSvc.return_value.get_all_registered_users.return_value = [
                {"user_id": "u1", "username": "alice", "github_username": "alice-gh"},
                {"user_id": "u2", "username": "bob", "github_username": "bob-gh"},
            ]
            mock_boto.return_value = self._boto_scan_empty()
            resp = client.get("/admin/users", headers=_h(admin_token()))
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_count"] == 2
            assert data["page"] == 1
            # Default tier applied
            assert all(u["membership_tier"] == "FREE" for u in data["users"])

    def test_enrichment_from_membership_and_credentials(self, client):
        mock_client = MagicMock()
        # First scan call: membership table; second: credentials in progress table.
        mock_client.scan.side_effect = [
            {
                "Items": [
                    {
                        "PK": {"S": "USER#u1"},
                        "SK": {"S": "MEMBERSHIP"},
                        "membership_tier": {"S": "BUILDER"},
                    },
                    {
                        "PK": {"S": "USER#u1"},
                        "SK": {"S": "CONTRIBUTOR_ROLE"},
                        "role": {"S": "maintainer"},
                    },
                    {
                        "PK": {"S": "USER#u1"},
                        "SK": {"S": "DISCORD_ACTIVE"},
                        "username": {"S": "alice#1234"},
                        "active": {"BOOL": True},
                    },
                ]
            },
            {
                "Items": [
                    {
                        "PK": {"S": "USER#u1"},
                        "SK": {"S": "CREDENTIAL#cred-1"},
                        "credential_status": {"S": "ACTIVE"},
                        "pathway_id": {"S": "devsecops-engineering"},
                        "credential_id": {"S": "cred-1"},
                        "issued_at": {"S": "2026-01-01"},
                    }
                ]
            },
        ]
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch("app.routers.admin.boto3_mod.client", return_value=mock_client),
        ):
            MockSvc.return_value.get_all_registered_users.return_value = [
                {"user_id": "u1", "username": "alice", "github_username": "alice-gh"},
            ]
            resp = client.get("/admin/users", headers=_h(admin_token()))
            assert resp.status_code == 200
            u = resp.json()["users"][0]
            assert u["membership_tier"] == "BUILDER"
            assert u["contributor_role"] == "maintainer"
            assert u["discord_username"] == "alice#1234"
            assert u["certifications_count"] == 1

    def test_role_filter_builder(self, client):
        mock_client = MagicMock()
        mock_client.scan.side_effect = [
            {
                "Items": [
                    {
                        "PK": {"S": "USER#u1"},
                        "SK": {"S": "MEMBERSHIP"},
                        "membership_tier": {"S": "BUILDER"},
                    }
                ]
            },
            {"Items": []},
        ]
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch("app.routers.admin.boto3_mod.client", return_value=mock_client),
        ):
            MockSvc.return_value.get_all_registered_users.return_value = [
                {"user_id": "u1", "username": "alice", "github_username": "a"},
                {"user_id": "u2", "username": "bob", "github_username": "b"},
            ]
            resp = client.get(
                "/admin/users?role=BUILDER", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_count"] == 1
            assert data["users"][0]["user_id"] == "u1"

    def test_search_filter(self, client):
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch("app.routers.admin.boto3_mod.client") as mock_boto,
        ):
            MockSvc.return_value.get_all_registered_users.return_value = [
                {"user_id": "u1", "username": "alice", "github_username": "a"},
                {"user_id": "u2", "username": "bob", "github_username": "b"},
            ]
            mock_boto.return_value = self._boto_scan_empty()
            resp = client.get(
                "/admin/users?search=alice", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            assert resp.json()["total_count"] == 1

    def test_role_filter_contributor_and_email(self, client):
        mock_client = MagicMock()
        mock_client.scan.side_effect = [
            {
                "Items": [
                    {
                        "PK": {"S": "USER#u1"},
                        "SK": {"S": "CONTRIBUTOR_ROLE"},
                        "role": {"S": "mentor"},
                    }
                ]
            },
            {"Items": []},
        ]
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch("app.routers.admin.boto3_mod.client", return_value=mock_client),
        ):
            MockSvc.return_value.get_all_registered_users.return_value = [
                {
                    "user_id": "u1",
                    "username": "alice",
                    "github_username": "a",
                    "email": "alice@example.com",
                },
                {
                    "user_id": "u2",
                    "username": "bob",
                    "github_username": "b",
                    "email": "bob@example.com",
                },
            ]
            resp = client.get(
                "/admin/users?role=CONTRIBUTOR&email=alice",
                headers=_h(admin_token()),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_count"] == 1
            assert data["users"][0]["user_id"] == "u1"

    def test_role_filter_free(self, client):
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch("app.routers.admin.boto3_mod.client") as mock_boto,
        ):
            MockSvc.return_value.get_all_registered_users.return_value = [
                {"user_id": "u1", "username": "alice", "github_username": "a"},
            ]
            mock_boto.return_value = self._boto_scan_empty()
            resp = client.get("/admin/users?role=FREE", headers=_h(admin_token()))
            assert resp.status_code == 200
            assert resp.json()["total_count"] == 1

    def test_membership_scan_error_handled(self, client):
        """Membership scan raising is caught; defaults applied, credential scan runs."""
        mock_client = MagicMock()
        mock_client.scan.side_effect = [
            Exception("membership scan fail"),
            {"Items": []},
        ]
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch("app.routers.admin.boto3_mod.client", return_value=mock_client),
        ):
            MockSvc.return_value.get_all_registered_users.return_value = [
                {"user_id": "u1", "username": "alice", "github_username": "a"},
            ]
            resp = client.get("/admin/users", headers=_h(admin_token()))
            assert resp.status_code == 200
            assert resp.json()["users"][0]["membership_tier"] == "FREE"

    def test_service_error_500(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_all_registered_users.side_effect = Exception("x")
            resp = client.get("/admin/users", headers=_h(admin_token()))
            assert resp.status_code == 500

    def test_invalid_page_400(self, client):
        resp = client.get("/admin/users?page=abc", headers=_h(admin_token()))
        assert resp.status_code == 400

    def test_page_size_out_of_range_400(self, client):
        resp = client.get(
            "/admin/users?page_size=0", headers=_h(admin_token())
        )
        assert resp.status_code == 400


# ===========================================================================
# User profile (admin view)
# ===========================================================================


class TestUserProfile:
    def test_non_admin_403(self, client):
        assert (
            client.get(
                "/admin/users/u1/profile", headers=_h(plain_token())
            ).status_code
            == 403
        )

    def test_not_found_404(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_user_profile.return_value = None
            resp = client.get(
                "/admin/users/u1/profile", headers=_h(admin_token())
            )
            assert resp.status_code == 404

    def test_success(self, client):
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch("app.routers.admin.calculate_user_badges") as mock_badges,
        ):
            svc = MockSvc.return_value
            svc.get_user_profile.return_value = {"user_id": "u1", "username": "alice"}
            svc.get_user_stats.return_value = {
                "completed_count": 10,
                "overall_completion": 80,
                "quizzes_passed": 3,
                "walkthroughs_completed": 2,
                "capstone_submissions": 1,
                "current_streak": 4,
                "longest_streak": 9,
            }
            svc.get_user_progress.return_value = []
            svc.get_user_walkthrough_progress.return_value = [{"id": "w1"}]
            svc.get_contributor_role.return_value = {"role": "mentor"}
            mock_badges.return_value = [{"id": "b1"}]

            resp = client.get(
                "/admin/users/u1/profile", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["user"]["username"] == "alice"
            assert data["stats"]["completed_count"] == 10
            assert data["badges"] == [{"id": "b1"}]
            assert data["walkthrough_progress"] == [{"id": "w1"}]
            assert data["contributor_role"] == {"role": "mentor"}

    def test_stats_failure_degrades(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            svc = MockSvc.return_value
            svc.get_user_profile.return_value = {"user_id": "u1"}
            svc.get_user_stats.side_effect = Exception("boom")
            svc.get_user_walkthrough_progress.return_value = []
            svc.get_contributor_role.return_value = None
            resp = client.get(
                "/admin/users/u1/profile", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            assert resp.json()["stats"]["completed_count"] == 0


# ===========================================================================
# Active sessions
# ===========================================================================


class TestActiveSessions:
    def test_non_admin_403(self, client):
        assert (
            client.get("/admin/sessions", headers=_h(plain_token())).status_code == 403
        )

    def test_success(self, client):
        mock_client = MagicMock()
        mock_client.scan.return_value = {
            "Items": [
                {
                    "user_id": {"S": "u1"},
                    "created_at": {"N": "100"},
                    "expires_at": {"N": "99999999999"},
                },
                {
                    "user_id": {"S": "u1"},
                    "created_at": {"N": "200"},
                    "expires_at": {"N": "99999999999"},
                },
            ]
        }
        mock_client.batch_get_item.return_value = {
            "Responses": {
                "test-progress": [
                    {"PK": {"S": "USER#u1"}, "github_username": {"S": "alice"}}
                ]
            }
        }
        with patch("app.routers.admin.boto3_mod.client", return_value=mock_client):
            resp = client.get("/admin/sessions", headers=_h(admin_token()))
            assert resp.status_code == 200
            data = resp.json()
            # Only latest session per user is kept
            assert data["total_active"] == 1
            assert data["sessions"][0]["username"] == "alice"
            assert data["sessions"][0]["created_at"] == 200


# ===========================================================================
# Exports
# ===========================================================================


class TestExports:
    def test_users_non_admin_403(self, client):
        assert (
            client.get("/admin/export/users", headers=_h(plain_token())).status_code
            == 403
        )

    def test_export_users_success(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            svc = MockSvc.return_value
            svc.get_all_registered_users.return_value = [
                {"user_id": "u1", "username": "alice", "github_username": "a"},
            ]
            svc.get_user_stats.return_value = {
                "completed_count": 5,
                "overall_completion": 50,
                "quizzes_passed": 2,
            }
            resp = client.get("/admin/export/users", headers=_h(admin_token()))
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/csv")
            assert "alice" in resp.text
            assert "user_id" in resp.text

    def test_export_users_stats_failure_still_writes_row(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            svc = MockSvc.return_value
            svc.get_all_registered_users.return_value = [
                {"user_id": "u1", "username": "alice", "github_username": "a"},
            ]
            svc.get_user_stats.side_effect = Exception("boom")
            resp = client.get("/admin/export/users", headers=_h(admin_token()))
            assert resp.status_code == 200
            assert "alice" in resp.text

    def test_export_capstones_success(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_capstone_submissions.return_value = (
                [
                    {
                        "user_id": "u1",
                        "github_username": "a",
                        "content_id": "devsecops-capstone",
                        "repo_url": "https://github.com/x/y",
                        "submitted_at": "2026-01-01",
                    }
                ],
                1,
            )
            resp = client.get(
                "/admin/export/capstone-submissions", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            assert "devsecops-capstone" in resp.text

    def test_export_capstones_error_500(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_capstone_submissions.side_effect = Exception("x")
            resp = client.get(
                "/admin/export/capstone-submissions", headers=_h(admin_token())
            )
            assert resp.status_code == 500


# ===========================================================================
# Capstone review
# ===========================================================================


class TestSubmitReview:
    def test_non_admin_403(self, client):
        resp = client.post(
            "/admin/submissions/u1/c1/review",
            headers=_h(plain_token()),
            json={"feedback": "good"},
        )
        assert resp.status_code == 403

    def test_missing_feedback_400(self, client):
        with patch("app.routers.admin.AdminService"):
            resp = client.post(
                "/admin/submissions/u1/c1/review",
                headers=_h(admin_token()),
                json={"feedback": ""},
            )
            assert resp.status_code == 400
            assert resp.json()["detail"] == "Feedback is required"

    def test_submission_not_found_404(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_capstone_submission.return_value = None
            resp = client.post(
                "/admin/submissions/u1/c1/review",
                headers=_h(admin_token()),
                json={"feedback": "nice work"},
            )
            assert resp.status_code == 404

    def test_not_reviewable_state_400(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_capstone_submission.return_value = {
                "status": "reviewed"
            }
            resp = client.post(
                "/admin/submissions/u1/c1/review",
                headers=_h(admin_token()),
                json={"feedback": "nice work"},
            )
            assert resp.status_code == 400

    def test_success_passed_marks_progress(self, client):
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch("app.routers.admin.ProgressDB") as MockProg,
            patch("app.routers.admin.create_notification") as mock_notif,
            patch(
                "app.routers.admin.send_review_notification_to_learner"
            ) as mock_email,
        ):
            svc = MockSvc.return_value
            svc.get_capstone_submission.return_value = {"status": "pending_review"}
            svc.get_user_profile.return_value = {
                "email": "jane@example.com",
                "username": "jane",
            }
            resp = client.post(
                "/admin/submissions/u1/devsecops-capstone/review",
                headers=_h(admin_token()),
                json={"feedback": "great job", "grade": "passed"},
            )
            assert resp.status_code == 200
            assert resp.json()["message"] == "Review submitted successfully"
            svc.save_capstone_review.assert_called_once()
            svc.update_capstone_submission_status.assert_called_once_with(
                "u1", "devsecops-capstone", "passed"
            )
            MockProg.return_value.save_progress.assert_called_once()
            mock_notif.assert_called_once()
            mock_email.assert_called_once()

    def test_invalid_json_body_400(self, client):
        with patch("app.routers.admin.AdminService"):
            resp = client.post(
                "/admin/submissions/u1/c1/review",
                headers={**_h(admin_token()), "Content-Type": "application/json"},
                content=b"{not valid json",
            )
            assert resp.status_code == 400
            assert resp.json()["detail"] == "Invalid request body"

    def test_notification_and_email_failures_still_succeed(self, client):
        """Notification/email failures are swallowed; review still succeeds."""
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch(
                "app.routers.admin.create_notification",
                side_effect=Exception("notif boom"),
            ),
            patch(
                "app.routers.admin.send_review_notification_to_learner",
                side_effect=Exception("email boom"),
            ),
        ):
            svc = MockSvc.return_value
            svc.get_capstone_submission.return_value = {"status": "pending_review"}
            svc.get_user_profile.return_value = {
                "email": "jane@example.com",
                "username": "jane",
            }
            resp = client.post(
                "/admin/submissions/u1/some-capstone/review",
                headers=_h(admin_token()),
                json={"feedback": "ok"},
            )
            assert resp.status_code == 200

    def test_service_error_500(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_capstone_submission.side_effect = Exception(
                "boom"
            )
            resp = client.post(
                "/admin/submissions/u1/c1/review",
                headers=_h(admin_token()),
                json={"feedback": "ok"},
            )
            assert resp.status_code == 500

    def test_success_default_reviewed_grade(self, client):
        with (
            patch("app.routers.admin.AdminService") as MockSvc,
            patch("app.routers.admin.create_notification"),
            patch("app.routers.admin.send_review_notification_to_learner"),
        ):
            svc = MockSvc.return_value
            svc.get_capstone_submission.return_value = {"status": "pending_review"}
            svc.get_user_profile.return_value = {"email": None}
            resp = client.post(
                "/admin/submissions/u1/some-capstone/review",
                headers=_h(admin_token()),
                json={"feedback": "ok"},
            )
            assert resp.status_code == 200
            svc.update_capstone_submission_status.assert_called_once_with(
                "u1", "some-capstone", "reviewed"
            )


class TestGetReviewAdmin:
    def test_non_admin_403(self, client):
        resp = client.get(
            "/admin/submissions/u1/c1/review", headers=_h(plain_token())
        )
        assert resp.status_code == 403

    def test_success_with_review(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_capstone_review.return_value = {
                "feedback": "nice"
            }
            resp = client.get(
                "/admin/submissions/u1/c1/review", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            assert resp.json()["review"]["feedback"] == "nice"

    def test_success_no_review(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_capstone_review.return_value = None
            resp = client.get(
                "/admin/submissions/u1/c1/review", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            assert resp.json()["review"] is None

    def test_service_error_500(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_capstone_review.side_effect = Exception("boom")
            resp = client.get(
                "/admin/submissions/u1/c1/review", headers=_h(admin_token())
            )
            assert resp.status_code == 500


# ===========================================================================
# Contributor role mapping
# ===========================================================================


class TestContributorRole:
    def test_get_non_admin_403(self, client):
        resp = client.get(
            "/admin/users/u1/contributor-role", headers=_h(plain_token())
        )
        assert resp.status_code == 403

    def test_get_success(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_contributor_role.return_value = {
                "role": "maintainer"
            }
            resp = client.get(
                "/admin/users/u1/contributor-role", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            assert resp.json()["contributor_role"]["role"] == "maintainer"

    def test_set_missing_role_400(self, client):
        resp = client.put(
            "/admin/users/u1/contributor-role",
            headers=_h(admin_token()),
            json={"note": "x"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Role is required"

    def test_set_empty_body_400(self, client):
        resp = client.put(
            "/admin/users/u1/contributor-role",
            headers=_h(admin_token()),
            content=b"",
        )
        assert resp.status_code == 400

    def test_set_invalid_json_400(self, client):
        resp = client.put(
            "/admin/users/u1/contributor-role",
            headers={**_h(admin_token()), "Content-Type": "application/json"},
            content=b"{bad json",
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid request body"

    def test_get_service_error_500(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_contributor_role.side_effect = Exception("boom")
            resp = client.get(
                "/admin/users/u1/contributor-role", headers=_h(admin_token())
            )
            assert resp.status_code == 500

    def test_set_success(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.set_contributor_role.return_value = {
                "role": "mentor"
            }
            resp = client.put(
                "/admin/users/u1/contributor-role",
                headers=_h(admin_token()),
                json={"role": "mentor", "note": "great"},
            )
            assert resp.status_code == 200
            assert resp.json()["contributor_role"]["role"] == "mentor"

    def test_set_value_error_400(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.set_contributor_role.side_effect = ValueError(
                "invalid role"
            )
            resp = client.put(
                "/admin/users/u1/contributor-role",
                headers=_h(admin_token()),
                json={"role": "bogus"},
            )
            assert resp.status_code == 400
            assert resp.json()["detail"] == "invalid role"

    def test_set_success_with_discord_role_assignment(self, client):
        """When discord_role_contributor_id is set, the Discord role PUT runs."""
        from app.dependencies import get_settings as dep_get_settings

        settings_with_discord = TEST_SETTINGS.model_copy(
            update={"discord_role_contributor_id": "999"}
        )
        app.dependency_overrides[dep_get_settings] = lambda: settings_with_discord
        try:
            with (
                patch("app.routers.admin.AdminService") as MockSvc,
                patch("app.routers.admin.AdminDiscordService") as MockDiscord,
                patch("httpx.put") as mock_put,
            ):
                MockSvc.return_value.set_contributor_role.return_value = {
                    "role": "mentor"
                }
                discord = MockDiscord.return_value
                discord.get_user_detail.return_value = {"discord_user_id": "d123"}
                discord._get_bot_token.return_value = "bot-token"
                # Non-204 status exercises the warning-log branch
                mock_put.return_value = MagicMock(status_code=500)

                resp = client.put(
                    "/admin/users/u1/contributor-role",
                    headers=_h(admin_token()),
                    json={"role": "mentor"},
                )
                assert resp.status_code == 200
                mock_put.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_delete_success_with_discord_role_removal(self, client):
        """When discord_role_contributor_id is set, the Discord role DELETE runs."""
        from app.dependencies import get_settings as dep_get_settings

        settings_with_discord = TEST_SETTINGS.model_copy(
            update={"discord_role_contributor_id": "999"}
        )
        app.dependency_overrides[dep_get_settings] = lambda: settings_with_discord
        try:
            with (
                patch("app.routers.admin.AdminService") as MockSvc,
                patch("app.routers.admin.AdminDiscordService") as MockDiscord,
                patch("httpx.delete") as mock_delete,
            ):
                MockSvc.return_value.delete_contributor_role.return_value = True
                discord = MockDiscord.return_value
                discord.get_user_detail.return_value = {"discord_user_id": "d123"}
                discord._get_bot_token.return_value = "bot-token"
                # Non-204/404 status exercises the warning-log branch
                mock_delete.return_value = MagicMock(status_code=500)

                resp = client.delete(
                    "/admin/users/u1/contributor-role", headers=_h(admin_token())
                )
                assert resp.status_code == 200
                mock_delete.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_delete_non_admin_403(self, client):
        resp = client.delete(
            "/admin/users/u1/contributor-role", headers=_h(plain_token())
        )
        assert resp.status_code == 403

    def test_delete_success(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.delete_contributor_role.return_value = True
            resp = client.delete(
                "/admin/users/u1/contributor-role", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            assert resp.json()["message"] == "Contributor role removed"

    def test_delete_failure_500(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.delete_contributor_role.return_value = False
            resp = client.delete(
                "/admin/users/u1/contributor-role", headers=_h(admin_token())
            )
            assert resp.status_code == 500


# ===========================================================================
# Walkthrough access tiers
# ===========================================================================


class TestWalkthroughAccessTiers:
    def test_get_all_non_admin_403(self, client):
        resp = client.get(
            "/admin/walkthroughs/access-tiers", headers=_h(plain_token())
        )
        assert resp.status_code == 403

    def test_get_all_success(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_all_walkthrough_access_tiers.return_value = {
                "w1": "BUILDER"
            }
            resp = client.get(
                "/admin/walkthroughs/access-tiers", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            assert resp.json()["access_tiers"]["w1"] == "BUILDER"

    def test_set_missing_tier_400(self, client):
        resp = client.put(
            "/admin/walkthroughs/w1/access-tier",
            headers=_h(admin_token()),
            json={},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "access_tier is required"

    def test_set_empty_body_400(self, client):
        resp = client.put(
            "/admin/walkthroughs/w1/access-tier",
            headers=_h(admin_token()),
            content=b"",
        )
        assert resp.status_code == 400

    def test_set_invalid_json_400(self, client):
        resp = client.put(
            "/admin/walkthroughs/w1/access-tier",
            headers={**_h(admin_token()), "Content-Type": "application/json"},
            content=b"{bad json",
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid request body"

    def test_get_all_error_500(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.get_all_walkthrough_access_tiers.side_effect = (
                Exception("boom")
            )
            resp = client.get(
                "/admin/walkthroughs/access-tiers", headers=_h(admin_token())
            )
            assert resp.status_code == 500

    def test_set_success(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.set_walkthrough_access_tier.return_value = {
                "walkthrough_id": "w1",
                "access_tier": "BUILDER",
            }
            resp = client.put(
                "/admin/walkthroughs/w1/access-tier",
                headers=_h(admin_token()),
                json={"access_tier": "builder"},
            )
            assert resp.status_code == 200
            assert resp.json()["data"]["access_tier"] == "BUILDER"

    def test_set_value_error_400(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.set_walkthrough_access_tier.side_effect = ValueError(
                "bad tier"
            )
            resp = client.put(
                "/admin/walkthroughs/w1/access-tier",
                headers=_h(admin_token()),
                json={"access_tier": "GOLD"},
            )
            assert resp.status_code == 400

    def test_delete_success(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.set_walkthrough_access_tier.return_value = {}
            resp = client.delete(
                "/admin/walkthroughs/w1/access-tier", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            assert resp.json()["message"] == "Access tier reset to FREE"

    def test_delete_error_500(self, client):
        with patch("app.routers.admin.AdminService") as MockSvc:
            MockSvc.return_value.set_walkthrough_access_tier.side_effect = Exception(
                "boom"
            )
            resp = client.delete(
                "/admin/walkthroughs/w1/access-tier", headers=_h(admin_token())
            )
            assert resp.status_code == 500


# ===========================================================================
# Broadcasts
# ===========================================================================


class TestBroadcasts:
    def test_create_non_admin_403(self, client):
        resp = client.post(
            "/admin/broadcasts",
            headers=_h(plain_token()),
            json={"title": "t", "message": "m"},
        )
        assert resp.status_code == 403

    def test_create_missing_title_400(self, client):
        resp = client.post(
            "/admin/broadcasts",
            headers=_h(admin_token()),
            json={"message": "m"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Title is required"

    def test_create_title_too_long_400(self, client):
        resp = client.post(
            "/admin/broadcasts",
            headers=_h(admin_token()),
            json={"title": "x" * 101, "message": "m"},
        )
        assert resp.status_code == 400

    def test_create_missing_message_400(self, client):
        resp = client.post(
            "/admin/broadcasts",
            headers=_h(admin_token()),
            json={"title": "t"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Message is required"

    def test_create_message_too_long_400(self, client):
        resp = client.post(
            "/admin/broadcasts",
            headers=_h(admin_token()),
            json={"title": "t", "message": "x" * 2001},
        )
        assert resp.status_code == 400

    def test_create_empty_body_400(self, client):
        resp = client.post(
            "/admin/broadcasts", headers=_h(admin_token()), content=b""
        )
        assert resp.status_code == 400

    def test_create_invalid_json_400(self, client):
        resp = client.post(
            "/admin/broadcasts",
            headers={**_h(admin_token()), "Content-Type": "application/json"},
            content=b"{bad json",
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid request body"

    def test_create_service_error_500(self, client):
        with patch("app.routers.admin.BroadcastService") as MockSvc:
            MockSvc.return_value.create_broadcast.side_effect = Exception("boom")
            resp = client.post(
                "/admin/broadcasts",
                headers=_h(admin_token()),
                json={"title": "t", "message": "hello"},
            )
            assert resp.status_code == 500

    def test_create_success(self, client):
        with (
            patch("app.routers.admin.BroadcastService") as MockSvc,
            patch("app.routers.admin.send_broadcast_emails"),
        ):
            MockSvc.return_value.create_broadcast.return_value = {
                "broadcast_id": "b1",
                "title": "t",
            }
            resp = client.post(
                "/admin/broadcasts",
                headers=_h(admin_token()),
                json={"title": "t", "message": "hello", "link": "/x"},
            )
            assert resp.status_code == 201
            assert resp.json()["broadcast"]["broadcast_id"] == "b1"

    def test_list_success(self, client):
        with patch("app.routers.admin.BroadcastService") as MockSvc:
            MockSvc.return_value.get_all_broadcasts.return_value = [
                {"broadcast_id": "b1"}
            ]
            resp = client.get("/admin/broadcasts", headers=_h(admin_token()))
            assert resp.status_code == 200
            assert resp.json()["broadcasts"][0]["broadcast_id"] == "b1"

    def test_list_error_500(self, client):
        with patch("app.routers.admin.BroadcastService") as MockSvc:
            MockSvc.return_value.get_all_broadcasts.side_effect = Exception("x")
            resp = client.get("/admin/broadcasts", headers=_h(admin_token()))
            assert resp.status_code == 500

    def test_delete_success(self, client):
        with patch("app.routers.admin.BroadcastService") as MockSvc:
            MockSvc.return_value.delete_broadcast.return_value = True
            resp = client.delete(
                "/admin/broadcasts/b1", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            assert resp.json()["message"] == "Broadcast deleted"

    def test_delete_failure_500(self, client):
        with patch("app.routers.admin.BroadcastService") as MockSvc:
            MockSvc.return_value.delete_broadcast.return_value = False
            resp = client.delete(
                "/admin/broadcasts/b1", headers=_h(admin_token())
            )
            assert resp.status_code == 500

    def test_delete_non_admin_403(self, client):
        resp = client.delete("/admin/broadcasts/b1", headers=_h(plain_token()))
        assert resp.status_code == 403


# ===========================================================================
# Journey analytics
# ===========================================================================


class TestJourneyAnalytics:
    def test_non_admin_403(self, client):
        resp = client.get("/admin/journey-analytics", headers=_h(plain_token()))
        assert resp.status_code == 403

    def test_unauthenticated_401(self, client):
        assert client.get("/admin/journey-analytics").status_code == 401

    def test_success_empty(self, client):
        """No journey items — returns zeroed totals and 30-day timeline."""
        mock_client = MagicMock()
        # First scan: JOURNEY# items (empty). Second: membership scan (empty).
        mock_client.scan.side_effect = [
            {"Items": []},
            {"Items": []},
        ]
        with patch("app.routers.admin.boto3_mod.client", return_value=mock_client):
            resp = client.get(
                "/admin/journey-analytics", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["totals"]["journeys_started"] == 0
            assert data["totals"]["completion_rate"] == 0
            assert "phase_distribution" in data
            assert "task_completion_rates" in data

    def test_success_with_user(self, client):
        """A single started-but-incomplete journey is counted and placed in a phase."""
        now = datetime.now(timezone.utc)
        mock_client = MagicMock()
        mock_client.scan.side_effect = [
            {
                "Items": [
                    {
                        "PK": {"S": "USER#u1"},
                        "SK": {"S": "JOURNEY#_meta"},
                        "started_at": {"S": now.isoformat()},
                    },
                    {
                        "PK": {"S": "USER#u1"},
                        "SK": {"S": "JOURNEY#connect-discord"},
                        "completed_at": {"S": now.isoformat()},
                    },
                ]
            },
            {
                "Items": [
                    {
                        "PK": {"S": "USER#u1"},
                        "SK": {"S": "MEMBERSHIP"},
                        "membership_tier": {"S": "BUILDER"},
                        "subscription_status": {"S": "active"},
                    }
                ]
            },
        ]
        with patch("app.routers.admin.boto3_mod.client", return_value=mock_client):
            resp = client.get(
                "/admin/journey-analytics", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["totals"]["journeys_started"] == 1
            assert data["by_tier"]["BUILDER"]["journeys_started"] == 1
            assert data["key_rates"]["discord_connection_rate"] == 100.0

    def test_success_completed_journey(self, client):
        """A fully-completed BUILDER journey exercises the completion/duration path."""
        from app.config.journey_tasks import BUILDER_VALID_TASK_IDS

        start = datetime.now(timezone.utc) - timedelta(days=5)
        done = datetime.now(timezone.utc) - timedelta(days=1)
        items = [
            {
                "PK": {"S": "USER#u1"},
                "SK": {"S": "JOURNEY#_meta"},
                "started_at": {"S": start.isoformat()},
            }
        ]
        for task_id in BUILDER_VALID_TASK_IDS:
            items.append(
                {
                    "PK": {"S": "USER#u1"},
                    "SK": {"S": f"JOURNEY#{task_id}"},
                    "completed_at": {"S": done.isoformat()},
                }
            )
        mock_client = MagicMock()
        mock_client.scan.side_effect = [
            {"Items": items},
            {
                "Items": [
                    {
                        "PK": {"S": "USER#u1"},
                        "SK": {"S": "CONTRIBUTOR_ROLE"},
                    }
                ]
            },
        ]
        with patch("app.routers.admin.boto3_mod.client", return_value=mock_client):
            resp = client.get(
                "/admin/journey-analytics", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["totals"]["journeys_started"] == 1
            assert data["totals"]["journeys_completed"] == 1
            assert data["totals"]["completion_rate"] == 100.0
            # Contributor is treated as a BUILDER-tier journey
            assert data["by_tier"]["BUILDER"]["journeys_completed"] == 1
            assert data["totals"]["average_duration_days"] >= 1

    def test_membership_scan_error_handled(self, client):
        """A failing membership scan is caught; journey items still processed."""
        now = datetime.now(timezone.utc)
        mock_client = MagicMock()
        mock_client.scan.side_effect = [
            {
                "Items": [
                    {
                        "PK": {"S": "USER#u1"},
                        "SK": {"S": "JOURNEY#_meta"},
                        "started_at": {"S": now.isoformat()},
                    }
                ]
            },
            Exception("membership scan failed"),
        ]
        with patch("app.routers.admin.boto3_mod.client", return_value=mock_client):
            resp = client.get(
                "/admin/journey-analytics", headers=_h(admin_token())
            )
            assert resp.status_code == 200
            # User defaults to FREE tier since membership scan failed
            assert resp.json()["by_tier"]["FREE"]["journeys_started"] == 1

    def test_service_error_500(self, client):
        mock_client = MagicMock()
        mock_client.scan.side_effect = Exception("scan failed")
        with patch("app.routers.admin.boto3_mod.client", return_value=mock_client):
            resp = client.get(
                "/admin/journey-analytics", headers=_h(admin_token())
            )
            assert resp.status_code == 500
            assert resp.json()["detail"] == "Failed to fetch journey analytics"
