"""Unit tests for Stripe webhook processing (Task 14).

Tests handle_webhook(), all 4 event type handlers, signature verification,
idempotency, and the route handler.

Validates: Requirements 2.1–2.11, 18.9, 19.10
"""

import json
import os
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, call

import pytest

# Set required env vars before importing
os.environ.setdefault("MEMBERSHIP_TABLE", "test-membership-table")
os.environ.setdefault("STRIPE_SECRET_NAME", "test-stripe-secret")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET_NAME", "test-stripe-webhook-secret")
os.environ.setdefault("FRONTEND_URL", "https://test.devsecblueprint.com")
os.environ.setdefault("JWT_SECRET_NAME", "test-jwt-secret")
os.environ.setdefault(
    "DISCORD_SYNC_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/test/queue.fifo"
)

import backend.membership.services.stripe_service as stripe_service
from backend.membership.services.stripe_service import (
    handle_webhook,
    handle_stripe_webhook,
    _extract_user_id,
    _extract_tier_from_subscription,
    _timestamp_to_iso,
)

# ---------------------------------------------------------------------------
# Fixtures and Helpers
# ---------------------------------------------------------------------------


def _build_stripe_event(
    event_type: str, event_id: str = "evt_test123", data_object: dict = None
):
    """Build a mock Stripe event dict."""
    return {
        "id": event_id,
        "type": event_type,
        "data": {"object": data_object or {}},
    }


def _checkout_completed_event(
    customer_id="cus_123", subscription_id="sub_456", mode="subscription"
):
    """Build a checkout.session.completed event."""
    return _build_stripe_event(
        "checkout.session.completed",
        data_object={
            "mode": mode,
            "customer": customer_id,
            "subscription": subscription_id,
        },
    )


def _subscription_updated_event(
    customer_id="cus_123", subscription_id="sub_456", status="active"
):
    """Build a customer.subscription.updated event."""
    return _build_stripe_event(
        "customer.subscription.updated",
        data_object={
            "id": subscription_id,
            "customer": customer_id,
            "status": status,
            "current_period_end": 1700000000,
            "items": {"data": [{"price": {"product": "prod_abc"}}]},
        },
    )


def _subscription_deleted_event(customer_id="cus_123", subscription_id="sub_456"):
    """Build a customer.subscription.deleted event."""
    return _build_stripe_event(
        "customer.subscription.deleted",
        data_object={
            "id": subscription_id,
            "customer": customer_id,
        },
    )


def _payment_failed_event(customer_id="cus_123", subscription_id="sub_456"):
    """Build an invoice.payment_failed event."""
    return _build_stripe_event(
        "invoice.payment_failed",
        data_object={
            "customer": customer_id,
            "subscription": subscription_id,
        },
    )


def _user_dynamo_item(user_id="user-abc"):
    """Build a DynamoDB item representing a user resolved via GSI2."""
    return {
        "PK": {"S": f"USER#{user_id}"},
        "SK": {"S": "MEMBERSHIP"},
        "user_id": {"S": user_id},
        "membership_tier": {"S": "FREE"},
        "stripe_customer_id": {"S": "cus_123"},
    }


# ---------------------------------------------------------------------------
# Tests: Signature Verification
# ---------------------------------------------------------------------------


class TestWebhookSignatureVerification:
    """Test that webhook signature is verified correctly."""

    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_valid_signature_processes_event(self, mock_secret, mock_stripe, mock_db):
        """Valid signature allows event processing."""
        mock_secret.return_value = {"secret_key": "whsec_test123"}
        mock_stripe.Webhook.construct_event.return_value = _build_stripe_event(
            "checkout.session.completed",
            data_object={"mode": "payment", "customer": "cus_x"},
        )
        mock_db.check_stripe_event_processed.return_value = False

        result = handle_webhook('{"test": true}', "t=123,v1=abc")

        assert result["processed"] is True
        mock_stripe.Webhook.construct_event.assert_called_once_with(
            '{"test": true}', "t=123,v1=abc", "whsec_test123"
        )

    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_invalid_signature_raises_valueerror(self, mock_secret, mock_stripe):
        """Invalid signature raises ValueError for caller to return 400."""
        mock_secret.return_value = {"secret_key": "whsec_test123"}
        mock_stripe.Webhook.construct_event.side_effect = (
            stripe_service.stripe.error.SignatureVerificationError("bad sig", "header")
        )

        with pytest.raises(ValueError, match="Invalid webhook signature"):
            handle_webhook('{"test": true}', "t=123,v1=bad")


