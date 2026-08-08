"""Preservation Property Tests — Existing Guild Member Sync and Non-Builder Tier Changes.

Written BEFORE implementing the fix. These tests capture the correct baseline
behavior for inputs where the bug condition does NOT hold:
- In-guild users get correct role reconciliation
- Unmanaged roles are never modified
- BUILDER→BUILDER renewals produce no lifecycle events
- Sync is idempotent

These tests should PASS on both unfixed and fixed code, confirming no regressions.

Requirements: 3.1, 3.2, 3.3, 3.6, 3.7, 3.8
"""

import importlib
import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings as hypothesis_settings, assume
from hypothesis import strategies as st

# Ensure backend is importable
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(backend_dir))


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

user_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
    min_size=5,
    max_size=20,
)

tier_strategy = st.sampled_from(["FREE", "EXPLORER", "BUILDER", "BUILDER_ACADEMY"])

# Unmanaged roles that should never be modified by sync
UNMANAGED_ROLES = [
    "ROLE_SCHOLAR",
    "ROLE_CONTRIBUTOR",
    "ROLE_COMMUNITY_MANAGER",
    "ROLE_ADMIN",
]

# Managed roles controlled by the sync system
MANAGED_ROLE_IDS = [
    "ROLE_FREE",
    "ROLE_EXPLORER",
    "ROLE_BUILDER",
    "ROLE_BUILDER_ACADEMY",
]

