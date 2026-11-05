"""Characterization tests pinning Builder access behavior at three gates.

Originally task 1.1 of the student-builder-membership spec, these tests pin the
access decisions at three Builder gates:

  1. ``EntitlementService.has_video_recordings_entitlement`` — the single gate
     behind video recordings and Builder Sessions access.
  2. ``routers/progress.py`` ``save_progress`` capstone gate.
  3. ``routers/progress.py`` ``_determine_journey_tier`` (returns ``"BUILDER"``
     only for an active Builder member or an admin, else ``"FREE"``).

Each gate is pinned over the matrix:

    membership_tier == "BUILDER"
      × subscription_status ∈ {active, past_due, canceled, none}
      × role ∈ {admin, contributor, neither}

The CONTRIBUTOR_ROLE no longer grants Builder-equivalent access: that perk was
time-limited and expired on 2026-11-01. The ``contributor`` role is still swept
across the matrix, but it must now produce the SAME decision as ``neither`` —
the gates ignore it. Requirements: 1.10
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import Settings
from app.main import app
from app.routers.progress import _determine_journey_tier
from app.services.entitlement_service import EntitlementService

# ---------------------------------------------------------------------------
# The characterization matrix
# ---------------------------------------------------------------------------
#
# Subscription statuses exercised. ``None`` models a user with no MEMBERSHIP
# record attribute for subscription_status (treated as not-active everywhere).
BUILDER_SUB_STATUSES = ["active", "past_due", "canceled", None]

# Roles exercised independently of tier.
ROLES = ["admin", "contributor", "neither"]


def _expected_builder_decision(subscription_status: str | None, role: str) -> bool:
    """The reference access decision for a BUILDER-tier user.

    Behavior at the entitlement and capstone gates:
      - admin        -> always granted
      - contributor  -> NO special grant (the perk expired 2026-11-01); the
                        contributor is judged purely on tier + status
      - neither      -> granted iff subscription_status == "active"

    Because the matrix pins a BUILDER-tier user, a contributor and a plain
    member land on the identical decision: granted iff the subscription is
    active. The ``role`` dimension is still swept to prove the contributor role
    has no effect.

    past_due is intentionally NOT active: Builders with a failed payment lose
    access immediately until payment is updated.
    """
    if role == "admin":
        return True
    return subscription_status == "active"


# ===========================================================================
# Gate 1 — EntitlementService.has_video_recordings_entitlement
# ===========================================================================
#
# This gate funnels video recordings AND Builder Sessions access. It is a pure
# method over (user, membership) plus a MembershipDB-backed contributor lookup,
# so we drive it directly with a mocked MembershipDB (mirroring
# tests/test_entitlement_properties.py).


def _make_entitlement_service(contributor_item=None):
    """Build an EntitlementService whose MembershipDB contributor lookup is
    mocked. ``contributor_item`` is returned by ``get_contributor_role`` (None
    means no contributor role)."""
    service = EntitlementService.__new__(EntitlementService)
    membership_db = MagicMock()
    membership_db.get_contributor_role.return_value = contributor_item
    service._membership_db = membership_db
    return service


def _builder_membership(subscription_status: str | None) -> dict:
    """A raw DynamoDB MEMBERSHIP item for a BUILDER-tier user.

    When ``subscription_status`` is None the attribute is omitted entirely,
    modelling a record with no subscription_status set.
    """
    item: dict = {"membership_tier": {"S": "BUILDER"}}
    if subscription_status is not None:
        item["subscription_status"] = {"S": subscription_status}
    return item


@pytest.mark.parametrize("subscription_status", BUILDER_SUB_STATUSES)
@pytest.mark.parametrize("role", ROLES)
def test_entitlement_builder_matrix(subscription_status, role):
    """Pin has_video_recordings_entitlement over Builder × status × role."""
    user = {"sub": "user-1", "is_admin": role == "admin"}
    contributor_item = {"role": {"S": "contributor"}} if role == "contributor" else None
    service = _make_entitlement_service(contributor_item=contributor_item)

    result = service.has_video_recordings_entitlement(
        user, _builder_membership(subscription_status)
    )

    assert result is _expected_builder_decision(
        subscription_status, role
    ), f"entitlement gate changed for status={subscription_status!r}, role={role!r}"


# ===========================================================================
# Shared test harness for the progress router (capstone + journey)
# ===========================================================================

TEST_SECRET_KEY = "test-secret-key-for-jwt-signing-32chars"

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
    """Token whose provider+login (github:adminuser) matches admin_users."""
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


def _membership_get_item_response(subscription_status: str | None) -> dict:
    """DynamoDB get_item response for a BUILDER MEMBERSHIP record."""
    item: dict = {"membership_tier": {"S": "BUILDER"}}
    if subscription_status is not None:
        item["subscription_status"] = {"S": subscription_status}
    return {"Item": item}


def _make_get_item_side_effect(subscription_status: str | None, role: str):
    """Build a boto3 get_item side effect keyed by the requested SK.

    - MEMBERSHIP     -> BUILDER record with the given subscription_status.
    - CONTRIBUTOR_ROLE -> an item only when role == "contributor".
    """

    def side_effect(**kwargs):
        sk = kwargs["Key"]["SK"]["S"]
        if sk == "MEMBERSHIP":
            return _membership_get_item_response(subscription_status)
        if sk == "CONTRIBUTOR_ROLE":
            if role == "contributor":
                return {"Item": {"PK": {"S": "USER#user-123"}}}
            return {}
        return {}

    return side_effect


# ===========================================================================
# Gate 2 — save_progress capstone gate (PUT /progress with repo_url)
# ===========================================================================
#
# A 200 (submission accepted) characterizes "access granted"; a 403
# characterizes "access denied". We hold the repo_url valid so the only gate
# that can produce a 403 is the Builder-access check.


@pytest.mark.parametrize("subscription_status", BUILDER_SUB_STATUSES)
@pytest.mark.parametrize("role", ROLES)
def test_capstone_gate_builder_matrix(client, mock_auth, subscription_status, role):
    """Pin the capstone gate over Builder × status × role."""
    token = _make_admin_token() if role == "admin" else _make_token()

    with (
        patch("app.routers.progress.boto3.client") as mock_boto,
        patch(
            "app.services.progress_db.ProgressDB.get_capstone_submission",
            return_value=None,
        ),
        patch("app.services.progress_db.ProgressDB.save_capstone_submission"),
        patch("app.services.progress_db.ProgressDB.delete_progress"),
        patch("app.services.email.send_capstone_notification", return_value=True),
    ):
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.get_item.side_effect = _make_get_item_side_effect(
            subscription_status, role
        )

        # Admins authenticate as github:adminuser, so the repo must be under
        # that account; everyone else is github:testuser.
        owner = "adminuser" if role == "admin" else "testuser"
        resp = client.put(
            "/progress",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "content_id": "cap-1",
                "repo_url": f"https://github.com/{owner}/myrepo",
            },
        )

    granted = _expected_builder_decision(subscription_status, role)
    if granted:
        assert resp.status_code == 200, (
            f"capstone gate denied an expected-granted case: "
            f"status={subscription_status!r}, role={role!r} -> {resp.status_code}"
        )
        assert resp.json()["submission"]["repo_name"] == "myrepo"
    else:
        assert resp.status_code == 403, (
            f"capstone gate granted an expected-denied case: "
            f"status={subscription_status!r}, role={role!r} -> {resp.status_code}"
        )
        assert "Builder" in resp.json()["detail"]


# ===========================================================================
# Gate 3 — _determine_journey_tier
# ===========================================================================
#
# Returns "BUILDER" only for an admin OR a BUILDER-tier user with an active
# subscription; "FREE" otherwise. The contributor role is NOT consulted by this
# function, so a contributor without an active Builder subscription maps to
# "FREE" — this is captured as current behavior.


def _journey_expected(subscription_status: str | None, role: str) -> str:
    """Reference tier returned by the CURRENT _determine_journey_tier.

    Admin -> BUILDER. Otherwise BUILDER iff active (tier is BUILDER here).
    Contributor role is not considered by this function.
    """
    if role == "admin":
        return "BUILDER"
    return "BUILDER" if subscription_status == "active" else "FREE"


@pytest.mark.parametrize("subscription_status", BUILDER_SUB_STATUSES)
@pytest.mark.parametrize("role", ROLES)
def test_determine_journey_tier_builder_matrix(subscription_status, role):
    """Pin _determine_journey_tier over Builder × status × role."""
    user = {"sub": "user-123", "is_admin": role == "admin"}

    with patch("app.routers.progress.boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.get_item.side_effect = _make_get_item_side_effect(
            subscription_status, role
        )

        result = _determine_journey_tier(user, TEST_SETTINGS)

    assert result == _journey_expected(subscription_status, role), (
        f"journey tier changed for status={subscription_status!r}, role={role!r}: "
        f"got {result!r}"
    )