# ---------------------------------------------------------------------------
# Tests: Idempotency
# ---------------------------------------------------------------------------


class TestWebhookIdempotency:
    """Test that duplicate events are skipped."""

    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_duplicate_event_skipped(self, mock_secret, mock_stripe, mock_db):
        """Already-processed event is skipped with reason=duplicate."""
        mock_secret.return_value = {"secret_key": "whsec_test"}
        mock_stripe.Webhook.construct_event.return_value = _build_stripe_event(
            "checkout.session.completed", event_id="evt_duplicate"
        )
        mock_db.check_stripe_event_processed.return_value = True

        result = handle_webhook("{}", "sig")

        assert result["processed"] is False
        assert result["reason"] == "duplicate"
        assert result["event_id"] == "evt_duplicate"
        # Should NOT mark event processed again
        mock_db.mark_stripe_event_processed.assert_not_called()

    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_new_event_marked_processed(self, mock_secret, mock_stripe, mock_db):
        """New event is marked as processed after handling."""
        mock_secret.return_value = {"secret_key": "whsec_test"}
        mock_stripe.Webhook.construct_event.return_value = _build_stripe_event(
            "some.unhandled.event", event_id="evt_new123"
        )
        mock_db.check_stripe_event_processed.return_value = False

        result = handle_webhook("{}", "sig")

        assert result["processed"] is True
        assert result["event_id"] == "evt_new123"
        mock_db.mark_stripe_event_processed.assert_called_once_with("evt_new123")


# ---------------------------------------------------------------------------
# Tests: checkout.session.completed
# ---------------------------------------------------------------------------


class TestCheckoutCompleted:
    """Test _handle_checkout_completed processing."""

    @patch("backend.membership.services.stripe_service.publish_sync_event")
    @patch("backend.membership.services.stripe_service.write_audit_log")
    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_new_subscription_updates_tier(
        self, mock_secret, mock_stripe, mock_db, mock_audit, mock_sync
    ):
        """checkout.session.completed with subscription mode updates membership tier."""
        mock_secret.return_value = {"secret_key": "whsec_test"}

        event = _checkout_completed_event()
        mock_stripe.Webhook.construct_event.return_value = event
        mock_db.check_stripe_event_processed.return_value = False
        mock_db.resolve_stripe_customer.return_value = _user_dynamo_item("user-abc")

        # Mock subscription retrieval
        mock_subscription = {
            "status": "active",
            "current_period_end": 1700000000,
            "items": {
                "data": [{"price": {"product": {"metadata": {"dsb_tier": "BUILDER"}}}}]
            },
        }
        mock_stripe.Subscription.retrieve.return_value = mock_subscription

        result = handle_webhook("{}", "sig")

        assert result["processed"] is True
        # Verify membership was updated
        mock_db.put_membership.assert_called_once()
        put_arg = mock_db.put_membership.call_args[0][0]
        assert put_arg["membership_tier"] == {"S": "BUILDER"}
        assert put_arg["user_id"] == {"S": "user-abc"}
        assert put_arg["stripe_subscription_id"] == {"S": "sub_456"}
        assert put_arg["subscription_status"] == {"S": "active"}

    @patch("backend.membership.services.stripe_service.publish_sync_event")
    @patch("backend.membership.services.stripe_service.write_audit_log")
    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_publishes_sync_event(
        self, mock_secret, mock_stripe, mock_db, mock_audit, mock_sync
    ):
        """checkout.session.completed publishes sync event for Discord role sync."""
        mock_secret.return_value = {"secret_key": "whsec_test"}

        event = _checkout_completed_event()
        mock_stripe.Webhook.construct_event.return_value = event
        mock_db.check_stripe_event_processed.return_value = False
        mock_db.resolve_stripe_customer.return_value = _user_dynamo_item("user-abc")
        mock_stripe.Subscription.retrieve.return_value = {
            "status": "active",
            "current_period_end": 1700000000,
            "items": {
                "data": [{"price": {"product": {"metadata": {"dsb_tier": "EXPLORER"}}}}]
            },
        }

        handle_webhook("{}", "sig")

        mock_sync.assert_called_once_with("user-abc", "tier_change", "EXPLORER")

    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_non_subscription_mode_ignored(self, mock_secret, mock_stripe, mock_db):
        """checkout.session.completed with mode != subscription is ignored."""
        mock_secret.return_value = {"secret_key": "whsec_test"}

        event = _checkout_completed_event(mode="payment")
        mock_stripe.Webhook.construct_event.return_value = event
        mock_db.check_stripe_event_processed.return_value = False

        result = handle_webhook("{}", "sig")

        assert result["processed"] is True
        mock_db.resolve_stripe_customer.assert_not_called()

    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_unresolved_customer_logs_error(self, mock_secret, mock_stripe, mock_db):
        """checkout.session.completed with unknown customer logs error gracefully."""
        mock_secret.return_value = {"secret_key": "whsec_test"}

        event = _checkout_completed_event(customer_id="cus_unknown")
        mock_stripe.Webhook.construct_event.return_value = event
        mock_db.check_stripe_event_processed.return_value = False
        mock_db.resolve_stripe_customer.return_value = None

        result = handle_webhook("{}", "sig")

        # Should still process without crash and mark as processed
        assert result["processed"] is True
        mock_db.put_membership.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: customer.subscription.updated
