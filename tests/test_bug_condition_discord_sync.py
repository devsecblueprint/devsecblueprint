"""Bug Condition Exploration Test — Discord Auto-Enrollment and Builder Activation Gaps.

This test is written BEFORE implementing the fix. It encodes the EXPECTED (correct)
behavior. On unfixed code it will FAIL — confirming the bugs exist. After the fix
is applied it should PASS — confirming the bugs are resolved.

Three bug scenarios tested:
1. User with DISCORD_ACTIVE (platform_state=Server_Joined) where get_member_roles
   returns None — sync should attempt guild enrollment (currently skips).
2. Trigger Sync for non-guild-member — recovery action should be taken (currently skips).
3. After _activate_subscription sets tier to BUILDER — a BUILDER_ACTIVATED DynamoDB
   item should exist (currently does NOT exist).

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
"""

import importlib
import json
import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings, assume
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

trigger_source_strategy = st.sampled_from(
    [
        "stripe_webhook",
        "admin_grant",
        "contributor_grant",
        "scholar_grant",
        "campaign",
        "promotion",
        "system",
    ]
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
        "stripe_subscription_id": {"S": "sub_test123"},
    }


def _get_sync_module():
    """Import discord_sync module with boto3 mocked to avoid AWS calls."""
    with patch("boto3.client"):
        import app.services.discord_sync as discord_sync_mod

        importlib.reload(discord_sync_mod)
        return discord_sync_mod


def _get_builder_activation_module():
    """Import builder_activation module with boto3 mocked."""
    with patch("boto3.client"):
        import app.services.builder_activation as builder_activation_mod

        importlib.reload(builder_activation_mod)
        return builder_activation_mod


# ---------------------------------------------------------------------------
# Bug Condition 1: Guild Enrollment Gap
# When get_member_roles returns None (not in guild), sync should attempt
# guild enrollment. Currently it returns {"status": "skipped", "reason": "not_in_guild"}.
# ---------------------------------------------------------------------------


class TestBugCondition1_GuildEnrollmentGap:
    """Bug: _sync_user_roles skips non-guild-members without enrollment attempt.

    EXPECTED after fix: sync_discord_access attempts guild enrollment via
    PUT /guilds/{guild_id}/members/{user_id} and returns a SyncResult with
    guild_action in ["joined", "join_failed"].
    """

    @given(user_id=user_id_strategy, tier=tier_strategy)
    @settings(max_examples=20, deadline=None)
    def test_non_guild_member_gets_enrollment_attempted(self, user_id, tier):
        """For user with DISCORD_ACTIVE but not in guild, sync should attempt enrollment.

        On UNFIXED code: This test FAILS because sync_discord_access does not exist
        or _sync_user_roles returns {"status": "skipped", "reason": "not_in_guild"}
        with no enrollment attempt.

        On FIXED code: sync_discord_access returns SyncResult with
        guild_action in ["joined", "join_failed"].
        """
        assume(len(user_id) > 0)

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
            elif sk == "BUILDER_ACTIVATED":
                return {}
            return {}

        mock_dynamodb.get_item.side_effect = get_item_side_effect
        mock_dynamodb.update_item.return_value = {}

        # Mock Discord client: get_member_roles returns None (not in guild)
        mock_discord_client = MagicMock()
        mock_discord_client.get_member_roles.return_value = None
        mock_discord_client.add_member_with_bot.return_value = True
        mock_discord_client.add_role.return_value = True
        mock_discord_client.remove_role.return_value = True

        with patch("boto3.client", return_value=mock_dynamodb):
            discord_sync = _get_sync_module()

            # Verify sync_discord_access exists (will fail on unfixed code)
            assert hasattr(
                discord_sync, "sync_discord_access"
            ), "sync_discord_access function should exist in discord_sync module"

            with patch.object(
                discord_sync, "_get_discord_client", return_value=mock_discord_client
            ):
                result = discord_sync.sync_discord_access(user_id, mock_settings)

            # After fix: result should be a SyncResult with guild_action
            assert hasattr(result, "guild_action"), (
                f"sync_discord_access should return SyncResult with guild_action, "
                f"got {type(result)}: {result}"
            )
            assert result.guild_action in ("joined", "join_failed"), (
                f"For non-guild-member, guild_action should be 'joined' or 'join_failed', "
                f"got '{result.guild_action}'"
            )


