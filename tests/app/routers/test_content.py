"""Tests for the content router (app.routers.content).

Covers walkthrough progress, access tiers, quiz submission, testimonials
(user + admin moderation), notifications, and broadcast endpoints.

Service functions/classes are imported into the content router module, so
they are patched at the `app.routers.content.<name>` namespace.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import Settings
from app.main import app
from app.services.quiz_service import QuizNotFoundError, RegistryUnavailableError

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
    return _make_token({"sub": "admin-1", "github_login": "adminuser"})


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


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# GET /api/walkthroughs/{id}/progress
# ---------------------------------------------------------------------------


class TestGetWalkthroughProgress:
    def test_no_token_401(self, client, mock_auth):
        resp = client.get("/api/walkthroughs/wt1/progress")
        assert resp.status_code == 401

    def test_success(self, client, mock_auth):
        token = _make_token()
        prog = {"status": "completed", "started_at": "x", "completed_at": "y"}
        with patch("app.routers.content._get_progress", return_value=prog):
            resp = client.get("/api/walkthroughs/wt1/progress", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json() == {"progress": prog}

    def test_error_falls_back_to_not_started(self, client, mock_auth):
        """On service error the endpoint returns a default not_started progress."""
        token = _make_token()
        with patch(
            "app.routers.content._get_progress", side_effect=RuntimeError("boom")
        ):
            resp = client.get("/api/walkthroughs/wt1/progress", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["progress"]["status"] == "not_started"


# ---------------------------------------------------------------------------
# POST /api/walkthroughs/{id}/progress
# ---------------------------------------------------------------------------


class TestUpdateWalkthroughProgress:
    def test_empty_body_400(self, client, mock_auth):
        token = _make_token()
        resp = client.post(
            "/api/walkthroughs/wt1/progress", headers=_auth(token), content=b""
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid request"

    def test_missing_status_400(self, client, mock_auth):
        token = _make_token()
        resp = client.post(
            "/api/walkthroughs/wt1/progress", headers=_auth(token), json={}
        )
        assert resp.status_code == 400

    def test_invalid_json_400(self, client, mock_auth):
        token = _make_token()
        resp = client.post(
            "/api/walkthroughs/wt1/progress",
            headers={**_auth(token), "Content-Type": "application/json"},
            content=b"{not json",
        )
        assert resp.status_code == 400

    def test_free_walkthrough_success(self, client, mock_auth):
        """A FREE-tier walkthrough updates without a membership check."""
        token = _make_token()
        with (
            patch("app.routers.content.AdminService") as MockAdmin,
            patch("app.routers.content._update_progress") as mock_update,
        ):
            MockAdmin.return_value.get_walkthrough_access_tier.return_value = "FREE"
            resp = client.post(
                "/api/walkthroughs/wt1/progress",
                headers=_auth(token),
                json={"status": "completed"},
            )
        assert resp.status_code == 200
        assert resp.json() == {"message": "Progress updated successfully"}
        mock_update.assert_called_once_with("user-123", "wt1", "completed")

    def test_builder_locked_without_access_403(self, client, mock_auth):
        """BUILDER walkthrough + FREE user (no membership, no contributor) -> 403."""
        token = _make_token()
        with (
            patch("app.routers.content.AdminService") as MockAdmin,
            patch("app.routers.content.MembershipDB") as MockMembership,
            patch("app.routers.content.boto3.client") as mock_boto,
        ):
            MockAdmin.return_value.get_walkthrough_access_tier.return_value = "BUILDER"
            MockMembership.return_value.get_membership.return_value = None
            mock_boto.return_value.get_item.return_value = {}  # no contributor role
            resp = client.post(
                "/api/walkthroughs/wt1/progress",
                headers=_auth(token),
                json={"status": "completed"},
            )
        assert resp.status_code == 403
        assert "Builder" in resp.json()["detail"]

    def test_builder_with_membership_success(self, client, mock_auth):
        """BUILDER walkthrough + active BUILDER membership -> update succeeds."""
        token = _make_token()
        with (
            patch("app.routers.content.AdminService") as MockAdmin,
            patch("app.routers.content.MembershipDB") as MockMembership,
            patch("app.routers.content._update_progress") as mock_update,
        ):
            MockAdmin.return_value.get_walkthrough_access_tier.return_value = "BUILDER"
            MockMembership.return_value.get_membership.return_value = {
                "membership_tier": {"S": "BUILDER"},
                "subscription_status": {"S": "active"},
            }
            resp = client.post(
                "/api/walkthroughs/wt1/progress",
                headers=_auth(token),
                json={"status": "completed"},
            )
        assert resp.status_code == 200
        mock_update.assert_called_once()

    def test_admin_bypasses_builder_gate(self, client, mock_auth):
        """An admin user updates a BUILDER walkthrough without a membership check."""
        token = _make_admin_token()
        with (
            patch("app.routers.content.AdminService") as MockAdmin,
            patch("app.routers.content._update_progress") as mock_update,
        ):
            MockAdmin.return_value.get_walkthrough_access_tier.return_value = "BUILDER"
            resp = client.post(
                "/api/walkthroughs/wt1/progress",
                headers=_auth(token),
                json={"status": "completed"},
            )
        assert resp.status_code == 200
        mock_update.assert_called_once_with("admin-1", "wt1", "completed")

    def test_invalid_status_value_400(self, client, mock_auth):
        token = _make_token()
        with (
            patch("app.routers.content.AdminService") as MockAdmin,
            patch(
                "app.routers.content._update_progress",
                side_effect=ValueError("bad status"),
            ),
        ):
            MockAdmin.return_value.get_walkthrough_access_tier.return_value = "FREE"
            resp = client.post(
                "/api/walkthroughs/wt1/progress",
                headers=_auth(token),
                json={"status": "bogus"},
            )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid status value"

    def test_update_service_error_500(self, client, mock_auth):
        token = _make_token()
        with (
            patch("app.routers.content.AdminService") as MockAdmin,
            patch(
                "app.routers.content._update_progress",
                side_effect=RuntimeError("db down"),
            ),
        ):
            MockAdmin.return_value.get_walkthrough_access_tier.return_value = "FREE"
            resp = client.post(
                "/api/walkthroughs/wt1/progress",
                headers=_auth(token),
                json={"status": "completed"},
            )
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /api/walkthroughs/{id}/progress
# ---------------------------------------------------------------------------


class TestResetWalkthroughProgress:
    def test_success(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.content._reset_progress") as m:
            resp = client.delete("/api/walkthroughs/wt1/progress", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json() == {"message": "Walkthrough progress reset successfully"}
        m.assert_called_once_with("user-123", "wt1")

    def test_error_500(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.routers.content._reset_progress", side_effect=RuntimeError("boom")
        ):
            resp = client.delete("/api/walkthroughs/wt1/progress", headers=_auth(token))
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to reset progress"


# ---------------------------------------------------------------------------
# GET /api/walkthroughs/access-tiers
# ---------------------------------------------------------------------------


class TestAccessTiers:
    def test_success_only_locked(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.content.AdminService") as MockAdmin:
            MockAdmin.return_value.get_all_walkthrough_access_tiers.return_value = {
                "wt1": "BUILDER",
                "wt2": "FREE",
            }
            resp = client.get("/api/walkthroughs/access-tiers", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json() == {"access_tiers": {"wt1": "BUILDER"}}

    def test_error_returns_empty(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.content.AdminService") as MockAdmin:
            MockAdmin.return_value.get_all_walkthrough_access_tiers.side_effect = (
                RuntimeError("boom")
            )
            resp = client.get("/api/walkthroughs/access-tiers", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json() == {"access_tiers": {}}


# ---------------------------------------------------------------------------
# POST /quiz/submit
# ---------------------------------------------------------------------------


class TestQuizSubmit:
    def test_missing_fields_400(self, client, mock_auth):
        token = _make_token()
        resp = client.post("/quiz/submit", headers=_auth(token), json={})
        assert resp.status_code == 400

    def test_answers_not_dict_400(self, client, mock_auth):
        token = _make_token()
        resp = client.post(
            "/quiz/submit",
            headers=_auth(token),
            json={"module_id": "m1", "answers": ["a", "b"]},
        )
        assert resp.status_code == 400

    def test_invalid_json_400(self, client, mock_auth):
        token = _make_token()
        resp = client.post(
            "/quiz/submit",
            headers={**_auth(token), "Content-Type": "application/json"},
            content=b"{bad",
        )
        assert resp.status_code == 400

    def test_pass_success(self, client, mock_auth):
        token = _make_token()
        result = {"passed": True, "score": 100, "passing_score": 80}
        with patch("app.routers.content.submit_quiz", return_value=result):
            resp = client.post(
                "/quiz/submit",
                headers=_auth(token),
                json={"module_id": "m1", "answers": {"q1": "a"}},
            )
        assert resp.status_code == 200
        assert resp.json() == result

    def test_fail_success(self, client, mock_auth):
        """A failing quiz still returns 200 with passed=False."""
        token = _make_token()
        result = {"passed": False, "score": 40, "passing_score": 80}
        with patch("app.routers.content.submit_quiz", return_value=result):
            resp = client.post(
                "/quiz/submit",
                headers=_auth(token),
                json={"module_id": "m1", "answers": {"q1": "a"}},
            )
        assert resp.status_code == 200
        assert resp.json()["passed"] is False

    def test_quiz_not_found_404(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.routers.content.submit_quiz",
            side_effect=QuizNotFoundError("no such quiz"),
        ):
            resp = client.post(
                "/quiz/submit",
                headers=_auth(token),
                json={"module_id": "m1", "answers": {"q1": "a"}},
            )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "no such quiz"

    def test_registry_unavailable_503(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.routers.content.submit_quiz",
            side_effect=RegistryUnavailableError(),
        ):
            resp = client.post(
                "/quiz/submit",
                headers=_auth(token),
                json={"module_id": "m1", "answers": {"q1": "a"}},
            )
        assert resp.status_code == 503

    def test_value_error_400(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.routers.content.submit_quiz", side_effect=ValueError("bad answers")
        ):
            resp = client.post(
                "/quiz/submit",
                headers=_auth(token),
                json={"module_id": "m1", "answers": {"q1": "a"}},
            )
        assert resp.status_code == 400

    def test_generic_error_500(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.routers.content.submit_quiz", side_effect=RuntimeError("whoops")
        ):
            resp = client.post(
                "/quiz/submit",
                headers=_auth(token),
                json={"module_id": "m1", "answers": {"q1": "a"}},
            )
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/testimonials
# ---------------------------------------------------------------------------


class TestSubmitTestimonial:
    def test_validation_error_missing_name_and_quote_400(self, client, mock_auth):
        token = _make_token()
        resp = client.post(
            "/api/testimonials",
            headers=_auth(token),
            json={"display_name": "", "quote": ""},
        )
        assert resp.status_code == 400
        assert "Validation error" in resp.json()["detail"]

    def test_validation_bad_linkedin_400(self, client, mock_auth):
        token = _make_token()
        resp = client.post(
            "/api/testimonials",
            headers=_auth(token),
            json={
                "display_name": "Jane",
                "quote": "Loved it",
                "linkedin_url": "https://notlinkedin.com/jane",
            },
        )
        assert resp.status_code == 400
        assert "linkedin_url" in resp.json()["detail"]

    def test_validation_quote_too_long_400(self, client, mock_auth):
        token = _make_token()
        resp = client.post(
            "/api/testimonials",
            headers=_auth(token),
            json={"display_name": "Jane", "quote": "x" * 351},
        )
        assert resp.status_code == 400
        assert "quote exceeds" in resp.json()["detail"]

    def test_create_new_201(self, client, mock_auth):
        token = _make_token()
        record = {"user_id": "user-123", "status": "pending", "quote": "Great"}
        with (
            patch("app.routers.content.get_testimonial", return_value=None),
            patch(
                "app.routers.content.create_testimonial", return_value=record
            ) as mock_create,
            patch(
                "app.routers.content.send_testimonial_notification", return_value=True
            ),
        ):
            resp = client.post(
                "/api/testimonials",
                headers=_auth(token),
                json={
                    "display_name": "Jane",
                    "quote": "Great",
                    "linkedin_url": "https://www.linkedin.com/in/jane",
                },
            )
        assert resp.status_code == 201
        assert resp.json()["message"] == "Testimonial submitted successfully"
        assert resp.json()["testimonial"] == record
        mock_create.assert_called_once()

    def test_update_existing_pending_200(self, client, mock_auth):
        token = _make_token()
        updated = {"user_id": "user-123", "status": "pending", "quote": "Updated"}
        with (
            patch(
                "app.routers.content.get_testimonial",
                return_value={"status": "pending"},
            ),
            patch(
                "app.routers.content.update_testimonial", return_value=updated
            ) as mock_update,
            patch(
                "app.routers.content.send_testimonial_notification", return_value=True
            ),
        ):
            resp = client.post(
                "/api/testimonials",
                headers=_auth(token),
                json={"display_name": "Jane", "quote": "Updated"},
            )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Testimonial updated successfully"
        mock_update.assert_called_once()

    def test_already_approved_409(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.routers.content.get_testimonial",
            return_value={"status": "approved"},
        ):
            resp = client.post(
                "/api/testimonials",
                headers=_auth(token),
                json={"display_name": "Jane", "quote": "Great"},
            )
        assert resp.status_code == 409
        assert resp.json()["detail"] == "Testimonial already exists"

    def test_service_error_500(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.routers.content.get_testimonial", side_effect=RuntimeError("boom")
        ):
            resp = client.post(
                "/api/testimonials",
                headers=_auth(token),
                json={"display_name": "Jane", "quote": "Great"},
            )
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/testimonials/me
# ---------------------------------------------------------------------------


class TestGetMyTestimonial:
    def test_found(self, client, mock_auth):
        token = _make_token()
        record = {"user_id": "user-123", "status": "pending"}
        with patch("app.routers.content.get_testimonial", return_value=record):
            resp = client.get("/api/testimonials/me", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json() == {"testimonial": record}

    def test_not_found_404(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.content.get_testimonial", return_value=None):
            resp = client.get("/api/testimonials/me", headers=_auth(token))
        assert resp.status_code == 404
        assert resp.json()["detail"] == "No testimonial found"

    def test_error_500(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.routers.content.get_testimonial", side_effect=RuntimeError("boom")
        ):
            resp = client.get("/api/testimonials/me", headers=_auth(token))
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/testimonials/approved (public)
# ---------------------------------------------------------------------------


class TestApprovedTestimonials:
    def test_public_no_auth_success(self, client, mock_auth):
        approved = [
            {
                "user_id": "u1",
                "display_name": "Jane",
                "quote": "Great",
                "linkedin_url": "https://www.linkedin.com/in/jane",
            },
            {"user_id": "u2", "display_name": "", "quote": "skip me"},
        ]
        with (
            patch(
                "app.routers.content.get_testimonials_by_status",
                return_value=approved,
            ),
            patch("app.routers.content.boto3.client") as mock_boto,
        ):
            mock_boto.return_value.get_item.return_value = {
                "Item": {"avatar_url": {"S": "https://avatar/jane"}}
            }
            resp = client.get("/api/testimonials/approved")
        assert resp.status_code == 200
        testimonials = resp.json()["testimonials"]
        # Only the valid record (non-empty name+quote) is returned
        assert len(testimonials) == 1
        assert testimonials[0]["display_name"] == "Jane"
        assert testimonials[0]["avatar_url"] == "https://avatar/jane"
        assert "user_id" not in testimonials[0]

    def test_empty_list(self, client, mock_auth):
        with patch("app.routers.content.get_testimonials_by_status", return_value=[]):
            resp = client.get("/api/testimonials/approved")
        assert resp.status_code == 200
        assert resp.json() == {"testimonials": []}

    def test_error_500(self, client, mock_auth):
        with patch(
            "app.routers.content.get_testimonials_by_status",
            side_effect=RuntimeError("boom"),
        ):
            resp = client.get("/api/testimonials/approved")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/notifications  &  DELETE /api/notifications/{id}
# ---------------------------------------------------------------------------


class TestNotifications:
    def test_get_success(self, client, mock_auth):
        token = _make_token()
        notes = [{"id": "n1", "message": "hello"}]
        with patch("app.routers.content._get_notifications", return_value=notes):
            resp = client.get("/api/notifications", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json() == {"notifications": notes}

    def test_get_error_500(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.routers.content._get_notifications", side_effect=RuntimeError("boom")
        ):
            resp = client.get("/api/notifications", headers=_auth(token))
        assert resp.status_code == 500

    def test_delete_success(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.content._delete_notification") as m:
            resp = client.delete("/api/notifications/n1", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json() == {"message": "Notification deleted"}
        m.assert_called_once_with("user-123", "n1")

    def test_delete_error_500(self, client, mock_auth):
        token = _make_token()
        with patch(
            "app.routers.content._delete_notification",
            side_effect=RuntimeError("boom"),
        ):
            resp = client.delete("/api/notifications/n1", headers=_auth(token))
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /admin/testimonials  (admin only)
# ---------------------------------------------------------------------------


class TestAdminListTestimonials:
    def test_non_admin_403(self, client, mock_auth):
        token = _make_token()
        resp = client.get("/admin/testimonials", headers=_auth(token))
        assert resp.status_code == 403

    def test_list_all(self, client, mock_auth):
        token = _make_admin_token()
        items = [{"user_id": "u1"}, {"user_id": "u2"}]
        with patch("app.routers.content.get_all_testimonials", return_value=items):
            resp = client.get("/admin/testimonials", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json() == {"testimonials": items}

    def test_list_filtered_pending(self, client, mock_auth):
        token = _make_admin_token()
        items = [{"user_id": "u1", "status": "pending"}]
        with patch(
            "app.routers.content.get_testimonials_by_status", return_value=items
        ) as m:
            resp = client.get(
                "/admin/testimonials?status=pending", headers=_auth(token)
            )
        assert resp.status_code == 200
        assert resp.json() == {"testimonials": items}
        m.assert_called_once_with("pending")

    def test_invalid_filter_400(self, client, mock_auth):
        token = _make_admin_token()
        resp = client.get("/admin/testimonials?status=bogus", headers=_auth(token))
        assert resp.status_code == 400

    def test_error_500(self, client, mock_auth):
        token = _make_admin_token()
        with patch(
            "app.routers.content.get_all_testimonials",
            side_effect=RuntimeError("boom"),
        ):
            resp = client.get("/admin/testimonials", headers=_auth(token))
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# PUT /admin/testimonials/{id}/status  (admin moderation)
# ---------------------------------------------------------------------------


class TestAdminUpdateTestimonialStatus:
    def test_non_admin_403(self, client, mock_auth):
        token = _make_token()
        resp = client.put(
            "/admin/testimonials/u1/status",
            headers=_auth(token),
            json={"action": "approve"},
        )
        assert resp.status_code == 403

    def test_invalid_action_400(self, client, mock_auth):
        token = _make_admin_token()
        resp = client.put(
            "/admin/testimonials/u1/status",
            headers=_auth(token),
            json={"action": "nonsense"},
        )
        assert resp.status_code == 400

    def test_invalid_json_400(self, client, mock_auth):
        token = _make_admin_token()
        resp = client.put(
            "/admin/testimonials/u1/status",
            headers={**_auth(token), "Content-Type": "application/json"},
            content=b"{bad",
        )
        assert resp.status_code == 400

    def test_testimonial_not_found_404(self, client, mock_auth):
        token = _make_admin_token()
        with patch("app.routers.content.get_testimonial", return_value=None):
            resp = client.put(
                "/admin/testimonials/u1/status",
                headers=_auth(token),
                json={"action": "approve"},
            )
        assert resp.status_code == 404

    def test_approve_success(self, client, mock_auth):
        token = _make_admin_token()
        updated = {"user_id": "u1", "status": "approved"}
        with (
            patch(
                "app.routers.content.get_testimonial",
                return_value={"status": "pending"},
            ),
            patch("app.routers.content.update_testimonial", return_value=updated),
        ):
            resp = client.put(
                "/admin/testimonials/u1/status",
                headers=_auth(token),
                json={"action": "approve", "note": "ok"},
            )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Testimonial approved"
        assert resp.json()["testimonial"] == updated

    def test_approve_wrong_state_400(self, client, mock_auth):
        token = _make_admin_token()
        with patch(
            "app.routers.content.get_testimonial",
            return_value={"status": "approved"},
        ):
            resp = client.put(
                "/admin/testimonials/u1/status",
                headers=_auth(token),
                json={"action": "approve"},
            )
        assert resp.status_code == 400
        assert "Invalid status transition" in resp.json()["detail"]

    def test_reject_success(self, client, mock_auth):
        token = _make_admin_token()
        with (
            patch(
                "app.routers.content.get_testimonial",
                return_value={"status": "pending"},
            ),
            patch("app.routers.content.delete_testimonial") as mock_del,
        ):
            resp = client.put(
                "/admin/testimonials/u1/status",
                headers=_auth(token),
                json={"action": "reject"},
            )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Testimonial rejected and deleted"
        mock_del.assert_called_once_with("u1")

    def test_reject_wrong_state_400(self, client, mock_auth):
        token = _make_admin_token()
        with patch(
            "app.routers.content.get_testimonial",
            return_value={"status": "approved"},
        ):
            resp = client.put(
                "/admin/testimonials/u1/status",
                headers=_auth(token),
                json={"action": "reject"},
            )
        assert resp.status_code == 400

    def test_revoke_success(self, client, mock_auth):
        token = _make_admin_token()
        updated = {"user_id": "u1", "status": "pending"}
        with (
            patch(
                "app.routers.content.get_testimonial",
                return_value={"status": "approved"},
            ),
            patch("app.routers.content.update_testimonial", return_value=updated),
        ):
            resp = client.put(
                "/admin/testimonials/u1/status",
                headers=_auth(token),
                json={"action": "revoke"},
            )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Testimonial revoked to pending"

    def test_revoke_wrong_state_400(self, client, mock_auth):
        token = _make_admin_token()
        with patch(
            "app.routers.content.get_testimonial",
            return_value={"status": "pending"},
        ):
            resp = client.put(
                "/admin/testimonials/u1/status",
                headers=_auth(token),
                json={"action": "revoke"},
            )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Broadcast endpoints
# ---------------------------------------------------------------------------


class TestBroadcasts:
    def test_get_unread_success(self, client, mock_auth):
        token = _make_token()
        broadcasts = [{"broadcast_id": "b1", "message": "hi"}]
        with patch("app.routers.content.BroadcastService") as MockSvc:
            MockSvc.return_value.get_unread_broadcasts.return_value = broadcasts
            resp = client.get("/api/broadcasts/unread", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json() == {"broadcasts": broadcasts}

    def test_get_unread_error_returns_empty(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.content.BroadcastService") as MockSvc:
            MockSvc.return_value.get_unread_broadcasts.side_effect = RuntimeError("x")
            resp = client.get("/api/broadcasts/unread", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json() == {"broadcasts": []}

    def test_dismiss_success(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.content.BroadcastService") as MockSvc:
            MockSvc.return_value.dismiss_broadcast.return_value = None
            resp = client.post("/api/broadcasts/b1/dismiss", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json() == {"message": "Broadcast dismissed"}

    def test_dismiss_error_500(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.content.BroadcastService") as MockSvc:
            MockSvc.return_value.dismiss_broadcast.side_effect = RuntimeError("x")
            resp = client.post("/api/broadcasts/b1/dismiss", headers=_auth(token))
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to dismiss broadcast"

    def test_dismiss_all_success(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.content.BroadcastService") as MockSvc:
            inst = MockSvc.return_value
            inst.get_unread_broadcasts.return_value = [{"broadcast_id": "b1"}]
            inst.dismiss_all_broadcasts.return_value = True
            resp = client.post("/api/broadcasts/dismiss-all", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json() == {"message": "All broadcasts dismissed"}
        inst.dismiss_all_broadcasts.assert_called_once_with("user-123", ["b1"])

    def test_dismiss_all_none_unread(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.content.BroadcastService") as MockSvc:
            MockSvc.return_value.get_unread_broadcasts.return_value = []
            resp = client.post("/api/broadcasts/dismiss-all", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json() == {"message": "All broadcasts dismissed"}

    def test_dismiss_all_failure_500(self, client, mock_auth):
        token = _make_token()
        with patch("app.routers.content.BroadcastService") as MockSvc:
            inst = MockSvc.return_value
            inst.get_unread_broadcasts.return_value = [{"broadcast_id": "b1"}]
            inst.dismiss_all_broadcasts.return_value = False
            resp = client.post("/api/broadcasts/dismiss-all", headers=_auth(token))
        assert resp.status_code == 500
