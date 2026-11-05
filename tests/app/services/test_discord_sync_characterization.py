"""Characterization tests pinning the Discord granted-role set for a BUILDER
user (refactor safety net).

These tests lock in the *current* behavior of
``app.services.discord_sync._get_granted_role_ids`` for a user whose membership
tier is ``BUILDER``, BEFORE task 3.2 adds a ``STUDENT_BUILDER`` entry to
``_get_tier_role_map``.

The granted-role set for a BUILDER user is exactly:
  - the configured Builder tier role (``discord_role_builder_id``), plus
  - the contributor role (``discord_role_contributor_id``) IFF the user has a
    ``CONTRIBUTOR_ROLE`` record in DynamoDB.

Every assertion here MUST pass against the UNCHANGED production code, and MUST
still pass after the STUDENT_BUILDER role-map addition (which does not alter the
Builder mapping).

Requirements: 1.10
Property 4: Builder behavior is unchanged by the refactor
"""

import importlib
import os
import sys
from unittest.mock import MagicMock, patch

# Ensure backend is importable (mirrors tests/test_preservation_discord_sync.py).
backend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend")
sys.path.insert(0, os.path.abspath(backend_dir))


def _make_settings():
    """Mock Settings with the Discord role fields the role map reads."""
    s = MagicMock()
    s.membership_table = "test-membership-table"
    s.discord_role_free_id = "ROLE_FREE"
    s.discord_role_explorer_id = "ROLE_EXPLORER"
    s.discord_role_builder_id = "ROLE_BUILDER"
    s.discord_role_builder_academy_id = "ROLE_BUILDER_ACADEMY"
    s.discord_role_contributor_id = "ROLE_CONTRIBUTOR"
    return s


def _get_sync_module():
    """Import discord_sync with boto3 patched so no AWS client is created at import."""
    with patch("boto3.client"):
        import app.services.discord_sync as discord_sync_mod

        importlib.reload(discord_sync_mod)
        return discord_sync_mod


def _granted_with_contributor(user_id, tier, *, has_contributor):
    """Compute _get_granted_role_ids with the CONTRIBUTOR_ROLE lookup mocked."""
    settings = _make_settings()
    mock_dynamodb = MagicMock()
    mock_dynamodb.get_item.return_value = (
        {"Item": {"PK": {"S": f"USER#{user_id}"}}} if has_contributor else {}
    )
    with patch("boto3.client", return_value=mock_dynamodb):
        discord_sync = _get_sync_module()
        return discord_sync._get_granted_role_ids(user_id, tier, settings)


class TestBuilderTierRoleMapping:
    """The tier→role map resolves BUILDER to the configured Builder role."""

    def test_builder_maps_to_builder_role_id(self):
        settings = _make_settings()
        discord_sync = _get_sync_module()
        role_map = discord_sync._get_tier_role_map(settings)
        assert role_map["BUILDER"] == "ROLE_BUILDER"

    def test_tier_role_map_contains_known_tiers(self):
        """Pin the exact set of tier keys the map exposes.

        STUDENT_BUILDER now maps to the standard Builder role
        (``discord_role_builder_id``) — the same role as BUILDER. The
        BUILDER_ACADEMY entry is retained (mapped to
        ``discord_role_builder_academy_id``) so the Academy role stays managed
        and a stale Academy grant is removed as drift.
        """
        settings = _make_settings()
        discord_sync = _get_sync_module()
        role_map = discord_sync._get_tier_role_map(settings)
        assert role_map == {
            "FREE": "ROLE_FREE",
            "EXPLORER": "ROLE_EXPLORER",
            "BUILDER": "ROLE_BUILDER",
            "BUILDER_ACADEMY": "ROLE_BUILDER_ACADEMY",
            "STUDENT_BUILDER": "ROLE_BUILDER",
        }

    def test_student_builder_maps_to_builder_role(self):
        """STUDENT_BUILDER resolves to the standard Builder role — the same
        Discord role as BUILDER and exactly ``settings.discord_role_builder_id``
        — so students are indistinguishable from Builders in Discord. The
        BUILDER_ACADEMY mapping is retained only so the Academy role stays
        managed for drift cleanup."""
        settings = _make_settings()
        discord_sync = _get_sync_module()
        role_map = discord_sync._get_tier_role_map(settings)
        assert (
            role_map["STUDENT_BUILDER"]
            == role_map["BUILDER"]
            == settings.discord_role_builder_id
        )
        # The Academy role is still managed (present in the map) so a stale
        # academy grant on a former student is removed as drift.
        assert role_map["BUILDER_ACADEMY"] == settings.discord_role_builder_academy_id


class TestBuilderGrantedRoleSet:
    """Pin the exact granted-role set _get_granted_role_ids returns for a
    BUILDER user across the contributor-role presence matrix."""

    def test_builder_without_contributor_grants_only_builder_role(self):
        granted = _granted_with_contributor(
            "user-123", "BUILDER", has_contributor=False
        )
        assert granted == {"ROLE_BUILDER"}

    def test_builder_with_contributor_grants_builder_and_contributor_roles(self):
        granted = _granted_with_contributor("user-123", "BUILDER", has_contributor=True)
        assert granted == {"ROLE_BUILDER", "ROLE_CONTRIBUTOR"}

    def test_builder_granted_set_always_includes_builder_role(self):
        """The Builder tier role is present regardless of contributor status."""
        without = _granted_with_contributor(
            "user-123", "BUILDER", has_contributor=False
        )
        with_contrib = _granted_with_contributor(
            "user-123", "BUILDER", has_contributor=True
        )
        assert "ROLE_BUILDER" in without
        assert "ROLE_BUILDER" in with_contrib


class TestStudentBuilderRoleReconciliation:
    """A STUDENT_BUILDER user receives the standard Builder role, while the
    Academy role remains managed so a stale academy grant is removed as drift."""

    def test_student_builder_granted_set_is_builder_role_not_academy(self):
        """Granted set for a STUDENT_BUILDER user is exactly {ROLE_BUILDER}
        (the standard Builder role), NOT the academy role."""
        granted = _granted_with_contributor(
            "user-123", "STUDENT_BUILDER", has_contributor=False
        )
        assert granted == {"ROLE_BUILDER"}
        assert "ROLE_BUILDER_ACADEMY" not in granted

    def test_student_builder_with_contributor_grants_builder_and_contributor(self):
        granted = _granted_with_contributor(
            "user-123", "STUDENT_BUILDER", has_contributor=True
        )
        assert granted == {"ROLE_BUILDER", "ROLE_CONTRIBUTOR"}
        assert "ROLE_BUILDER_ACADEMY" not in granted

    def test_academy_role_still_in_managed_set_for_drift_removal(self):
        """The Academy role stays in the managed-role set so a stale academy
        role on a former student is removed as drift on the next sync, while
        the Builder role is added."""
        settings = _make_settings()
        discord_sync = _get_sync_module()
        managed = set(discord_sync._get_managed_role_ids(settings))
        assert "ROLE_BUILDER_ACADEMY" in managed
        assert "ROLE_BUILDER" in managed
