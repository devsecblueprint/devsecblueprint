"""Unit tests for the Stripe Customer Portal session (Task 16).

Tests the create_portal_session function in stripe_service.py
and the handle_stripe_portal handler in stripe_handlers.py.

Validates: Requirements 3.2, 3.3, 3.4, 3.7
"""

import json
import os
from unittest.mock import patch, MagicMock

import pytest

os.environ.setdefault("MEMBERSHIP_TABLE", "test-membership-table")
os.environ.setdefault("STRIPE_SECRET_NAME", "test-stripe-secret")
os.environ.setdefault("FRONTEND_URL", "https://test.devsecblueprint.com")
os.environ.setdefault("JWT_SECRET_NAME", "test-jwt-secret")

from backend.membership.services.stripe_service import create_portal_session
from backend.membership.handlers.stripe_handlers import handle_stripe_portal


class TestCreatePortalSession:
    """Tests for create_portal_session service function."""

    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service._get_stripe_key")
    def test_creates_portal_session_successfully(self, mock_key, mock_db, mock_stripe):
        """User with stripe_customer_id gets a portal URL."""
        mock_key.return_value = "sk_test_123"
        mock_db.get_membership.return_value = {
            "PK": {"S": "USER#user-1"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": "user-1"},
            "membership_tier": {"S": "BUILDER"},
            "stripe_customer_id": {"S": "cus_abc123"},
            "subscription_status": {"S": "active"},
        }

        mock_session = MagicMock()
        mock_session.url = "https://billing.stripe.com/portal_session_xyz"
        mock_stripe.billing_portal.Session.create.return_value = mock_session

        result = create_portal_session("user-1")

        assert result == {"portal_url": "https://billing.stripe.com/portal_session_xyz"}
        mock_stripe.billing_portal.Session.create.assert_called_once_with(
            customer="cus_abc123",
            return_url="https://test.devsecblueprint.com/settings/subscription",
        )

    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service._get_stripe_key")
    def test_raises_valueerror_when_no_stripe_customer_id(
        self, mock_key, mock_db, mock_stripe
    ):
        """User with membership record but no stripe_customer_id raises ValueError."""
        mock_key.return_value = "sk_test_123"
        mock_db.get_membership.return_value = {
            "PK": {"S": "USER#user-2"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": "user-2"},
            "membership_tier": {"S": "FREE"},
        }

        with pytest.raises(ValueError, match="No subscription found"):
            create_portal_session("user-2")

        mock_stripe.billing_portal.Session.create.assert_not_called()

    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service._get_stripe_key")
    def test_raises_valueerror_when_no_membership_record(
        self, mock_key, mock_db, mock_stripe
    ):
        """User with no membership record at all raises ValueError."""
        mock_key.return_value = "sk_test_123"
        mock_db.get_membership.return_value = None

        with pytest.raises(ValueError, match="No subscription found"):
            create_portal_session("user-3")

        mock_stripe.billing_portal.Session.create.assert_not_called()

    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service._get_stripe_key")
    def test_return_url_uses_frontend_url(self, mock_key, mock_db, mock_stripe):
        """Portal session return_url uses FRONTEND_URL + /settings/subscription."""
        mock_key.return_value = "sk_test_123"
        mock_db.get_membership.return_value = {
            "PK": {"S": "USER#user-4"},
            "SK": {"S": "MEMBERSHIP"},
            "stripe_customer_id": {"S": "cus_url_check"},
        }

        mock_session = MagicMock()
        mock_session.url = "https://billing.stripe.com/portal_abc"
        mock_stripe.billing_portal.Session.create.return_value = mock_session

        create_portal_session("user-4")

        call_kwargs = mock_stripe.billing_portal.Session.create.call_args[1]
        assert (
            call_kwargs["return_url"]
            == "https://test.devsecblueprint.com/settings/subscription"
        )

    @patch("backend.membership.services.stripe_service.stripe")
    @patch("backend.membership.services.stripe_service.membership_db")
    @patch("backend.membership.services.stripe_service._get_stripe_key")
    def test_propagates_stripe_api_error(self, mock_key, mock_db, mock_stripe):
        """Stripe API failures propagate as exceptions."""
        mock_key.return_value = "sk_test_123"
        mock_db.get_membership.return_value = {
            "PK": {"S": "USER#user-5"},
            "SK": {"S": "MEMBERSHIP"},
            "stripe_customer_id": {"S": "cus_error_test"},
        }

        mock_stripe.billing_portal.Session.create.side_effect = Exception(
            "Stripe API unavailable"
        )

        with pytest.raises(Exception, match="Stripe API unavailable"):
            create_portal_session("user-5")


class TestHandleStripePortal:
    """Tests for the handle_stripe_portal handler function."""

    @patch("backend.membership.handlers.stripe_handlers.create_portal_session")
    @patch("backend.membership.handlers.stripe_handlers.require_auth")
    def test_returns_200_with_portal_url(self, mock_auth, mock_create):
        """Authenticated user with subscription gets portal URL."""
        mock_auth.return_value = ({"sub": "user-1", "is_admin": False}, None)
        mock_create.return_value = {
            "portal_url": "https://billing.stripe.com/portal_xyz"
        }

        event = {"headers": {"authorization": "Bearer valid-token"}, "body": ""}
        result = handle_stripe_portal(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["portal_url"] == "https://billing.stripe.com/portal_xyz"
        mock_create.assert_called_once_with("user-1")

    @patch("backend.membership.handlers.stripe_handlers.require_auth")
    def test_returns_401_when_unauthenticated(self, mock_auth):
        """Unauthenticated request gets 401."""
        mock_auth.return_value = (
            None,
            {
                "statusCode": 401,
                "body": '{"error":"Authentication required"}',
                "headers": {},
            },
        )

        event = {"headers": {}, "body": ""}
        result = handle_stripe_portal(event)

        assert result["statusCode"] == 401

    @patch("backend.membership.handlers.stripe_handlers.require_auth")
    def test_returns_401_when_no_sub_claim(self, mock_auth):
        """User payload without sub claim gets 401."""
        mock_auth.return_value = ({"is_admin": False}, None)  # No "sub" key

        event = {"headers": {"authorization": "Bearer token"}, "body": ""}
        result = handle_stripe_portal(event)

        assert result["statusCode"] == 401

    @patch("backend.membership.handlers.stripe_handlers.create_portal_session")
    @patch("backend.membership.handlers.stripe_handlers.require_auth")
    def test_returns_400_when_no_customer(self, mock_auth, mock_create):
        """User with no stripe customer gets 400."""
        mock_auth.return_value = ({"sub": "user-2", "is_admin": False}, None)
        mock_create.side_effect = ValueError(
            "No subscription found. Visit the pricing page to subscribe."
        )

        event = {"headers": {"authorization": "Bearer token"}, "body": ""}
        result = handle_stripe_portal(event)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "No subscription found" in body["error"]
        assert "pricing" in body["error"].lower()

    @patch("backend.membership.handlers.stripe_handlers.create_portal_session")
    @patch("backend.membership.handlers.stripe_handlers.require_auth")
    def test_returns_500_on_stripe_failure(self, mock_auth, mock_create):
        """Stripe API failure returns 500."""
        mock_auth.return_value = ({"sub": "user-3", "is_admin": False}, None)
        mock_create.side_effect = Exception("Stripe API error")

        event = {"headers": {"authorization": "Bearer token"}, "body": ""}
        result = handle_stripe_portal(event)

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "portal" in body["error"].lower() or "failed" in body["error"].lower()