# ---------------------------------------------------------------------------
# Bug Condition 2: Trigger Sync Non-Guild-Member Recovery
# ---------------------------------------------------------------------------


class TestBugCondition2_TriggerSyncNoRecovery:
    """Bug: perform_sync skips non-guild-members without recovery action.

    EXPECTED after fix: sync_discord_access is used which attempts enrollment.
    """

    @given(user_id=user_id_strategy)
    @settings(max_examples=15, deadline=None)
    def test_trigger_sync_attempts_recovery_for_non_guild_member(self, user_id):
        """Trigger Sync for non-guild-member should attempt recovery (enrollment).

        On UNFIXED code: This test FAILS because sync_discord_access does not exist.

        On FIXED code: sync_discord_access attempts guild enrollment before giving up.
        """
        assume(len(user_id) > 0)

        mock_settings = _make_settings()
        discord_active_item = _make_discord_active_item(user_id)
        membership_item = _make_membership_item(user_id, "BUILDER")

        mock_dynamodb = MagicMock()

        def get_item_side_effect(**kwargs):
            key = kwargs.get("Key", {})
            sk = key.get("SK", {}).get("S", "")
            if sk == "DISCORD_ACTIVE":
                return {"Item": discord_active_item}
            elif sk == "MEMBERSHIP":
                return {"Item": membership_item}
            elif sk == "BUILDER_ACTIVATED":
                return {}
            return {}

        mock_dynamodb.get_item.side_effect = get_item_side_effect
        mock_dynamodb.update_item.return_value = {}

        mock_discord_client = MagicMock()
        mock_discord_client.get_member_roles.return_value = None
        mock_discord_client.add_member_with_bot.return_value = True
        mock_discord_client.add_role.return_value = True

        with patch("boto3.client", return_value=mock_dynamodb):
            discord_sync = _get_sync_module()

            assert hasattr(
                discord_sync, "sync_discord_access"
            ), "sync_discord_access function should exist in discord_sync module"

            with patch.object(
                discord_sync, "_get_discord_client", return_value=mock_discord_client
            ):
                result = discord_sync.sync_discord_access(user_id, mock_settings)

            assert hasattr(
                result, "guild_action"
            ), f"Expected SyncResult with guild_action, got {type(result)}: {result}"
            assert result.guild_action != "not_attempted", (
                f"For non-guild-member trigger sync, enrollment should be attempted, "
                f"got guild_action='{result.guild_action}'"
            )


# ---------------------------------------------------------------------------
# Bug Condition 3: Missing Builder Activation Event
# ---------------------------------------------------------------------------


