"""Tests for the shared Builder-equivalence predicate ``is_builder_equivalent``.

Covers both concrete example cases and a Hypothesis property test asserting the
predicate is true for exactly the two canonical Builder-equivalent tier strings.

Validates: Requirements 1.2
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.tiers import (
    BUILDER,
    BUILDER_EQUIVALENT_TIERS,
    STUDENT_BUILDER,
    is_builder_equivalent,
)

# ---------------------------------------------------------------------------
# Concrete unit tests (Task 2.2)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tier, expected",
    [
        ("BUILDER", True),
        ("STUDENT_BUILDER", True),
        ("FREE", False),
        ("EXPLORER", False),
        ("", False),
        (None, False),
        ("builder", False),  # lowercase is not canonical
    ],
)
def test_is_builder_equivalent_concrete_cases(tier, expected):
    """is_builder_equivalent returns True only for the canonical Builder tiers."""
    assert is_builder_equivalent(tier) is expected


def test_builder_equivalent_tiers_membership():
    """The exposed set contains exactly the two Builder-equivalent tiers."""
    assert BUILDER_EQUIVALENT_TIERS == frozenset({BUILDER, STUDENT_BUILDER})


# ---------------------------------------------------------------------------
# Property test (Task 2.3)
# ---------------------------------------------------------------------------

_BUILDER_EQUIVALENT = {"BUILDER", "STUDENT_BUILDER"}


@given(tier=st.text())
@settings(max_examples=200)
def test_builder_equivalence_over_arbitrary_strings(tier: str) -> None:
    """Feature: student-builder-membership, Property 1: Builder equivalence over arbitrary tier strings

    For any arbitrary string ``tier``, ``is_builder_equivalent(tier)`` is True
    if and only if ``tier`` is exactly ``"BUILDER"`` or ``"STUDENT_BUILDER"``.

    Validates: Requirements 1.2
    """
    assert is_builder_equivalent(tier) is (tier in _BUILDER_EQUIVALENT)
