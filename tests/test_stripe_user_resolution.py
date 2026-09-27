"""Tests for StripeService webhook user resolution.

Covers StripeService._resolve_user_id, which maps a Stripe webhook event to a
DSB user_id using, in order:
  1. dsb_user_id on the event object's metadata (checkout sessions),
  2. the event's ``customer`` id matched against the stored stripe_customer_id
     on a membership record.

The customer-id lookup is the fix for invoice.payment_failed events, whose
payload carries no dsb_user_id metadata but does include the ``customer`` id.
The invoice ``customer_email`` is intentionally not used, since the payment
email can differ from the user's DSB account email.
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
    return s


def _make_stripe_service():
    """Build a StripeService with boto3 mocked so no AWS calls happen."""
    with patch("boto3.client"):
        import app.services.stripe_service as stripe_service_mod

        svc = stripe_service_mod.StripeService(_make_settings())
    svc._dynamodb_client = MagicMock()
    return svc


class TestResolveUserId:
    def test_prefers_event_object_metadata(self):
        svc = _make_stripe_service()
        svc._resolve_user_from_customer = MagicMock()
        result = svc._resolve_user_id(
            {"metadata": {"dsb_user_id": "u_meta"}}, "cus_123"
        )
        assert result == "u_meta"
        # Metadata wins; no DB lookup needed.
        svc._resolve_user_from_customer.assert_not_called()

    def test_resolves_from_customer_id(self):
        """invoice.payment_failed: no dsb_user_id metadata, resolve by the
        customer id on the payload."""
        svc = _make_stripe_service()
        svc._resolve_user_from_customer = MagicMock(return_value="u_cust")
        result = svc._resolve_user_id(
            {"customer_email": "pay-email@example.com"}, "cus_V8gaoF1FHoQc5b"
        )
        assert result == "u_cust"
        svc._resolve_user_from_customer.assert_called_once_with("cus_V8gaoF1FHoQc5b")

    def test_ignores_customer_email(self):
        """The payment email must not be used for resolution."""
        svc = _make_stripe_service()
        svc._resolve_user_from_customer = MagicMock(return_value=None)
        result = svc._resolve_user_id(
            {"customer_email": "pay-email@example.com"}, "cus_123"
        )
        assert result is None
        # Only the customer id was consulted.
        svc._resolve_user_from_customer.assert_called_once_with("cus_123")

    def test_returns_none_without_customer(self):
        svc = _make_stripe_service()
        result = svc._resolve_user_id({}, None)
        assert result is None


class TestResolveUserFromCustomer:
    def test_matches_membership_row(self):
        svc = _make_stripe_service()
        svc._dynamodb_client.scan.return_value = {"Items": [{"PK": {"S": "USER#u1"}}]}
        result = svc._resolve_user_from_customer("cus_V8gaoF1FHoQc5b")
        assert result == "u1"
        # Scan filters on the stored customer id + MEMBERSHIP row.
        _, kwargs = svc._dynamodb_client.scan.call_args
        assert kwargs["ExpressionAttributeValues"][":cid"] == {
            "S": "cus_V8gaoF1FHoQc5b"
        }

    def test_returns_none_when_no_match(self):
        svc = _make_stripe_service()
        svc._dynamodb_client.scan.return_value = {"Items": []}
        result = svc._resolve_user_from_customer("cus_missing")
        assert result is None
