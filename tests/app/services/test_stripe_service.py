"""Unit tests for app.services.stripe_service.StripeService.

Targets the parts NOT already exercised by tests/test_stripe_reconcile.py,
tests/test_stripe_user_resolution.py, and tests/test_reconcile_stripe_sweep.py
(those cover reconcile_subscription_from_stripe, _resolve_user_id, and
_resolve_user_from_customer). Here we cover: get_products (+cache), checkout
session creation, subscription status, portal session, the webhook dispatcher
for every event type, tier derivation, period-end extraction, and the DynamoDB
helpers.

Mocking approach mirrors the existing stripe tests: construct StripeService
under patch("boto3.client") so no AWS clients are built, then reassign
svc._dynamodb_client to a MagicMock. The module's `stripe` SDK is patched per
test with patch.object(mod.stripe, ...) on the specific calls used, which keeps
real exception classes (e.g. SignatureVerificationError) intact. Secret
retrieval is stubbed via svc._get_stripe_key / svc._get_webhook_secret.
"""

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.services import stripe_service as mod
from app.services.stripe_service import StripeService


def _make_settings():
    s = MagicMock()
    s.membership_table = "test-membership"
    s.progress_table = "test-progress"
    s.stripe_secret_name = "stripe-secret"
    s.stripe_webhook_secret_name = "stripe-webhook-secret"
    s.frontend_origin = "https://devsecblueprint.com"
    return s


def _make_service():
    with patch("boto3.client"):
        svc = StripeService(_make_settings())
    svc._dynamodb_client = MagicMock()
    svc._get_stripe_key = MagicMock(return_value="sk_test")
    svc._get_webhook_secret = MagicMock(return_value="whsec_test")
    return svc


def _reset_product_cache():
    StripeService._products_cache["data"] = None
    StripeService._products_cache["timestamp"] = 0.0


def _membership(**fields):
    item = {"PK": {"S": "USER#u1"}, "SK": {"S": "MEMBERSHIP"}}
    item.update(fields)
    return item


@pytest.fixture(autouse=True)
def _clear_cache():
    _reset_product_cache()
    yield
    _reset_product_cache()


# ---------------------------------------------------------------------------
# get_products
# ---------------------------------------------------------------------------


def _product(pid="prod_1", tier="BUILDER", name="Builder"):
    p = MagicMock()
    p.id = pid
    p.name = name
    p.description = "desc"
    # metadata supports `in` and index access (StripeObject-like)
    p.metadata = {"dsb_tier": tier} if tier else {}
    return p


def _price(interval="month", unit_amount=1200, currency="usd", pid="price_1"):
    pr = MagicMock()
    pr.id = pid
    pr.currency = currency
    pr.unit_amount = unit_amount
    if interval:
        pr.recurring = MagicMock(interval=interval)
    else:
        pr.recurring = None
    return pr


class TestGetProducts:
    def test_fetches_and_filters_dsb_products(self):
        svc = _make_service()
        products = MagicMock(data=[_product(), _product(pid="p2", tier=None)])
        prices = MagicMock(data=[_price(interval="month", unit_amount=1500)])
        with (
            patch.object(mod.stripe.Product, "list", return_value=products),
            patch.object(mod.stripe.Price, "list", return_value=prices),
        ):
            result = svc.get_products()

        assert len(result) == 1
        entry = result[0]
        assert entry["dsb_tier"] == "BUILDER"
        assert entry["price"] == 1500
        assert entry["monthly_price"] == 1500  # month interval = unchanged
        assert entry["interval"] == "month"
        assert entry["price_id"] == "price_1"

    def test_yearly_price_divides_monthly(self):
        svc = _make_service()
        products = MagicMock(data=[_product()])
        prices = MagicMock(data=[_price(interval="year", unit_amount=12000)])
        with (
            patch.object(mod.stripe.Product, "list", return_value=products),
            patch.object(mod.stripe.Price, "list", return_value=prices),
        ):
            result = svc.get_products()
        assert result[0]["monthly_price"] == 1000  # 12000 / 12

    def test_returns_cached_within_ttl(self):
        svc = _make_service()
        StripeService._products_cache["data"] = [{"id": "cached"}]
        StripeService._products_cache["timestamp"] = time.time()
        with patch.object(mod.stripe.Product, "list") as plist:
            result = svc.get_products()
        assert result == [{"id": "cached"}]
        plist.assert_not_called()

    def test_returns_stale_cache_on_api_error(self):
        svc = _make_service()
        StripeService._products_cache["data"] = [{"id": "stale"}]
        StripeService._products_cache["timestamp"] = 0.0  # expired
        with patch.object(
            mod.stripe.Product, "list", side_effect=RuntimeError("stripe down")
        ):
            result = svc.get_products()
        assert result == [{"id": "stale"}]

    def test_raises_when_no_cache_and_error(self):
        svc = _make_service()
        with patch.object(
            mod.stripe.Product, "list", side_effect=RuntimeError("stripe down")
        ):
            with pytest.raises(RuntimeError):
                svc.get_products()


# ---------------------------------------------------------------------------
# create_checkout_session
# ---------------------------------------------------------------------------


class TestCreateCheckoutSession:
    def test_rejects_active_subscription(self):
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(subscription_status={"S": "active"})
        )
        with pytest.raises(ValueError, match="already has an active subscription"):
            svc.create_checkout_session("u1", "price_1")

    def test_creates_customer_when_missing_then_session(self):
        svc = _make_service()
        svc._get_membership = MagicMock(return_value=None)
        svc._put_membership = MagicMock()
        customer = MagicMock(id="cus_new")
        session = MagicMock(url="https://checkout/sess")
        with (
            patch.object(mod.stripe.Customer, "create", return_value=customer),
            patch.object(
                mod.stripe.checkout.Session, "create", return_value=session
            ) as sess_create,
        ):
            result = svc.create_checkout_session("u1", "price_1")

        assert result == {"checkout_url": "https://checkout/sess"}
        svc._put_membership.assert_called_once()
        kwargs = sess_create.call_args.kwargs
        assert kwargs["customer"] == "cus_new"
        assert kwargs["mode"] == "subscription"
        assert kwargs["line_items"] == [{"price": "price_1", "quantity": 1}]
        assert kwargs["metadata"] == {"dsb_user_id": "u1"}
        assert "payment_method_types" not in kwargs

    def test_reuses_existing_customer_id(self):
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(stripe_customer_id={"S": "cus_existing"})
        )
        session = MagicMock(url="https://checkout/sess")
        with (
            patch.object(mod.stripe.Customer, "create") as cust_create,
            patch.object(
                mod.stripe.checkout.Session, "create", return_value=session
            ) as sess_create,
        ):
            result = svc.create_checkout_session("u1", "price_1")

        assert result == {"checkout_url": "https://checkout/sess"}
        cust_create.assert_not_called()
        assert sess_create.call_args.kwargs["customer"] == "cus_existing"
        assert "payment_method_types" not in sess_create.call_args.kwargs


# ---------------------------------------------------------------------------
# get_subscription_status
# ---------------------------------------------------------------------------


class TestGetSubscriptionStatus:
    def test_defaults_when_no_membership(self):
        svc = _make_service()
        svc._get_membership = MagicMock(return_value=None)
        result = svc.get_subscription_status("u1")
        assert result == {
            "membership_tier": "FREE",
            "subscription_status": None,
            "current_period_end": None,
            "stripe_subscription_id": None,
            "subscription_started_at": None,
        }

    def test_reads_membership_fields(self):
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(
                membership_tier={"S": "BUILDER"},
                subscription_status={"S": "active"},
                current_period_end={"S": "2025-01-01T00:00:00+00:00"},
                stripe_subscription_id={"S": "sub_9"},
                subscription_started_at={"S": "2024-01-01T00:00:00+00:00"},
            )
        )
        result = svc.get_subscription_status("u1")
        assert result["membership_tier"] == "BUILDER"
        assert result["subscription_status"] == "active"
        assert result["stripe_subscription_id"] == "sub_9"


# ---------------------------------------------------------------------------
# create_portal_session
# ---------------------------------------------------------------------------


class TestCreatePortalSession:
    def test_raises_without_customer(self):
        svc = _make_service()
        svc._get_membership = MagicMock(return_value=None)
        with pytest.raises(ValueError, match="No subscription found"):
            svc.create_portal_session("u1")

    def test_creates_portal_url(self):
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(stripe_customer_id={"S": "cus_1"})
        )
        session = MagicMock(url="https://portal/sess")
        with patch.object(
            mod.stripe.billing_portal.Session, "create", return_value=session
        ) as create:
            result = svc.create_portal_session("u1")
        assert result == {"portal_url": "https://portal/sess"}
        kwargs = create.call_args.kwargs
        assert kwargs["customer"] == "cus_1"
        assert kwargs["return_url"].endswith("/settings/subscription")


# ---------------------------------------------------------------------------
# verify_and_process_webhook
# ---------------------------------------------------------------------------


def _event(event_type, obj, event_id="evt_1"):
    """Build a construct_event return value whose .to_dict() yields the event."""
    raw = MagicMock()
    raw.to_dict.return_value = {
        "type": event_type,
        "id": event_id,
        "data": {"object": obj},
    }
    return raw


class TestWebhookSignature:
    def test_invalid_signature_raises_value_error(self):
        svc = _make_service()
        err = mod.stripe.SignatureVerificationError("bad", "sig")
        with patch.object(mod.stripe.Webhook, "construct_event", side_effect=err):
            with pytest.raises(ValueError, match="Invalid webhook signature"):
                svc.verify_and_process_webhook("body", "sig-header")