# ---------------------------------------------------------------------------


class TestSubscriptionUpdated:
    """Test _handle_subscription_updated processing."""

    @patch("backend.membership.services.stripe_service.publish_sync_event")
    @patch("backend.membership.services.stripe_service.write_audit_log")
    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_tier_change_publishes_sync(
        self, mock_secret, mock_stripe, mock_db, mock_audit, mock_sync
    ):
        """Tier change triggers SQS sync event."""
        mock_secret.return_value = {"secret_key": "whsec_test"}

        event = _subscription_updated_event()
        mock_stripe.Webhook.construct_event.return_value = event
        mock_db.check_stripe_event_processed.return_value = False
        mock_db.resolve_stripe_customer.return_value = _user_dynamo_item("user-abc")
        mock_db.get_membership.return_value = {
            "membership_tier": {"S": "FREE"},
        }

        # Product returns new tier
        mock_product = MagicMock()
        mock_product.get.side_effect = lambda key, default=None: (
            {"dsb_tier": "BUILDER"} if key == "metadata" else default
        )
        mock_stripe.Product.retrieve.return_value = mock_product

        handle_webhook("{}", "sig")

        mock_sync.assert_called_once_with("user-abc", "tier_change", "BUILDER")

    @patch("backend.membership.services.stripe_service.publish_sync_event")
    @patch("backend.membership.services.stripe_service.write_audit_log")
    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_same_tier_no_sync(
        self, mock_secret, mock_stripe, mock_db, mock_audit, mock_sync
    ):
        """No tier change skips SQS sync event."""
        mock_secret.return_value = {"secret_key": "whsec_test"}

        event = _subscription_updated_event()
        mock_stripe.Webhook.construct_event.return_value = event
        mock_db.check_stripe_event_processed.return_value = False
        mock_db.resolve_stripe_customer.return_value = _user_dynamo_item("user-abc")
        mock_db.get_membership.return_value = {
            "membership_tier": {"S": "BUILDER"},
        }

        # Product returns same tier as current
        mock_product = MagicMock()
        mock_product.get.side_effect = lambda key, default=None: (
            {"dsb_tier": "BUILDER"} if key == "metadata" else default
        )
        mock_stripe.Product.retrieve.return_value = mock_product

        handle_webhook("{}", "sig")

        mock_sync.assert_not_called()

    @patch("backend.membership.services.stripe_service.publish_sync_event")
    @patch("backend.membership.services.stripe_service.write_audit_log")
    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_updates_subscription_status_and_period_end(
        self, mock_secret, mock_stripe, mock_db, mock_audit, mock_sync
    ):
        """subscription.updated updates status and current_period_end."""
        mock_secret.return_value = {"secret_key": "whsec_test"}

        event = _subscription_updated_event(status="past_due")
        mock_stripe.Webhook.construct_event.return_value = event
        mock_db.check_stripe_event_processed.return_value = False
        mock_db.resolve_stripe_customer.return_value = _user_dynamo_item("user-abc")
        mock_db.get_membership.return_value = {
            "membership_tier": {"S": "BUILDER"},
        }

        mock_product = MagicMock()
        mock_product.get.side_effect = lambda key, default=None: (
            {"dsb_tier": "BUILDER"} if key == "metadata" else default
        )
        mock_stripe.Product.retrieve.return_value = mock_product

        handle_webhook("{}", "sig")

        put_arg = mock_db.put_membership.call_args[0][0]
        assert put_arg["subscription_status"] == {"S": "past_due"}
        assert "current_period_end" in put_arg


