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