class TestWebhookCheckoutCompleted:
    def test_activates_subscription_and_sends_email(self):
        svc = _make_service()
        svc._activate_subscription = MagicMock()
        svc._record_payment_event = MagicMock()
        svc._determine_tier_from_subscription = MagicMock(return_value="BUILDER")
        svc._extract_current_period_end = MagicMock(return_value=1700000000)
        svc._get_user_email = MagicMock(return_value="user@example.com")
        svc._get_user_display_name = MagicMock(return_value="Jane")

        obj = {
            "customer": "cus_1",
            "metadata": {"dsb_user_id": "u1"},
            "subscription": "sub_1",
        }
        sub = MagicMock()
        sub.to_dict.return_value = {"id": "sub_1", "status": "active"}
        with (
            patch.object(
                mod.stripe.Webhook,
                "construct_event",
                return_value=_event("checkout.session.completed", obj),
            ),
            patch.object(mod.stripe.Subscription, "retrieve", return_value=sub),
            patch.object(mod, "send_subscription_welcome_email") as send_welcome,
        ):
            result = svc.verify_and_process_webhook("body", "sig")

        assert result == {"processed": True, "event_id": "evt_1", "user_id": "u1"}
        svc._activate_subscription.assert_called_once_with(
            "u1", "BUILDER", "sub_1", "active", 1700000000
        )
        send_welcome.assert_called_once()
        assert send_welcome.call_args.kwargs["tier"] == "BUILDER"

    def test_email_failure_is_swallowed(self):
        svc = _make_service()
        svc._activate_subscription = MagicMock()
        svc._record_payment_event = MagicMock()
        svc._determine_tier_from_subscription = MagicMock(return_value="BUILDER")
        svc._extract_current_period_end = MagicMock(return_value=None)
        svc._get_user_email = MagicMock(side_effect=RuntimeError("boom"))

        obj = {"metadata": {"dsb_user_id": "u1"}, "subscription": "sub_1"}
        sub = MagicMock()
        sub.to_dict.return_value = {"id": "sub_1"}
        with (
            patch.object(
                mod.stripe.Webhook,
                "construct_event",
                return_value=_event("checkout.session.completed", obj),
            ),
            patch.object(mod.stripe.Subscription, "retrieve", return_value=sub),
        ):
            result = svc.verify_and_process_webhook("body", "sig")
        # Still processed despite email failure
        assert result["processed"] is True


class TestWebhookSubscriptionUpdated:
    def test_updates_state(self):
        svc = _make_service()
        svc._resolve_user_id = MagicMock(return_value="u1")
        svc._update_subscription_state = MagicMock()
        svc._record_payment_event = MagicMock()
        svc._determine_tier_from_subscription = MagicMock(return_value="EXPLORER")
        svc._extract_current_period_end = MagicMock(return_value=1700000000)

        obj = {"id": "sub_1", "status": "active", "customer": "cus_1"}
        with patch.object(
            mod.stripe.Webhook,
            "construct_event",
            return_value=_event("customer.subscription.updated", obj),
        ):
            result = svc.verify_and_process_webhook("body", "sig")

        assert result == {"processed": True, "event_id": "evt_1", "user_id": "u1"}
        svc._update_subscription_state.assert_called_once_with(
            "u1", "EXPLORER", "sub_1", "active", 1700000000
        )


class TestWebhookSubscriptionDeleted:
    def test_downgrades_and_emails(self):
        svc = _make_service()
        svc._resolve_user_id = MagicMock(return_value="u1")
        svc._update_subscription_state = MagicMock()
        svc._record_payment_event = MagicMock()
        svc._get_membership = MagicMock(
            return_value=_membership(membership_tier={"S": "BUILDER"})
        )
        svc._get_user_email = MagicMock(return_value="user@example.com")
        svc._get_user_display_name = MagicMock(return_value="Jane")

        obj = {"id": "sub_1", "customer": "cus_1"}
        with (
            patch.object(
                mod.stripe.Webhook,
                "construct_event",
                return_value=_event("customer.subscription.deleted", obj),
            ),
            patch.object(mod, "send_subscription_expired_email") as send_expired,
        ):
            result = svc.verify_and_process_webhook("body", "sig")

        assert result == {"processed": True, "event_id": "evt_1", "user_id": "u1"}
        svc._update_subscription_state.assert_called_once_with(
            "u1", "FREE", "sub_1", "canceled"
        )
        send_expired.assert_called_once()
        assert send_expired.call_args.kwargs["previous_tier"] == "BUILDER"


class TestWebhookInvoicePaymentSucceeded:
    def test_records_payment_event(self):
        svc = _make_service()
        svc._resolve_user_id = MagicMock(return_value="u1")
        svc._record_payment_event = MagicMock()

        obj = {"subscription": "sub_1", "customer": "cus_1"}
        with patch.object(
            mod.stripe.Webhook,
            "construct_event",
            return_value=_event("invoice.payment_succeeded", obj),
        ):
            result = svc.verify_and_process_webhook("body", "sig")

        assert result == {"processed": True, "event_id": "evt_1", "user_id": "u1"}
        svc._record_payment_event.assert_called_once_with(
            "u1", "payment_succeeded", "", "sub_1", "evt_1"
        )


class TestWebhookInvoicePaymentFailed:
    def test_records_and_emails_user(self):
        svc = _make_service()
        svc._resolve_user_id = MagicMock(return_value="u1")
        svc._record_payment_event = MagicMock()
        svc._get_membership = MagicMock(
            return_value=_membership(membership_tier={"S": "BUILDER"})
        )
        svc._get_user_email = MagicMock(return_value="user@example.com")
        svc._get_user_display_name = MagicMock(return_value="Jane")

        obj = {"subscription": "sub_1", "customer": "cus_1"}
        with (
            patch.object(
                mod.stripe.Webhook,
                "construct_event",
                return_value=_event("invoice.payment_failed", obj),
            ),
            patch.object(mod, "send_payment_failed_email") as send_failed,
        ):
            result = svc.verify_and_process_webhook("body", "sig")

        # payment_failed intentionally omits user_id to skip Discord sync
        assert result == {"processed": True, "event_id": "evt_1"}
        svc._record_payment_event.assert_called_once_with(
            "u1", "payment_failed", "", "sub_1", "evt_1"
        )
        send_failed.assert_called_once()

    def test_user_without_email_logs_and_skips_send(self):
        svc = _make_service()
        svc._resolve_user_id = MagicMock(return_value="u1")
        svc._record_payment_event = MagicMock()
        svc._get_membership = MagicMock(
            return_value=_membership(membership_tier={"S": "BUILDER"})
        )
        svc._get_user_email = MagicMock(return_value=None)
        svc._get_user_display_name = MagicMock(return_value="Jane")

        obj = {"subscription": "sub_1", "customer": "cus_1"}
        with (
            patch.object(
                mod.stripe.Webhook,
                "construct_event",
                return_value=_event("invoice.payment_failed", obj),
            ),
            patch.object(mod, "send_payment_failed_email") as send_failed,
        ):
            result = svc.verify_and_process_webhook("body", "sig")

        assert result == {"processed": True, "event_id": "evt_1"}
        send_failed.assert_not_called()

    def test_unresolved_user_still_processed(self):
        svc = _make_service()
        svc._resolve_user_id = MagicMock(return_value=None)
        svc._record_payment_event = MagicMock()

        obj = {"subscription": "sub_1", "customer": "cus_unknown"}
        with patch.object(
            mod.stripe.Webhook,
            "construct_event",
            return_value=_event("invoice.payment_failed", obj),
        ):
            result = svc.verify_and_process_webhook("body", "sig")

        assert result == {"processed": True, "event_id": "evt_1"}
        svc._record_payment_event.assert_not_called()


class TestWebhookUnhandled:
    def test_unhandled_type_returns_reason(self):
        svc = _make_service()
        svc._resolve_user_id = MagicMock(return_value=None)
        obj = {"customer": "cus_1"}
        with patch.object(
            mod.stripe.Webhook,
            "construct_event",
            return_value=_event("customer.created", obj),
        ):
            result = svc.verify_and_process_webhook("body", "sig")
        assert result == {
            "processed": False,
            "event_id": "evt_1",
            "reason": "unhandled_type",
        }


# ---------------------------------------------------------------------------
# _determine_tier_from_subscription / _extract_current_period_end
# ---------------------------------------------------------------------------


class TestDetermineTier:
    def test_no_items_returns_free(self):
        svc = _make_service()
        assert svc._determine_tier_from_subscription({"items": {"data": []}}) == "FREE"

    def test_reads_product_metadata(self):
        svc = _make_service()
        sub = {"items": {"data": [{"price": {"product": "prod_1"}}]}}
        product = MagicMock()
        product.metadata = {"dsb_tier": "builder"}
        with patch.object(mod.stripe.Product, "retrieve", return_value=product):
            assert svc._determine_tier_from_subscription(sub) == "BUILDER"

    def test_product_without_dsb_tier_returns_free(self):
        svc = _make_service()
        sub = {"items": {"data": [{"price": {"product": "prod_1"}}]}}
        product = MagicMock()
        product.metadata = {}
        with patch.object(mod.stripe.Product, "retrieve", return_value=product):
            assert svc._determine_tier_from_subscription(sub) == "FREE"

    def test_exception_returns_free(self):
        svc = _make_service()
        sub = {"items": {"data": [{"price": {"product": "prod_1"}}]}}
        with patch.object(
            mod.stripe.Product, "retrieve", side_effect=RuntimeError("boom")
        ):
            assert svc._determine_tier_from_subscription(sub) == "FREE"


class TestExtractCurrentPeriodEnd:
    def test_prefers_item_value(self):
        sub = {
            "items": {"data": [{"current_period_end": 123}]},
            "current_period_end": 999,
        }
        assert StripeService._extract_current_period_end(sub) == 123

    def test_falls_back_to_root(self):
        sub = {"items": {"data": []}, "current_period_end": 999}
        assert StripeService._extract_current_period_end(sub) == 999