# ---------------------------------------------------------------------------
# Tests: customer.subscription.deleted
# ---------------------------------------------------------------------------


class TestSubscriptionDeleted:
    """Test _handle_subscription_deleted processing."""

    @patch("backend.membership.services.stripe_service.publish_sync_event")
    @patch("backend.membership.services.stripe_service.write_audit_log")
    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_downgrades_to_free(
        self, mock_secret, mock_stripe, mock_db, mock_audit, mock_sync
    ):
        """subscription.deleted downgrades user to FREE."""
        mock_secret.return_value = {"secret_key": "whsec_test"}

        event = _subscription_deleted_event()
        mock_stripe.Webhook.construct_event.return_value = event
        mock_db.check_stripe_event_processed.return_value = False
        mock_db.resolve_stripe_customer.return_value = _user_dynamo_item("user-abc")
        mock_db.get_membership.return_value = {
            "membership_tier": {"S": "BUILDER"},
        }

        handle_webhook("{}", "sig")

        put_arg = mock_db.put_membership.call_args[0][0]
        assert put_arg["membership_tier"] == {"S": "FREE"}
        # subscription fields should NOT be present (cleared)
        assert "stripe_subscription_id" not in put_arg
        assert "subscription_status" not in put_arg
        assert "current_period_end" not in put_arg

    @patch("backend.membership.services.stripe_service.publish_sync_event")
    @patch("backend.membership.services.stripe_service.write_audit_log")
    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_publishes_free_sync_event(
        self, mock_secret, mock_stripe, mock_db, mock_audit, mock_sync
    ):
        """subscription.deleted publishes sync event with FREE tier."""
        mock_secret.return_value = {"secret_key": "whsec_test"}

        event = _subscription_deleted_event()
        mock_stripe.Webhook.construct_event.return_value = event
        mock_db.check_stripe_event_processed.return_value = False
        mock_db.resolve_stripe_customer.return_value = _user_dynamo_item("user-abc")
        mock_db.get_membership.return_value = {
            "membership_tier": {"S": "EXPLORER"},
        }

        handle_webhook("{}", "sig")

        mock_sync.assert_called_once_with("user-abc", "tier_change", "FREE")

    @patch("backend.membership.services.stripe_service.publish_sync_event")
    @patch("backend.membership.services.stripe_service.write_audit_log")
    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_writes_subscription_ended_audit(
        self, mock_secret, mock_stripe, mock_db, mock_audit, mock_sync
    ):
        """subscription.deleted writes Subscription_Ended audit entry with state change."""
        mock_secret.return_value = {"secret_key": "whsec_test"}

        event = _subscription_deleted_event()
        mock_stripe.Webhook.construct_event.return_value = event
        mock_db.check_stripe_event_processed.return_value = False
        mock_db.resolve_stripe_customer.return_value = _user_dynamo_item("user-abc")
        mock_db.get_membership.return_value = {
            "membership_tier": {"S": "BUILDER"},
        }

        handle_webhook("{}", "sig")

        mock_audit.assert_called_once()
        audit_event = mock_audit.call_args[0][0]
        assert audit_event.event_type.value == "Subscription_Ended"
        assert audit_event.dsb_user_id == "user-abc"
        assert audit_event.previous_state == "BUILDER"
        assert audit_event.new_state == "FREE"
        assert audit_event.stripe_event_id == "evt_test123"


# ---------------------------------------------------------------------------
# Tests: invoice.payment_failed
# ---------------------------------------------------------------------------


class TestPaymentFailed:
    """Test _handle_payment_failed processing."""

    @patch("backend.membership.services.stripe_service.write_audit_log")
    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_writes_audit_only(self, mock_secret, mock_stripe, mock_db, mock_audit):
        """payment_failed writes audit log only, no membership change."""
        mock_secret.return_value = {"secret_key": "whsec_test"}

        event = _payment_failed_event()
        mock_stripe.Webhook.construct_event.return_value = event
        mock_db.check_stripe_event_processed.return_value = False
        mock_db.resolve_stripe_customer.return_value = _user_dynamo_item("user-abc")

        handle_webhook("{}", "sig")

        mock_audit.assert_called_once()
        audit_event = mock_audit.call_args[0][0]
        assert audit_event.event_type.value == "Payment_Failed"
        # No membership change
        mock_db.put_membership.assert_not_called()

    @patch("backend.membership.services.stripe_service.write_audit_log")
    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.get_secret")
    def test_no_sync_event_published(
        self, mock_secret, mock_stripe, mock_db, mock_audit
    ):
        """payment_failed does NOT publish a sync event."""
        mock_secret.return_value = {"secret_key": "whsec_test"}

        event = _payment_failed_event()
        mock_stripe.Webhook.construct_event.return_value = event
        mock_db.check_stripe_event_processed.return_value = False
        mock_db.resolve_stripe_customer.return_value = _user_dynamo_item("user-abc")

        with patch(
            "backend.membership.services.stripe_service.publish_sync_event"
        ) as mock_sync:
            handle_webhook("{}", "sig")
            mock_sync.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: Route Handler (handle_stripe_webhook)
