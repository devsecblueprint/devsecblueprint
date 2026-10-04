"""Tests for the learner-facing certification router — /certifications/* endpoints.

Covers listing pathways with status, candidate record retrieval, enrollment,
review history, capstone submission, credential retrieval, certificate preview,
and certificate download. Exercises success paths plus 401/404/400/500 branches.
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


def _make_token(claims: dict | None = None) -> str:
    """Create a valid JWT token for testing."""
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


@pytest.fixture
def client():
    from app.dependencies import get_settings as dep_get_settings

    app.dependency_overrides[dep_get_settings] = lambda: TEST_SETTINGS
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_auth():
    """Prime the JWT secret cache so no boto3 call is needed for auth."""
    from app.auth.jwt import _jwt_secret_cache

    _jwt_secret_cache["secret_key"] = TEST_SECRET_KEY
    _jwt_secret_cache["fetched_at"] = 9999999999.0
    yield
    _jwt_secret_cache["secret_key"] = None
    _jwt_secret_cache["fetched_at"] = 0.0


def _pathway_obj(pathway_id="devsecops-engineering"):
    """Build a simple object mimicking a PathwayDefinition for list_pathways."""
    obj = MagicMock()
    obj.pathway_id = pathway_id
    obj.display_name = "DevSecOps Engineering"
    obj.description = "A pathway"
    obj.version = "v1"
    return obj


AUTH = {"Authorization": None}


def _h(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# GET /certifications
# ---------------------------------------------------------------------------


class TestListPathwaysWithStatus:
    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/certifications")
        assert resp.status_code == 401

    def test_success_not_started_when_no_candidate(self, client):
        token = _make_token()
        with (
            patch("app.routers.certification.PathwayService") as MockPathway,
            patch("app.routers.certification.CertificationDB") as MockDB,
        ):
            MockPathway.return_value.list_pathways.return_value = [_pathway_obj()]
            MockDB.return_value.get_candidate_record.return_value = None

            resp = client.get("/certifications", headers=_h(token))
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["pathway_id"] == "devsecops-engineering"
            assert data[0]["candidate_status"] == "NOT_STARTED"

    def test_success_uses_candidate_status(self, client):
        token = _make_token()
        with (
            patch("app.routers.certification.PathwayService") as MockPathway,
            patch("app.routers.certification.CertificationDB") as MockDB,
        ):
            MockPathway.return_value.list_pathways.return_value = [_pathway_obj()]
            MockDB.return_value.get_candidate_record.return_value = {
                "candidate_status": "IN_PROGRESS"
            }

            resp = client.get("/certifications", headers=_h(token))
            assert resp.status_code == 200
            assert resp.json()[0]["candidate_status"] == "IN_PROGRESS"


# ---------------------------------------------------------------------------
# GET /certifications/{pathway_id}
# ---------------------------------------------------------------------------


class TestGetCandidateRecord:
    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/certifications/devsecops-engineering")
        assert resp.status_code == 401

    def test_success(self, client):
        token = _make_token()
        with patch("app.routers.certification.CertificationDB") as MockDB:
            MockDB.return_value.get_candidate_record.return_value = {
                "pathway_id": "devsecops-engineering",
                "candidate_status": "IN_PROGRESS",
            }
            resp = client.get("/certifications/devsecops-engineering", headers=_h(token))
            assert resp.status_code == 200
            assert resp.json()["candidate_status"] == "IN_PROGRESS"

    def test_not_found_returns_404(self, client):
        token = _make_token()
        with patch("app.routers.certification.CertificationDB") as MockDB:
            MockDB.return_value.get_candidate_record.return_value = None
            resp = client.get("/certifications/unknown", headers=_h(token))
            assert resp.status_code == 404
            assert "No candidate record" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# POST /certifications/{pathway_id}/enroll
# ---------------------------------------------------------------------------


class TestEnroll:
    def test_unauthenticated_returns_401(self, client):
        resp = client.post("/certifications/devsecops-engineering/enroll")
        assert resp.status_code == 401

    def test_success_creates_candidate(self, client):
        token = _make_token()
        with patch("app.routers.certification.CertificationDB") as MockDB:
            db = MockDB.return_value
            db.get_candidate_record.return_value = None
            db.get_active_pathway.return_value = {"version": "v1"}
            db.put_candidate_record.return_value = None

            resp = client.post(
                "/certifications/devsecops-engineering/enroll", headers=_h(token)
            )
            assert resp.status_code == 201
            data = resp.json()
            assert data["pathway_id"] == "devsecops-engineering"
            assert data["candidate_status"] == "IN_PROGRESS"
            assert data["review_gate"]["status"] == "PENDING_SUBMISSION"
            db.put_candidate_record.assert_called_once()

    def test_already_enrolled_returns_409(self, client):
        token = _make_token()
        with patch("app.routers.certification.CertificationDB") as MockDB:
            MockDB.return_value.get_candidate_record.return_value = {
                "candidate_status": "IN_PROGRESS"
            }
            resp = client.post(
                "/certifications/devsecops-engineering/enroll", headers=_h(token)
            )
            assert resp.status_code == 409
            assert "Already enrolled" in resp.json()["detail"]

    def test_unknown_pathway_returns_404(self, client):
        token = _make_token()
        with patch("app.routers.certification.CertificationDB") as MockDB:
            db = MockDB.return_value
            db.get_candidate_record.return_value = None
            db.get_active_pathway.return_value = None
            resp = client.post("/certifications/unknown/enroll", headers=_h(token))
            assert resp.status_code == 404
            assert "not found" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# GET /certifications/{pathway_id}/reviews
# ---------------------------------------------------------------------------


class TestReviewHistory:
    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/certifications/devsecops-engineering/reviews")
        assert resp.status_code == 401

    def test_success(self, client):
        token = _make_token()
        with patch("app.routers.certification.ReviewSessionService") as MockSvc:
            MockSvc.return_value.get_revision_history.return_value = [
                {"revision_number": 1, "status": "PASSED"}
            ]
            resp = client.get(
                "/certifications/devsecops-engineering/reviews", headers=_h(token)
            )
            assert resp.status_code == 200
            assert resp.json()[0]["revision_number"] == 1


# ---------------------------------------------------------------------------
# POST /certifications/{pathway_id}/submit
# ---------------------------------------------------------------------------


class TestSubmitCapstone:
    def test_unauthenticated_returns_401(self, client):
        resp = client.post(
            "/certifications/devsecops-engineering/submit",
            json={"submission_url": "https://github.com/x/y"},
        )
        assert resp.status_code == 401

    def test_success(self, client):
        token = _make_token()
        with patch("app.routers.certification.ReviewSessionService") as MockSvc:
            MockSvc.return_value.submit_capstone.return_value = {
                "revision_number": 1,
                "status": "PENDING_REVIEW",
            }
            resp = client.post(
                "/certifications/devsecops-engineering/submit",
                headers=_h(token),
                json={"submission_url": "https://github.com/x/y"},
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "PENDING_REVIEW"

    def test_missing_url_returns_422(self, client):
        token = _make_token()
        resp = client.post(
            "/certifications/devsecops-engineering/submit",
            headers=_h(token),
            json={},
        )
        assert resp.status_code == 422

    def test_empty_url_returns_422(self, client):
        token = _make_token()
        resp = client.post(
            "/certifications/devsecops-engineering/submit",
            headers=_h(token),
            json={"submission_url": ""},
        )
        assert resp.status_code == 422

    def test_value_error_returns_400(self, client):
        token = _make_token()
        with patch("app.routers.certification.ReviewSessionService") as MockSvc:
            MockSvc.return_value.submit_capstone.side_effect = ValueError(
                "Not enrolled"
            )
            resp = client.post(
                "/certifications/devsecops-engineering/submit",
                headers=_h(token),
                json={"submission_url": "https://github.com/x/y"},
            )
            assert resp.status_code == 400
            assert resp.json()["detail"] == "Not enrolled"


# ---------------------------------------------------------------------------
# GET /certifications/{pathway_id}/credential
# ---------------------------------------------------------------------------


class TestGetCredential:
    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/certifications/devsecops-engineering/credential")
        assert resp.status_code == 401

    def test_success(self, client):
        token = _make_token()
        with patch("app.routers.certification.CertificationDB") as MockDB:
            db = MockDB.return_value
            db.get_candidate_record.return_value = {"credential_id": "cred-1"}
            db.get_credential.return_value = {
                "credential_id": "cred-1",
                "credential_status": "ACTIVE",
            }
            resp = client.get(
                "/certifications/devsecops-engineering/credential", headers=_h(token)
            )
            assert resp.status_code == 200
            assert resp.json()["credential_id"] == "cred-1"

    def test_no_candidate_returns_404(self, client):
        token = _make_token()
        with patch("app.routers.certification.CertificationDB") as MockDB:
            MockDB.return_value.get_candidate_record.return_value = None
            resp = client.get(
                "/certifications/devsecops-engineering/credential", headers=_h(token)
            )
            assert resp.status_code == 404

    def test_candidate_without_credential_id_returns_404(self, client):
        token = _make_token()
        with patch("app.routers.certification.CertificationDB") as MockDB:
            MockDB.return_value.get_candidate_record.return_value = {
                "candidate_status": "IN_PROGRESS"
            }
            resp = client.get(
                "/certifications/devsecops-engineering/credential", headers=_h(token)
            )
            assert resp.status_code == 404

    def test_credential_missing_returns_404(self, client):
        token = _make_token()
        with patch("app.routers.certification.CertificationDB") as MockDB:
            db = MockDB.return_value
            db.get_candidate_record.return_value = {"credential_id": "cred-1"}
            db.get_credential.return_value = None
            resp = client.get(
                "/certifications/devsecops-engineering/credential", headers=_h(token)
            )
            assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /certifications/{pathway_id}/credential/preview
# ---------------------------------------------------------------------------


class TestPreviewCertificate:
    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/certifications/devsecops-engineering/credential/preview")
        assert resp.status_code == 401

    def test_success_returns_png(self, client):
        token = _make_token()
        with (
            patch("app.routers.certification.CertificationDB") as MockDB,
            patch("app.routers.certification.get_pathway_config") as mock_pw,
            patch("app.routers.certification.CertificateGenerator") as MockGen,
        ):
            db = MockDB.return_value
            db.get_candidate_record.return_value = {"credential_id": "cred-1"}
            db.get_credential.return_value = {
                "credential_id": "cred-1",
                "full_name_at_issuance": "Jane Doe",
                "issued_at": "2026-01-01",
                "expires_at": "2027-01-01",
            }
            mock_pw.return_value = {
                "display_name": "DevSecOps Engineering",
                "description": "desc",
            }
            MockGen.return_value.generate_pdf_bytes.return_value = b"\x89PNG-bytes"

            resp = client.get(
                "/certifications/devsecops-engineering/credential/preview",
                headers=_h(token),
            )
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "image/png"
            assert resp.content == b"\x89PNG-bytes"

    def test_no_credential_returns_404(self, client):
        token = _make_token()
        with patch("app.routers.certification.CertificationDB") as MockDB:
            MockDB.return_value.get_candidate_record.return_value = None
            resp = client.get(
                "/certifications/devsecops-engineering/credential/preview",
                headers=_h(token),
            )
            assert resp.status_code == 404

    def test_generation_failure_returns_500(self, client):
        token = _make_token()
        with (
            patch("app.routers.certification.CertificationDB") as MockDB,
            patch("app.routers.certification.get_pathway_config") as mock_pw,
            patch("app.routers.certification.CertificateGenerator") as MockGen,
        ):
            db = MockDB.return_value
            db.get_candidate_record.return_value = {"credential_id": "cred-1"}
            db.get_credential.return_value = {
                "credential_id": "cred-1",
                "full_name_at_issuance": "Jane Doe",
                "issued_at": "2026-01-01",
                "expires_at": "2027-01-01",
            }
            mock_pw.return_value = None
            MockGen.return_value.generate_pdf_bytes.return_value = None

            resp = client.get(
                "/certifications/devsecops-engineering/credential/preview",
                headers=_h(token),
            )
            assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /certifications/{pathway_id}/credential/download
# ---------------------------------------------------------------------------


class TestDownloadCertificate:
    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/certifications/devsecops-engineering/credential/download")
        assert resp.status_code == 401

    def test_success_returns_url(self, client):
        token = _make_token()
        with (
            patch("app.routers.certification.CertificationDB") as MockDB,
            patch("app.routers.certification.get_pathway_config") as mock_pw,
            patch("app.routers.certification.CertificateGenerator") as MockGen,
        ):
            db = MockDB.return_value
            db.get_candidate_record.return_value = {"credential_id": "cred-1"}
            db.get_credential.return_value = {
                "credential_id": "cred-1",
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
                "/certifications/devsecops-engineering/credential/download",
                headers=_h(token),
            )
            assert resp.status_code == 200
            assert resp.json()["download_url"].startswith("https://s3.example.com")

    def test_no_candidate_returns_404(self, client):
        token = _make_token()
        with patch("app.routers.certification.CertificationDB") as MockDB:
            MockDB.return_value.get_candidate_record.return_value = None
            resp = client.get(
                "/certifications/devsecops-engineering/credential/download",
                headers=_h(token),
            )
            assert resp.status_code == 404

    def test_credential_missing_returns_404(self, client):
        token = _make_token()
        with patch("app.routers.certification.CertificationDB") as MockDB:
            db = MockDB.return_value
            db.get_candidate_record.return_value = {"credential_id": "cred-1"}
            db.get_credential.return_value = None
            resp = client.get(
                "/certifications/devsecops-engineering/credential/download",
                headers=_h(token),
            )
            assert resp.status_code == 404

    def test_generation_failure_returns_500(self, client):
        token = _make_token()
        with (
            patch("app.routers.certification.CertificationDB") as MockDB,
            patch("app.routers.certification.get_pathway_config") as mock_pw,
            patch("app.routers.certification.CertificateGenerator") as MockGen,
        ):
            db = MockDB.return_value
            db.get_candidate_record.return_value = {"credential_id": "cred-1"}
            db.get_credential.return_value = {
                "credential_id": "cred-1",
                "full_name_at_issuance": "Jane Doe",
                "issued_at": "2026-01-01",
                "expires_at": "2027-01-01",
            }
            mock_pw.return_value = {"display_name": "DevSecOps", "description": ""}
            MockGen.return_value.generate_svg_content.return_value = None

            resp = client.get(
                "/certifications/devsecops-engineering/credential/download",
                headers=_h(token),
            )
            assert resp.status_code == 500
