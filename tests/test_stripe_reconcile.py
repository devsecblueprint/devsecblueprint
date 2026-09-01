"""Tests for admin-triggered Discord sync reconciling tier against Stripe.

Covers:
- StripeService.reconcile_subscription_from_stripe: derives tier from the live
  Stripe subscription, downgrades to FREE when no active subscription, and
  no-ops when the user has never checked out (no stripe_customer_id).
- discord_tasks._run_sync: runs the Stripe reconcile before the Discord role
  sync for the "admin_sync" operation, and skips it for other operations.
"""

import os
import sys
from unittest.mock import MagicMock, patch

# Ensure backend is importable
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(backend_dir))


def _make_settings():
    s = MagicMock()
    s.membership_table = "test-membership-table"
    s.progress_table = "test-progress-table"
    s.stripe_secret_name = "stripe-secret"
    s.stripe_webhook_secret_name = "stripe-webhook-secret"
    s.frontend_origin = "http://localhost:3000"
    return s


def _membership_item(tier="FREE", customer_id="cus_test123"):
    item = {
        "PK": {"S": "USER#u1"},
        "SK": {"S": "MEMBERSHIP"},
        "membership_tier": {"S": tier},
    }
    if customer_id is not None:
        item["stripe_customer_id"] = {"S": customer_id}
    return item


def _make_stripe_service(membership_item):
    """Build a StripeService with boto3 + secret access mocked out."""
    with patch("boto3.client"):
        import app.services.stripe_service as stripe_service_mod

        svc = stripe_service_mod.StripeService(_make_settings())

    # Stub the DynamoDB / secret helpers so no AWS calls happen.
    svc._get_membership = MagicMock(return_value=membership_item)
    svc._get_stripe_key = MagicMock(return_value="sk_test")
    svc._update_subscription_state = MagicMock()
    svc._activate_subscription = MagicMock()
    # tier is resolved from product metadata; stub to avoid Stripe product calls
    svc._determine_tier_from_subscription = MagicMock(return_value="BUILDER")
    return svc


def _sub_list(*subs):
    """Return an object whose .to_dict() mimics stripe.Subscription.list()."""
    obj = MagicMock()
    obj.to_dict.return_value = {"data": list(subs)}
    return obj


class TestReconcileSubscriptionFromStripe:
    def test_no_customer_id_is_a_noop(self):
        svc = _make_stripe_service(_membership_item(tier="FREE", customer_id=None))
        result = svc.reconcile_subscription_from_stripe("u1")
        assert result == {"reconciled": False, "reason": "no_customer"}
        svc._activate_subscription.assert_not_called()
        svc._update_subscription_state.assert_not_called()

    def test_active_subscription_upgrades_free_user(self):
        svc = _make_stripe_service(_membership_item(tier="FREE"))
        active = {"id": "sub_1", "status": "active", "items": {"data": []}}
        with patch("app.services.stripe_service.stripe") as mock_stripe:
            mock_stripe.Subscription.list.return_value = _sub_list(active)
            result = svc.reconcile_subscription_from_stripe("u1")

        assert result["reconciled"] is True
        assert result["tier"] == "BUILDER"
        assert result["changed"] is True
        # From FREE -> first-time activation path records start date
        svc._activate_subscription.assert_called_once()
        svc._update_subscription_state.assert_not_called()

    def test_active_subscription_updates_existing_paid_user(self):
        svc = _make_stripe_service(_membership_item(tier="BUILDER"))
        active = {"id": "sub_1", "status": "active", "items": {"data": []}}
        with patch("app.services.stripe_service.stripe") as mock_stripe:
            mock_stripe.Subscription.list.return_value = _sub_list(active)
            result = svc.reconcile_subscription_from_stripe("u1")

        assert result["reconciled"] is True
        assert result["tier"] == "BUILDER"
        assert result["changed"] is False
        svc._update_subscription_state.assert_called_once()
        svc._activate_subscription.assert_not_called()

    def test_no_active_subscription_downgrades_to_free(self):
        svc = _make_stripe_service(
            {
                **_membership_item(tier="BUILDER"),
                "stripe_subscription_id": {"S": "sub_old"},
            }
        )
        canceled = {"id": "sub_old", "status": "canceled", "items": {"data": []}}
        with patch("app.services.stripe_service.stripe") as mock_stripe:
            mock_stripe.Subscription.list.return_value = _sub_list(canceled)
            result = svc.reconcile_subscription_from_stripe("u1")

        assert result["reconciled"] is True
        assert result["reason"] == "downgraded_to_free"
        assert result["tier"] == "FREE"
        assert result["changed"] is True
        svc._update_subscription_state.assert_called_once()
        args = svc._update_subscription_state.call_args.args
        assert args[0] == "u1" and args[1] == "FREE"

    def test_already_free_no_active_subscription_no_write(self):
        svc = _make_stripe_service(_membership_item(tier="FREE"))
        with patch("app.services.stripe_service.stripe") as mock_stripe:
            mock_stripe.Subscription.list.return_value = _sub_list()
            result = svc.reconcile_subscription_from_stripe("u1")

        assert result["reconciled"] is True
        assert result["changed"] is False
        assert result["tier"] == "FREE"
        svc._update_subscription_state.assert_not_called()
        svc._activate_subscription.assert_not_called()

    def test_stripe_error_reported_not_raised(self):
        svc = _make_stripe_service(_membership_item(tier="BUILDER"))
        with patch("app.services.stripe_service.stripe") as mock_stripe:
            mock_stripe.Subscription.list.side_effect = RuntimeError("boom")
            result = svc.reconcile_subscription_from_stripe("u1")

        assert result == {"reconciled": False, "reason": "stripe_error"}
        svc._update_subscription_state.assert_not_called()


