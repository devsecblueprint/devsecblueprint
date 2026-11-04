"""Shared membership-tier constants and the Builder-equivalence predicate.

Provides a single source of truth for the "Builder-or-better" access decision
so that every access-control call site can share one pure predicate instead of
a hardcoded ``membership_tier == "BUILDER"`` check. Adding a future
Builder-equivalent tier is a one-line change to ``BUILDER_EQUIVALENT_TIERS``.

Requirements: 1.2
"""

BUILDER = "BUILDER"
STUDENT_BUILDER = "STUDENT_BUILDER"

# Tiers that receive Builder-equivalent access.
BUILDER_EQUIVALENT_TIERS = frozenset({BUILDER, STUDENT_BUILDER})


def is_builder_equivalent(membership_tier: str | None) -> bool:
    """Return True iff the tier grants Builder-equivalent access.

    True for BUILDER and STUDENT_BUILDER. False for everything else,
    including None, "", and any unrecognized value. Case-sensitive on the
    canonical upper-cased tier values stored in DynamoDB.

    Args:
        membership_tier: The user's ``membership_tier`` value, or None.

    Returns:
        True only for the canonical ``"BUILDER"`` and ``"STUDENT_BUILDER"``
        values; False for None, ``""``, lowercase variants, and any other
        unrecognized value.
    """
    return membership_tier in BUILDER_EQUIVALENT_TIERS