# ---------------------------------------------------------------------------
# DynamoDB helpers
# ---------------------------------------------------------------------------


class TestGetMembership:
    def test_returns_item(self):
        svc = _make_service()
        svc._dynamodb_client.get_item.return_value = {"Item": {"PK": {"S": "x"}}}
        assert svc._get_membership("u1") == {"PK": {"S": "x"}}
        kwargs = svc._dynamodb_client.get_item.call_args.kwargs
        assert kwargs["Key"]["PK"] == {"S": "USER#u1"}
        assert kwargs["Key"]["SK"] == {"S": "MEMBERSHIP"}

    def test_client_error_returns_none(self):
        svc = _make_service()
        svc._dynamodb_client.get_item.side_effect = mod.ClientError(
            {"Error": {"Code": "ResourceNotFound", "Message": "no"}}, "GetItem"
        )
        assert svc._get_membership("u1") is None


class TestPutMembership:
    def test_update_item_called_with_fields(self):
        svc = _make_service()
        svc._put_membership("u1", "cus_1", "BUILDER")
        kwargs = svc._dynamodb_client.update_item.call_args.kwargs
        assert kwargs["ExpressionAttributeValues"][":cid"] == {"S": "cus_1"}
        assert kwargs["ExpressionAttributeValues"][":tier"] == {"S": "BUILDER"}

    def test_client_error_raises(self):
        svc = _make_service()
        svc._dynamodb_client.update_item.side_effect = mod.ClientError(
            {"Error": {"Code": "Throttling", "Message": "no"}}, "UpdateItem"
        )
        with pytest.raises(mod.ClientError):
            svc._put_membership("u1", "cus_1")


class TestUpdateSubscriptionState:
    def test_writes_period_end_when_present(self):
        svc = _make_service()
        svc._update_subscription_state("u1", "BUILDER", "sub_1", "active", 1700000000)
        kwargs = svc._dynamodb_client.update_item.call_args.kwargs
        values = kwargs["ExpressionAttributeValues"]
        assert values[":tier"] == {"S": "BUILDER"}
        assert values[":status"] == {"S": "active"}
        assert ":cpe" in values  # period end persisted
        assert "current_period_end" in kwargs["UpdateExpression"]

    def test_omits_period_end_when_none(self):
        svc = _make_service()
        svc._update_subscription_state("u1", "FREE", "sub_1", "canceled")
        kwargs = svc._dynamodb_client.update_item.call_args.kwargs
        assert ":cpe" not in kwargs["ExpressionAttributeValues"]

    def test_client_error_is_swallowed(self):
        svc = _make_service()
        svc._dynamodb_client.update_item.side_effect = mod.ClientError(
            {"Error": {"Code": "Throttling", "Message": "no"}}, "UpdateItem"
        )
        # Must not raise
        svc._update_subscription_state("u1", "FREE", "sub_1", "canceled")


class TestActivateSubscription:
    def test_non_builder_skips_journey_init(self):
        svc = _make_service()
        svc._get_membership = MagicMock(return_value=None)
        with patch.object(mod, "ProgressDB") as pdb:
            svc._activate_subscription("u1", "EXPLORER", "sub_1", "active")
        pdb.assert_not_called()
        svc._dynamodb_client.update_item.assert_called_once()

    def test_builder_from_free_records_activation(self):
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(membership_tier={"S": "FREE"})
        )
        progress = MagicMock()
        with (
            patch.object(mod, "ProgressDB", return_value=progress),
            patch.object(mod, "record_builder_activation") as rec,
        ):
            svc._activate_subscription("u1", "BUILDER", "sub_1", "active", 1700000000)
        progress.save_journey_meta.assert_called_once_with("u1")
        rec.assert_called_once()
        assert rec.call_args.kwargs["previous_tier"] == "FREE"

    def test_membership_read_failure_defaults_to_free(self):
        svc = _make_service()
        svc._get_membership = MagicMock(side_effect=RuntimeError("read failed"))
        progress = MagicMock()
        with (
            patch.object(mod, "ProgressDB", return_value=progress),
            patch.object(mod, "record_builder_activation") as rec,
        ):
            svc._activate_subscription("u1", "BUILDER", "sub_1", "active")
        # previous_tier defaulted to FREE, so activation is recorded
        rec.assert_called_once()
        assert rec.call_args.kwargs["previous_tier"] == "FREE"

    def test_journey_init_failure_is_swallowed(self):
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(membership_tier={"S": "FREE"})
        )
        progress = MagicMock()
        progress.save_journey_meta.side_effect = RuntimeError("journey boom")
        with (
            patch.object(mod, "ProgressDB", return_value=progress),
            patch.object(mod, "record_builder_activation") as rec,
        ):
            # Must not raise despite journey init failure
            svc._activate_subscription("u1", "BUILDER", "sub_1", "active")
        rec.assert_called_once()

    def test_builder_activation_record_failure_is_swallowed(self):
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(membership_tier={"S": "FREE"})
        )
        progress = MagicMock()
        with (
            patch.object(mod, "ProgressDB", return_value=progress),
            patch.object(
                mod,
                "record_builder_activation",
                side_effect=RuntimeError("activation boom"),
            ),
        ):
            # Must not raise despite activation-record failure
            svc._activate_subscription("u1", "BUILDER", "sub_1", "active")
        progress.save_journey_meta.assert_called_once()

    def test_client_error_on_update_is_swallowed(self):
        svc = _make_service()
        svc._get_membership = MagicMock(return_value=None)
        svc._dynamodb_client.update_item.side_effect = mod.ClientError(
            {"Error": {"Code": "Throttling", "Message": "no"}}, "UpdateItem"
        )
        # Must not raise
        svc._activate_subscription("u1", "EXPLORER", "sub_1", "active")

    def test_builder_from_builder_skips_activation_record(self):
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(membership_tier={"S": "BUILDER"})
        )
        progress = MagicMock()
        with (
            patch.object(mod, "ProgressDB", return_value=progress),
            patch.object(mod, "record_builder_activation") as rec,
        ):
            svc._activate_subscription("u1", "BUILDER", "sub_1", "active")
        progress.save_journey_meta.assert_called_once()
        rec.assert_not_called()


class TestUserProfileLookups:
    def test_get_user_email_returns_value(self):
        svc = _make_service()
        svc._dynamodb_client.get_item.return_value = {
            "Item": {"email": {"S": "a@b.com"}}
        }
        assert svc._get_user_email("u1") == "a@b.com"

    def test_get_user_email_none_when_missing(self):
        svc = _make_service()
        svc._dynamodb_client.get_item.return_value = {}
        assert svc._get_user_email("u1") is None

    def test_get_user_email_client_error_none(self):
        svc = _make_service()
        svc._dynamodb_client.get_item.side_effect = mod.ClientError(
            {"Error": {"Code": "X", "Message": "no"}}, "GetItem"
        )
        assert svc._get_user_email("u1") is None

    def test_get_user_display_name_returns_value(self):
        svc = _make_service()
        svc._dynamodb_client.get_item.return_value = {
            "Item": {"username": {"S": "Jane"}}
        }
        assert svc._get_user_display_name("u1") == "Jane"


class TestRecordPaymentEvent:
    def test_puts_item(self):
        svc = _make_service()
        svc._record_payment_event("u1", "payment_succeeded", "BUILDER", "sub_1", "evt")
        kwargs = svc._dynamodb_client.put_item.call_args.kwargs
        item = kwargs["Item"]
        assert item["PK"] == {"S": "USER#u1"}
        assert item["event_type"] == {"S": "payment_succeeded"}
        assert item["stripe_event_id"] == {"S": "evt"}

    def test_client_error_swallowed(self):
        svc = _make_service()
        svc._dynamodb_client.put_item.side_effect = mod.ClientError(
            {"Error": {"Code": "X", "Message": "no"}}, "PutItem"
        )
        # Must not raise
        svc._record_payment_event("u1", "x", "", "sub", "evt")


# ---------------------------------------------------------------------------
# Student Builder activation bootstrap (_activate_subscription)
#
# Task 4.1 gated the Builder-journey-meta bootstrap on is_builder_equivalent(tier)
# and the activation-event guard on `not is_builder_equivalent(previous_tier)`.
# These tests pin that a FREE->STUDENT_BUILDER activation initializes the journey
# meta and records the activation event exactly once, while an activation from an
# already-Builder-equivalent tier (STUDENT_BUILDER or BUILDER) does not re-record.
# Requirements: 1.6, 6.1
# ---------------------------------------------------------------------------


class TestStudentBuilderActivation:
    def test_free_to_student_builder_initializes_journey_and_records_once(self):
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(membership_tier={"S": "FREE"})
        )
        progress = MagicMock()
        with (
            patch.object(mod, "ProgressDB", return_value=progress) as pdb,
            patch.object(mod, "record_builder_activation") as rec,
        ):
            svc._activate_subscription(
                "u1", "STUDENT_BUILDER", "sub_1", "active", 1700000000
            )

        # Journey meta is bootstrapped exactly once for the Builder-equivalent tier
        pdb.assert_called_once_with(svc._settings)
        progress.save_journey_meta.assert_called_once_with("u1")
        # Activation event recorded exactly once with the real previous tier
        rec.assert_called_once()
        assert rec.call_args.kwargs["previous_tier"] == "FREE"
        assert rec.call_args.kwargs["activation_source"] == "STRIPE_SUBSCRIPTION"

    def test_student_builder_to_student_builder_does_not_double_record(self):
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(membership_tier={"S": "STUDENT_BUILDER"})
        )
        progress = MagicMock()
        with (
            patch.object(mod, "ProgressDB", return_value=progress),
            patch.object(mod, "record_builder_activation") as rec,
        ):
            svc._activate_subscription("u1", "STUDENT_BUILDER", "sub_1", "active")

        # Journey meta still re-initialized (idempotent, tier is Builder-equivalent)
        progress.save_journey_meta.assert_called_once_with("u1")
        # But the activation event is NOT re-recorded: previous tier already
        # Builder-equivalent.
        rec.assert_not_called()

    def test_builder_to_student_builder_does_not_re_record(self):
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(membership_tier={"S": "BUILDER"})
        )
        progress = MagicMock()
        with (
            patch.object(mod, "ProgressDB", return_value=progress),
            patch.object(mod, "record_builder_activation") as rec,
        ):
            svc._activate_subscription("u1", "STUDENT_BUILDER", "sub_1", "active")

        progress.save_journey_meta.assert_called_once_with("u1")
        rec.assert_not_called()


