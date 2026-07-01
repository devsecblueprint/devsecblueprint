"""Unit tests for the Stripe checkout session creation (Task 13).

Tests the create_checkout_session function in stripe_service.py
and the handle_stripe_checkout handler.

Validates: Requirements 1.4–1.7, 1.12, 18.10
"""

import json
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

import pytest

# Set required env vars before importing the module
os.environ.setdefault("MEMBERSHIP_TABLE", "test-membership-table")
os.environ.setdefault("STRIPE_SECRET_NAME", "test-stripe-secret")
os.environ.setdefault("FRONTEND_URL", "https://test.devsecblueprint.com")
os.environ.setdefault("JWT_SECRET_NAME", "test-jwt-secret")

from services.stripe_service import create_checkout_session
from handlers.stripe_handlers import handle_stripe_checkout


class TestCreateCheckoutSession:
    """Tests for create_checkout_session service function."""

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.membership_db")
    @patch("services.stripe_service._get_stripe_key")
    def test_creates_session_for_new_user_no_membership(
        self, mock_key, mock_db, mock_stripe
    ):
        """User with no membership record: creates customer and session."""
        mock_key.return_value = "sk_test_123"
        mock_db.get_membership.return_value = None

        mock_customer = MagicMock()
        mock_customer.id = "cus_new123"
        mock_stripe.Customer.create.return_value = mock_customer

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session_abc"
        mock_stripe.checkout.Session.create.return_value = mock_session

        result = create_checkout_session("user-1", "price_abc123")

        assert result == {"checkout_url": "https://checkout.stripe.com/session_abc"}
        mock_stripe.Customer.create.assert_called_once_with(
            metadata={"dsb_user_id": "user-1"}
        )
        mock_db.put_membership.assert_called_once()
        mock_stripe.checkout.Session.create.assert_called_once()

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.membership_db")
    @patch("services.stripe_service._get_stripe_key")
    def test_creates_session_with_existing_customer(
        self, mock_key, mock_db, mock_stripe
    ):
        """User with existing stripe_customer_id: uses it directly."""
        mock_key.return_value = "sk_test_123"
        mock_db.get_membership.return_value = {
            "PK": {"S": "USER#user-2"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": "user-2"},
            "membership_tier": {"S": "FREE"},
            "stripe_customer_id": {"S": "cus_existing456"},
        }

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session_def"
        mock_stripe.checkout.Session.create.return_value = mock_session

        result = create_checkout_session("user-2", "price_xyz789")

        assert result == {"checkout_url": "https://checkout.stripe.com/session_def"}
        # Should NOT create a new customer
        mock_stripe.Customer.create.assert_not_called()
        mock_db.put_membership.assert_not_called()

        # Verify session was created with correct params
        session_call = mock_stripe.checkout.Session.create.call_args
        assert session_call[1]["customer"] == "cus_existing456"
        assert session_call[1]["mode"] == "subscription"
        assert session_call[1]["line_items"] == [
            {"price": "price_xyz789", "quantity": 1}
        ]

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.membership_db")
    @patch("services.stripe_service._get_stripe_key")
    def test_rejects_active_subscription(self, mock_key, mock_db, mock_stripe):
        """User with active subscription: raises ValueError."""
        mock_key.return_value = "sk_test_123"
        mock_db.get_membership.return_value = {
            "PK": {"S": "USER#user-3"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": "user-3"},
            "membership_tier": {"S": "BUILDER"},
            "stripe_customer_id": {"S": "cus_active789"},
            "subscription_status": {"S": "active"},
        }

        with pytest.raises(ValueError, match="already has an active subscription"):
            create_checkout_session("user-3", "price_abc123")

        mock_stripe.checkout.Session.create.assert_not_called()

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.membership_db")
    @patch("services.stripe_service._get_stripe_key")
    def test_rejects_past_due_subscription(self, mock_key, mock_db, mock_stripe):
        """User with past_due subscription: also rejected."""
        mock_key.return_value = "sk_test_123"
        mock_db.get_membership.return_value = {
            "PK": {"S": "USER#user-4"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": "user-4"},
            "membership_tier": {"S": "EXPLORER"},
            "stripe_customer_id": {"S": "cus_pastdue"},
            "subscription_status": {"S": "past_due"},
        }

        with pytest.raises(ValueError, match="already has an active subscription"):
            create_checkout_session("user-4", "price_abc123")

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.membership_db")
    @patch("services.stripe_service._get_stripe_key")
    def test_allows_canceled_subscription(self, mock_key, mock_db, mock_stripe):
        """User with canceled subscription: allowed to create new checkout."""
        mock_key.return_value = "sk_test_123"
        mock_db.get_membership.return_value = {
            "PK": {"S": "USER#user-5"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": "user-5"},
            "membership_tier": {"S": "FREE"},
            "stripe_customer_id": {"S": "cus_canceled"},
            "subscription_status": {"S": "canceled"},
        }

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session_ghi"
        mock_stripe.checkout.Session.create.return_value = mock_session

        result = create_checkout_session("user-5", "price_abc123")
        assert result == {"checkout_url": "https://checkout.stripe.com/session_ghi"}

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.membership_db")
    @patch("services.stripe_service._get_stripe_key")
    def test_stores_customer_id_on_new_creation(self, mock_key, mock_db, mock_stripe):
        """When creating a new customer, stores customer_id on membership record."""
        mock_key.return_value = "sk_test_123"
        mock_db.get_membership.return_value = None

        mock_customer = MagicMock()
        mock_customer.id = "cus_brand_new"
        mock_stripe.Customer.create.return_value = mock_customer

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session_jkl"
        mock_stripe.checkout.Session.create.return_value = mock_session

        create_checkout_session("user-6", "price_abc123")

        # Verify put_membership was called with the stripe_customer_id
        put_call = mock_db.put_membership.call_args[0][0]
        assert put_call["stripe_customer_id"] == {"S": "cus_brand_new"}
        assert put_call["user_id"] == {"S": "user-6"}
        assert put_call["PK"] == {"S": "USER#user-6"}
        assert put_call["SK"] == {"S": "MEMBERSHIP"}

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.membership_db")
    @patch("services.stripe_service._get_stripe_key")
    def test_preserves_existing_tier_on_customer_creation(
        self, mock_key, mock_db, mock_stripe
    ):
        """When membership exists but no customer, preserves existing tier."""
        mock_key.return_value = "sk_test_123"
        mock_db.get_membership.return_value = {
            "PK": {"S": "USER#user-7"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": "user-7"},
            "membership_tier": {"S": "FREE"},
            # No stripe_customer_id
        }

        mock_customer = MagicMock()
        mock_customer.id = "cus_for_free_user"
        mock_stripe.Customer.create.return_value = mock_customer

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session_mno"
        mock_stripe.checkout.Session.create.return_value = mock_session

        create_checkout_session("user-7", "price_abc123")

        put_call = mock_db.put_membership.call_args[0][0]
        assert put_call["membership_tier"] == {"S": "FREE"}

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.membership_db")
    @patch("services.stripe_service._get_stripe_key")
    def test_checkout_session_urls_use_frontend_url(
        self, mock_key, mock_db, mock_stripe
    ):
        """Success and cancel URLs use the configured FRONTEND_URL."""
        mock_key.return_value = "sk_test_123"
        mock_db.get_membership.return_value = {
            "PK": {"S": "USER#user-8"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": "user-8"},
            "membership_tier": {"S": "FREE"},
            "stripe_customer_id": {"S": "cus_url_test"},
        }

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session_pqr"
        mock_stripe.checkout.Session.create.return_value = mock_session

        create_checkout_session("user-8", "price_abc123")

        session_call = mock_stripe.checkout.Session.create.call_args[1]
        assert (
            "test.devsecblueprint.com/checkout/success" in session_call["success_url"]
        )
        assert "{CHECKOUT_SESSION_ID}" in session_call["success_url"]
        assert "test.devsecblueprint.com/pricing" in session_call["cancel_url"]

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.membership_db")
    @patch("services.stripe_service._get_stripe_key")
    def test_metadata_includes_user_id(self, mock_key, mock_db, mock_stripe):
        """Checkout session metadata includes dsb_user_id for traceability."""
        mock_key.return_value = "sk_test_123"
        mock_db.get_membership.return_value = {
            "PK": {"S": "USER#user-9"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": "user-9"},
            "membership_tier": {"S": "FREE"},
            "stripe_customer_id": {"S": "cus_meta_test"},
        }

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session_stu"
        mock_stripe.checkout.Session.create.return_value = mock_session

        create_checkout_session("user-9", "price_abc123")

        session_call = mock_stripe.checkout.Session.create.call_args[1]
        assert session_call["metadata"] == {"dsb_user_id": "user-9"}


class TestHandleStripeCheckout:
    """Tests for the handle_stripe_checkout handler function."""

    def _make_event(self, body=None, authenticated=True):
        """Helper to build an API Gateway event."""
        event = {
            "headers": {},
            "body": json.dumps(body) if body else "",
        }
        if authenticated:
            event["headers"]["authorization"] = "Bearer valid-token"
        return event

    @patch("handlers.stripe_handlers.create_checkout_session")
    @patch("handlers.stripe_handlers.require_auth")
    def test_returns_checkout_url_on_success(self, mock_auth, mock_create):
        mock_auth.return_value = ({"sub": "user-1", "is_admin": False}, None)
        mock_create.return_value = {"checkout_url": "https://checkout.stripe.com/abc"}

        event = self._make_event(body={"price_id": "price_test123"})
        result = handle_stripe_checkout(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["checkout_url"] == "https://checkout.stripe.com/abc"

    @patch("handlers.stripe_handlers.require_auth")
    def test_returns_401_when_unauthenticated(self, mock_auth):
        mock_auth.return_value = (
            None,
            {
                "statusCode": 401,
                "body": '{"error":"Authentication required"}',
                "headers": {},
            },
        )

        event = self._make_event(authenticated=False)
        result = handle_stripe_checkout(event)

        assert result["statusCode"] == 401

    @patch("handlers.stripe_handlers.require_auth")
    def test_returns_400_when_no_body(self, mock_auth):
        mock_auth.return_value = ({"sub": "user-1", "is_admin": False}, None)

        event = {"headers": {"authorization": "Bearer token"}, "body": ""}
        result = handle_stripe_checkout(event)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "body" in body["error"].lower() or "required" in body["error"].lower()

    @patch("handlers.stripe_handlers.require_auth")
    def test_returns_400_when_invalid_json(self, mock_auth):
        mock_auth.return_value = ({"sub": "user-1", "is_admin": False}, None)

        event = {"headers": {"authorization": "Bearer token"}, "body": "not json"}
        result = handle_stripe_checkout(event)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "json" in body["error"].lower() or "invalid" in body["error"].lower()

    @patch("handlers.stripe_handlers.require_auth")
    def test_returns_400_when_missing_price_id(self, mock_auth):
        mock_auth.return_value = ({"sub": "user-1", "is_admin": False}, None)

        event = self._make_event(body={"something_else": "value"})
        result = handle_stripe_checkout(event)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "price_id" in body["error"]

    @patch("handlers.stripe_handlers.require_auth")
    def test_returns_400_when_invalid_price_id_format(self, mock_auth):
        mock_auth.return_value = ({"sub": "user-1", "is_admin": False}, None)

        event = self._make_event(body={"price_id": "not_a_valid_price"})
        result = handle_stripe_checkout(event)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "price_id" in body["error"].lower() or "format" in body["error"].lower()

    @patch("handlers.stripe_handlers.create_checkout_session")
    @patch("handlers.stripe_handlers.require_auth")
    def test_returns_400_when_user_has_active_subscription(
        self, mock_auth, mock_create
    ):
        mock_auth.return_value = ({"sub": "user-1", "is_admin": False}, None)
        mock_create.side_effect = ValueError("User already has an active subscription")

        event = self._make_event(body={"price_id": "price_test123"})
        result = handle_stripe_checkout(event)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "active subscription" in body["error"]

    @patch("handlers.stripe_handlers.create_checkout_session")
    @patch("handlers.stripe_handlers.require_auth")
    def test_returns_500_on_stripe_failure(self, mock_auth, mock_create):
        mock_auth.return_value = ({"sub": "user-1", "is_admin": False}, None)
        mock_create.side_effect = Exception("Stripe API error")

        event = self._make_event(body={"price_id": "price_test123"})
        result = handle_stripe_checkout(event)

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "failed" in body["error"].lower() or "checkout" in body["error"].lower()
