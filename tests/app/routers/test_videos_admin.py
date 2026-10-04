"""Tests for the admin videos router — /admin/videos/*.

These routes require admin via require_admin, which derives admin status
from settings.admin_users matching (provider, provider_login). We set
admin_users="github:testadmin" and mint tokens with github_login=testadmin.

VideoService is injected via get_video_service, overridden with a mock.
VideoSyncService (for /sync) is constructed inline in the handler, so we
patch it at the router import site.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from jose import jwt

from app.config import Settings
from app.main import app
from app.models.videos import VideoResponse, VideoStatus

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
    admin_users="github:testadmin",
)

TEST_SECRET_KEY = "test-secret-key-for-jwt-signing-32chars"


def _make_token(admin: bool = False) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "user-123",
        "avatar": "https://avatar.url",
        "name": "Test User",
        "provider": "github",
        "github_login": "testadmin" if admin else "regularuser",
        "iat": now,
        "exp": now + timedelta(hours=8),
    }
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")


def _video_response(video_id="vid-1", status=VideoStatus.DRAFT) -> VideoResponse:
    return VideoResponse(
        id=video_id,
        title="Intro to DevSecOps",
        slug="intro-to-devsecops",
        description="A talk",
        thumbnail_url=None,
        duration_seconds=3600,
        instructor="Jane",
        instructors=[],
        recorded_at="2024-01-01T00:00:00Z",
        status=status,
        tags=["security"],
        resources=[],
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-02T00:00:00Z",
        published_at=None,
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
def mock_video_svc():
    svc = MagicMock()
    svc.list_videos_admin = AsyncMock()
    svc.create_video = AsyncMock()
    svc.get_video_admin = AsyncMock()
    svc.update_video = AsyncMock()
    svc.transition_status = AsyncMock()
    svc.check_processing_status = AsyncMock()
    return svc


@pytest.fixture
def client(mock_video_svc):
    from app.dependencies import get_settings as dep_get_settings
    from app.routers.videos_admin import (
        get_video_service,
        get_cloudflare_service,
    )

    app.dependency_overrides[dep_get_settings] = lambda: TEST_SETTINGS
    app.dependency_overrides[get_video_service] = lambda: mock_video_svc
    app.dependency_overrides[get_cloudflare_service] = lambda: MagicMock()
    yield TestClient(app)
    app.dependency_overrides.clear()


def _admin_header():
    return {"Authorization": f"Bearer {_make_token(admin=True)}"}


def _user_header():
    return {"Authorization": f"Bearer {_make_token(admin=False)}"}


# ---------------------------------------------------------------------------
# GET /admin/videos (list)
# ---------------------------------------------------------------------------


class TestListVideos:
    def test_requires_auth(self, client, mock_auth):
        assert client.get("/admin/videos").status_code == 401

    def test_forbidden_for_non_admin(self, client, mock_auth):
        response = client.get("/admin/videos", headers=_user_header())
        assert response.status_code == 403
        assert response.json()["detail"] == "Forbidden"

    def test_success(self, client, mock_auth, mock_video_svc):
        mock_video_svc.list_videos_admin.return_value = ([_video_response()], 1)
        response = client.get("/admin/videos", headers=_admin_header())
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert len(data["recordings"]) == 1
        assert data["recordings"][0]["id"] == "vid-1"

    def test_status_filter_passed_through(self, client, mock_auth, mock_video_svc):
        mock_video_svc.list_videos_admin.return_value = ([], 0)
        response = client.get(
            "/admin/videos?status=PUBLISHED&page=2&page_size=5",
            headers=_admin_header(),
        )
        assert response.status_code == 200
        mock_video_svc.list_videos_admin.assert_awaited_once_with(
            status="PUBLISHED", page=2, page_size=5
        )

    def test_invalid_page_size_422(self, client, mock_auth):
        response = client.get("/admin/videos?page_size=500", headers=_admin_header())
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /admin/videos (create)
# ---------------------------------------------------------------------------


class TestCreateVideo:
    def _valid_body(self):
        return {
            "title": "New Video",
            "description": "desc",
            "cloudflare_stream_id": "cf-abc123",
            "instructor": "Jane",
            "recorded_at": "2024-01-01T00:00:00Z",
            "tags": ["security"],
            "resources": [],
        }

    def test_success_201(self, client, mock_auth, mock_video_svc):
        mock_video_svc.create_video.return_value = _video_response()
        response = client.post(
            "/admin/videos", headers=_admin_header(), json=self._valid_body()
        )
        assert response.status_code == 201
        assert response.json()["id"] == "vid-1"

    def test_forbidden_for_non_admin(self, client, mock_auth):
        response = client.post(
            "/admin/videos", headers=_user_header(), json=self._valid_body()
        )
        assert response.status_code == 403

    def test_missing_required_field_422(self, client, mock_auth):
        body = self._valid_body()
        del body["cloudflare_stream_id"]
        response = client.post("/admin/videos", headers=_admin_header(), json=body)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /admin/videos/{id}
# ---------------------------------------------------------------------------


class TestGetVideo:
    def test_success(self, client, mock_auth, mock_video_svc):
        mock_video_svc.get_video_admin.return_value = _video_response()
        response = client.get("/admin/videos/vid-1", headers=_admin_header())
        assert response.status_code == 200
        assert response.json()["id"] == "vid-1"

    def test_not_found_404(self, client, mock_auth, mock_video_svc):
        mock_video_svc.get_video_admin.side_effect = HTTPException(
            status_code=404, detail="Video not found"
        )
        response = client.get("/admin/videos/missing", headers=_admin_header())
        assert response.status_code == 404

    def test_forbidden_for_non_admin(self, client, mock_auth):
        assert (
            client.get("/admin/videos/vid-1", headers=_user_header()).status_code == 403
        )


# ---------------------------------------------------------------------------
# PUT /admin/videos/{id}
# ---------------------------------------------------------------------------


class TestUpdateVideo:
    def test_success(self, client, mock_auth, mock_video_svc):
        mock_video_svc.update_video.return_value = _video_response()
        response = client.put(
            "/admin/videos/vid-1",
            headers=_admin_header(),
            json={"title": "Updated Title"},
        )
        assert response.status_code == 200
        mock_video_svc.update_video.assert_awaited_once()

    def test_forbidden_for_non_admin(self, client, mock_auth):
        response = client.put(
            "/admin/videos/vid-1", headers=_user_header(), json={"title": "x"}
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# POST /admin/videos/{id}/status
# ---------------------------------------------------------------------------


class TestTransitionStatus:
    def test_success(self, client, mock_auth, mock_video_svc):
        mock_video_svc.transition_status.return_value = _video_response(
            status=VideoStatus.PROCESSING
        )
        response = client.post(
            "/admin/videos/vid-1/status",
            headers=_admin_header(),
            json={"target_status": "PROCESSING"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "PROCESSING"
        mock_video_svc.transition_status.assert_awaited_once_with(
            "vid-1", VideoStatus.PROCESSING
        )

    def test_invalid_transition_400(self, client, mock_auth, mock_video_svc):
        mock_video_svc.transition_status.side_effect = HTTPException(
            status_code=400, detail="Invalid status transition"
        )
        response = client.post(
            "/admin/videos/vid-1/status",
            headers=_admin_header(),
            json={"target_status": "ARCHIVED"},
        )
        assert response.status_code == 400

    def test_invalid_enum_422(self, client, mock_auth):
        response = client.post(
            "/admin/videos/vid-1/status",
            headers=_admin_header(),
            json={"target_status": "NOT_A_STATUS"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /admin/videos/{id}/stream-status
# ---------------------------------------------------------------------------


class TestStreamStatus:
    def test_success(self, client, mock_auth, mock_video_svc):
        mock_video_svc.check_processing_status.return_value = _video_response(
            status=VideoStatus.READY
        )
        response = client.get(
            "/admin/videos/vid-1/stream-status", headers=_admin_header()
        )
        assert response.status_code == 200
        assert response.json()["status"] == "READY"

    def test_forbidden_for_non_admin(self, client, mock_auth):
        assert (
            client.get(
                "/admin/videos/vid-1/stream-status", headers=_user_header()
            ).status_code
            == 403
        )


# ---------------------------------------------------------------------------
# POST /admin/videos/sync
# ---------------------------------------------------------------------------


class TestSync:
    def test_success(self, client, mock_auth):
        with patch("app.routers.videos_admin.VideoSyncService") as mock_sync_cls:
            instance = MagicMock()
            instance.sync_all = AsyncMock(return_value=3)
            mock_sync_cls.return_value = instance
            response = client.post("/admin/videos/sync", headers=_admin_header())

        assert response.status_code == 200
        data = response.json()
        assert data["synced"] == 3
        assert "3" in data["message"]

    def test_forbidden_for_non_admin(self, client, mock_auth):
        assert (
            client.post("/admin/videos/sync", headers=_user_header()).status_code == 403
        )


# ---------------------------------------------------------------------------
# Dependency-provider / helper functions (unit-level, no HTTP)
# ---------------------------------------------------------------------------


class TestDependencyProviders:
    def test_get_cloudflare_service_builds_instance(self):
        from app.routers.videos_admin import get_cloudflare_service
        from app.services.cloudflare_stream_service import CloudflareStreamService

        with patch(
            "app.routers.videos_admin._get_cloudflare_token", return_value="tok"
        ):
            svc = get_cloudflare_service(TEST_SETTINGS)
        assert isinstance(svc, CloudflareStreamService)

    def test_get_video_service_builds_instance(self):
        from app.routers.videos_admin import get_video_service
        from app.services.video_service import VideoService

        svc = get_video_service(TEST_SETTINGS, MagicMock())
        assert isinstance(svc, VideoService)

    def test_cloudflare_token_empty_when_no_secret_name(self):
        from app.routers.videos_admin import _get_cloudflare_token

        settings = TEST_SETTINGS.model_copy(update={"cloudflare_secret_name": ""})
        assert _get_cloudflare_token(settings) == ""

    def test_cloudflare_token_from_secrets_manager(self):
        from app.routers.videos_admin import _get_cloudflare_token

        settings = TEST_SETTINGS.model_copy(
            update={"cloudflare_secret_name": "cf-secret"}
        )
        with patch("app.routers.videos_admin.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.get_secret_value.return_value = {
                "SecretString": '{"secret_key": "cf-api-token"}'
            }
            assert _get_cloudflare_token(settings) == "cf-api-token"

    def test_cloudflare_token_error_returns_empty(self):
        from app.routers.videos_admin import _get_cloudflare_token

        settings = TEST_SETTINGS.model_copy(
            update={"cloudflare_secret_name": "cf-secret"}
        )
        with patch("app.routers.videos_admin.boto3.client") as mock_boto:
            mock_boto.side_effect = RuntimeError("boom")
            assert _get_cloudflare_token(settings) == ""
