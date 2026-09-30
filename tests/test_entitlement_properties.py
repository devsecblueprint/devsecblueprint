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

from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def _make_service_with_membership(membership_item):
    """Build an EntitlementService whose membership lookup returns the given
    item, and whose settings expose a membership_table name (read by the
    contributor lookup)."""
    service = EntitlementService.__new__(EntitlementService)
    membership_db = MagicMock()
    membership_db.get_membership.return_value = membership_item
    membership_db._settings = SimpleNamespace(membership_table="test-membership")
    service._membership_db = membership_db
    return service


def _dynamodb_with_contributor(has_role: bool):
    """Return a boto3-client factory whose get_item reports whether a
    CONTRIBUTOR_ROLE record exists."""
    client = MagicMock()
    client.get_item.return_value = (
        {"Item": {"role": {"S": "contributor"}}} if has_role else {}
    )
    return MagicMock(return_value=client)


def test_contributor_without_membership_is_granted():
    """A contributor with no MEMBERSHIP record must still get access."""
    user = {"sub": "contributor-1", "is_admin": False}
    service = _make_service_with_membership(None)  # no membership record

    with patch("boto3.client", _dynamodb_with_contributor(True)):
        assert service.has_video_recordings_entitlement(user) is True


def test_contributor_with_free_membership_is_granted():
    """A contributor who also has a FREE membership record still gets access."""
    user = {"sub": "contributor-2", "is_admin": False}
    membership = {
        "membership_tier": {"S": "FREE"},
        "subscription_status": {"S": ""},
    }
    service = _make_service_with_membership(membership)

    with patch("boto3.client", _dynamodb_with_contributor(True)):
        assert service.has_video_recordings_entitlement(user) is True


def test_non_contributor_without_membership_is_denied():
    """A non-contributor, non-admin with no membership is denied."""
    user = {"sub": "free-user", "is_admin": False}
    service = _make_service_with_membership(None)

    with patch("boto3.client", _dynamodb_with_contributor(False)):
        assert service.has_video_recordings_entitlement(user) is False


def test_admin_short_circuits_before_lookups():
    """Admins are granted without any DynamoDB lookups."""
    user = {"sub": "admin-user", "is_admin": True}
    service = _make_service_with_membership(None)

    boto3_factory = _dynamodb_with_contributor(False)
    with patch("boto3.client", boto3_factory):
        assert service.has_video_recordings_entitlement(user) is True
    # Admin path should not perform a contributor lookup.
    boto3_factory.assert_not_called()