# ---------------------------------------------------------------------------
# Catalog-backed tier resolution recognizes Student Builder
#
# Task 7.1 reworked _determine_tier_from_subscription to resolve a product's
# dsb_tier from the cached product catalog (get_products()) by matching
# product_id, falling back to stripe.Product.retrieve only on a cache miss. The
# resolved dsb_tier is upper-cased, defaulting to FREE when no recognized
# dsb_tier is found.
#
# Task 7.2 (property) exercises that resolution over arbitrary dsb_tier metadata
# values, including case variants, using the catalog path.
# Task 7.3 (unit) exercises STUDENT_BUILDER recognition end-to-end across the
# four event-driven paths: checkout.session.completed,
# customer.subscription.updated, customer.subscription.deleted, and
# reconcile_subscription_from_stripe.
# Requirements: 1.1, 7.1, 7.2, 7.3, 7.4
# ---------------------------------------------------------------------------


def _sub_for_product(product_id: str) -> dict:
    """Build a minimal subscription dict whose single item references product_id."""
    return {"items": {"data": [{"price": {"product": product_id}}]}}


def _catalog_row(product_id: str, dsb_tier, price_id="price_1", interval="month"):
    """A get_products()-shaped catalog row for a single product/price."""
    return {
        "id": product_id,
        "name": "Some Product",
        "description": "",
        "price": 1200,
        "monthly_price": 1200,
        "currency": "usd",
        "interval": interval,
        "dsb_tier": dsb_tier,
        "price_id": price_id,
    }


class TestDetermineTierCatalogBacked:
    """Catalog-first resolution of _determine_tier_from_subscription (Task 7.1)."""

    def test_resolves_student_builder_from_catalog(self):
        svc = _make_service()
        svc.get_products = MagicMock(
            return_value=[_catalog_row("prod_sb", "STUDENT_BUILDER")]
        )
        with patch.object(mod.stripe.Product, "retrieve") as retrieve:
            tier = svc._determine_tier_from_subscription(_sub_for_product("prod_sb"))
        assert tier == "STUDENT_BUILDER"
        # Catalog hit means no per-event Stripe Product.retrieve call.
        retrieve.assert_not_called()

    def test_catalog_value_is_upper_cased(self):
        svc = _make_service()
        svc.get_products = MagicMock(
            return_value=[_catalog_row("prod_sb", "student_builder")]
        )
        with patch.object(mod.stripe.Product, "retrieve") as retrieve:
            tier = svc._determine_tier_from_subscription(_sub_for_product("prod_sb"))
        assert tier == "STUDENT_BUILDER"
        retrieve.assert_not_called()

    def test_cache_miss_falls_back_to_product_retrieve(self):
        svc = _make_service()
        # Catalog does not contain the subscription's product id.
        svc.get_products = MagicMock(
            return_value=[_catalog_row("prod_other", "BUILDER")]
        )
        product = MagicMock()
        product.metadata = {"dsb_tier": "STUDENT_BUILDER"}
        with patch.object(
            mod.stripe.Product, "retrieve", return_value=product
        ) as retrieve:
            tier = svc._determine_tier_from_subscription(_sub_for_product("prod_sb"))
        assert tier == "STUDENT_BUILDER"
        retrieve.assert_called_once_with("prod_sb")


class TestTierResolutionProperty:
    """Property 5 — tier resolution recognizes Student Builder."""

    @settings(max_examples=200)
    @given(
        raw_tier=st.one_of(
            st.sampled_from(
                [
                    "STUDENT_BUILDER",
                    "student_builder",
                    "Student_Builder",
                    "BUILDER",
                    "builder",
                    "Builder",
                    "EXPLORER",
                    "free",
                ]
            ),
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"),
                    whitelist_characters="_",
                ),
                min_size=0,
                max_size=24,
            ),
        )
    )
    def test_catalog_tier_resolves_to_uppercase_or_free(self, raw_tier):
        """Feature: student-builder-membership, Property 5: Tier resolution recognizes Student Builder

        For any Stripe subscription whose catalog row carries a dsb_tier value,
        the resolver returns that value upper-cased (so STUDENT_BUILDER and
        BUILDER are recognized across case variants); a falsy/absent dsb_tier
        resolves to FREE.

        Validates: Requirements 1.1, 7.1, 7.2, 7.3, 7.4
        """
        svc = _make_service()
        svc.get_products = MagicMock(return_value=[_catalog_row("prod_x", raw_tier)])
        # No fallback expected: product id is present in the catalog.
        with patch.object(mod.stripe.Product, "retrieve") as retrieve:
            tier = svc._determine_tier_from_subscription(_sub_for_product("prod_x"))

        expected = raw_tier.upper() if raw_tier else "FREE"
        assert tier == expected
        retrieve.assert_not_called()

    @settings(max_examples=200)
    @given(
        raw_tier=st.one_of(
            st.none(),
            st.sampled_from(
                [
                    "STUDENT_BUILDER",
                    "student_builder",
                    "BUILDER",
                    "builder",
                    "EXPLORER",
                ]
            ),
        )
    )
    def test_cache_miss_fallback_resolves_from_product_metadata(self, raw_tier):
        """Feature: student-builder-membership, Property 5: Tier resolution recognizes Student Builder

        On a catalog cache miss, the resolver falls back to
        stripe.Product.retrieve and upper-cases the product's dsb_tier metadata,
        defaulting to FREE when the dsb_tier key is absent.

        Note: the fallback path defaults to FREE only on key-absence (it does
        not coerce an explicit empty-string value to FREE); that empty-string ->
        FREE coercion is exercised on the catalog path above. This generator
        therefore models absent (None) and recognized/case-variant values.

        Validates: Requirements 1.1, 7.1, 7.2, 7.3, 7.4
        """
        svc = _make_service()
        # Subscription product id not present in the catalog -> fallback path.
        svc.get_products = MagicMock(return_value=[])
        product = MagicMock()
        product.metadata = {"dsb_tier": raw_tier} if raw_tier is not None else {}
        with patch.object(mod.stripe.Product, "retrieve", return_value=product):
            tier = svc._determine_tier_from_subscription(_sub_for_product("prod_x"))

        expected = raw_tier.upper() if raw_tier else "FREE"
        assert tier == expected


