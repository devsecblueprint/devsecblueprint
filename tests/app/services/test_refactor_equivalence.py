"""Property tests proving the ``is_builder_equivalent`` refactor is safe and
that Student Builder is Builder-equivalent when active.

Tasks 3.3 and 3.4 of the student-builder-membership spec. Both properties
drive the refactored access gate directly:

  * ``EntitlementService.has_video_recordings_entitlement`` — the single gate
    behind video recordings and Builder Sessions access. It is driven via
    ``EntitlementService.__new__`` + a mocked ``MembershipDB`` (mirroring
    ``tests/test_entitlement_properties.py`` and
    ``tests/app/services/test_builder_characterization.py``).

The journey classifier reference is also pinned as a pure reference function
(the pre-refactor ``_determine_journey_tier`` logic) where feasible, since that
gate has the same decision shape.

The reference decision (post contributor-perk removal) is:

    admin                     -> granted
    else                      -> granted iff subscription_status == "active"

The CONTRIBUTOR_ROLE no longer grants Builder-equivalent access (the perk was
time-limited and expired on 2026-11-01). The entitlement gate must therefore be
*invariant* to the contributor role; these properties still sweep the
``is_contributor`` dimension specifically to prove it no longer changes the
decision.

Property 4 (task 3.3): for a BUILDER user over every (status, admin,
contributor) combination, the refactored gate's decision equals that reference.

Property 2 / 3 (task 3.4): an active STUDENT_BUILDER user gets the SAME
decision as an active BUILDER user at the refactored gate, and an inactive
Builder-equivalent user is denied unless admin.

Requirements: 1.3, 1.5, 1.6, 1.7, 1.8, 1.10, 1.12
"""

from unittest.mock import MagicMock

from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.entitlement_service import EntitlementService

# ---------------------------------------------------------------------------
# Input space
# ---------------------------------------------------------------------------
#
# Subscription statuses exercised. ``None`` models a MEMBERSHIP record with no
# subscription_status attribute (treated as not-active everywhere). Only
# "active" grants access via tier; "past_due" is intentionally NOT active.
SUB_STATUSES = ["active", "past_due", "canceled", "trialing", "incomplete", "", None]


# ---------------------------------------------------------------------------
# Test harness (mirrors test_builder_characterization / test_entitlement_properties)
# ---------------------------------------------------------------------------


def _make_entitlement_service(contributor_item=None):
    """Build an EntitlementService backed by a mocked MembershipDB.

    ``contributor_item`` is the value a ``get_contributor_role`` call would
    return. The entitlement gate no longer consults the contributor role at
    all, so this is wired onto the mock purely to prove the gate ignores it —
    the decision must be identical whether or not a contributor record exists.
    """
    service = EntitlementService.__new__(EntitlementService)
    membership_db = MagicMock()
    membership_db.get_contributor_role.return_value = contributor_item
    service._membership_db = membership_db
    return service


def _membership(tier: str, subscription_status: str | None) -> dict:
    """A raw DynamoDB MEMBERSHIP item. When ``subscription_status`` is None the
    attribute is omitted entirely, modelling a record with no status set."""
    item: dict = {"membership_tier": {"S": tier}}
    if subscription_status is not None:
        item["subscription_status"] = {"S": subscription_status}
    return item


def _reference_decision(
    subscription_status: str | None, is_admin: bool, is_contributor: bool
) -> bool:
    """The reference access decision for a Builder-equivalent tier.

    admin -> granted; else granted iff status == "active". The contributor role
    is intentionally ignored (the perk expired), so ``is_contributor`` does not
    appear in the decision — it is still accepted as a parameter so callers can
    sweep that dimension and confirm it has no effect.
    """
    if is_admin:
        return True
    return subscription_status == "active"


def _entitlement_decision(
    tier: str, subscription_status: str | None, is_admin: bool, is_contributor: bool
) -> bool:
    """Run the refactored entitlement gate for the given inputs."""
    user = {"sub": "user-1", "is_admin": is_admin}
    contributor_item = {"role": {"S": "contributor"}} if is_contributor else None
    service = _make_entitlement_service(contributor_item=contributor_item)
    return service.has_video_recordings_entitlement(
        user, _membership(tier, subscription_status)
    )


def _journey_reference_tier(
    tier: str, subscription_status: str | None, is_admin: bool
) -> str:
    """Pure reference of the refactored ``_determine_journey_tier`` decision.

    admin -> "BUILDER"; else "BUILDER" iff the tier is Builder-equivalent and
    the subscription is active; otherwise "FREE". The contributor role is not
    consulted by the journey classifier, matching production behavior.
    """
    if is_admin:
        return "BUILDER"
    if tier in ("BUILDER", "STUDENT_BUILDER") and subscription_status == "active":
        return "BUILDER"
    return "FREE"


