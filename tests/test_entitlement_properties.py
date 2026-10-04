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
# Contributor role grants Builder-equivalent access (regression tests)
#
# Contributors typically have NO MEMBERSHIP record — their access comes solely
# from a CONTRIBUTOR_ROLE record. The entitlement check must therefore honor
# the contributor role independently of the membership lookup, including when
# membership is None.
# ---------------------------------------------------------------------------

from unittest.mock import MagicMock


def _make_service(membership_item, contributor_item=None, contributor_error=None):
    """Build an EntitlementService backed by a mocked MembershipDB.

    Args:
        membership_item: value returned by get_membership.
        contributor_item: value returned by get_contributor_role (None = no
            contributor role; a dict = has the role).
        contributor_error: if set, get_contributor_role raises it instead.
    """
    service = EntitlementService.__new__(EntitlementService)
    membership_db = MagicMock()
    membership_db.get_membership.return_value = membership_item
    if contributor_error is not None:
        membership_db.get_contributor_role.side_effect = contributor_error
    else:
        membership_db.get_contributor_role.return_value = contributor_item
    service._membership_db = membership_db
    return service


def test_contributor_without_membership_is_granted():
    """A contributor with no MEMBERSHIP record must still get access."""
    user = {"sub": "contributor-1", "is_admin": False}
    service = _make_service(None, contributor_item={"role": {"S": "contributor"}})

    assert service.has_video_recordings_entitlement(user) is True


def test_contributor_with_free_membership_is_granted():
    """A contributor who also has a FREE membership record still gets access."""
    user = {"sub": "contributor-2", "is_admin": False}
    membership = {
        "membership_tier": {"S": "FREE"},
        "subscription_status": {"S": ""},
    }
    service = _make_service(membership, contributor_item={"role": {"S": "contributor"}})

    assert service.has_video_recordings_entitlement(user) is True


def test_non_contributor_without_membership_is_denied():
    """A non-contributor, non-admin with no membership is denied."""
    user = {"sub": "free-user", "is_admin": False}
    service = _make_service(None, contributor_item=None)

    assert service.has_video_recordings_entitlement(user) is False


def test_admin_short_circuits_before_lookups():
    """Admins are granted without any DynamoDB lookups."""
    user = {"sub": "admin-user", "is_admin": True}
    service = _make_service(None, contributor_item=None)

    assert service.has_video_recordings_entitlement(user) is True
    # Admin path should not perform any membership/contributor lookups.
    service._membership_db.get_contributor_role.assert_not_called()
    service._membership_db.get_membership.assert_not_called()


def test_contributor_lookup_error_falls_back_to_builder_membership():
    """If the contributor lookup errors, a BUILDER+active member is still
    granted via the membership-tier fallback (error is logged, not fatal)."""
    user = {"sub": "builder-1", "is_admin": False}
    membership = {
        "membership_tier": {"S": "BUILDER"},
        "subscription_status": {"S": "active"},
    }
    service = _make_service(
        membership, contributor_error=RuntimeError("dynamodb unavailable")
    )

    assert service.has_video_recordings_entitlement(user) is True


def test_contributor_lookup_error_denies_free_member():
    """If the contributor lookup errors and the member is only FREE, access is
    denied — but the failure is surfaced via logging, not silently."""
    user = {"sub": "free-2", "is_admin": False}
    membership = {
        "membership_tier": {"S": "FREE"},
        "subscription_status": {"S": ""},
    }
    service = _make_service(
        membership, contributor_error=RuntimeError("dynamodb unavailable")
    )

    assert service.has_video_recordings_entitlement(user) is False
