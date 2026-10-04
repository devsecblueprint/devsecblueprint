"""Tests for the admin/reviewer certification router — /admin/certifications/*.

Covers stats, pathway management, candidate listing/detail, review outcome
recording (including credential issuance), grandfathering grant, revocation,
content uncompletion, and certificate preview. Exercises success paths plus
401 (unauthenticated), 403 (non-admin / non-reviewer), 404, and 400 branches.
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
    reviewer_users="github:revieweruser",
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


def reviewer_token():
    return _make_token("revieweruser")


def plain_token():
    return _make_token("plainuser")


def _h(token):
    return {"Authorization": f"Bearer {token}"}


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


def _eligibility(eligible, credential_id=None):
    """Build a stub EligibilityResult-like object with model_dump()."""
    obj = MagicMock()
    obj.eligible = eligible
    obj.credential_id = credential_id
    obj.model_dump.return_value = {
        "eligible": eligible,
        "blocking_reasons": [],
        "credential_id": credential_id,
    }
    return obj


def _credential(credential_id="cred-1"):
    """Build a stub Credential object with model_dump()."""
    obj = MagicMock()
    obj.credential_id = credential_id
    obj.full_name_at_issuance = "Jane Doe"
    obj.issued_at = "2026-01-01"
    obj.expires_at = "2027-01-01"
    obj.model_dump.return_value = {
        "credential_id": credential_id,
        "credential_status": "ACTIVE",
        "full_name_at_issuance": "Jane Doe",
    }
    return obj


# ---------------------------------------------------------------------------
# GET /admin/certifications/stats  (reviewer or admin)
# ---------------------------------------------------------------------------


class TestStats:
    def test_unauthenticated_401(self, client):
        assert client.get("/admin/certifications/stats").status_code == 401

    def test_non_reviewer_403(self, client):
        resp = client.get(
            "/admin/certifications/stats", headers=_h(plain_token())
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Forbidden"

    def test_reviewer_success(self, client):
        with patch("app.routers.certification_admin.CertificationDB") as MockDB:
            db = MockDB.return_value
            db.list_candidates.return_value = (
                [
                    {
                        "candidate_status": "IN_PROGRESS",
                        "review_gate": {"status": "PENDING_REVIEW"},
                    },
                    {
                        "candidate_status": "AWARDED",
                        "review_gate": {"status": "PASSED"},
                    },
                ],
                None,
            )
            db._dynamodb.scan.return_value = {
                "Items": [
                    {"credential_status": {"S": "ACTIVE"}},
                    {"credential_status": {"S": "REVOKED"}},
                ]
            }
            db._table_name = "test-table"

            resp = client.get(
                "/admin/certifications/stats", headers=_h(reviewer_token())
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["candidates_by_status"]["IN_PROGRESS"] == 1
            assert data["candidates_by_status"]["AWARDED"] == 1
            assert data["pending_reviews"] == 1
            assert data["credentials_by_status"]["ACTIVE"] == 1

    def test_admin_also_allowed(self, client):
        with patch("app.routers.certification_admin.CertificationDB") as MockDB:
            db = MockDB.return_value
            db.list_candidates.return_value = ([], None)
            db._dynamodb.scan.return_value = {"Items": []}
            db._table_name = "test-table"
            resp = client.get(
                "/admin/certifications/stats", headers=_h(admin_token())
            )
            assert resp.status_code == 200

    def test_candidate_and_credential_pagination(self, client):
        """Exercise multi-page candidate listing and credential scan pagination."""
        with patch("app.routers.certification_admin.CertificationDB") as MockDB:
            db = MockDB.return_value
            # Two pages of candidates: first returns a next_key, second ends it.
            db.list_candidates.side_effect = [
                (
                    [
                        {
                            "candidate_status": "IN_PROGRESS",
                            "review_gate": {"status": "PENDING_REVIEW"},
                        }
                    ],
                    {"last": "key"},
                ),
                (
                    [
                        {
                            "candidate_status": "AWARDED",
                            "review_gate": {"status": "PASSED"},
                        }
                    ],
                    None,
                ),
            ]
            # Two pages of credentials scan.
            db._dynamodb.scan.side_effect = [
                {
                    "Items": [{"credential_status": {"S": "ACTIVE"}}],
                    "LastEvaluatedKey": {"k": "v"},
                },
                {"Items": [{"credential_status": {"S": "EXPIRED"}}]},
            ]
            db._table_name = "test-table"

            resp = client.get(
                "/admin/certifications/stats", headers=_h(reviewer_token())
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["candidates_by_status"]["IN_PROGRESS"] == 1
            assert data["candidates_by_status"]["AWARDED"] == 1
            assert data["pending_reviews"] == 1
            assert data["credentials_by_status"]["ACTIVE"] == 1
            assert data["credentials_by_status"]["EXPIRED"] == 1

    def test_credentials_scan_error_handled(self, client):
        with patch("app.routers.certification_admin.CertificationDB") as MockDB:
            db = MockDB.return_value
            db.list_candidates.return_value = ([], None)
            db._dynamodb.scan.side_effect = Exception("boom")
            db._table_name = "test-table"
            resp = client.get(
                "/admin/certifications/stats", headers=_h(reviewer_token())
            )
            # Error is caught; credentials_by_status just stays empty
            assert resp.status_code == 200
            assert resp.json()["credentials_by_status"] == {}


# ---------------------------------------------------------------------------
# POST/PUT /admin/certifications/pathways  (admin only, disabled -> 400)
# ---------------------------------------------------------------------------


_PATHWAY_BODY = {
    "version": "v2",
    "display_name": "Name",
    "description": "desc",
    "capstone_content_id": "cap",
    "learning_requirements": ["a"],
}


class TestPathwayManagement:
    def test_create_pathway_non_admin_403(self, client):
        resp = client.post(
            "/admin/certifications/pathways?pathway_id=p1",
            headers=_h(reviewer_token()),
            json=_PATHWAY_BODY,
        )
        assert resp.status_code == 403

    def test_create_pathway_admin_disabled_400(self, client):
        resp = client.post(
            "/admin/certifications/pathways?pathway_id=p1",
            headers=_h(admin_token()),
            json=_PATHWAY_BODY,
        )
        assert resp.status_code == 400
        assert "managed in code" in resp.json()["detail"]

    def test_create_pathway_missing_query_422(self, client):
        resp = client.post(
            "/admin/certifications/pathways",
            headers=_h(admin_token()),
            json=_PATHWAY_BODY,
        )
        assert resp.status_code == 422

    def test_create_pathway_invalid_body_422(self, client):
        resp = client.post(
            "/admin/certifications/pathways?pathway_id=p1",
            headers=_h(admin_token()),
            json={"version": "v2"},
        )
        assert resp.status_code == 422

    def test_update_pathway_admin_disabled_400(self, client):
        resp = client.put(
            "/admin/certifications/pathways/p1",
            headers=_h(admin_token()),
            json=_PATHWAY_BODY,
        )
        assert resp.status_code == 400

    def test_update_pathway_non_admin_403(self, client):
        resp = client.put(
            "/admin/certifications/pathways/p1",
            headers=_h(reviewer_token()),
            json=_PATHWAY_BODY,
        )
        assert resp.status_code == 403

    def test_list_pathways_reviewer_success(self, client):
        with patch("app.routers.certification_admin.PathwayService") as MockSvc:
            pw = MagicMock()
            pw.model_dump.return_value = {"pathway_id": "p1"}
            MockSvc.return_value.list_pathways.return_value = [pw]
            resp = client.get(
                "/admin/certifications/pathways", headers=_h(reviewer_token())
            )
            assert resp.status_code == 200
            assert resp.json() == [{"pathway_id": "p1"}]

    def test_list_pathways_unauthenticated_401(self, client):
        assert client.get("/admin/certifications/pathways").status_code == 401

    def test_get_pathway_versions_success(self, client):
        with patch("app.routers.certification_admin.PathwayService") as MockSvc:
            v = MagicMock()
            v.model_dump.return_value = {"version": "v1"}
            MockSvc.return_value.get_pathway_versions.return_value = [v]
            resp = client.get(
                "/admin/certifications/pathways/p1", headers=_h(reviewer_token())
            )
            assert resp.status_code == 200
            assert resp.json() == [{"version": "v1"}]

    def test_get_pathway_versions_value_error_400(self, client):
        with patch("app.routers.certification_admin.PathwayService") as MockSvc:
            MockSvc.return_value.get_pathway_versions.side_effect = ValueError(
                "unknown pathway"
            )
            resp = client.get(
                "/admin/certifications/pathways/p1", headers=_h(reviewer_token())
            )
            assert resp.status_code == 400
            assert resp.json()["detail"] == "unknown pathway"


# ---------------------------------------------------------------------------
# GET /admin/certifications/candidates  (reviewer or admin)
# ---------------------------------------------------------------------------


class TestListCandidates:
    def test_non_reviewer_403(self, client):
        resp = client.get(
            "/admin/certifications/candidates", headers=_h(plain_token())
        )
        assert resp.status_code == 403

    def test_success_enriches_candidates(self, client):
        with (
            patch("app.routers.certification_admin.CertificationDB") as MockDB,
            patch(
                "app.routers.certification_admin.get_pathway_config"
            ) as mock_pw,
        ):
            db = MockDB.return_value
            db.list_candidates.return_value = (
                [
                    {
                        "user_id": "u1",
                        "pathway_id": "devsecops-engineering",
                        "candidate_status": "IN_PROGRESS",
                        "review_gate": {"status": "PENDING_REVIEW"},
                        "updated_at": "2026-01-01",
                    }
                ],
                {"last": "key"},
            )
            db.get_user_full_name.return_value = "Jane Doe"
            db.get_user_username.return_value = "jane"
            mock_pw.return_value = {"display_name": "DevSecOps Engineering"}

            resp = client.get(
                "/admin/certifications/candidates", headers=_h(reviewer_token())
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["has_more"] is True
            assert data["candidates"][0]["display_name"] == "Jane Doe"
            assert (
                data["candidates"][0]["pathway_display_name"]
                == "DevSecOps Engineering"
            )
            assert data["candidates"][0]["review_session_status"] == "PENDING_REVIEW"

    def test_falls_back_to_username_then_id(self, client):
        with (
            patch("app.routers.certification_admin.CertificationDB") as MockDB,
            patch(
                "app.routers.certification_admin.get_pathway_config"
            ) as mock_pw,
        ):
            db = MockDB.return_value
            db.list_candidates.return_value = (
                [
                    {
                        "user_id": "abcdef123456",
                        "pathway_id": "",
                        "candidate_status": "IN_PROGRESS",
                        "review_gate": {},
                    }
                ],
                None,
            )
            db.get_user_full_name.return_value = None
            db.get_user_username.return_value = None
            mock_pw.return_value = None

            resp = client.get(
                "/admin/certifications/candidates", headers=_h(reviewer_token())
            )
            assert resp.status_code == 200
            data = resp.json()
            # display name falls back to first 8 chars of user_id
            assert data["candidates"][0]["display_name"] == "abcdef12"
            assert data["candidates"][0]["review_session_status"] == "PENDING_SUBMISSION"

    def test_invalid_limit_422(self, client):
        resp = client.get(
            "/admin/certifications/candidates?limit=500",
            headers=_h(reviewer_token()),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /admin/certifications/candidates/{user_id}/{pathway_id}
# ---------------------------------------------------------------------------


class TestCandidateDetail:
    def test_non_reviewer_403(self, client):
        resp = client.get(
            "/admin/certifications/candidates/u1/p1", headers=_h(plain_token())
        )
        assert resp.status_code == 403

    def test_not_found_404(self, client):
        with patch("app.routers.certification_admin.CertificationDB") as MockDB:
            MockDB.return_value.get_candidate_record.return_value = None
            resp = client.get(
                "/admin/certifications/candidates/u1/p1",
                headers=_h(reviewer_token()),
            )
            assert resp.status_code == 404
            assert resp.json()["detail"] == "Candidate not found"

    def test_success_with_credential(self, client):
        with patch("app.routers.certification_admin.CertificationDB") as MockDB:
            db = MockDB.return_value
            db.get_candidate_record.return_value = {
                "candidate_status": "AWARDED",
                "credential_id": "cred-1",
            }
            db.get_review_history.return_value = [{"revision_number": 1}]
            db.get_credential.return_value = {"credential_id": "cred-1"}
            resp = client.get(
                "/admin/certifications/candidates/u1/p1",
                headers=_h(reviewer_token()),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["candidate"]["candidate_status"] == "AWARDED"
            assert data["credential"]["credential_id"] == "cred-1"
            assert len(data["review_history"]) == 1

    def test_success_without_credential(self, client):
        with patch("app.routers.certification_admin.CertificationDB") as MockDB:
            db = MockDB.return_value
            db.get_candidate_record.return_value = {"candidate_status": "IN_PROGRESS"}
            db.get_review_history.return_value = []
            resp = client.get(
                "/admin/certifications/candidates/u1/p1",
                headers=_h(reviewer_token()),
            )
            assert resp.status_code == 200
            assert resp.json()["credential"] is None


# ---------------------------------------------------------------------------
# POST /admin/certifications/candidates/{u}/{p}/review-outcome
# ---------------------------------------------------------------------------


_REVIEW_BODY = {
    "status": "PASSED",
    "rubric_scores": {"dim1": {"score": 5, "comment": "good"}},
    "evaluation_dimensions": {"dim1": "excellent"},
    "reviewer_notes": "well done",
}


class TestReviewOutcome:
    def test_non_reviewer_403(self, client):
        resp = client.post(
            "/admin/certifications/candidates/u1/p1/review-outcome",
            headers=_h(plain_token()),
            json=_REVIEW_BODY,
        )
        assert resp.status_code == 403

    def test_invalid_body_422(self, client):
        resp = client.post(
            "/admin/certifications/candidates/u1/p1/review-outcome",
            headers=_h(reviewer_token()),
            json={"status": "PASSED"},
        )
        assert resp.status_code == 422

    def test_value_error_400(self, client):
        with patch(
            "app.routers.certification_admin.ReviewSessionService"
        ) as MockSvc:
            MockSvc.return_value.record_review_outcome.side_effect = ValueError(
                "no pending session"
            )
            resp = client.post(
                "/admin/certifications/candidates/u1/p1/review-outcome",
                headers=_h(reviewer_token()),
                json=_REVIEW_BODY,
            )
            assert resp.status_code == 400
            assert resp.json()["detail"] == "no pending session"

    def test_not_eligible_records_review(self, client):
        with patch(
            "app.routers.certification_admin.ReviewSessionService"
        ) as MockSvc:
            MockSvc.return_value.record_review_outcome.return_value = _eligibility(
                False
            )
            resp = client.post(
                "/admin/certifications/candidates/u1/p1/review-outcome",
                headers=_h(reviewer_token()),
                json=_REVIEW_BODY,
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "review_recorded"

    def test_eligibility_none_records_review(self, client):
        with patch(
            "app.routers.certification_admin.ReviewSessionService"
        ) as MockSvc:
            MockSvc.return_value.record_review_outcome.return_value = None
            resp = client.post(
                "/admin/certifications/candidates/u1/p1/review-outcome",
                headers=_h(reviewer_token()),
                json=_REVIEW_BODY,
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "review_recorded"
            assert resp.json()["eligibility"] is None

    def test_eligible_already_awarded_idempotent(self, client):
        with patch(
            "app.routers.certification_admin.ReviewSessionService"
        ) as MockSvc:
            MockSvc.return_value.record_review_outcome.return_value = _eligibility(
                True, credential_id="existing-cred"
            )
            resp = client.post(
                "/admin/certifications/candidates/u1/p1/review-outcome",
                headers=_h(reviewer_token()),
                json=_REVIEW_BODY,
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "already_awarded"
            assert resp.json()["credential_id"] == "existing-cred"

    def test_eligible_issues_credential(self, client):
        with (
            patch(
                "app.routers.certification_admin.ReviewSessionService"
            ) as MockReview,
            patch("app.routers.certification_admin.CertificationDB") as MockDB,
            patch(
                "app.routers.certification_admin.get_pathway_config"
            ) as mock_pw,
            patch(
                "app.routers.certification_admin.CredentialLifecycleService"
            ) as MockCred,
            patch(
                "app.routers.certification_admin.CertificateGenerator"
            ) as MockGen,
            patch(
                "app.routers.certification_admin.send_credential_issued_notification"
            ) as mock_email,
            patch(
                "app.routers.certification_admin.CompletionistService"
            ) as MockComp,
        ):
            MockReview.return_value.record_review_outcome.return_value = _eligibility(
                True, credential_id=None
            )
            db = MockDB.return_value
            db.get_candidate_record.return_value = {"prior_credential_id": None}
            db.get_user_email.return_value = "jane@example.com"
            db.get_user_username.return_value = "jane"
            mock_pw.return_value = {
                "version": "v1",
                "display_name": "DevSecOps Engineering",
                "description": "desc",
            }
            MockCred.return_value.issue_credential.return_value = _credential("cred-1")
            MockGen.return_value.generate.return_value = "s3/key.png"

            resp = client.post(
                "/admin/certifications/candidates/u1/p1/review-outcome",
                headers=_h(reviewer_token()),
                json=_REVIEW_BODY,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "credential_issued"
            assert data["credential_id"] == "cred-1"
            mock_email.assert_called_once()
            MockComp.return_value.evaluate.assert_called_once_with("u1")
            db.update_certificate_s3_key.assert_called_once()

    def test_eligible_issue_no_email_skips_notification(self, client):
        with (
            patch(
                "app.routers.certification_admin.ReviewSessionService"
            ) as MockReview,
            patch("app.routers.certification_admin.CertificationDB") as MockDB,
            patch(
                "app.routers.certification_admin.get_pathway_config"
            ) as mock_pw,
            patch(
                "app.routers.certification_admin.CredentialLifecycleService"
            ) as MockCred,
            patch(
                "app.routers.certification_admin.CertificateGenerator"
            ) as MockGen,
            patch(
                "app.routers.certification_admin.send_credential_issued_notification"
            ) as mock_email,
            patch(
                "app.routers.certification_admin.CompletionistService"
            ) as MockComp,
        ):
            MockReview.return_value.record_review_outcome.return_value = _eligibility(
                True, credential_id=None
            )
            db = MockDB.return_value
            db.get_candidate_record.return_value = {
                "prior_credential_id": "old-cred"
            }
            db.get_user_email.return_value = None
            mock_pw.return_value = {
                "version": "v1",
                "display_name": "DevSecOps",
                "description": "",
            }
            MockCred.return_value.issue_credential.return_value = _credential("cred-2")
            MockGen.return_value.generate.return_value = None  # no s3 key

            resp = client.post(
                "/admin/certifications/candidates/u1/p1/review-outcome",
                headers=_h(reviewer_token()),
                json=_REVIEW_BODY,
            )
            assert resp.status_code == 200
            assert resp.json()["credential_id"] == "cred-2"
            mock_email.assert_not_called()
            db.update_certificate_s3_key.assert_not_called()

    def test_eligible_issue_value_error_400(self, client):
        with (
            patch(
                "app.routers.certification_admin.ReviewSessionService"
            ) as MockReview,
            patch("app.routers.certification_admin.CertificationDB") as MockDB,
            patch(
                "app.routers.certification_admin.get_pathway_config"
            ) as mock_pw,
            patch(
                "app.routers.certification_admin.CredentialLifecycleService"
            ) as MockCred,
        ):
            MockReview.return_value.record_review_outcome.return_value = _eligibility(
                True, credential_id=None
            )
            MockDB.return_value.get_candidate_record.return_value = {}
            mock_pw.return_value = None
            MockCred.return_value.issue_credential.side_effect = ValueError(
                "missing full name"
            )
            resp = client.post(
                "/admin/certifications/candidates/u1/p1/review-outcome",
                headers=_h(reviewer_token()),
                json=_REVIEW_BODY,
            )
            assert resp.status_code == 400
            assert resp.json()["detail"] == "missing full name"


# ---------------------------------------------------------------------------
# POST /admin/certifications/candidates/{u}/{p}/grant  (admin only)
# ---------------------------------------------------------------------------


class TestGrantCredential:
    def test_non_admin_403(self, client):
        resp = client.post(
            "/admin/certifications/candidates/u1/p1/grant",
            headers=_h(reviewer_token()),
        )
        assert resp.status_code == 403

    def test_value_error_400(self, client):
        with patch(
            "app.routers.certification_admin.CredentialLifecycleService"
        ) as MockCred:
            MockCred.return_value.grant_credential.side_effect = ValueError(
                "no full name"
            )
            resp = client.post(
                "/admin/certifications/candidates/u1/p1/grant",
                headers=_h(admin_token()),
            )
            assert resp.status_code == 400
            assert resp.json()["detail"] == "no full name"

    def test_success(self, client):
        with (
            patch(
                "app.routers.certification_admin.CredentialLifecycleService"
            ) as MockCred,
            patch("app.routers.certification_admin.CertificationDB") as MockDB,
            patch(
                "app.routers.certification_admin.get_pathway_config"
            ) as mock_pw,
            patch(
                "app.routers.certification_admin.CertificateGenerator"
            ) as MockGen,
            patch(
                "app.routers.certification_admin.send_credential_issued_notification"
            ) as mock_email,
            patch(
                "app.routers.certification_admin.CompletionistService"
            ) as MockComp,
        ):
            MockCred.return_value.grant_credential.return_value = _credential("cred-g")
            db = MockDB.return_value
            db.get_user_email.return_value = "jane@example.com"
            db.get_user_username.return_value = "jane"
            mock_pw.return_value = {
                "display_name": "DevSecOps Engineering",
                "description": "desc",
            }
            MockGen.return_value.generate.return_value = "s3/key.png"

            resp = client.post(
                "/admin/certifications/candidates/u1/p1/grant",
                headers=_h(admin_token()),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "credential_granted"
            assert data["credential_id"] == "cred-g"
            mock_email.assert_called_once()
            MockComp.return_value.evaluate.assert_called_once_with("u1")


# ---------------------------------------------------------------------------
# POST /admin/certifications/credentials/{id}/revoke  (admin only)
# ---------------------------------------------------------------------------


class TestRevokeCredential:
    def test_non_admin_403(self, client):
        resp = client.post(
            "/admin/certifications/credentials/cred-1/revoke",
            headers=_h(reviewer_token()),
            json={"reason": "fraud detected here"},
        )
        assert resp.status_code == 403

    def test_short_reason_422(self, client):
        resp = client.post(
            "/admin/certifications/credentials/cred-1/revoke",
            headers=_h(admin_token()),
            json={"reason": "no"},
        )
        assert resp.status_code == 422

    def test_value_error_400(self, client):
        with patch(
            "app.routers.certification_admin.CredentialLifecycleService"
        ) as MockCred:
            MockCred.return_value.revoke_credential.side_effect = ValueError(
                "already revoked"
            )
            resp = client.post(
                "/admin/certifications/credentials/cred-1/revoke",
                headers=_h(admin_token()),
                json={"reason": "fraud detected here"},
            )
            assert resp.status_code == 400
            assert resp.json()["detail"] == "already revoked"

    def test_success_triggers_completionist(self, client):
        with (
            patch(
                "app.routers.certification_admin.CredentialLifecycleService"
            ) as MockCred,
            patch("app.routers.certification_admin.CertificationDB") as MockDB,
            patch(
                "app.routers.certification_admin.CompletionistService"
            ) as MockComp,
        ):
            MockCred.return_value.revoke_credential.return_value = _credential("cred-1")
            MockDB.return_value.get_credential_by_id.return_value = {"user_id": "u1"}
            resp = client.post(
                "/admin/certifications/credentials/cred-1/revoke",
                headers=_h(admin_token()),
                json={"reason": "fraud detected here"},
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "credential_revoked"
            MockComp.return_value.evaluate.assert_called_once_with("u1")

    def test_success_no_user_lookup_skips_completionist(self, client):
        with (
            patch(
                "app.routers.certification_admin.CredentialLifecycleService"
            ) as MockCred,
            patch("app.routers.certification_admin.CertificationDB") as MockDB,
            patch(
                "app.routers.certification_admin.CompletionistService"
            ) as MockComp,
        ):
            MockCred.return_value.revoke_credential.return_value = _credential("cred-1")
            MockDB.return_value.get_credential_by_id.return_value = None
            resp = client.post(
                "/admin/certifications/credentials/cred-1/revoke",
                headers=_h(admin_token()),
                json={"reason": "fraud detected here"},
            )
            assert resp.status_code == 200
            MockComp.return_value.evaluate.assert_not_called()


# ---------------------------------------------------------------------------
# POST /admin/certifications/candidates/{u}/uncomplete-content  (admin only)
# ---------------------------------------------------------------------------


class TestUncompleteContent:
    def test_non_admin_403(self, client):
        resp = client.post(
            "/admin/certifications/candidates/u1/uncomplete-content?content_id=c1",
            headers=_h(reviewer_token()),
        )
        assert resp.status_code == 403

    def test_missing_content_id_422(self, client):
        resp = client.post(
            "/admin/certifications/candidates/u1/uncomplete-content",
            headers=_h(admin_token()),
        )
        assert resp.status_code == 422

    def test_success(self, client):
        with patch("app.routers.certification_admin.ProgressDB") as MockDB:
            MockDB.return_value.delete_progress.return_value = None
            resp = client.post(
                "/admin/certifications/candidates/u1/uncomplete-content?content_id=c1",
                headers=_h(admin_token()),
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "uncompleted"
            assert resp.json()["content_id"] == "c1"

    def test_delete_error_500(self, client):
        with patch("app.routers.certification_admin.ProgressDB") as MockDB:
            MockDB.return_value.delete_progress.side_effect = Exception("db error")
            resp = client.post(
                "/admin/certifications/candidates/u1/uncomplete-content?content_id=c1",
                headers=_h(admin_token()),
            )
            assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /admin/certifications/credentials/{id}/preview  (admin only)
# ---------------------------------------------------------------------------


class TestAdminPreviewCertificate:
    def test_non_admin_403(self, client):
        resp = client.get(
            "/admin/certifications/credentials/cred-1/preview",
            headers=_h(reviewer_token()),
        )
        assert resp.status_code == 403

    def test_not_found_404(self, client):
        with patch("app.routers.certification_admin.CertificationDB") as MockDB:
            MockDB.return_value.get_credential_by_id.return_value = None
            resp = client.get(
                "/admin/certifications/credentials/cred-1/preview",
                headers=_h(admin_token()),
            )
            assert resp.status_code == 404

    def test_success(self, client):
        with (
            patch("app.routers.certification_admin.CertificationDB") as MockDB,
            patch(
                "app.routers.certification_admin.get_pathway_config"
            ) as mock_pw,
            patch(
                "app.routers.certification_admin.CertificateGenerator"
            ) as MockGen,
        ):
            MockDB.return_value.get_credential_by_id.return_value = {
                "credential_id": "cred-1",
                "pathway_id": "devsecops-engineering",
                "full_name_at_issuance": "Jane Doe",
                "issued_at": "2026-01-01",
                "expires_at": "2027-01-01",
            }
            mock_pw.return_value = {
                "display_name": "DevSecOps Engineering",
                "description": "desc",
            }
            MockGen.return_value.generate_svg_content.return_value = (
                "https://s3.example.com/cert.png?signed"
            )
            resp = client.get(
                "/admin/certifications/credentials/cred-1/preview",
                headers=_h(admin_token()),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["preview_url"].startswith("https://s3.example.com")
            assert data["credential_id"] == "cred-1"
            assert data["full_name"] == "Jane Doe"

    def test_generation_failure_500(self, client):
        with (
            patch("app.routers.certification_admin.CertificationDB") as MockDB,
            patch(
                "app.routers.certification_admin.get_pathway_config"
            ) as mock_pw,
            patch(
                "app.routers.certification_admin.CertificateGenerator"
            ) as MockGen,
        ):
            MockDB.return_value.get_credential_by_id.return_value = {
                "credential_id": "cred-1",
                "pathway_id": "p1",
                "full_name_at_issuance": "Jane Doe",
                "issued_at": "2026-01-01",
                "expires_at": "2027-01-01",
            }
            mock_pw.return_value = None
            MockGen.return_value.generate_svg_content.return_value = None
            resp = client.get(
                "/admin/certifications/credentials/cred-1/preview",
                headers=_h(admin_token()),
            )
            assert resp.status_code == 500
