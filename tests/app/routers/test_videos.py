"""Tests for the member videos router — /api/videos/*.

The router builds EntitlementService and VideoService via dependency
functions (get_entitlement_service, get_video_service). We override those
dependencies with mock service objects so no boto3/Cloudflare calls happen.
Entitlement enforcement is exercised by making require_video_recordings
either pass or raise HTTPException(403).
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from jose import jwt

from app.config import Settings
from app.main import app
from app.models.videos import (
    CatalogResponse,
    PlaybackTokenResponse,
    ProgressSaveResponse,
    VideoResponse,
    VideoStatus,
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


def _video_response(
    video_id: str = "vid-1", status=VideoStatus.PUBLISHED
) -> VideoResponse:
    return VideoResponse(
        id=video_id,
        title="Intro to DevSecOps",
        slug="intro-to-devsecops",
        description="A talk",
        thumbnail_url="https://img/thumb.png",
        duration_seconds=3600,
        instructor="Jane",
        instructors=[],
        recorded_at="2024-01-01T00:00:00Z",
        status=status,
        tags=["security"],
        resources=[],
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-02T00:00:00Z",
        published_at="2024-01-03T00:00:00Z",
    )


@pytest.fixture
def mock_auth():
    from app.auth.jwt import _jwt_secret_cache

    _jwt_secret_cache["secret_key"] = TEST_SECRET_KEY
    _jwt_secret_cache["fetched_at"] = 9999999999.0
    yield
    _jwt_secret_cache["secret_key"] = None
    _jwt_secret_cache["fetched_at"] = 0.0


@pytest.fixture
def mock_entitlement():
    """An entitlement service that grants access by default."""
    svc = MagicMock()
    svc.require_video_recordings.return_value = None
    return svc


@pytest.fixture
def mock_video_svc():
    """A video service with async methods mocked."""
    svc = MagicMock()
    svc.get_catalog = AsyncMock()
    svc.get_video_detail = AsyncMock()
    svc.get_playback_token = AsyncMock()
    # get_progress and save_progress are sync in the service
    svc.get_progress = MagicMock()
    svc.save_progress = MagicMock()
    return svc


@pytest.fixture
def client(mock_entitlement, mock_video_svc):
    from app.dependencies import get_settings as dep_get_settings
    from app.routers.videos import (
        get_entitlement_service,
        get_video_service,
    )

    app.dependency_overrides[dep_get_settings] = lambda: TEST_SETTINGS
    app.dependency_overrides[get_entitlement_service] = lambda: mock_entitlement
    app.dependency_overrides[get_video_service] = lambda: mock_video_svc
    yield TestClient(app)
    app.dependency_overrides.clear()


def _auth_header():
    return {"Authorization": f"Bearer {_make_token()}"}


# ---------------------------------------------------------------------------
# GET /api/videos (catalog)
# ---------------------------------------------------------------------------


class TestCatalog:
    def test_requires_auth(self, client, mock_auth):
        assert client.get("/api/videos").status_code == 401

    def test_success(self, client, mock_auth, mock_video_svc):
        mock_video_svc.get_catalog.return_value = CatalogResponse(
            continue_watching=[],
            latest=[],
            all_published=[],
            total_count=0,
            page=1,
            page_size=20,
        )
        response = client.get("/api/videos", headers=_auth_header())
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["page"] == 1
        mock_video_svc.get_catalog.assert_awaited_once()

    def test_entitlement_denied_403(self, client, mock_auth, mock_entitlement):
        mock_entitlement.require_video_recordings.side_effect = HTTPException(
            status_code=403, detail="Insufficient entitlement for videos"
        )
        response = client.get("/api/videos", headers=_auth_header())
        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient entitlement for videos"

    def test_invalid_page_422(self, client, mock_auth):
        response = client.get("/api/videos?page=0", headers=_auth_header())
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/videos/{id_or_slug}
# ---------------------------------------------------------------------------


class TestGetVideo:
    def test_success(self, client, mock_auth, mock_video_svc):
        mock_video_svc.get_video_detail.return_value = _video_response()
        response = client.get("/api/videos/intro-to-devsecops", headers=_auth_header())
        assert response.status_code == 200
        assert response.json()["slug"] == "intro-to-devsecops"

    def test_not_found_404(self, client, mock_auth, mock_video_svc):
        mock_video_svc.get_video_detail.side_effect = HTTPException(
            status_code=404, detail="Video not found or unavailable"
        )
        response = client.get("/api/videos/missing", headers=_auth_header())
        assert response.status_code == 404
        assert response.json()["detail"] == "Video not found or unavailable"

    def test_entitlement_denied_403(self, client, mock_auth, mock_entitlement):
        mock_entitlement.require_video_recordings.side_effect = HTTPException(
            status_code=403, detail="Insufficient entitlement for videos"
        )
        response = client.get("/api/videos/vid-1", headers=_auth_header())
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/videos/{id}/playback
# ---------------------------------------------------------------------------


class TestPlayback:
    def test_success(self, client, mock_auth, mock_video_svc):
        mock_video_svc.get_playback_token.return_value = PlaybackTokenResponse(
            token="signed-token", expires_in_seconds=14400
        )
        response = client.post("/api/videos/vid-1/playback", headers=_auth_header())
        assert response.status_code == 200
        data = response.json()
        assert data["token"] == "signed-token"
        assert data["expires_in_seconds"] == 14400

    def test_requires_auth(self, client, mock_auth):
        assert client.post("/api/videos/vid-1/playback").status_code == 401


# ---------------------------------------------------------------------------
# GET /api/videos/{id}/progress
# ---------------------------------------------------------------------------


class TestGetProgress:
    def test_with_existing_progress(self, client, mock_auth, mock_video_svc):
        mock_video_svc.get_progress.return_value = {
            "position_seconds": 120.0,
            "duration_seconds": 3600.0,
            "percent_complete": 3,
            "completed": False,
            "last_watched_at": "2024-06-01T00:00:00Z",
        }
        response = client.get("/api/videos/vid-1/progress", headers=_auth_header())
        assert response.status_code == 200
        data = response.json()
        assert data["position_seconds"] == 120.0
        assert data["percent_complete"] == 3
        assert data["completed"] is False

    def test_no_progress_returns_nulls(self, client, mock_auth, mock_video_svc):
        mock_video_svc.get_progress.return_value = None
        response = client.get("/api/videos/vid-1/progress", headers=_auth_header())
        assert response.status_code == 200
        data = response.json()
        assert data["position_seconds"] is None
        assert data["completed"] is None


# ---------------------------------------------------------------------------
# PUT /api/videos/{id}/progress
# ---------------------------------------------------------------------------


class TestSaveProgress:
    def test_success(self, client, mock_auth, mock_video_svc):
        mock_video_svc.save_progress.return_value = ProgressSaveResponse(
            percent_complete=50, completed=False
        )
        response = client.put(
            "/api/videos/vid-1/progress",
            headers=_auth_header(),
            json={"position_seconds": 1800, "duration_seconds": 3600},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["percent_complete"] == 50
        assert data["completed"] is False
        mock_video_svc.save_progress.assert_called_once()

    def test_position_exceeds_duration_422(self, client, mock_auth, mock_video_svc):
        response = client.put(
            "/api/videos/vid-1/progress",
            headers=_auth_header(),
            json={"position_seconds": 4000, "duration_seconds": 3600},
        )
        assert response.status_code == 422
        assert "positionSeconds cannot exceed" in response.json()["detail"]
        mock_video_svc.save_progress.assert_not_called()

    def test_negative_position_422(self, client, mock_auth):
        response = client.put(
            "/api/videos/vid-1/progress",
            headers=_auth_header(),
            json={"position_seconds": -1, "duration_seconds": 3600},
        )
        assert response.status_code == 422

    def test_requires_auth(self, client, mock_auth):
        response = client.put(
            "/api/videos/vid-1/progress",
            json={"position_seconds": 10, "duration_seconds": 3600},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Dependency-provider / helper functions (unit-level, no HTTP)
# ---------------------------------------------------------------------------


class TestDependencyProviders:
    def test_get_entitlement_service_builds_instance(self):
        from app.routers.videos import get_entitlement_service
        from app.services.entitlement_service import EntitlementService

        svc = get_entitlement_service(TEST_SETTINGS)
        assert isinstance(svc, EntitlementService)

    def test_get_cloudflare_service_builds_instance(self):
        from unittest.mock import patch
        from app.routers.videos import get_cloudflare_service
        from app.services.cloudflare_stream_service import CloudflareStreamService

        with patch("app.routers.videos._get_cloudflare_token", return_value="tok"):
            svc = get_cloudflare_service(TEST_SETTINGS)
        assert isinstance(svc, CloudflareStreamService)

    def test_get_video_service_builds_instance(self):
        from app.routers.videos import get_video_service
        from app.services.video_service import VideoService

        cf = MagicMock()
        svc = get_video_service(TEST_SETTINGS, cf)
        assert isinstance(svc, VideoService)

    def test_cloudflare_token_empty_when_no_secret_name(self):
        from app.routers.videos import _get_cloudflare_token

        settings = TEST_SETTINGS.model_copy(update={"cloudflare_secret_name": ""})
        assert _get_cloudflare_token(settings) == ""

    def test_cloudflare_token_from_secrets_manager(self):
        from unittest.mock import patch
        from app.routers.videos import _get_cloudflare_token

        settings = TEST_SETTINGS.model_copy(
            update={"cloudflare_secret_name": "cf-secret"}
        )
        with patch("app.routers.videos.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.get_secret_value.return_value = {
                "SecretString": '{"secret_key": "cf-api-token"}'
            }
            assert _get_cloudflare_token(settings) == "cf-api-token"

    def test_cloudflare_token_error_returns_empty(self):
        from unittest.mock import patch
        from app.routers.videos import _get_cloudflare_token

        settings = TEST_SETTINGS.model_copy(
            update={"cloudflare_secret_name": "cf-secret"}
        )
        with patch("app.routers.videos.boto3.client") as mock_boto:
            mock_boto.side_effect = RuntimeError("boom")
            assert _get_cloudflare_token(settings) == ""
