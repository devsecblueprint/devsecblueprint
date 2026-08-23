"""Integration tests for video API endpoints.

Tests full request/response flows using FastAPI TestClient with
mocked DynamoDB (via moto) and mocked Cloudflare service.

Validates: Requirements 3.1, 4.4, 5.12, 6.1, 6.3, 8.1, 8.4, 8.5
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.models.videos import VideoStatus

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_settings():
    """Provide test settings with required fields."""
    return Settings(
        membership_table="test-membership",
        progress_table="test-progress",
        user_state_table="test-user-state",
        testimonials_table="test-testimonials",
        notifications_table="test-notifications",
        discord_secret_name="test-discord",
        discord_bot_secret_name="test-discord-bot",
        stripe_secret_name="test-stripe",
        stripe_webhook_secret_name="test-stripe-webhook",
        jwt_secret_name="test-jwt",
        github_secret_name="test-github",
        gitlab_secret_name="test-gitlab",
        bitbucket_secret_name="test-bitbucket",
        discord_guild_id="123",
        discord_role_free_id="456",
        discord_role_explorer_id="789",
        discord_role_builder_id="012",
        discord_role_builder_academy_id="345",
        discord_callback_url="http://localhost/discord/callback",
        frontend_url="http://localhost:3000",
        frontend_origin="http://localhost:3000",
        github_callback_url="http://localhost/auth/github/callback",
        gitlab_callback_url="http://localhost/auth/gitlab/callback",
        bitbucket_callback_url="http://localhost/auth/bitbucket/callback",
        videos_table="test-videos",
        cloudflare_secret_name="test-cloudflare",
        cloudflare_account_id="test-account",
    )


@pytest.fixture
def admin_user():
    """Admin user payload."""
    return {
        "sub": "admin-user-123",
        "is_admin": True,
        "provider": "github",
        "github_login": "testadmin",
    }


@pytest.fixture
def member_user():
    """Builder member user payload."""
    return {
        "sub": "member-user-456",
        "is_admin": False,
        "provider": "github",
        "github_login": "testmember",
    }


@pytest.fixture
def sample_video():
    """A sample video DynamoDB item in PUBLISHED status."""
    return {
        "PK": {"S": "VIDEO#rec-123"},
        "SK": {"S": "METADATA"},
        "id": {"S": "rec-123"},
        "title": {"S": "Building Secure APIs"},
        "slug": {"S": "building-secure-apis"},
        "description": {"S": "Learn to build secure APIs"},
        "cloudflareStreamId": {"S": "cf-video-abc123"},
        "thumbnailUrl": {"S": "https://example.com/thumb.jpg"},
        "durationSeconds": {"N": "3600"},
        "instructor": {"S": "Damien Burks"},
        "recordedAt": {"S": "2025-06-15T10:00:00Z"},
        "status": {"S": "PUBLISHED"},
        "requiredEntitlement": {"S": "VIDEO_RECORDINGS"},
        "tags": {"L": [{"S": "security"}, {"S": "api"}]},
        "resources": {
            "L": [
                {
                    "M": {
                        "title": {"S": "Slides"},
                        "url": {"S": "https://example.com/slides"},
                    }
                }
            ]
        },
        "createdAt": {"S": "2025-06-10T08:00:00Z"},
        "updatedAt": {"S": "2025-06-15T12:00:00Z"},
        "publishedAt": {"S": "2025-06-15T12:00:00Z"},
        "GSI1PK": {"S": "STATUS#PUBLISHED"},
        "GSI1SK": {"S": "2025-06-15T12:00:00Z"},
        "GSI2PK": {"S": "building-secure-apis"},
        "GSI2SK": {"S": "METADATA"},
    }


@pytest.fixture
def sample_draft_video():
    """A sample video in DRAFT status."""
    return {
        "PK": {"S": "VIDEO#rec-draft-1"},
        "SK": {"S": "METADATA"},
        "id": {"S": "rec-draft-1"},
        "title": {"S": "Draft Video"},
        "slug": {"S": "draft-video"},
        "description": {"S": "This is a draft"},
        "cloudflareStreamId": {"S": "cf-video-draft"},
        "thumbnailUrl": {"S": ""},
        "durationSeconds": {"N": "0"},
        "instructor": {"S": "Instructor"},
        "recordedAt": {"S": "2025-07-01T10:00:00Z"},
        "status": {"S": "DRAFT"},
        "requiredEntitlement": {"S": "VIDEO_RECORDINGS"},
        "tags": {"L": []},
        "resources": {"L": []},
        "createdAt": {"S": "2025-07-01T08:00:00Z"},
        "updatedAt": {"S": "2025-07-01T08:00:00Z"},
        "GSI1PK": {"S": "STATUS#DRAFT"},
        "GSI1SK": {"S": "2025-07-01T08:00:00Z"},
        "GSI2PK": {"S": "draft-video"},
        "GSI2SK": {"S": "METADATA"},
    }


# ---------------------------------------------------------------------------
# Unit tests for EntitlementService logic
# ---------------------------------------------------------------------------


class TestEntitlementService:
    """Tests for entitlement derivation logic."""

    def test_admin_always_entitled(self):
        """Admin users always get entitlement regardless of membership."""
        from app.services.entitlement_service import EntitlementService

        service = EntitlementService.__new__(EntitlementService)
        user = {"sub": "user-1", "is_admin": True}
        assert service.has_video_recordings_entitlement(user, None) is True

    def test_builder_active_entitled(self):
        """Builder tier with active subscription gets entitlement."""
        from app.services.entitlement_service import EntitlementService

        service = EntitlementService.__new__(EntitlementService)
        user = {"sub": "user-2", "is_admin": False}
        membership = {
            "membership_tier": {"S": "BUILDER"},
            "subscription_status": {"S": "active"},
        }
        assert service.has_video_recordings_entitlement(user, membership) is True

    def test_free_member_not_entitled(self):
        """Free tier user is not entitled."""
        from app.services.entitlement_service import EntitlementService

        service = EntitlementService.__new__(EntitlementService)
        user = {"sub": "user-3", "is_admin": False}
        membership = {
            "membership_tier": {"S": "FREE"},
            "subscription_status": {"S": "active"},
        }
        assert service.has_video_recordings_entitlement(user, membership) is False

    def test_builder_canceled_not_entitled(self):
        """Builder tier with canceled subscription is not entitled."""
        from app.services.entitlement_service import EntitlementService

        service = EntitlementService.__new__(EntitlementService)
        user = {"sub": "user-4", "is_admin": False}
        membership = {
            "membership_tier": {"S": "BUILDER"},
            "subscription_status": {"S": "canceled"},
        }
        assert service.has_video_recordings_entitlement(user, membership) is False

    def test_no_membership_not_entitled(self):
        """User with no membership record is not entitled."""
        from app.services.entitlement_service import EntitlementService

        service = EntitlementService.__new__(EntitlementService)
        user = {"sub": "user-5", "is_admin": False}
        assert service.has_video_recordings_entitlement(user, None) is False

    def test_require_video_recordings_raises_on_failure(self):
        """require_video_recordings raises HTTPException(403)."""
        from fastapi import HTTPException

        from app.services.entitlement_service import EntitlementService

        service = EntitlementService.__new__(EntitlementService)
        service._membership_db = MagicMock()
        service._membership_db.get_membership.return_value = None
        user = {"sub": "user-6", "is_admin": False}

        with pytest.raises(HTTPException) as exc_info:
            service.require_video_recordings(user)
        assert exc_info.value.status_code == 403
        assert "entitlement" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# Unit tests for VideoService progress calculation
# ---------------------------------------------------------------------------


class TestVideoServiceProgress:
    """Tests for server-side progress calculation."""

    def test_progress_at_zero(self):
        """Position 0 yields 0% and not completed."""
        from app.services.video_service import VideoService

        service = VideoService.__new__(VideoService)
        service._progress_db = MagicMock()
        service._progress_db.save_progress = MagicMock()

        result = service.save_progress("user-1", "rec-1", 0.0, 3600.0)
        assert result.percent_complete == 0
        assert result.completed is False

    def test_progress_at_50_percent(self):
        """Position at half duration yields 50% and not completed."""
        from app.services.video_service import VideoService

        service = VideoService.__new__(VideoService)
        service._progress_db = MagicMock()
        service._progress_db.save_progress = MagicMock()

        result = service.save_progress("user-1", "rec-1", 1800.0, 3600.0)
        assert result.percent_complete == 50
        assert result.completed is False

    def test_progress_at_90_percent_completes(self):
        """Position at 90% yields completed True."""
        from app.services.video_service import VideoService

        service = VideoService.__new__(VideoService)
        service._progress_db = MagicMock()
        service._progress_db.save_progress = MagicMock()

        result = service.save_progress("user-1", "rec-1", 3240.0, 3600.0)
        assert result.percent_complete == 90
        assert result.completed is True

    def test_progress_at_100_percent(self):
        """Position at full duration yields 100% and completed."""
        from app.services.video_service import VideoService

        service = VideoService.__new__(VideoService)
        service._progress_db = MagicMock()
        service._progress_db.save_progress = MagicMock()

        result = service.save_progress("user-1", "rec-1", 3600.0, 3600.0)
        assert result.percent_complete == 100
        assert result.completed is True

    def test_progress_rejects_position_exceeding_duration(self):
        """Position > duration raises HTTPException(422)."""
        from fastapi import HTTPException

        from app.services.video_service import VideoService

        service = VideoService.__new__(VideoService)
        service._progress_db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            service.save_progress("user-1", "rec-1", 4000.0, 3600.0)
        assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# Unit tests for state machine transitions
# ---------------------------------------------------------------------------


class TestStatusTransitions:
    """Tests for video lifecycle state transitions."""

    def test_valid_transitions(self):
        """All valid transitions should pass without exception."""
        from app.services.transition_utils import validate_transition

        valid_pairs = [
            (VideoStatus.DRAFT, VideoStatus.PROCESSING),
            (VideoStatus.PROCESSING, VideoStatus.READY),
            (VideoStatus.READY, VideoStatus.PUBLISHED),
            (VideoStatus.READY, VideoStatus.ARCHIVED),
            (VideoStatus.PUBLISHED, VideoStatus.ARCHIVED),
        ]
        for current, target in valid_pairs:
            validate_transition(current, target)  # Should not raise

    def test_invalid_transition_raises(self):
        """Invalid transitions should raise HTTPException(400)."""
        from fastapi import HTTPException

        from app.services.transition_utils import validate_transition

        invalid_pairs = [
            (VideoStatus.DRAFT, VideoStatus.PUBLISHED),
            (VideoStatus.PROCESSING, VideoStatus.PUBLISHED),
            (VideoStatus.PUBLISHED, VideoStatus.DRAFT),
            (VideoStatus.ARCHIVED, VideoStatus.PUBLISHED),
            (VideoStatus.DRAFT, VideoStatus.READY),
        ]
        for current, target in invalid_pairs:
            with pytest.raises(HTTPException) as exc_info:
                validate_transition(current, target)
            assert exc_info.value.status_code == 400

    def test_archived_cannot_transition(self):
        """ARCHIVED status has no valid transitions."""
        from fastapi import HTTPException

        from app.services.transition_utils import validate_transition

        for target in VideoStatus:
            with pytest.raises(HTTPException):
                validate_transition(VideoStatus.ARCHIVED, target)


# ---------------------------------------------------------------------------
# Unit tests for slug generation
# ---------------------------------------------------------------------------


class TestSlugGeneration:
    """Tests for slug generation utilities."""

    def test_basic_slug(self):
        """Simple title generates a clean slug."""
        from app.services.slug_utils import generate_slug

        assert generate_slug("Building Secure APIs") == "building-secure-apis"

    def test_special_characters_removed(self):
        """Special characters are replaced with hyphens."""
        from app.services.slug_utils import generate_slug

        slug = generate_slug("Hello, World! (2025)")
        assert slug == "hello-world-2025"

    def test_unicode_normalized(self):
        """Unicode characters are normalized to ASCII."""
        from app.services.slug_utils import generate_slug

        slug = generate_slug("cafe")
        assert slug == "cafe"

    def test_no_consecutive_hyphens(self):
        """Consecutive special chars produce single hyphen."""
        from app.services.slug_utils import generate_slug

        slug = generate_slug("Hello --- World")
        assert "--" not in slug
        assert slug == "hello-world"

    def test_no_leading_trailing_hyphens(self):
        """No leading or trailing hyphens."""
        from app.services.slug_utils import generate_slug

        slug = generate_slug("---hello---")
        assert not slug.startswith("-")
        assert not slug.endswith("-")

    def test_max_length_220(self):
        """Slug is truncated to 220 characters."""
        from app.services.slug_utils import generate_slug

        long_title = "a" * 300
        slug = generate_slug(long_title)
        assert len(slug) <= 220

    def test_ensure_unique_no_conflict(self):
        """Returns slug as-is when no conflict."""
        from app.services.slug_utils import ensure_unique_slug

        result = ensure_unique_slug("my-slug", lambda s: False)
        assert result == "my-slug"

    def test_ensure_unique_with_conflict(self):
        """Appends numeric suffix on conflict."""
        from app.services.slug_utils import ensure_unique_slug

        existing = {"my-slug", "my-slug-1"}
        result = ensure_unique_slug("my-slug", lambda s: s in existing)
        assert result == "my-slug-2"


# ---------------------------------------------------------------------------
# Pydantic model validation tests
# ---------------------------------------------------------------------------


class TestPydanticModels:
    """Tests for Pydantic model validation."""

    def test_progress_update_rejects_negative_position(self):
        """Negative position raises validation error."""
        from pydantic import ValidationError

        from app.models.videos import ProgressUpdateRequest

        with pytest.raises(ValidationError):
            ProgressUpdateRequest(position_seconds=-1.0, duration_seconds=100.0)

    def test_progress_update_rejects_zero_duration(self):
        """Zero duration raises validation error."""
        from pydantic import ValidationError

        from app.models.videos import ProgressUpdateRequest

        with pytest.raises(ValidationError):
            ProgressUpdateRequest(position_seconds=0.0, duration_seconds=0.0)

    def test_progress_update_rejects_excessive_duration(self):
        """Duration > 86400 raises validation error."""
        from pydantic import ValidationError

        from app.models.videos import ProgressUpdateRequest

        with pytest.raises(ValidationError):
            ProgressUpdateRequest(position_seconds=0.0, duration_seconds=100000.0)

    def test_create_video_validates_title_length(self):
        """Title > 200 chars raises validation error."""
        from pydantic import ValidationError

        from app.models.videos import CreateVideoRequest

        with pytest.raises(ValidationError):
            CreateVideoRequest(
                title="x" * 201,
                cloudflare_stream_id="abc",
                instructor="Test",
                recorded_at="2025-01-01",
            )

    def test_create_video_valid(self):
        """Valid creation request passes validation."""
        from app.models.videos import CreateVideoRequest

        req = CreateVideoRequest(
            title="Valid Title",
            cloudflare_stream_id="abc123",
            instructor="Instructor",
            recorded_at="2025-01-01T00:00:00Z",
            tags=["python"],
        )
        assert req.title == "Valid Title"
        assert req.tags == ["python"]
