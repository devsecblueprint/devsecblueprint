"""Tests for the verification router — /api/verification/student/*.

Pins the JWT gating and the VerificationService-exception -> HTTP-status-code
mapping for the three Student Builder verification routes:

- POST /api/verification/student/submit       (auth, 202 on success)
- POST /api/verification/student/confirm       (auth, 200 on success)
- GET  /api/verification/student/eligibility   (auth)

VerificationService is injected via ``get_verification_service`` and overridden
with a MagicMock whose ``submit``/``confirm``/``get_eligibility`` raise the
various service exceptions or return values. Settings and the JWT secret are
overridden/primed exactly as in the stripe + walkthrough router tests.

NOTE: the router's rate limiters (``_SUBMIT_RATE_LIMITER`` 5/hr,
``_CONFIRM_RATE_LIMITER`` 10/hr) are module-level and persist across tests in
the same process. An autouse fixture clears their internal ``_state`` between
tests so rate-limit counts never bleed across cases.

Requirements: 3.2, 3.3, 3.4, 3.6, 4.5, 4.7, 4.8
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import Settings
from app.main import app
from app.services.verification_service import (
    ApyHubUnavailable,
    EmailSendError,
    InvalidEmailError,
    InvalidTokenError,
    NotAcademicError,
)

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


def _auth_header(sub: str = "user-123") -> dict:
    return {"Authorization": f"Bearer {_make_token(sub)}"}


@pytest.fixture
def mock_auth():
    from app.auth.jwt import _jwt_secret_cache

    _jwt_secret_cache["secret_key"] = TEST_SECRET_KEY
    _jwt_secret_cache["fetched_at"] = 9999999999.0
    yield
    _jwt_secret_cache["secret_key"] = None
    _jwt_secret_cache["fetched_at"] = 0.0


@pytest.fixture
def mock_service():
    return MagicMock()


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Clear the module-level rate-limiter state before and after each test so
    per-user request counts never bleed across tests in the same process."""
    from app.routers.verification import (
        _CONFIRM_RATE_LIMITER,
        _SUBMIT_RATE_LIMITER,
    )

    _SUBMIT_RATE_LIMITER._state.clear()
    _CONFIRM_RATE_LIMITER._state.clear()
    yield
    _SUBMIT_RATE_LIMITER._state.clear()
    _CONFIRM_RATE_LIMITER._state.clear()


@pytest.fixture
def client(mock_service):
    from app.dependencies import get_settings as dep_get_settings
    from app.routers.verification import get_verification_service

    app.dependency_overrides[dep_get_settings] = lambda: TEST_SETTINGS
    app.dependency_overrides[get_verification_service] = lambda: mock_service
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# JWT gating — all three routes return 401 without a valid token
# ---------------------------------------------------------------------------


class TestAuthRequired:
    def test_submit_requires_auth(self, client, mock_auth):
        response = client.post(
            "/api/verification/student/submit",
            json={"academic_email": "student@uni.edu"},
        )
        assert response.status_code == 401

    def test_confirm_requires_auth(self, client, mock_auth):
        response = client.post(
            "/api/verification/student/confirm",
            json={"token": "tok-abc"},
        )
        assert response.status_code == 401

    def test_eligibility_requires_auth(self, client, mock_auth):
        response = client.get("/api/verification/student/eligibility")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/verification/student/submit — error -> status mapping + success
# ---------------------------------------------------------------------------


class TestSubmit:
    def test_success_returns_202(self, client, mock_auth, mock_service):
        mock_service.submit.return_value = None
        response = client.post(
            "/api/verification/student/submit",
            headers=_auth_header("submit-success"),
            json={"academic_email": "student@uni.edu"},
        )
        assert response.status_code == 202
        mock_service.submit.assert_called_once_with("submit-success", "student@uni.edu")

    def test_invalid_email_maps_to_400(self, client, mock_auth, mock_service):
        mock_service.submit.side_effect = InvalidEmailError("bad email")
        response = client.post(
            "/api/verification/student/submit",
            headers=_auth_header("submit-400"),
            json={"academic_email": "not-an-email"},
        )
        assert response.status_code == 400

    def test_not_academic_maps_to_422(self, client, mock_auth, mock_service):
        mock_service.submit.side_effect = NotAcademicError("not academic")
        response = client.post(
            "/api/verification/student/submit",
            headers=_auth_header("submit-422"),
            json={"academic_email": "person@gmail.com"},
        )
        assert response.status_code == 422

    def test_apyhub_unavailable_maps_to_503(self, client, mock_auth, mock_service):
        mock_service.submit.side_effect = ApyHubUnavailable("unavailable")
        response = client.post(
            "/api/verification/student/submit",
            headers=_auth_header("submit-503"),
            json={"academic_email": "student@uni.edu"},
        )
        assert response.status_code == 503

    def test_email_send_error_maps_to_502(self, client, mock_auth, mock_service):
        mock_service.submit.side_effect = EmailSendError("send failed")
        response = client.post(
            "/api/verification/student/submit",
            headers=_auth_header("submit-502"),
            json={"academic_email": "student@uni.edu"},
        )
        assert response.status_code == 502