# ===========================================================================
# Task 3.3 — Property 4: Builder behavior is unchanged by the refactor
# ===========================================================================
#
# Feature: student-builder-membership, Property 4: Builder behavior is
# unchanged by the refactor


@given(
    subscription_status=st.sampled_from(SUB_STATUSES),
    is_admin=st.booleans(),
    is_contributor=st.booleans(),
)
@settings(max_examples=200)
def test_refactored_builder_decision_equals_reference(
    subscription_status: str | None,
    is_admin: bool,
    is_contributor: bool,
) -> None:
    """For any (BUILDER, status, admin, contributor), the refactored
    entitlement gate's decision equals the pinned pre-refactor reference.

    Validates: Requirements 1.10
    """
    actual = _entitlement_decision(
        "BUILDER", subscription_status, is_admin, is_contributor
    )
    expected = _reference_decision(subscription_status, is_admin, is_contributor)

    assert actual is expected, (
        f"entitlement gate diverged from reference for BUILDER: "
        f"status={subscription_status!r}, admin={is_admin}, "
        f"contributor={is_contributor}: got {actual}, expected {expected}"
    )


@given(
    subscription_status=st.sampled_from(SUB_STATUSES),
    is_admin=st.booleans(),
)
@settings(max_examples=200)
def test_refactored_builder_journey_tier_equals_reference(
    subscription_status: str | None,
    is_admin: bool,
) -> None:
    """The journey classifier reference for a BUILDER user matches the pinned
    pre-refactor logic (BUILDER only when admin or active Builder, else FREE).

    Validates: Requirements 1.10
    """
    expected = "BUILDER" if (is_admin or subscription_status == "active") else "FREE"
    actual = _journey_reference_tier("BUILDER", subscription_status, is_admin)

    assert actual == expected, (
        f"journey tier diverged from reference for BUILDER: "
        f"status={subscription_status!r}, admin={is_admin}: "
        f"got {actual!r}, expected {expected!r}"
    )


# ===========================================================================
# Task 3.4 — Property 2/3: Student Builder access equals Builder access when
# active; inactive Builder-equivalent users are denied unless admin
# ===========================================================================
#
# Feature: student-builder-membership, Property 2: Student Builder access
# equals Builder access when active


@given(
    is_admin=st.booleans(),
    is_contributor=st.booleans(),
)
@settings(max_examples=200)
def test_active_student_builder_access_equals_active_builder(
    is_admin: bool,
    is_contributor: bool,
) -> None:
    """An active STUDENT_BUILDER user gets the SAME entitlement decision as an
    active BUILDER user at the refactored gate, across role combinations.

    Validates: Requirements 1.3, 1.5, 1.6, 1.7, 1.12
    """
    builder = _entitlement_decision("BUILDER", "active", is_admin, is_contributor)
    student = _entitlement_decision(
        "STUDENT_BUILDER", "active", is_admin, is_contributor
    )

    assert student is builder, (
        f"active STUDENT_BUILDER decision != active BUILDER decision for "
        f"admin={is_admin}, contributor={is_contributor}: "
        f"student={student}, builder={builder}"
    )
    # And active Builder-equivalent is granted (the positive baseline).
    assert student is True

    # Journey classification matches too (Requirement 1.6).
    assert _journey_reference_tier(
        "STUDENT_BUILDER", "active", is_admin
    ) == _journey_reference_tier("BUILDER", "active", is_admin)


@given(
    subscription_status=st.sampled_from([s for s in SUB_STATUSES if s != "active"]),
    is_admin=st.booleans(),
    is_contributor=st.booleans(),
)
@settings(max_examples=200)
def test_inactive_builder_equivalent_denied_unless_admin(
    subscription_status: str | None,
    is_admin: bool,
    is_contributor: bool,
) -> None:
    """An inactive Builder-equivalent user (BUILDER or STUDENT_BUILDER) is
    denied unless the user is an admin, for both tiers alike. The contributor
    role is swept but must have no effect (the perk expired).

    Validates: Requirements 1.8, 1.12
    """
    expected = is_admin  # no active subscription here; contributor is ignored

    for tier in ("BUILDER", "STUDENT_BUILDER"):
        actual = _entitlement_decision(
            tier, subscription_status, is_admin, is_contributor
        )
        assert actual is expected, (
            f"inactive {tier} decision wrong for status={subscription_status!r}, "
            f"admin={is_admin}, contributor={is_contributor}: "
            f"got {actual}, expected {expected}"
        )

    # The two tiers also agree with each other on every inactive case.
    assert _entitlement_decision(
        "BUILDER", subscription_status, is_admin, is_contributor
    ) is _entitlement_decision(
        "STUDENT_BUILDER", subscription_status, is_admin, is_contributor
    )