# ---------------------------------------------------------------------------


class TestHandleStripeWebhookRoute:
    """Test the Lambda route handler for POST /api/stripe/webhook."""

    @patch("backend.membership.services.stripe_service.handle_webhook")
    def test_returns_200_on_success(self, mock_handle):
        """Successful webhook processing returns 200."""
        mock_handle.return_value = {"processed": True, "event_id": "evt_abc"}

        event = {
            "headers": {"stripe-signature": "t=123,v1=abc"},
            "body": '{"test": true}',
        }

        result = handle_stripe_webhook(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["processed"] is True
        assert body["event_id"] == "evt_abc"

    @patch("backend.membership.services.stripe_service.handle_webhook")
    def test_returns_400_on_signature_failure(self, mock_handle):
        """Invalid signature returns 400."""
        mock_handle.side_effect = ValueError("Invalid webhook signature")

        event = {
            "headers": {"stripe-signature": "t=123,v1=bad"},
            "body": '{"test": true}',
        }

        result = handle_stripe_webhook(event)

        assert result["statusCode"] == 400

    def test_returns_400_when_missing_signature_header(self):
        """Missing Stripe-Signature header returns 400."""
        event = {
            "headers": {},
            "body": '{"test": true}',
        }

        result = handle_stripe_webhook(event)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Stripe-Signature" in body["error"]

    @patch("backend.membership.services.stripe_service.handle_webhook")
    def test_returns_200_on_processing_error(self, mock_handle):
        """Processing error returns 200 (avoid Stripe retries for non-transient errors)."""
        mock_handle.side_effect = Exception("DB unavailable")

        event = {
            "headers": {"stripe-signature": "t=123,v1=abc"},
            "body": '{"test": true}',
        }

        result = handle_stripe_webhook(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["processed"] is False


# ---------------------------------------------------------------------------
# Tests: Utility Helpers
# ---------------------------------------------------------------------------


class TestExtractUserId:
    """Test _extract_user_id helper."""

    def test_extracts_from_user_id_attribute(self):
        item = {"user_id": {"S": "user-direct"}, "PK": {"S": "USER#user-pk"}}
        assert _extract_user_id(item) == "user-direct"

    def test_falls_back_to_pk(self):
        item = {"PK": {"S": "USER#user-from-pk"}}
        assert _extract_user_id(item) == "user-from-pk"

    def test_returns_none_for_missing_data(self):
        assert _extract_user_id({}) is None
        assert _extract_user_id({"PK": {"S": "OTHER#something"}}) is None


class TestExtractTierFromSubscription:
    """Test _extract_tier_from_subscription helper."""

    def test_extracts_from_expanded_product(self):
        subscription = {
            "items": {
                "data": [
                    {
                        "price": {
                            "product": {"metadata": {"dsb_tier": "BUILDER_ACADEMY"}}
                        }
                    }
                ]
            }
        }
        assert _extract_tier_from_subscription(subscription) == "BUILDER_ACADEMY"

    def test_defaults_to_free_when_no_metadata(self):
        subscription = {"items": {"data": [{"price": {"product": {"metadata": {}}}}]}}
        assert _extract_tier_from_subscription(subscription) == "FREE"

    def test_defaults_to_free_when_no_items(self):
        subscription = {"items": {"data": []}}
        assert _extract_tier_from_subscription(subscription) == "FREE"


class TestTimestampToIso:
    """Test _timestamp_to_iso helper."""

    def test_converts_timestamp(self):
        result = _timestamp_to_iso(1700000000)
        assert result is not None
        assert "2023" in result

    def test_none_returns_none(self):
        assert _timestamp_to_iso(None) is None