# ---------------------------------------------------------------------------
# POST /api/verification/student/confirm — error -> status mapping + success
# ---------------------------------------------------------------------------


class TestConfirm:
    def test_success_returns_200_with_eligibility(
        self, client, mock_auth, mock_service
    ):
        expires_at = "2026-01-01T00:00:00+00:00"
        mock_service.confirm.return_value = {
            "eligible": True,
            "expires_at": expires_at,
        }
        response = client.post(
            "/api/verification/student/confirm",
            headers=_auth_header("confirm-success"),
            json={"token": "tok-valid"},
        )
        assert response.status_code == 200
        assert response.json() == {"eligible": True, "expires_at": expires_at}
        mock_service.confirm.assert_called_once_with("confirm-success", "tok-valid")

    def test_invalid_token_maps_to_400(self, client, mock_auth, mock_service):
        mock_service.confirm.side_effect = InvalidTokenError("bad token")
        response = client.post(
            "/api/verification/student/confirm",
            headers=_auth_header("confirm-400"),
            json={"token": "tok-bad"},
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/verification/student/eligibility — {eligible, expires_at}
# ---------------------------------------------------------------------------


class TestEligibility:
    def test_eligible_true_with_record(self, client, mock_auth, mock_service):
        expires_at = "2026-01-01T00:00:00+00:00"
        mock_service.get_eligibility.return_value = {
            "eligible": True,
            "expires_at": expires_at,
        }
        response = client.get(
            "/api/verification/student/eligibility",
            headers=_auth_header("elig-true"),
        )
        assert response.status_code == 200
        assert response.json() == {"eligible": True, "expires_at": expires_at}
        mock_service.get_eligibility.assert_called_once_with("elig-true")

    def test_eligible_false_without_record(self, client, mock_auth, mock_service):
        mock_service.get_eligibility.return_value = None
        response = client.get(
            "/api/verification/student/eligibility",
            headers=_auth_header("elig-false"),
        )
        assert response.status_code == 200
        assert response.json() == {"eligible": False, "expires_at": None}


# ---------------------------------------------------------------------------
# _FixedWindowRateLimiter — direct unit tests of the limiter itself
# ---------------------------------------------------------------------------


class TestFixedWindowRateLimiter:
    def test_allows_up_to_max_then_rejects(self):
        from app.routers.verification import _FixedWindowRateLimiter

        limiter = _FixedWindowRateLimiter(max_requests=2, window_seconds=3600)
        assert limiter.allow("k") is True
        assert limiter.allow("k") is True
        # Third call within the same window exceeds max -> rejected.
        assert limiter.allow("k") is False

    def test_window_rollover_resets_count(self, monkeypatch):
        import app.routers.verification as verification_module
        from app.routers.verification import _FixedWindowRateLimiter

        fake_now = {"t": 1000.0}
        monkeypatch.setattr(
            verification_module.time, "monotonic", lambda: fake_now["t"]
        )

        limiter = _FixedWindowRateLimiter(max_requests=2, window_seconds=3600)
        assert limiter.allow("k") is True
        assert limiter.allow("k") is True
        assert limiter.allow("k") is False  # over threshold in window 1

        # Advance the clock past the window so the next call rolls over.
        fake_now["t"] += 3601.0
        assert limiter.allow("k") is True  # fresh window -> allowed again


# ---------------------------------------------------------------------------
# Rate limiting — endpoints return 429 past the per-user threshold
# ---------------------------------------------------------------------------


class TestRateLimiting:
    def test_submit_sixth_request_returns_429(self, client, mock_auth, mock_service):
        # Service succeeds every time, so only the limiter (5/hr) trips the 429.
        mock_service.submit.return_value = None
        for _ in range(5):
            ok = client.post(
                "/api/verification/student/submit",
                headers=_auth_header("submit-429"),
                json={"academic_email": "student@uni.edu"},
            )
            assert ok.status_code == 202
        sixth = client.post(
            "/api/verification/student/submit",
            headers=_auth_header("submit-429"),
            json={"academic_email": "student@uni.edu"},
        )
        assert sixth.status_code == 429

    def test_confirm_eleventh_request_returns_429(
        self, client, mock_auth, mock_service
    ):
        # Service succeeds every time, so only the limiter (10/hr) trips the 429.
        mock_service.confirm.return_value = {"eligible": True, "expires_at": None}
        for _ in range(10):
            ok = client.post(
                "/api/verification/student/confirm",
                headers=_auth_header("confirm-429"),
                json={"token": "tok-valid"},
            )
            assert ok.status_code == 200
        eleventh = client.post(
            "/api/verification/student/confirm",
            headers=_auth_header("confirm-429"),
            json={"token": "tok-valid"},
        )
        assert eleventh.status_code == 429


# ---------------------------------------------------------------------------
# Unexpected service errors map to 500 on all three routes
# ---------------------------------------------------------------------------


class TestUnexpectedErrors:
    def test_submit_generic_exception_maps_to_500(
        self, client, mock_auth, mock_service
    ):
        mock_service.submit.side_effect = RuntimeError("boom")
        response = client.post(
            "/api/verification/student/submit",
            headers=_auth_header("submit-500"),
            json={"academic_email": "student@uni.edu"},
        )
        assert response.status_code == 500

    def test_confirm_generic_exception_maps_to_500(
        self, client, mock_auth, mock_service
    ):
        mock_service.confirm.side_effect = RuntimeError("boom")
        response = client.post(
            "/api/verification/student/confirm",
            headers=_auth_header("confirm-500"),
            json={"token": "tok-valid"},
        )
        assert response.status_code == 500

    def test_eligibility_generic_exception_maps_to_500(
        self, client, mock_auth, mock_service
    ):
        mock_service.get_eligibility.side_effect = RuntimeError("boom")
        response = client.get(
            "/api/verification/student/eligibility",
            headers=_auth_header("elig-500"),
        )
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# Missing-sub 401 handler branches (submit line 167, confirm line 208)
# ---------------------------------------------------------------------------
#
# NOTE: ``get_current_user`` (app/auth/jwt.py) already rejects a token whose
# ``sub`` claim is missing/empty with 401 *before* the route handler runs, so a
# real empty-sub JWT can never reach the handler's own ``if not user_id: 401``
# guard. The eligibility route's equivalent guard is likewise unreachable via a
# real token. To exercise the handler-level guards directly (lines 167 and 208)
# we override ``get_current_user`` to return a payload with no usable ``sub``.


class TestMissingSubHandlerGuard:
    def test_submit_missing_sub_returns_401(self, mock_service):
        from app.auth.jwt import get_current_user
        from app.dependencies import get_settings as dep_get_settings
        from app.routers.verification import get_verification_service

        app.dependency_overrides[dep_get_settings] = lambda: TEST_SETTINGS
        app.dependency_overrides[get_verification_service] = lambda: mock_service
        app.dependency_overrides[get_current_user] = lambda: {"sub": ""}
        try:
            local_client = TestClient(app)
            response = local_client.post(
                "/api/verification/student/submit",
                json={"academic_email": "student@uni.edu"},
            )
            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()

    def test_confirm_missing_sub_returns_401(self, mock_service):
        from app.auth.jwt import get_current_user
        from app.dependencies import get_settings as dep_get_settings
        from app.routers.verification import get_verification_service

        app.dependency_overrides[dep_get_settings] = lambda: TEST_SETTINGS
        app.dependency_overrides[get_verification_service] = lambda: mock_service
        app.dependency_overrides[get_current_user] = lambda: {"sub": ""}
        try:
            local_client = TestClient(app)
            response = local_client.post(
                "/api/verification/student/confirm",
                json={"token": "tok-valid"},
            )
            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()