def _run(coro):
    import asyncio

    return asyncio.new_event_loop().run_until_complete(coro)


class TestRunSyncWiring:
    def test_admin_sync_runs_reconcile_before_role_sync(self):
        with patch("boto3.client"):
            import app.background.discord_tasks as tasks

        call_order = []

        def fake_reconcile(user_id):
            call_order.append("reconcile")
            return {
                "reconciled": True,
                "reason": "synced_from_stripe",
                "tier": "BUILDER",
            }

        def fake_role_sync(user_id, settings):
            call_order.append("role_sync")
            return MagicMock(
                sync_status="success",
                guild_action="already_member",
                roles_added=[],
                roles_removed=[],
                error_code=None,
            )

        fake_stripe_service = MagicMock()
        fake_stripe_service.reconcile_subscription_from_stripe.side_effect = (
            fake_reconcile
        )

        with (
            patch.object(tasks, "get_settings", return_value=_make_settings()),
            patch(
                "app.services.stripe_service.StripeService",
                return_value=fake_stripe_service,
            ),
            patch.object(tasks, "sync_discord_access", side_effect=fake_role_sync),
        ):
            _run(tasks._run_sync("u1", "admin_sync", "manual"))

        assert call_order == ["reconcile", "role_sync"]

    def test_non_admin_sync_skips_reconcile(self):
        with patch("boto3.client"):
            import app.background.discord_tasks as tasks

        called = {"reconcile": False}

        fake_stripe_service = MagicMock()

        def fake_reconcile(user_id):
            called["reconcile"] = True
            return {"reconciled": True}

        fake_stripe_service.reconcile_subscription_from_stripe.side_effect = (
            fake_reconcile
        )

        def fake_role_sync(user_id, settings):
            return MagicMock(
                sync_status="success",
                guild_action="already_member",
                roles_added=[],
                roles_removed=[],
                error_code=None,
            )

        with (
            patch.object(tasks, "get_settings", return_value=_make_settings()),
            patch(
                "app.services.stripe_service.StripeService",
                return_value=fake_stripe_service,
            ),
            patch.object(tasks, "sync_discord_access", side_effect=fake_role_sync),
        ):
            _run(tasks._run_sync("u1", "stripe_webhook", "evt"))

        assert called["reconcile"] is False
