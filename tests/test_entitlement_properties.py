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
