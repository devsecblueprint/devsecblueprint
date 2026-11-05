"""Property tests for VIDEO_RECORDINGS entitlement derivation.

Property 1: Entitlement derivation correctness
For any user with a given (tier, subscription_status, is_admin) triple,
the VIDEO_RECORDINGS entitlement SHALL be granted if and only if
is_admin == True OR (tier == "BUILDER" AND subscription_status == "active").

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.entitlement_service import EntitlementService

TIERS = ["FREE", "BUILDER", "EXPLORER", "", "CONTRIBUTOR"]
SUBSCRIPTION_STATUSES = [
    "active",
    "canceled",
    "past_due",
    "trialing",
    "",
    "incomplete",
]


@given(
    tier=st.sampled_from(TIERS),
    subscription_status=st.sampled_from(SUBSCRIPTION_STATUSES),
    is_admin=st.booleans(),
)
@settings(max_examples=200)
def test_entitlement_derivation_correctness(
    tier: str,
    subscription_status: str,
    is_admin: bool,
) -> None:
    """Verify entitlement is granted iff admin or BUILDER+active."""
    user = {"sub": "user-123", "is_admin": is_admin}

    membership: dict | None = None
    if tier or subscription_status:
        membership = {
            "membership_tier": {"S": tier},
            "subscription_status": {"S": subscription_status},
        }

    service = EntitlementService.__new__(EntitlementService)
    result = service.has_video_recordings_entitlement(user, membership)

    expected = is_admin or (tier == "BUILDER" and subscription_status == "active")
    assert result == expected, (
        f"Expected {expected} for tier={tier!r}, "
        f"status={subscription_status!r}, admin={is_admin}"
    )


@given(is_admin=st.booleans())
@settings(max_examples=50)
def test_entitlement_none_membership_denies_non_admin(
    is_admin: bool,
) -> None:
    """Verify that None membership denies non-admins."""
    user = {"sub": "user-456", "is_admin": is_admin}

    service = EntitlementService.__new__(EntitlementService)
    result = service.has_video_recordings_entitlement(user, None)

    if is_admin:
        assert result is True
    else:
        assert result is False


# ---------------------------------------------------------------------------
# Contributor role no longer grants Builder-equivalent access.
#
# The contributor perk was time-limited and expired on 2026-11-01. A
# CONTRIBUTOR_ROLE record now carries NO entitlement: contributors are granted
# access only through their own membership tier (BUILDER-equivalent + active)
# or admin status, exactly like any other user. The role record is retained
# for recognition/admin filtering, so the entitlement service must not even
# consult it.
# ---------------------------------------------------------------------------

from unittest.mock import MagicMock


def _make_service(membership_item):
    """Build an EntitlementService backed by a mocked MembershipDB.

    Args:
        membership_item: value returned by get_membership.
    """
    service = EntitlementService.__new__(EntitlementService)
    membership_db = MagicMock()
    membership_db.get_membership.return_value = membership_item
    service._membership_db = membership_db
    return service


def test_contributor_without_membership_is_denied():
    """A contributor with no MEMBERSHIP record is no longer granted access.

    The perk expired; with no membership record there is nothing to grant on.
    """
    user = {"sub": "contributor-1", "is_admin": False}
    service = _make_service(None)

    assert service.has_video_recordings_entitlement(user) is False


def test_contributor_with_free_membership_is_denied():
    """A contributor who only holds a FREE membership is denied.

    Previously the contributor role overrode the FREE tier; it no longer does.
    """
    user = {"sub": "contributor-2", "is_admin": False}
    membership = {
        "membership_tier": {"S": "FREE"},
        "subscription_status": {"S": ""},
    }
    service = _make_service(membership)

    assert service.has_video_recordings_entitlement(user) is False


def test_contributor_with_builder_membership_is_granted():
    """A contributor who independently holds an active BUILDER membership is
    still granted — via the membership tier, not the contributor role."""
    user = {"sub": "contributor-3", "is_admin": False}
    membership = {
        "membership_tier": {"S": "BUILDER"},
        "subscription_status": {"S": "active"},
    }
    service = _make_service(membership)

    assert service.has_video_recordings_entitlement(user) is True


def test_non_contributor_without_membership_is_denied():
    """A non-contributor, non-admin with no membership is denied."""
    user = {"sub": "free-user", "is_admin": False}
    service = _make_service(None)

    assert service.has_video_recordings_entitlement(user) is False


def test_admin_short_circuits_before_lookups():
    """Admins are granted without any DynamoDB lookups."""
    user = {"sub": "admin-user", "is_admin": True}
    service = _make_service(None)

    assert service.has_video_recordings_entitlement(user) is True
    # Admin path must not perform any membership lookup.
    service._membership_db.get_membership.assert_not_called()


def test_entitlement_never_consults_contributor_role():
    """The entitlement gate must not read the CONTRIBUTOR_ROLE record at all.

    Guards against a regression that re-introduces the expired perk.
    """
    user = {"sub": "free-3", "is_admin": False}
    membership = {
        "membership_tier": {"S": "FREE"},
        "subscription_status": {"S": ""},
    }
    service = _make_service(membership)

    assert service.has_video_recordings_entitlement(user) is False
    service._membership_db.get_contributor_role.assert_not_called()