class TestBugCondition3_MissingBuilderActivation:
    """Bug: _activate_subscription sets tier to BUILDER but no BUILDER_ACTIVATED event.

    EXPECTED after fix: After record_builder_activation is called for a
    FREE→BUILDER or EXPLORER→BUILDER transition, a BUILDER_ACTIVATED DynamoDB
    item should exist.
    """

    @given(
        user_id=user_id_strategy,
        previous_tier=st.sampled_from(["FREE", "EXPLORER"]),
        activation_source=trigger_source_strategy,
    )
    @settings(max_examples=20, deadline=None)
    def test_builder_activation_records_lifecycle_event(
        self, user_id, previous_tier, activation_source
    ):
        """After tier transition to BUILDER, BUILDER_ACTIVATED item should exist.

        On UNFIXED code: This test FAILS because builder_activation module
        does not exist.

        On FIXED code: record_builder_activation writes the BUILDER_ACTIVATED item.
        """
        assume(len(user_id) > 0)

        mock_settings = _make_settings()

        # Track DynamoDB writes to verify BUILDER_ACTIVATED is written
        dynamodb_items_written = {}

        mock_dynamodb = MagicMock()

        def get_item_side_effect(**kwargs):
            key = kwargs.get("Key", {})
            sk = key.get("SK", {}).get("S", "")
            pk = key.get("PK", {}).get("S", "")

            if sk == "MEMBERSHIP":
                return {
                    "Item": {
                        "PK": {"S": pk},
                        "SK": {"S": "MEMBERSHIP"},
                        "membership_tier": {"S": previous_tier},
                        "subscription_status": {"S": "active"},
                        "stripe_customer_id": {"S": "cus_test"},
                    }
                }
            elif sk == "BUILDER_ACTIVATED":
                item_key = f"{pk}#BUILDER_ACTIVATED"
                if item_key in dynamodb_items_written:
                    return {"Item": dynamodb_items_written[item_key]}
                return {}
            return {}

        def put_item_side_effect(**kwargs):
            item = kwargs.get("Item", {})
            pk = item.get("PK", {}).get("S", "")
            sk = item.get("SK", {}).get("S", "")
            item_key = f"{pk}#{sk}"
            dynamodb_items_written[item_key] = item

        def update_item_side_effect(**kwargs):
            pass

        mock_dynamodb.get_item.side_effect = get_item_side_effect
        mock_dynamodb.put_item.side_effect = put_item_side_effect
        mock_dynamodb.update_item.side_effect = update_item_side_effect

        with patch("boto3.client", return_value=mock_dynamodb):
            builder_activation = _get_builder_activation_module()

            result = builder_activation.record_builder_activation(
                user_id=user_id,
                activation_source="STRIPE_SUBSCRIPTION",
                previous_tier=previous_tier,
                settings=mock_settings,
            )

            # Verify BUILDER_ACTIVATED item was written
            item_key = f"USER#{user_id}#BUILDER_ACTIVATED"
            assert item_key in dynamodb_items_written, (
                f"BUILDER_ACTIVATED item should be written to DynamoDB after "
                f"{previous_tier}→BUILDER transition. No item found."
            )

            written_item = dynamodb_items_written[item_key]
            assert written_item["SK"]["S"] == "BUILDER_ACTIVATED"
            assert "activated_at" in written_item
            assert written_item["activation_source"]["S"] == "STRIPE_SUBSCRIPTION"
            assert written_item["previous_tier"]["S"] == previous_tier

    @given(user_id=user_id_strategy)
    @settings(max_examples=10, deadline=None)
    def test_builder_activation_deduplication(self, user_id):
        """Second write of BUILDER_ACTIVATED should be deduplicated (return False).

        On UNFIXED code: This test FAILS because builder_activation module
        does not exist.

        On FIXED code: Second call returns False due to ConditionExpression.
        """
        assume(len(user_id) > 0)

        mock_settings = _make_settings()
        mock_dynamodb = MagicMock()

        from botocore.exceptions import ClientError

        first_call = [True]

        def put_item_side_effect(**kwargs):
            if first_call[0]:
                first_call[0] = False
                return {}
            else:
                error_response = {
                    "Error": {
                        "Code": "ConditionalCheckFailedException",
                        "Message": "The conditional request failed",
                    }
                }
                raise ClientError(error_response, "PutItem")

        mock_dynamodb.put_item.side_effect = put_item_side_effect
        mock_dynamodb.update_item.return_value = {}
        mock_dynamodb.get_item.return_value = {}

        with patch("boto3.client", return_value=mock_dynamodb):
            builder_activation = _get_builder_activation_module()

            # First call should succeed
            result1 = builder_activation.record_builder_activation(
                user_id=user_id,
                activation_source="STRIPE_SUBSCRIPTION",
                previous_tier="FREE",
                settings=mock_settings,
            )
            assert result1 is True, "First activation should succeed"

            # Second call should be deduplicated (return False, not raise)
            result2 = builder_activation.record_builder_activation(
                user_id=user_id,
                activation_source="STRIPE_SUBSCRIPTION",
                previous_tier="FREE",
                settings=mock_settings,
            )
            assert (
                result2 is False
            ), "Second activation should return False (deduplicated), not raise"
