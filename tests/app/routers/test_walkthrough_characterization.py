"""Characterization tests pinning the walkthrough access gate for BUILDER-tier
walkthroughs (refactor safety net).

These tests lock in the *current* behavior of the walkthrough paywall gate in
``app.routers.content`` (``POST /api/walkthroughs/{id}/progress``) across the
membership-tier / subscription-status / role matrix, BEFORE the
``is_builder_equivalent()`` refactor introduces STUDENT_BUILDER.

Every assertion here MUST pass against the UNCHANGED production code. After the
refactor (task 3.2) swaps ``item_tier == "BUILDER"`` for
``is_builder_equivalent(item_tier)``, these same assertions MUST still pass —
Builder behavior is unchanged by the refactor.

The gate (for a walkthrough whose access tier is ``BUILDER``) grants access iff:
  - the user is an admin, OR
  - the user's membership is ``BUILDER`` AND ``subscription_status == "active"``, OR
  - the user holds a ``CONTRIBUTOR_ROLE`` record.
Otherwise the endpoint returns 403.

Requirements: 1.10
Property 4: Builder behavior is unchanged by the refactor
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

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


def _membership_item(tier: str | None, status: str | None) -> dict | None:
    """Build a MEMBERSHIP DynamoDB-shaped item, or None for 'no membership'."""
    if tier is None:
        return None
    item: dict = {"membership_tier": {"S": tier}}
    if status is not None:
        item["subscription_status"] = {"S": status}
    return item


def _contributor_response(has_role: bool) -> dict:
    """Build the boto3 get_item response for a CONTRIBUTOR_ROLE lookup."""
    return {"Item": {"PK": {"S": "USER#user-123"}}} if has_role else {}


def _post_builder_walkthrough(
    client,
    token,
    *,
    membership,
    has_contributor,
):
    """Drive POST progress against a BUILDER-tier walkthrough with the given
    membership item and contributor-role presence. Returns the response."""
    with (
        patch("app.routers.content.AdminService") as MockAdmin,
        patch("app.routers.content.MembershipDB") as MockMembership,
        patch("app.routers.content.boto3.client") as mock_boto,
        patch("app.routers.content._update_progress") as mock_update,
    ):
        MockAdmin.return_value.get_walkthrough_access_tier.return_value = "BUILDER"
        MockMembership.return_value.get_membership.return_value = membership
        mock_boto.return_value.get_item.return_value = _contributor_response(
            has_contributor
        )
        resp = client.post(
            "/api/walkthroughs/wt-builder/progress",
            headers=_auth(token),
            json={"status": "completed"},
        )
    return resp, mock_update


# The membership-tier × subscription-status matrix exercised against a
# BUILDER-tier walkthrough. Only (BUILDER, active) grants access via the
# membership branch; every other combination must be denied unless the user
# is admin or holds the contributor role.
STATUS_VALUES = ["active", "past_due", "canceled", None]
TIER_VALUES = ["BUILDER", "FREE", "EXPLORER", None]


class TestWalkthroughGateBuilderMembershipMatrix:
    """Pin the membership-tier/subscription-status matrix for a BUILDER
    walkthrough when the user is NOT admin and has NO contributor role."""

    @pytest.mark.parametrize("status", STATUS_VALUES)
    def test_builder_tier_only_active_grants_access(self, client, mock_auth, status):
        token = _make_token()
        resp, mock_update = _post_builder_walkthrough(
            client,
            token,
            membership=_membership_item("BUILDER", status),
            has_contributor=False,
        )
        if status == "active":
            assert resp.status_code == 200
            mock_update.assert_called_once_with("user-123", "wt-builder", "completed")
        else:
            # past_due is excluded: access is cut off immediately on a failed
            # payment. canceled / missing status are likewise denied.
            assert resp.status_code == 403
            assert "Builder" in resp.json()["detail"]
            mock_update.assert_not_called()

    @pytest.mark.parametrize("tier", ["FREE", "EXPLORER", None])
    @pytest.mark.parametrize("status", STATUS_VALUES)
    def test_non_builder_tiers_denied(self, client, mock_auth, tier, status):
        token = _make_token()
        resp, mock_update = _post_builder_walkthrough(
            client,
            token,
            membership=_membership_item(tier, status),
            has_contributor=False,
        )
        assert resp.status_code == 403
        assert "Builder" in resp.json()["detail"]
        mock_update.assert_not_called()

    def test_no_membership_record_denied(self, client, mock_auth):
        token = _make_token()
        resp, mock_update = _post_builder_walkthrough(
            client,
            token,
            membership=None,
            has_contributor=False,
        )
        assert resp.status_code == 403
        mock_update.assert_not_called()


class TestWalkthroughGateAdminShortCircuit:
    """Admins bypass the membership/contributor checks entirely for a BUILDER
    walkthrough — no membership lookup is performed."""

    @pytest.mark.parametrize("status", STATUS_VALUES)
    @pytest.mark.parametrize("tier", TIER_VALUES)
    def test_admin_always_granted(self, client, mock_auth, tier, status):
        token = _make_admin_token()
        with (
            patch("app.routers.content.AdminService") as MockAdmin,
            patch("app.routers.content.MembershipDB") as MockMembership,
            patch("app.routers.content._update_progress") as mock_update,
        ):
            MockAdmin.return_value.get_walkthrough_access_tier.return_value = "BUILDER"
            resp = client.post(
                "/api/walkthroughs/wt-builder/progress",
                headers=_auth(token),
                json={"status": "completed"},
            )
        assert resp.status_code == 200
        mock_update.assert_called_once_with("admin-1", "wt-builder", "completed")
        # Admin short-circuits before any membership read.
        MockMembership.return_value.get_membership.assert_not_called()


class TestWalkthroughGateContributorShortCircuit:
    """A CONTRIBUTOR_ROLE record grants Builder-equivalent access regardless of
    membership tier/status (when the user is not admin)."""

    @pytest.mark.parametrize("status", STATUS_VALUES)
    @pytest.mark.parametrize("tier", ["FREE", "EXPLORER", None])
    def test_contributor_grants_access_for_non_builder(
        self, client, mock_auth, tier, status
    ):
        token = _make_token()
        resp, mock_update = _post_builder_walkthrough(
            client,
            token,
            membership=_membership_item(tier, status),
            has_contributor=True,
        )
        assert resp.status_code == 200
        mock_update.assert_called_once_with("user-123", "wt-builder", "completed")

    def test_contributor_grants_access_with_no_membership(self, client, mock_auth):
        token = _make_token()
        resp, mock_update = _post_builder_walkthrough(
            client,
            token,
            membership=None,
            has_contributor=True,
        )
        assert resp.status_code == 200
        mock_update.assert_called_once_with("user-123", "wt-builder", "completed")

    @pytest.mark.parametrize("status", ["past_due", "canceled", None])
    def test_contributor_grants_access_for_inactive_builder(
        self, client, mock_auth, status
    ):
        """Even an inactive BUILDER membership is granted when a contributor
        role is present (the contributor fallback runs after the membership
        branch fails)."""
        token = _make_token()
        resp, mock_update = _post_builder_walkthrough(
            client,
            token,
            membership=_membership_item("BUILDER", status),
            has_contributor=True,
        )
        assert resp.status_code == 200
        mock_update.assert_called_once_with("user-123", "wt-builder", "completed")


class TestWalkthroughGateFreeTierUnaffected:
    """A FREE-tier walkthrough is never gated — no membership/contributor
    checks happen regardless of the user's tier/status."""

    def test_free_walkthrough_grants_without_membership_check(self, client, mock_auth):
        token = _make_token()
        with (
            patch("app.routers.content.AdminService") as MockAdmin,
            patch("app.routers.content.MembershipDB") as MockMembership,
            patch("app.routers.content._update_progress") as mock_update,
        ):
            MockAdmin.return_value.get_walkthrough_access_tier.return_value = "FREE"
            resp = client.post(
                "/api/walkthroughs/wt-free/progress",
                headers=_auth(token),
                json={"status": "completed"},
            )
        assert resp.status_code == 200
        mock_update.assert_called_once_with("user-123", "wt-free", "completed")
        MockMembership.return_value.get_membership.assert_not_called()
