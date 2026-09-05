"""Tests for Stripe inclusion in the scheduled Discord reconciliation sweep.

reconcile_all_members must, for each active Discord member, reconcile the
membership tier against Stripe BEFORE syncing Discord roles, so that paid
tiers (Builders) self-heal from missed subscription webhooks. A Stripe failure
for one user must not skip that user's Discord sync or abort the sweep.
"""

import importlib
import os
import sys
from unittest.mock import MagicMock, patch

# Ensure backend is importable
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(backend_dir))


def _make_settings():
    s = MagicMock()
    s.membership_table = "test-membership-table"
    return s


def _discord_active(user_id):
    return {"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "DISCORD_ACTIVE"}}


def _sync_result(status="success", added=None, removed=None):
    return MagicMock(
        sync_status=status,
        roles_added=added or [],
        roles_removed=removed or [],
        error_code=None,
    )


def _get_module():
    with patch("boto3.client"):
        import app.services.discord_sync as mod

        importlib.reload(mod)
        return mod


def _run(coro):
    import asyncio

    return asyncio.new_event_loop().run_until_complete(coro)


class TestReconcileAllMembersStripe:
    def test_stripe_reconcile_runs_before_role_sync_per_user(self):
        mod = _get_module()
        calls = []

        def fake_stripe(user_id):
            calls.append(("stripe", user_id))
            return {
                "reconciled": True,
                "reason": "synced_from_stripe",
                "changed": False,
            }

        def fake_sync(user_id, settings):
            calls.append(("sync", user_id))
            return _sync_result()

        with (
            patch.object(mod, "get_settings", return_value=_make_settings()),
            patch.object(
                mod,
                "_scan_active_discord_users",
                return_value=[_discord_active("u1"), _discord_active("u2")],
            ),
            patch.object(mod, "_reconcile_tier_from_stripe", side_effect=fake_stripe),
            patch.object(mod, "sync_discord_access", side_effect=fake_sync),
            patch.object(mod.asyncio, "sleep", new=_async_noop),
        ):
            metrics = _run(mod.reconcile_all_members())

        # Per user, Stripe reconcile precedes the Discord sync
        assert calls == [
            ("stripe", "u1"),
            ("sync", "u1"),
            ("stripe", "u2"),
            ("sync", "u2"),
        ]
        assert metrics["stripe_reconciled"] == 2

    def test_stripe_change_is_counted(self):
        mod = _get_module()

        def fake_stripe(user_id):
            return {
                "reconciled": True,
                "reason": "downgraded_to_free",
                "changed": True,
                "previous_tier": "BUILDER",
                "tier": "FREE",
            }

        with (
            patch.object(mod, "get_settings", return_value=_make_settings()),
            patch.object(
                mod, "_scan_active_discord_users", return_value=[_discord_active("u1")]
            ),
            patch.object(mod, "_reconcile_tier_from_stripe", side_effect=fake_stripe),
            patch.object(
                mod, "sync_discord_access", side_effect=lambda uid, s: _sync_result()
            ),
            patch.object(mod.asyncio, "sleep", new=_async_noop),
        ):
            metrics = _run(mod.reconcile_all_members())

        assert metrics["stripe_reconciled"] == 1
        assert metrics["stripe_changed"] == 1

    def test_no_customer_is_not_counted_as_reconciled(self):
        mod = _get_module()

        def fake_stripe(user_id):
            return {"reconciled": False, "reason": "no_customer"}

        with (
            patch.object(mod, "get_settings", return_value=_make_settings()),
            patch.object(
                mod, "_scan_active_discord_users", return_value=[_discord_active("u1")]
            ),
            patch.object(mod, "_reconcile_tier_from_stripe", side_effect=fake_stripe),
            patch.object(
                mod, "sync_discord_access", side_effect=lambda uid, s: _sync_result()
            ),
            patch.object(mod.asyncio, "sleep", new=_async_noop),
        ):
            metrics = _run(mod.reconcile_all_members())

        assert metrics["stripe_reconciled"] == 0
        assert metrics["stripe_changed"] == 0

    def test_stripe_failure_does_not_skip_discord_sync(self):
        mod = _get_module()
        synced = []

        def boom(user_id):
            raise RuntimeError("stripe down")

        def fake_sync(user_id, settings):
            synced.append(user_id)
            return _sync_result()

        with (
            patch.object(mod, "get_settings", return_value=_make_settings()),
            patch.object(
                mod, "_scan_active_discord_users", return_value=[_discord_active("u1")]
            ),
            patch.object(mod, "_reconcile_tier_from_stripe", side_effect=boom),
            patch.object(mod, "sync_discord_access", side_effect=fake_sync),
            patch.object(mod.asyncio, "sleep", new=_async_noop),
        ):
            metrics = _run(mod.reconcile_all_members())

        # Discord sync still ran despite Stripe failure; sweep did not abort
        assert synced == ["u1"]
        assert metrics["stripe_reconciled"] == 0

    def test_stripe_failure_isolated_across_users(self):
        mod = _get_module()
        synced = []

        def flaky(user_id):
            if user_id == "u1":
                raise RuntimeError("stripe down")
            return {
                "reconciled": True,
                "reason": "synced_from_stripe",
                "changed": False,
            }

        with (
            patch.object(mod, "get_settings", return_value=_make_settings()),
            patch.object(
                mod,
                "_scan_active_discord_users",
                return_value=[_discord_active("u1"), _discord_active("u2")],
            ),
            patch.object(mod, "_reconcile_tier_from_stripe", side_effect=flaky),
            patch.object(
                mod,
                "sync_discord_access",
                side_effect=lambda uid, s: synced.append(uid) or _sync_result(),
            ),
            patch.object(mod.asyncio, "sleep", new=_async_noop),
        ):
            metrics = _run(mod.reconcile_all_members())

        # Both users synced; u2 still got its Stripe reconcile counted
        assert synced == ["u1", "u2"]
        assert metrics["stripe_reconciled"] == 1


async def _async_noop(*args, **kwargs):
    return None