class TestWebhookStudentBuilderRecognition:
    """Task 7.3 — STUDENT_BUILDER recognition across webhook event types.

    These drive the real (catalog-backed) _determine_tier_from_subscription via
    a patched get_products catalog, asserting the resolved STUDENT_BUILDER tier
    reaches the activation / state-update / downgrade writes.
    """

    _SB_PRODUCT = "prod_student_builder"

    def _sb_catalog(self):
        return [_catalog_row(self._SB_PRODUCT, "STUDENT_BUILDER")]

    def test_checkout_completed_activates_student_builder(self):
        svc = _make_service()
        svc.get_products = MagicMock(return_value=self._sb_catalog())
        svc._activate_subscription = MagicMock()
        svc._record_payment_event = MagicMock()
        svc._extract_current_period_end = MagicMock(return_value=1700000000)
        svc._get_user_email = MagicMock(return_value=None)
        svc._get_user_display_name = MagicMock(return_value=None)

        obj = {
            "customer": "cus_1",
            "metadata": {"dsb_user_id": "u1"},
            "subscription": "sub_1",
        }
        sub = MagicMock()
        sub.to_dict.return_value = _sub_for_product(self._SB_PRODUCT)
        # Activation re-verify (task 13.1): a STUDENT_BUILDER checkout only
        # activates when the user still holds active eligibility, so stub the
        # eligibility read to an active record.
        with (
            patch.object(
                mod.stripe.Webhook,
                "construct_event",
                return_value=_event("checkout.session.completed", obj),
            ),
            patch.object(mod.stripe.Subscription, "retrieve", return_value=sub),
            patch.object(mod.stripe.Product, "retrieve") as retrieve,
            patch(
                "app.services.verification_service.VerificationService."
                "get_eligibility",
                return_value={"expires_at": "2999-01-01T00:00:00+00:00"},
            ),
        ):
            result = svc.verify_and_process_webhook("body", "sig")

        assert result == {"processed": True, "event_id": "evt_1", "user_id": "u1"}
        svc._activate_subscription.assert_called_once_with(
            "u1", "STUDENT_BUILDER", "sub_1", "active", 1700000000
        )
        # Catalog resolution means no per-event Product.retrieve.
        retrieve.assert_not_called()

    def test_subscription_updated_writes_student_builder(self):
        svc = _make_service()
        svc.get_products = MagicMock(return_value=self._sb_catalog())
        svc._resolve_user_id = MagicMock(return_value="u1")
        svc._update_subscription_state = MagicMock()
        svc._record_payment_event = MagicMock()
        svc._extract_current_period_end = MagicMock(return_value=1700000000)

        obj = {
            "id": "sub_1",
            "status": "active",
            "customer": "cus_1",
            "items": {"data": [{"price": {"product": self._SB_PRODUCT}}]},
        }
        with (
            patch.object(
                mod.stripe.Webhook,
                "construct_event",
                return_value=_event("customer.subscription.updated", obj),
            ),
            patch.object(mod.stripe.Product, "retrieve") as retrieve,
        ):
            result = svc.verify_and_process_webhook("body", "sig")

        assert result == {"processed": True, "event_id": "evt_1", "user_id": "u1"}
        svc._update_subscription_state.assert_called_once_with(
            "u1", "STUDENT_BUILDER", "sub_1", "active", 1700000000
        )
        retrieve.assert_not_called()

    def test_subscription_deleted_downgrades_student_builder_to_free(self):
        svc = _make_service()
        svc.get_products = MagicMock(return_value=self._sb_catalog())
        svc._resolve_user_id = MagicMock(return_value="u1")
        svc._update_subscription_state = MagicMock()
        svc._record_payment_event = MagicMock()
        svc._get_membership = MagicMock(
            return_value=_membership(membership_tier={"S": "STUDENT_BUILDER"})
        )
        svc._get_user_email = MagicMock(return_value=None)
        svc._get_user_display_name = MagicMock(return_value=None)

        obj = {
            "id": "sub_1",
            "customer": "cus_1",
            "items": {"data": [{"price": {"product": self._SB_PRODUCT}}]},
        }
        with patch.object(
            mod.stripe.Webhook,
            "construct_event",
            return_value=_event("customer.subscription.deleted", obj),
        ):
            result = svc.verify_and_process_webhook("body", "sig")

        assert result == {"processed": True, "event_id": "evt_1", "user_id": "u1"}
        # Cancellation path always downgrades to FREE regardless of prior tier;
        # the previous STUDENT_BUILDER tier is surfaced to the expiration email.
        svc._update_subscription_state.assert_called_once_with(
            "u1", "FREE", "sub_1", "canceled"
        )

    def test_reconcile_writes_student_builder_from_active_subscription(self):
        svc = _make_service()
        svc.get_products = MagicMock(return_value=self._sb_catalog())
        svc._get_membership = MagicMock(
            return_value=_membership(
                stripe_customer_id={"S": "cus_1"},
                membership_tier={"S": "FREE"},
            )
        )
        svc._activate_subscription = MagicMock()
        svc._update_subscription_state = MagicMock()
        svc._extract_current_period_end = MagicMock(return_value=1700000000)

        active_sub = {
            "id": "sub_1",
            "status": "active",
            "items": {"data": [{"price": {"product": self._SB_PRODUCT}}]},
        }
        subs = MagicMock()
        subs.to_dict.return_value = {"data": [active_sub]}
        with (
            patch.object(mod.stripe.Subscription, "list", return_value=subs),
            patch.object(mod.stripe.Product, "retrieve") as retrieve,
        ):
            result = svc.reconcile_subscription_from_stripe("u1")

        assert result["reconciled"] is True
        assert result["tier"] == "STUDENT_BUILDER"
        assert result["changed"] is True
        # FREE -> STUDENT_BUILDER is a first-time activation.
        svc._activate_subscription.assert_called_once_with(
            "u1", "STUDENT_BUILDER", "sub_1", "active", 1700000000
        )
        retrieve.assert_not_called()


# ---------------------------------------------------------------------------
# Student Builder product/price discovery (Fail_Closed)
#
# Task 8.1 added get_student_builder_product() (cache-first via get_products(),
# group by dsb_tier, Fail_Closed on zero / >1 distinct product ids or no active
# recurring price) and select_price_for_interval(rows, interval) (single active
# recurring price matching 'month'/'year', Fail_Closed otherwise).
#
# get_products() returns one row per active recurring price, so a single
# Student Builder product with monthly + annual prices is TWO rows that share
# the same product 'id'. "Zero/one/two products" therefore means the number of
# DISTINCT 'id' values among the STUDENT_BUILDER rows -- not the row count.
#
# Task 8.2 (unit) pins the discovery Fail_Closed behavior plus the underlying
# get_products() Stripe-failure-with/without-cache behavior as it feeds
# discovery.
# Task 8.3 (property, Property 8) exercises select_price_for_interval over
# generated active-recurring price sets x requested interval.
# Requirements: 2.2, 2.6, 2.7, 2.8 / 5.3, 5.4, 5.5
# ---------------------------------------------------------------------------


def _sb_row(
    product_id="prod_sb",
    interval="month",
    price_id="price_sb_month",
    unit_amount=1200,
    currency="usd",
    tier="STUDENT_BUILDER",
):
    """A get_products()-shaped STUDENT_BUILDER price row.

    A single product with monthly + annual prices yields two of these rows
    sharing the same ``product_id`` but differing ``interval``/``price_id``.
    """
    return _catalog_row(
        product_id,
        tier,
        price_id=price_id,
        interval=interval,
    ) | {"price": unit_amount, "monthly_price": unit_amount, "currency": currency}


class TestGetStudentBuilderProduct:
    """Task 8.2 — Fail_Closed discovery of the unique STUDENT_BUILDER product."""

    def test_unique_product_happy_path_returns_monthly_and_annual(self):
        """One STUDENT_BUILDER product with monthly + annual prices (two rows
        sharing the same product id) is returned in full."""
        svc = _make_service()
        monthly = _sb_row(interval="month", price_id="price_m", unit_amount=1200)
        annual = _sb_row(interval="year", price_id="price_y", unit_amount=12000)
        # Mix in an unrelated Builder product to prove grouping by dsb_tier.
        svc.get_products = MagicMock(
            return_value=[
                _catalog_row("prod_builder", "BUILDER", price_id="price_b"),
                monthly,
                annual,
            ]
        )

        rows = svc.get_student_builder_product()

        assert len(rows) == 2
        assert {r["interval"] for r in rows} == {"month", "year"}
        assert {r["id"] for r in rows} == {"prod_sb"}
        assert {r["price_id"] for r in rows} == {"price_m", "price_y"}

    def test_zero_student_builder_products_fail_closed(self):
        """No STUDENT_BUILDER rows among the catalog -> ValueError."""
        svc = _make_service()
        svc.get_products = MagicMock(
            return_value=[
                _catalog_row("prod_builder", "BUILDER"),
                _catalog_row("prod_free", "FREE"),
            ]
        )
        with pytest.raises(ValueError, match="could not be uniquely identified"):
            svc.get_student_builder_product()

    def test_two_distinct_student_builder_products_fail_closed(self):
        """Two DISTINCT product ids both carrying dsb_tier=STUDENT_BUILDER ->
        ambiguous -> ValueError (never silently picks one)."""
        svc = _make_service()
        svc.get_products = MagicMock(
            return_value=[
                _sb_row(product_id="prod_sb_a", price_id="price_a"),
                _sb_row(product_id="prod_sb_b", price_id="price_b"),
            ]
        )
        with pytest.raises(ValueError, match="could not be uniquely identified"):
            svc.get_student_builder_product()

    def test_two_price_rows_one_product_is_not_ambiguous(self):
        """Two STUDENT_BUILDER rows that share ONE product id (monthly + annual)
        are a single product, not two -- so no Fail_Closed."""
        svc = _make_service()
        svc.get_products = MagicMock(
            return_value=[
                _sb_row(interval="month", price_id="price_m"),
                _sb_row(interval="year", price_id="price_y"),
            ]
        )
        rows = svc.get_student_builder_product()
        assert len(rows) == 2
        assert {r["id"] for r in rows} == {"prod_sb"}

    def test_product_with_only_one_time_price_fail_closed(self):
        """A uniquely identified STUDENT_BUILDER product whose rows carry no
        recurring interval (only a one-time price; interval is None) ->
        ValueError (no active recurring price)."""
        svc = _make_service()
        svc.get_products = MagicMock(
            return_value=[
                _sb_row(interval=None, price_id="price_once"),
            ]
        )
        with pytest.raises(ValueError, match="No active recurring"):
            svc.get_student_builder_product()

    def test_discovery_reflects_stale_cache_on_stripe_failure(self):
        """get_products() returns stale cached rows on a Stripe failure, and
        discovery resolves from exactly those rows (cache-first, no refetch)."""
        svc = _make_service()
        StripeService._products_cache["data"] = [
            _sb_row(interval="month", price_id="price_m"),
            _sb_row(interval="year", price_id="price_y"),
        ]
        StripeService._products_cache["timestamp"] = 0.0  # expired -> refetch attempt
        with patch.object(
            mod.stripe.Product, "list", side_effect=RuntimeError("stripe down")
        ):
            rows = svc.get_student_builder_product()
        assert {r["interval"] for r in rows} == {"month", "year"}

    def test_discovery_propagates_when_stripe_fails_without_cache(self):
        """With no cached catalog, a Stripe failure in get_products() propagates
        out of discovery (Fail_Closed: no fallback)."""
        svc = _make_service()
        _reset_product_cache()
        with patch.object(
            mod.stripe.Product, "list", side_effect=RuntimeError("stripe down")
        ):
            with pytest.raises(RuntimeError):
                svc.get_student_builder_product()