unmanaged_role_set_strategy = st.lists(
    st.sampled_from(UNMANAGED_ROLES),
    min_size=0,
    max_size=4,
    unique=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_settings():
    """Create a mock Settings object with all required Discord fields."""
    s = MagicMock()
    s.membership_table = "test-membership-table"
    s.progress_table = "test-progress-table"
    s.discord_guild_id = "123456789"
    s.discord_role_free_id = "ROLE_FREE"
    s.discord_role_explorer_id = "ROLE_EXPLORER"
    s.discord_role_builder_id = "ROLE_BUILDER"
    s.discord_role_builder_academy_id = "ROLE_BUILDER_ACADEMY"
    s.discord_bot_secret_name = "bot-secret"
    s.discord_secret_name = "discord-secret"
    s.discord_callback_url = "http://localhost/callback"
    s.stripe_secret_name = "stripe-secret"
    s.stripe_webhook_secret_name = "stripe-webhook-secret"
    s.frontend_origin = "http://localhost:3000"
    s.frontend_url = "http://localhost:3000"
    return s


TIER_TO_ROLE = {
    "FREE": "ROLE_FREE",
    "EXPLORER": "ROLE_EXPLORER",
    "BUILDER": "ROLE_BUILDER",
    "BUILDER_ACADEMY": "ROLE_BUILDER_ACADEMY",
}


def _make_discord_active_item(user_id, discord_user_id="disc_12345"):
    """Create a DynamoDB DISCORD_ACTIVE item."""
    return {
        "PK": {"S": f"USER#{user_id}"},
        "SK": {"S": "DISCORD_ACTIVE"},
        "discord_user_id": {"S": discord_user_id},
        "username": {"S": "testuser"},
        "display_name": {"S": "Test User"},
        "avatar_url": {"S": ""},
        "active": {"BOOL": True},
        "platform_state": {"S": "Server_Joined"},
        "connected_at": {"S": datetime.now(timezone.utc).isoformat()},
        "last_synced_at": {"S": ""},
        "last_sync_status": {"S": ""},
    }


def _make_membership_item(user_id, tier="FREE"):
    """Create a DynamoDB MEMBERSHIP item."""
    return {
        "PK": {"S": f"USER#{user_id}"},
        "SK": {"S": "MEMBERSHIP"},
        "membership_tier": {"S": tier},
        "subscription_status": {"S": "active"},
        "stripe_customer_id": {"S": "cus_test123"},
    }


def _get_sync_module():
    """Import discord_sync module with boto3 mocked to avoid AWS calls."""
    with patch("boto3.client"):
        import app.services.discord_sync as discord_sync_mod

        importlib.reload(discord_sync_mod)
        return discord_sync_mod


def _run_sync_user_roles(user_id, tier, current_discord_roles):
    """Run _sync_user_roles with proper mocks for an in-guild user.

    Args:
        user_id: User ID.
        tier: Membership tier.
        current_discord_roles: List of role IDs the user currently has in Discord.

    Returns:
        (result_dict, mock_discord_client) tuple.
    """
    mock_settings = _make_settings()
    discord_active_item = _make_discord_active_item(user_id)
    membership_item = _make_membership_item(user_id, tier)

    mock_dynamodb = MagicMock()

    def get_item_side_effect(**kwargs):
        key = kwargs.get("Key", {})
        sk = key.get("SK", {}).get("S", "")
        if sk == "DISCORD_ACTIVE":
            return {"Item": discord_active_item}
        elif sk == "MEMBERSHIP":
            return {"Item": membership_item}
        return {}

    mock_dynamodb.get_item.side_effect = get_item_side_effect

    mock_discord_client = MagicMock()
    mock_discord_client.get_member_roles.return_value = current_discord_roles
    mock_discord_client.add_role.return_value = True
    mock_discord_client.remove_role.return_value = True

    with patch("boto3.client", return_value=mock_dynamodb):
        discord_sync = _get_sync_module()

        with patch.object(
            discord_sync, "_get_discord_client", return_value=mock_discord_client
        ):
            result = discord_sync._sync_user_roles(user_id, mock_settings)

    return result, mock_discord_client


# ---------------------------------------------------------------------------
# Preservation Property 1: Sync only modifies managed roles, preserves unmanaged
# ---------------------------------------------------------------------------


class TestPreservation_UnmanagedRolesPreserved:
    """Unmanaged roles (SCHOLAR, CONTRIBUTOR, COMMUNITY_MANAGER, ADMIN)
    are NEVER modified by any sync operation."""

    @given(
        user_id=user_id_strategy,
        tier=tier_strategy,
        unmanaged_roles=unmanaged_role_set_strategy,
    )
    @hypothesis_settings(max_examples=30)
    def test_unmanaged_roles_never_removed(self, user_id, tier, unmanaged_roles):
        """Sync should never remove unmanaged roles from a guild member."""
        assume(len(user_id) > 0)

        expected_role = TIER_TO_ROLE[tier]
        current_roles = [expected_role] + unmanaged_roles

        result, mock_discord_client = _run_sync_user_roles(user_id, tier, current_roles)

        # Verify no unmanaged roles were removed
        for call in mock_discord_client.remove_role.call_args_list:
            removed_role_id = call[0][1] if len(call[0]) > 1 else None
            assert (
                removed_role_id not in UNMANAGED_ROLES
            ), f"Unmanaged role {removed_role_id} should never be removed by sync"

    @given(
        user_id=user_id_strategy,
        tier=tier_strategy,
        unmanaged_roles=unmanaged_role_set_strategy,
    )
    @hypothesis_settings(max_examples=30)
    def test_sync_only_adds_managed_roles(self, user_id, tier, unmanaged_roles):
        """Sync should only add managed (tier-based) roles, never unmanaged ones."""
        assume(len(user_id) > 0)

        # User has only unmanaged roles (needs managed role assigned)
        current_roles = list(unmanaged_roles)

        result, mock_discord_client = _run_sync_user_roles(user_id, tier, current_roles)

        # Verify only managed roles were added
        for call in mock_discord_client.add_role.call_args_list:
            added_role_id = call[0][1] if len(call[0]) > 1 else None
            assert (
                added_role_id in MANAGED_ROLE_IDS
            ), f"Only managed roles should be added by sync, got {added_role_id}"


# ---------------------------------------------------------------------------
# Preservation Property 2: Correct role = no changes
# ---------------------------------------------------------------------------


class TestPreservation_CorrectRoleNoChanges:
    """For in-guild users with the correct role already assigned, sync makes no changes."""

    @given(user_id=user_id_strategy, tier=tier_strategy)
    @hypothesis_settings(max_examples=25)
    def test_correct_role_results_in_no_changes(self, user_id, tier):
        """When user already has correct role, sync should add 0 and remove 0."""
        assume(len(user_id) > 0)

        expected_role = TIER_TO_ROLE[tier]
        current_roles = [expected_role]

        result, mock_discord_client = _run_sync_user_roles(user_id, tier, current_roles)

        assert result["status"] == "success"
        assert result.get("added", 0) == 0
        assert result.get("removed", 0) == 0

        mock_discord_client.add_role.assert_not_called()
        mock_discord_client.remove_role.assert_not_called()


# ---------------------------------------------------------------------------
# Preservation Property 3: BUILDER→BUILDER renewal produces no activation event
# ---------------------------------------------------------------------------


class TestPreservation_BuilderRenewalNoEvent:
    """BUILDER→BUILDER subscription renewal should NOT produce a BUILDER_ACTIVATED event."""

    @given(user_id=user_id_strategy)
    @hypothesis_settings(max_examples=15)
    def test_builder_to_builder_no_activation_event(self, user_id):
        """When tier is already BUILDER and a renewal occurs, no activation event is written.

        Verified by ensuring no DynamoDB put_item calls write BUILDER_ACTIVATED items.
        """
        assume(len(user_id) > 0)

        # BUILDER→BUILDER: user already has BUILDER role
        current_roles = ["ROLE_BUILDER"]

        mock_settings = _make_settings()
        discord_active_item = _make_discord_active_item(user_id)
        membership_item = _make_membership_item(user_id, "BUILDER")

        mock_dynamodb = MagicMock()
        items_written = []

        def get_item_side_effect(**kwargs):
            key = kwargs.get("Key", {})
            sk = key.get("SK", {}).get("S", "")
            if sk == "DISCORD_ACTIVE":
                return {"Item": discord_active_item}
            elif sk == "MEMBERSHIP":
                return {"Item": membership_item}
            return {}

        def put_item_side_effect(**kwargs):
            items_written.append(kwargs.get("Item", {}))

        mock_dynamodb.get_item.side_effect = get_item_side_effect
        mock_dynamodb.put_item.side_effect = put_item_side_effect
        mock_dynamodb.update_item.return_value = {}

        mock_discord_client = MagicMock()
        mock_discord_client.get_member_roles.return_value = current_roles
        mock_discord_client.add_role.return_value = True

        with patch("boto3.client", return_value=mock_dynamodb):
            discord_sync = _get_sync_module()

            with patch.object(
                discord_sync, "_get_discord_client", return_value=mock_discord_client
            ):
                result = discord_sync._sync_user_roles(user_id, mock_settings)

        # No BUILDER_ACTIVATED event should have been written
        for item in items_written:
            sk = item.get("SK", {}).get("S", "")
            assert (
                sk != "BUILDER_ACTIVATED"
            ), "BUILDER→BUILDER renewal should NOT produce a BUILDER_ACTIVATED event"


# ---------------------------------------------------------------------------
# Preservation Property 4: Idempotent sync (repeated calls = same result)
# ---------------------------------------------------------------------------


class TestPreservation_IdempotentSync:
    """Two successive sync calls for same user state produce same result."""

    @given(user_id=user_id_strategy, tier=tier_strategy)
    @hypothesis_settings(max_examples=20)
    def test_successive_syncs_produce_same_result(self, user_id, tier):
        """Running sync twice with same state should be idempotent."""
        assume(len(user_id) > 0)

        expected_role = TIER_TO_ROLE[tier]
        # Start with wrong role
        wrong_roles = [r for r in MANAGED_ROLE_IDS if r != expected_role]
        assume(len(wrong_roles) > 0)
        wrong_role = wrong_roles[0]
        current_roles_first = [wrong_role]

        mock_settings = _make_settings()
        discord_active_item = _make_discord_active_item(user_id)
        membership_item = _make_membership_item(user_id, tier)

        mock_dynamodb = MagicMock()

        def get_item_side_effect(**kwargs):
            key = kwargs.get("Key", {})
            sk = key.get("SK", {}).get("S", "")
            if sk == "DISCORD_ACTIVE":
                return {"Item": discord_active_item}
            elif sk == "MEMBERSHIP":
                return {"Item": membership_item}
            return {}

        mock_dynamodb.get_item.side_effect = get_item_side_effect

        mock_discord_client = MagicMock()
        mock_discord_client.add_role.return_value = True
        mock_discord_client.remove_role.return_value = True

        with patch("boto3.client", return_value=mock_dynamodb):
            discord_sync = _get_sync_module()

            # First call: user has wrong role
            mock_discord_client.get_member_roles.return_value = current_roles_first

            with patch.object(
                discord_sync, "_get_discord_client", return_value=mock_discord_client
            ):
                result1 = discord_sync._sync_user_roles(user_id, mock_settings)
                assert result1["status"] == "success"

                # Second call: roles now correct (simulating the first sync took effect)
                mock_discord_client.get_member_roles.return_value = [expected_role]
                mock_discord_client.add_role.reset_mock()
                mock_discord_client.remove_role.reset_mock()

                result2 = discord_sync._sync_user_roles(user_id, mock_settings)
                assert result2["status"] == "success"
                assert result2.get("added", 0) == 0
                assert result2.get("removed", 0) == 0

                mock_discord_client.add_role.assert_not_called()
                mock_discord_client.remove_role.assert_not_called()


# ---------------------------------------------------------------------------
# Preservation Property 5: Role reconciliation logic (wrong role → correct role)
# ---------------------------------------------------------------------------


class TestPreservation_RoleReconciliation:
    """In-guild user with wrong managed role gets corrected by sync."""

    @given(
        user_id=user_id_strategy,
        tier=tier_strategy,
        unmanaged_roles=unmanaged_role_set_strategy,
    )
    @hypothesis_settings(max_examples=25)
    def test_wrong_managed_role_gets_corrected(self, user_id, tier, unmanaged_roles):
        """User with wrong managed role should have it removed and correct one added."""
        assume(len(user_id) > 0)

        expected_role = TIER_TO_ROLE[tier]
        wrong_roles = [r for r in MANAGED_ROLE_IDS if r != expected_role]
        assume(len(wrong_roles) > 0)
        wrong_role = wrong_roles[0]

        current_roles = [wrong_role] + unmanaged_roles

        result, mock_discord_client = _run_sync_user_roles(user_id, tier, current_roles)

        assert result["status"] == "success"
        assert result.get("added", 0) >= 1 or result.get("removed", 0) >= 1

        # Verify expected role was added
        add_calls = mock_discord_client.add_role.call_args_list
        added_roles = [c[0][1] for c in add_calls]
        assert (
            expected_role in added_roles
        ), f"Expected role {expected_role} should have been added"

        # Verify wrong role was removed
        remove_calls = mock_discord_client.remove_role.call_args_list
        removed_roles = [c[0][1] for c in remove_calls]
        assert (
            wrong_role in removed_roles
        ), f"Wrong role {wrong_role} should have been removed"

        # Verify unmanaged roles were NOT touched
        for role in unmanaged_roles:
            assert (
                role not in removed_roles
            ), f"Unmanaged role {role} should not be removed"