class TestSelectPriceForInterval:
    """Task 8.2 — example-based coverage of select_price_for_interval."""

    def test_selects_matching_interval_row(self):
        svc = _make_service()
        monthly = _sb_row(interval="month", price_id="price_m")
        annual = _sb_row(interval="year", price_id="price_y")
        assert svc.select_price_for_interval([monthly, annual], "month") is monthly
        assert svc.select_price_for_interval([monthly, annual], "year") is annual

    def test_no_matching_interval_fail_closed(self):
        svc = _make_service()
        monthly = _sb_row(interval="month", price_id="price_m")
        with pytest.raises(ValueError, match="No active recurring"):
            svc.select_price_for_interval([monthly], "year")

    def test_unsupported_interval_fail_closed(self):
        svc = _make_service()
        monthly = _sb_row(interval="month", price_id="price_m")
        with pytest.raises(ValueError, match="Unsupported billing interval"):
            svc.select_price_for_interval([monthly], "week")

    def test_duplicate_matching_interval_fail_closed(self):
        """Two rows with the same interval (misconfigured duplicate) ->
        ValueError rather than silently picking one."""
        svc = _make_service()
        dup_a = _sb_row(interval="month", price_id="price_m_a")
        dup_b = _sb_row(interval="month", price_id="price_m_b")
        with pytest.raises(ValueError, match="Multiple active recurring"):
            svc.select_price_for_interval([dup_a, dup_b], "month")


# A price row carries exactly the fields select_price_for_interval reads
# (interval); we vary price_id so distinct rows are distinguishable.
_INTERVALS = ("month", "year")


@st.composite
def _recurring_price_rows(draw):
    """Generate a set of active recurring price rows.

    Each row has interval in {'month','year'} and a unique price_id. The set may
    contain zero, one, or many rows, and intervals may be duplicated -- exactly
    the shapes select_price_for_interval must triage (unique match, no match,
    duplicate match).
    """
    n = draw(st.integers(min_value=0, max_value=6))
    intervals = draw(st.lists(st.sampled_from(_INTERVALS), min_size=n, max_size=n))
    rows = [
        _sb_row(interval=iv, price_id=f"price_{i}_{iv}")
        for i, iv in enumerate(intervals)
    ]
    return rows


class TestSelectPriceForIntervalProperty:
    """Property 8 — price selection matches the requested interval."""

    @settings(max_examples=200)
    @given(rows=_recurring_price_rows(), interval=st.sampled_from(_INTERVALS))
    def test_selects_single_match_or_fail_closes(self, rows, interval):
        """Feature: student-builder-membership, Property 8: Price selection matches the requested interval

        For any set of active recurring price rows and a requested interval,
        select_price_for_interval returns the single row whose interval equals
        the requested interval when exactly one such row exists; otherwise it
        Fail_Closes (raises ValueError) -- i.e. when zero rows match, or when a
        duplicated interval makes the choice ambiguous. It never returns a row
        whose interval differs from the request.

        Validates: Requirements 5.3, 5.4, 5.5
        """
        svc = _make_service()
        matches = [r for r in rows if r["interval"] == interval]

        if len(matches) == 1:
            selected = svc.select_price_for_interval(rows, interval)
            # The returned row matches the request and is the unique match.
            assert selected["interval"] == interval
            assert selected is matches[0]
        else:
            # Zero matches or a duplicate interval set both Fail_Close.
            with pytest.raises(ValueError):
                svc.select_price_for_interval(rows, interval)

    @settings(max_examples=200)
    @given(
        data=st.data(),
        interval=st.sampled_from(_INTERVALS),
    )
    def test_mismatched_only_set_always_fail_closes(self, data, interval):
        """Feature: student-builder-membership, Property 8: Price selection matches the requested interval

        A set built exclusively from the OTHER interval (no row matches the
        request) always Fail_Closes, regardless of how many such rows exist.

        Validates: Requirements 5.3, 5.4, 5.5
        """
        svc = _make_service()
        other = "year" if interval == "month" else "month"
        n = data.draw(st.integers(min_value=1, max_value=5))
        rows = [
            _sb_row(interval=other, price_id=f"price_{i}_{other}") for i in range(n)
        ]
        with pytest.raises(ValueError, match="No active recurring"):
            svc.select_price_for_interval(rows, interval)


# ---------------------------------------------------------------------------
# Activation re-verification in checkout.session.completed
#
# Task 13.2 (Property 10, Requirement 5.12). Task 13.1 added a re-read of the
# user's STUDENT_ELIGIBILITY inside the checkout.session.completed branch: when
# the resolved tier is STUDENT_BUILDER, the grant proceeds only if the user
# STILL holds active eligibility at activation time. If eligibility has lapsed
# (get_eligibility -> None) the handler skips _activate_subscription, records a
# ``student_activation_blocked`` audit event (PAYMENT#{ts} shape) with the tier
# unchanged, and still reports the webhook as processed. An eligibility read
# failure fails closed (treated as blocked).
#
# VerificationService is lazily imported inside verify_and_process_webhook as
# ``from app.services.verification_service import VerificationService``, so it
# is patched at its definition module: app.services.verification_service.
# get_products is stubbed with a STUDENT_BUILDER catalog so the real
# (catalog-backed) _determine_tier_from_subscription resolves STUDENT_BUILDER.
# ---------------------------------------------------------------------------


class TestWebhookActivationReverify:
    """Task 13.2 — re-verify active eligibility before granting STUDENT_BUILDER."""

    _SB_PRODUCT = "prod_student_builder"

    def _sb_catalog(self):
        return [_catalog_row(self._SB_PRODUCT, "STUDENT_BUILDER")]

    def _checkout_obj(self):
        return {
            "customer": "cus_1",
            "metadata": {"dsb_user_id": "u1"},
            "subscription": "sub_1",
        }

    def test_still_eligible_grants_student_builder(self):
        """Active eligibility at activation -> _activate_subscription IS called
        with STUDENT_BUILDER and a subscription_activated event is recorded.

        Validates: Requirements 5.12
        """
        svc = _make_service()
        svc.get_products = MagicMock(return_value=self._sb_catalog())
        svc._activate_subscription = MagicMock()
        svc._record_payment_event = MagicMock()
        svc._extract_current_period_end = MagicMock(return_value=1700000000)
        svc._get_user_email = MagicMock(return_value=None)
        svc._get_user_display_name = MagicMock(return_value=None)

        sub = MagicMock()
        sub.to_dict.return_value = _sub_for_product(self._SB_PRODUCT)
        vs_cls = MagicMock()
        vs_cls.return_value.get_eligibility.return_value = {
            "expires_at": "2999-01-01T00:00:00+00:00"
        }
        with (
            patch.object(
                mod.stripe.Webhook,
                "construct_event",
                return_value=_event("checkout.session.completed", self._checkout_obj()),
            ),
            patch.object(mod.stripe.Subscription, "retrieve", return_value=sub),
            patch("app.services.verification_service.VerificationService", vs_cls),
        ):
            result = svc.verify_and_process_webhook("body", "sig")

        assert result == {"processed": True, "event_id": "evt_1", "user_id": "u1"}
        svc._activate_subscription.assert_called_once_with(
            "u1", "STUDENT_BUILDER", "sub_1", "active", 1700000000
        )
        vs_cls.return_value.get_eligibility.assert_called_once_with("u1")
        # The activation event is the subscription_activated grant, not a block.
        svc._record_payment_event.assert_called_once_with(
            "u1", "subscription_activated", "STUDENT_BUILDER", "sub_1", "evt_1"
        )

    def test_eligibility_lapsed_blocks_activation_and_audits(self):
        """Eligibility no longer active (get_eligibility -> None) ->
        _activate_subscription is NOT called, a student_activation_blocked audit
        event is recorded with the membership tier unchanged, and the webhook
        result is still processed=True.

        Validates: Requirements 5.12
        """
        svc = _make_service()
        svc.get_products = MagicMock(return_value=self._sb_catalog())
        svc._activate_subscription = MagicMock()
        svc._record_payment_event = MagicMock()
        svc._extract_current_period_end = MagicMock(return_value=1700000000)
        # Current membership tier that must be preserved on the audit record.
        svc._get_membership = MagicMock(
            return_value=_membership(membership_tier={"S": "FREE"})
        )

        sub = MagicMock()
        sub.to_dict.return_value = _sub_for_product(self._SB_PRODUCT)
        vs_cls = MagicMock()
        vs_cls.return_value.get_eligibility.return_value = None
        with (
            patch.object(
                mod.stripe.Webhook,
                "construct_event",
                return_value=_event("checkout.session.completed", self._checkout_obj()),
            ),
            patch.object(mod.stripe.Subscription, "retrieve", return_value=sub),
            patch("app.services.verification_service.VerificationService", vs_cls),
        ):
            result = svc.verify_and_process_webhook("body", "sig")

        # Handled, not an error: processed with no tier change.
        assert result == {
            "processed": True,
            "event_id": "evt_1",
            "user_id": "u1",
            "reason": "student_activation_blocked",
        }
        # No grant.
        svc._activate_subscription.assert_not_called()
        vs_cls.return_value.get_eligibility.assert_called_once_with("u1")
        # Exactly one audit event: the block, carrying the UNCHANGED tier.
        svc._record_payment_event.assert_called_once_with(
            "u1", "student_activation_blocked", "FREE", "sub_1", "evt_1"
        )

    def test_eligibility_read_failure_fails_closed(self):
        """An eligibility read error is treated as "no longer eligible": no
        grant, a student_activation_blocked audit event, processed=True.

        Validates: Requirements 5.12
        """
        svc = _make_service()
        svc.get_products = MagicMock(return_value=self._sb_catalog())
        svc._activate_subscription = MagicMock()
        svc._record_payment_event = MagicMock()
        svc._extract_current_period_end = MagicMock(return_value=1700000000)
        svc._get_membership = MagicMock(
            return_value=_membership(membership_tier={"S": "FREE"})
        )

        sub = MagicMock()
        sub.to_dict.return_value = _sub_for_product(self._SB_PRODUCT)
        vs_cls = MagicMock()
        vs_cls.return_value.get_eligibility.side_effect = RuntimeError("dynamo down")
        with (
            patch.object(
                mod.stripe.Webhook,
                "construct_event",
                return_value=_event("checkout.session.completed", self._checkout_obj()),
            ),
            patch.object(mod.stripe.Subscription, "retrieve", return_value=sub),
            patch("app.services.verification_service.VerificationService", vs_cls),
        ):
            result = svc.verify_and_process_webhook("body", "sig")

        assert result == {
            "processed": True,
            "event_id": "evt_1",
            "user_id": "u1",
            "reason": "student_activation_blocked",
        }
        svc._activate_subscription.assert_not_called()
        svc._record_payment_event.assert_called_once_with(
            "u1", "student_activation_blocked", "FREE", "sub_1", "evt_1"
        )


# ---------------------------------------------------------------------------
# Student Builder checkout guards (create_student_checkout_session)
#
# Task 12.2 (Requirements 5.1, 5.2, 5.5, 5.6, 5.7, 5.9, 5.11; Property 8, 9).
# create_student_checkout_session runs an eligibility + duplicate-subscription +
# price-selection gate strictly BEFORE touching Stripe:
#   - not active-eligible (get_eligibility -> None)  -> StudentEligibilityError
#     (403), raised before any Stripe customer/session call.
#   - existing active/past_due subscription           -> DuplicateSubscriptionError
#     (400).
#   - eligibility/membership read failure             -> EligibilityReadError
#     (503) with membership state unchanged.
#   - client price_id != resolved price               -> InvalidPriceSelectionError
#     (400).
#   - happy path -> subscription-mode Checkout Session carrying metadata
#     {dsb_user_id, dsb_tier: STUDENT_BUILDER, eligibility_verified,
#     eligibility_expires_at} and returns checkout_url.
#
# VerificationService is lazily imported inside create_student_checkout_session
# as ``from app.services.verification_service import VerificationService``, so it
# is patched at its definition module (app.services.verification_service).
# The resolved Student Builder price is controlled by stubbing
# svc.get_student_builder_product / svc.select_price_for_interval.
# ---------------------------------------------------------------------------


def _patch_verification(eligibility=None, *, error=None):
    """Return a MagicMock VerificationService class + the patch for it.

    ``eligibility`` is the value get_eligibility returns (a dict with
    'expires_at' for an active record, or None for not-eligible). When ``error``
    is provided, get_eligibility raises it instead (read failure path).
    """
    vs_cls = MagicMock()
    if error is not None:
        vs_cls.return_value.get_eligibility.side_effect = error
    else:
        vs_cls.return_value.get_eligibility.return_value = eligibility
    return vs_cls, patch(
        "app.services.verification_service.VerificationService", vs_cls
    )


class TestCreateStudentCheckoutSession:
    """Task 12.2 — guards for the eligibility-gated Student Builder checkout."""

    _RESOLVED_PRICE_ID = "price_sb_month"

    def _resolved_price(self):
        return _sb_row(interval="month", price_id=self._RESOLVED_PRICE_ID)

    def test_not_eligible_raises_before_any_stripe_call(self):
        """get_eligibility -> None rejects with StudentEligibilityError BEFORE
        resolving a Stripe customer or creating a session (Requirements 5.1, 5.2).

        Validates: Requirements 5.1, 5.2
        """
        svc = _make_service()
        svc._get_membership = MagicMock(return_value=None)
        # Price resolution / Stripe must never be reached on the reject path.
        svc.get_student_builder_product = MagicMock()
        svc.select_price_for_interval = MagicMock()

        vs_cls, vs_patch = _patch_verification(eligibility=None)
        with (
            vs_patch,
            patch.object(mod.stripe.Customer, "create") as cust_create,
            patch.object(mod.stripe.checkout.Session, "create") as sess_create,
        ):
            with pytest.raises(mod.StudentEligibilityError):
                svc.create_student_checkout_session(
                    "u1", self._RESOLVED_PRICE_ID, "month"
                )

        # No Stripe calls, and price was never even resolved.
        cust_create.assert_not_called()
        sess_create.assert_not_called()
        svc.get_student_builder_product.assert_not_called()
        svc.select_price_for_interval.assert_not_called()

    def test_active_subscription_raises_duplicate(self):
        """An existing active subscription -> DuplicateSubscriptionError (5.7).

        Validates: Requirements 5.7
        """
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(subscription_status={"S": "active"})
        )
        svc.get_student_builder_product = MagicMock()
        svc.select_price_for_interval = MagicMock()

        vs_cls, vs_patch = _patch_verification(
            eligibility={"expires_at": "2999-01-01T00:00:00+00:00"}
        )
        with (
            vs_patch,
            patch.object(mod.stripe.Customer, "create") as cust_create,
            patch.object(mod.stripe.checkout.Session, "create") as sess_create,
        ):
            with pytest.raises(mod.DuplicateSubscriptionError):
                svc.create_student_checkout_session(
                    "u1", self._RESOLVED_PRICE_ID, "month"
                )

        cust_create.assert_not_called()
        sess_create.assert_not_called()

    def test_past_due_subscription_raises_duplicate(self):
        """A past_due subscription also trips the duplicate guard (5.7).

        Validates: Requirements 5.7
        """
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(subscription_status={"S": "past_due"})
        )
        svc.get_student_builder_product = MagicMock()
        svc.select_price_for_interval = MagicMock()

        vs_cls, vs_patch = _patch_verification(
            eligibility={"expires_at": "2999-01-01T00:00:00+00:00"}
        )
        with (
            vs_patch,
            patch.object(mod.stripe.checkout.Session, "create") as sess_create,
        ):
            with pytest.raises(mod.DuplicateSubscriptionError):
                svc.create_student_checkout_session(
                    "u1", self._RESOLVED_PRICE_ID, "month"
                )
        sess_create.assert_not_called()

    def test_eligibility_read_failure_raises_read_error_state_unchanged(self):
        """A read failure on eligibility -> EligibilityReadError (503) and the
        membership state is left unchanged (no writes, Requirement 5.9).

        Validates: Requirements 5.9
        """
        svc = _make_service()
        svc._get_membership = MagicMock(return_value=None)
        svc._put_membership = MagicMock()
        svc.get_student_builder_product = MagicMock()
        svc.select_price_for_interval = MagicMock()

        vs_cls, vs_patch = _patch_verification(error=RuntimeError("dynamo down"))
        with (
            vs_patch,
            patch.object(mod.stripe.Customer, "create") as cust_create,
            patch.object(mod.stripe.checkout.Session, "create") as sess_create,
        ):
            with pytest.raises(mod.EligibilityReadError):
                svc.create_student_checkout_session(
                    "u1", self._RESOLVED_PRICE_ID, "month"
                )

        # State unchanged: no membership write, no Stripe interaction.
        svc._put_membership.assert_not_called()
        cust_create.assert_not_called()
        sess_create.assert_not_called()

    def test_membership_read_failure_raises_read_error_state_unchanged(self):
        """A read failure on the membership record -> EligibilityReadError (503),
        state unchanged (Requirement 5.9).

        Validates: Requirements 5.9
        """
        svc = _make_service()
        svc._get_membership = MagicMock(side_effect=RuntimeError("dynamo down"))
        svc._put_membership = MagicMock()

        vs_cls, vs_patch = _patch_verification(
            eligibility={"expires_at": "2999-01-01T00:00:00+00:00"}
        )
        with (
            vs_patch,
            patch.object(mod.stripe.checkout.Session, "create") as sess_create,
        ):
            with pytest.raises(mod.EligibilityReadError):
                svc.create_student_checkout_session(
                    "u1", self._RESOLVED_PRICE_ID, "month"
                )

        svc._put_membership.assert_not_called()
        sess_create.assert_not_called()

    def test_client_price_mismatch_raises_invalid_price(self):
        """A client price_id that differs from the resolved Student Builder price
        -> InvalidPriceSelectionError (400), with no session created (5.5).

        Validates: Requirements 5.5
        """
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(stripe_customer_id={"S": "cus_1"})
        )
        svc.get_student_builder_product = MagicMock(
            return_value=[self._resolved_price()]
        )
        svc.select_price_for_interval = MagicMock(return_value=self._resolved_price())

        vs_cls, vs_patch = _patch_verification(
            eligibility={"expires_at": "2999-01-01T00:00:00+00:00"}
        )
        with (
            vs_patch,
            patch.object(mod.stripe.checkout.Session, "create") as sess_create,
        ):
            with pytest.raises(mod.InvalidPriceSelectionError):
                svc.create_student_checkout_session(
                    "u1", "price_arbitrary_substitute", "month"
                )
        sess_create.assert_not_called()

    def test_happy_path_builds_session_with_eligibility_metadata(self):
        """Active-eligible, no active sub, matching price -> a subscription-mode
        Checkout Session is created with the eligibility snapshot in metadata and
        checkout_url is returned (Requirements 5.6, 5.11).

        Validates: Requirements 5.6, 5.11
        """
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(stripe_customer_id={"S": "cus_1"})
        )
        svc.get_student_builder_product = MagicMock(
            return_value=[self._resolved_price()]
        )
        svc.select_price_for_interval = MagicMock(return_value=self._resolved_price())

        session = MagicMock(url="https://checkout/student")
        vs_cls, vs_patch = _patch_verification(
            eligibility={"expires_at": "2999-01-01T00:00:00+00:00"}
        )
        with (
            vs_patch,
            patch.object(mod.stripe.Customer, "create") as cust_create,
            patch.object(
                mod.stripe.checkout.Session, "create", return_value=session
            ) as sess_create,
        ):
            result = svc.create_student_checkout_session(
                "u1", self._RESOLVED_PRICE_ID, "month"
            )

        assert result == {"checkout_url": "https://checkout/student"}
        # Existing customer reused, so no customer creation.
        cust_create.assert_not_called()
        kwargs = sess_create.call_args.kwargs
        assert kwargs["customer"] == "cus_1"
        assert kwargs["mode"] == "subscription"
        assert kwargs["line_items"] == [
            {"price": self._RESOLVED_PRICE_ID, "quantity": 1}
        ]
        assert kwargs["metadata"] == {
            "dsb_user_id": "u1",
            "dsb_tier": "STUDENT_BUILDER",
            "eligibility_verified": "true",
            "eligibility_expires_at": "2999-01-01T00:00:00+00:00",
        }

    def test_happy_path_creates_customer_when_missing(self):
        """When no stripe_customer_id exists yet, the happy path creates a Stripe
        customer, persists it, and still carries the Student Builder metadata.

        Validates: Requirements 5.6, 5.11
        """
        svc = _make_service()
        svc._get_membership = MagicMock(return_value=None)
        svc._put_membership = MagicMock()
        svc.get_student_builder_product = MagicMock(
            return_value=[self._resolved_price()]
        )
        svc.select_price_for_interval = MagicMock(return_value=self._resolved_price())

        customer = MagicMock(id="cus_new")
        session = MagicMock(url="https://checkout/student")
        vs_cls, vs_patch = _patch_verification(
            eligibility={"expires_at": "2999-01-01T00:00:00+00:00"}
        )
        with (
            vs_patch,
            patch.object(mod.stripe.Customer, "create", return_value=customer),
            patch.object(
                mod.stripe.checkout.Session, "create", return_value=session
            ) as sess_create,
        ):
            result = svc.create_student_checkout_session(
                "u1", self._RESOLVED_PRICE_ID, "month"
            )

        assert result == {"checkout_url": "https://checkout/student"}
        svc._put_membership.assert_called_once()
        assert sess_create.call_args.kwargs["customer"] == "cus_new"
        assert sess_create.call_args.kwargs["metadata"]["dsb_tier"] == "STUDENT_BUILDER"


# ---------------------------------------------------------------------------
# Property 9 — checkout is gated by active eligibility
#
# Task 12.3 (Requirements 5.1, 5.2, 5.7, 5.10; Property 9). Over the cross
# product of (eligible, subscription_status in {active, past_due, canceled,
# None}), a Checkout Session is created ONLY when the user is active-eligible
# AND holds no active/past_due subscription. On every reject path the method
# raises BEFORE any Stripe call -- asserted by patching
# stripe.checkout.Session.create and confirming it was never invoked.
# ---------------------------------------------------------------------------


class TestCheckoutGatedByEligibilityProperty:
    """Property 9 — checkout gated by active eligibility."""

    _RESOLVED_PRICE_ID = "price_sb_month"

    def _resolved_price(self):
        return _sb_row(interval="month", price_id=self._RESOLVED_PRICE_ID)

    @settings(max_examples=200)
    @given(
        eligible=st.booleans(),
        sub_status=st.sampled_from(["active", "past_due", "canceled", None]),
    )
    def test_session_created_only_when_active_eligible_and_no_active_sub(
        self, eligible, sub_status
    ):
        """Feature: student-builder-membership, Property 9: Checkout is gated by active eligibility

        For every (eligible, subscription_status) combination, a Checkout
        Session is created iff the user is active-eligible AND has no
        active/past_due subscription. On every reject path the method raises a
        StudentCheckoutError and stripe.checkout.Session.create is NEVER called
        (the gate runs before any Stripe interaction).

        Validates: Requirements 5.1, 5.2, 5.7, 5.10
        """
        svc = _make_service()

        membership = _membership()
        if sub_status is not None:
            membership["subscription_status"] = {"S": sub_status}
        membership["stripe_customer_id"] = {"S": "cus_1"}
        svc._get_membership = MagicMock(return_value=membership)
        svc.get_student_builder_product = MagicMock(
            return_value=[self._resolved_price()]
        )
        svc.select_price_for_interval = MagicMock(return_value=self._resolved_price())

        eligibility = {"expires_at": "2999-01-01T00:00:00+00:00"} if eligible else None
        session = MagicMock(url="https://checkout/student")
        vs_cls, vs_patch = _patch_verification(eligibility=eligibility)

        should_succeed = eligible and sub_status not in ("active", "past_due")

        with (
            vs_patch,
            patch.object(mod.stripe.Customer, "create"),
            patch.object(
                mod.stripe.checkout.Session, "create", return_value=session
            ) as sess_create,
        ):
            if should_succeed:
                result = svc.create_student_checkout_session(
                    "u1", self._RESOLVED_PRICE_ID, "month"
                )
                assert result == {"checkout_url": "https://checkout/student"}
                sess_create.assert_called_once()
            else:
                with pytest.raises(mod.StudentCheckoutError):
                    svc.create_student_checkout_session(
                        "u1", self._RESOLVED_PRICE_ID, "month"
                    )
                # Rejected before any Stripe call.
                sess_create.assert_not_called()


# ---------------------------------------------------------------------------
# Membership lifecycle transitions
#
# Task 16.2 (Requirements 6.1-6.6). cancel_subscription_for_switch cancels the
# Stripe subscription IMMEDIATELY (stripe.Subscription.cancel(subscription_id),
# NOT cancel_at_period_end) so subscription_status clears via the existing
# customer.subscription.deleted webhook and the duplicate-membership guard no
# longer blocks an immediate re-subscribe. With no active subscription it raises
# ValueError. STUDENT_BUILDER activation (FREE -> STUDENT_BUILDER) and
# cancellation (-> FREE) flow through the existing _activate_subscription /
# _update_subscription_state paths exactly as Builder does.
# ---------------------------------------------------------------------------


class TestCancelSubscriptionForSwitch:
    """Task 16.2 — immediate cancel-for-switch behavior."""

    def test_active_subscription_cancels_immediately(self):
        """An active subscription is canceled IMMEDIATELY via
        stripe.Subscription.cancel(subscription_id) (not cancel_at_period_end),
        and the method returns {"status": "canceled"}.

        Validates: Requirements 6.5, 6.6
        """
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(
                stripe_subscription_id={"S": "sub_1"},
                subscription_status={"S": "active"},
            )
        )
        with patch.object(mod.stripe.Subscription, "cancel") as cancel:
            result = svc.cancel_subscription_for_switch("u1")

        assert result == {"status": "canceled"}
        # Immediate cancel of the specific subscription id.
        cancel.assert_called_once_with("sub_1")

    def test_past_due_subscription_cancels_immediately(self):
        """A past_due subscription is also an active membership for the switch
        guard and is canceled immediately.

        Validates: Requirements 6.5, 6.6
        """
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(
                stripe_subscription_id={"S": "sub_pd"},
                subscription_status={"S": "past_due"},
            )
        )
        with patch.object(mod.stripe.Subscription, "cancel") as cancel:
            result = svc.cancel_subscription_for_switch("u1")

        assert result == {"status": "canceled"}
        cancel.assert_called_once_with("sub_pd")

    def test_no_active_subscription_raises_without_stripe_call(self):
        """No subscription id / non-active status -> ValueError, and Stripe is
        never called.

        Validates: Requirements 6.5, 6.6
        """
        svc = _make_service()
        svc._get_membership = MagicMock(return_value=None)
        with patch.object(mod.stripe.Subscription, "cancel") as cancel:
            with pytest.raises(ValueError, match="No active subscription"):
                svc.cancel_subscription_for_switch("u1")
        cancel.assert_not_called()

    def test_canceled_status_raises(self):
        """A membership whose subscription_status is already canceled has no
        active subscription to switch-cancel -> ValueError.

        Validates: Requirements 6.5, 6.6
        """
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(
                stripe_subscription_id={"S": "sub_1"},
                subscription_status={"S": "canceled"},
            )
        )
        with patch.object(mod.stripe.Subscription, "cancel") as cancel:
            with pytest.raises(ValueError, match="No active subscription"):
                svc.cancel_subscription_for_switch("u1")
        cancel.assert_not_called()


class TestStudentBuilderLifecycleCoverage:
    """Task 16.2 — STUDENT_BUILDER activation and cancellation flow through the
    existing membership-state paths exactly as Builder does."""

    def test_free_to_student_builder_activation_writes_tier(self):
        """A FREE -> STUDENT_BUILDER activation flows through
        _activate_subscription and persists membership_tier=STUDENT_BUILDER with
        subscription_status=active (Requirements 6.1, 6.2, 6.3).

        Validates: Requirements 6.1, 6.2, 6.3
        """
        svc = _make_service()
        svc._get_membership = MagicMock(
            return_value=_membership(membership_tier={"S": "FREE"})
        )
        progress = MagicMock()
        with (
            patch.object(mod, "ProgressDB", return_value=progress),
            patch.object(mod, "record_builder_activation"),
        ):
            svc._activate_subscription(
                "u1", "STUDENT_BUILDER", "sub_1", "active", 1700000000
            )

        kwargs = svc._dynamodb_client.update_item.call_args.kwargs
        values = kwargs["ExpressionAttributeValues"]
        assert values[":tier"] == {"S": "STUDENT_BUILDER"}
        assert values[":status"] == {"S": "active"}
        assert ":started" in values  # first-time activation records start date

    def test_student_builder_cancellation_downgrades_to_free(self):
        """A STUDENT_BUILDER cancellation flows through
        _update_subscription_state, writing membership_tier=FREE and
        subscription_status=canceled -- identical to the Builder downgrade path
        (Requirements 6.4, 6.5, 6.6).

        Validates: Requirements 6.4, 6.5, 6.6
        """
        svc = _make_service()
        svc._update_subscription_state("u1", "FREE", "sub_1", "canceled")

        kwargs = svc._dynamodb_client.update_item.call_args.kwargs
        values = kwargs["ExpressionAttributeValues"]
        assert values[":tier"] == {"S": "FREE"}
        assert values[":status"] == {"S": "canceled"}
