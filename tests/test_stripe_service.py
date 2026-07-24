"""
Tests for Stripe Service — get_products() with caching.

Validates: Requirements 1.1, 1.2, 22.2
"""

import time
import pytest
from unittest.mock import patch, MagicMock

import backend.membership.services.stripe_service as stripe_service
from backend.membership.services.stripe_service import get_products


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset the module-level cache before each test."""
    stripe_service._products_cache["data"] = None
    stripe_service._products_cache["timestamp"] = 0
    yield
    stripe_service._products_cache["data"] = None
    stripe_service._products_cache["timestamp"] = 0


def _make_product(product_id, name, dsb_tier, description=None):
    """Create a mock Stripe Product object."""
    product = MagicMock()
    product.id = product_id
    product.name = name
    product.description = description
    product.metadata = {"dsb_tier": dsb_tier} if dsb_tier else {}
    return product


def _make_price(price_id, unit_amount, currency="usd", interval="month"):
    """Create a mock Stripe Price object."""
    price = MagicMock()
    price.id = price_id
    price.unit_amount = unit_amount
    price.currency = currency
    if interval:
        price.recurring = MagicMock()
        price.recurring.interval = interval
    else:
        price.recurring = None
    return price


class TestGetProducts:
    """Test the get_products function."""

    @patch("backend.membership.services.stripe_service.get_secret")
    @patch("backend.membership.services.stripe_service.stripe")
    def test_fetches_products_with_dsb_tier(self, mock_stripe, mock_get_secret):
        """Test that only products with dsb_tier metadata are returned."""
        mock_get_secret.return_value = {"secret_key": "sk_test_123"}

        product_with_tier = _make_product(
            "prod_1", "Explorer Plan", "EXPLORER", "Explorer tier"
        )
        product_without_tier = _make_product("prod_2", "Random Product", None)

        mock_stripe.Product.list.return_value = MagicMock(
            data=[product_with_tier, product_without_tier]
        )
        mock_stripe.Price.list.return_value = MagicMock(
            data=[_make_price("price_1", 999, "usd", "month")]
        )

        result = get_products()

        assert len(result) == 1
        assert result[0]["id"] == "prod_1"
        assert result[0]["name"] == "Explorer Plan"
        assert result[0]["description"] == "Explorer tier"
        assert result[0]["price"] == 999
        assert result[0]["currency"] == "usd"
        assert result[0]["interval"] == "month"
        assert result[0]["dsb_tier"] == "EXPLORER"
        assert result[0]["price_id"] == "price_1"

    @patch("backend.membership.services.stripe_service.get_secret")
    @patch("backend.membership.services.stripe_service.stripe")
    def test_multiple_prices_per_product(self, mock_stripe, mock_get_secret):
        """Test that multiple prices for a product create multiple entries."""
        mock_get_secret.return_value = {"secret_key": "sk_test_123"}

        product = _make_product("prod_1", "Builder Plan", "BUILDER")
        mock_stripe.Product.list.return_value = MagicMock(data=[product])
        mock_stripe.Price.list.return_value = MagicMock(
            data=[
                _make_price("price_monthly", 1999, "usd", "month"),
                _make_price("price_yearly", 19999, "usd", "year"),
            ]
        )

        result = get_products()

        assert len(result) == 2
        assert result[0]["price_id"] == "price_monthly"
        assert result[0]["interval"] == "month"
        assert result[1]["price_id"] == "price_yearly"
        assert result[1]["interval"] == "year"

    @patch("backend.membership.services.stripe_service.get_secret")
    @patch("backend.membership.services.stripe_service.stripe")
    def test_one_time_price_has_none_interval(self, mock_stripe, mock_get_secret):
        """Test that a one-time price has interval set to None."""
        mock_get_secret.return_value = {"secret_key": "sk_test_123"}

        product = _make_product("prod_1", "One-time Access", "BUILDER")
        mock_stripe.Product.list.return_value = MagicMock(data=[product])
        mock_stripe.Price.list.return_value = MagicMock(
            data=[_make_price("price_once", 4999, "usd", None)]
        )

        result = get_products()

        assert result[0]["interval"] is None

    @patch("backend.membership.services.stripe_service.get_secret")
    @patch("backend.membership.services.stripe_service.stripe")
    def test_description_defaults_to_empty_string(self, mock_stripe, mock_get_secret):
        """Test that a product with no description returns empty string."""
        mock_get_secret.return_value = {"secret_key": "sk_test_123"}

        product = _make_product("prod_1", "No Desc Plan", "FREE")
        mock_stripe.Product.list.return_value = MagicMock(data=[product])
        mock_stripe.Price.list.return_value = MagicMock(
            data=[_make_price("price_1", 0, "usd", "month")]
        )

        result = get_products()

        assert result[0]["description"] == ""

    @patch("backend.membership.services.stripe_service.get_secret")
    @patch("backend.membership.services.stripe_service.stripe")
    def test_returns_cached_data_within_ttl(self, mock_stripe, mock_get_secret):
        """Test that cached data is returned without calling Stripe API again."""
        mock_get_secret.return_value = {"secret_key": "sk_test_123"}

        product = _make_product("prod_1", "Cached Plan", "EXPLORER")
        mock_stripe.Product.list.return_value = MagicMock(data=[product])
        mock_stripe.Price.list.return_value = MagicMock(
            data=[_make_price("price_1", 999, "usd", "month")]
        )

        # First call populates cache
        result1 = get_products()
        assert len(result1) == 1

        # Reset mocks to verify no second call
        mock_stripe.Product.list.reset_mock()
        mock_stripe.Price.list.reset_mock()

        # Second call should use cache
        result2 = get_products()
        assert result2 == result1
        mock_stripe.Product.list.assert_not_called()
        mock_stripe.Price.list.assert_not_called()

    @patch("backend.membership.services.stripe_service.time.time")
    @patch("backend.membership.services.stripe_service.get_secret")
    @patch("backend.membership.services.stripe_service.stripe")
    def test_cache_expires_after_ttl(self, mock_stripe, mock_get_secret, mock_time):
        """Test that cache is refreshed after 5 minutes."""
        mock_get_secret.return_value = {"secret_key": "sk_test_123"}

        product = _make_product("prod_1", "Plan", "EXPLORER")
        mock_stripe.Product.list.return_value = MagicMock(data=[product])
        mock_stripe.Price.list.return_value = MagicMock(
            data=[_make_price("price_1", 999, "usd", "month")]
        )

        # First call at time=1000
        mock_time.return_value = 1000
        get_products()
        assert mock_stripe.Product.list.call_count == 1

        # Call at time=1200 (within TTL) — should use cache
        mock_time.return_value = 1200
        get_products()
        assert mock_stripe.Product.list.call_count == 1

        # Call at time=1301 (after 5min TTL) — should refresh
        mock_time.return_value = 1301
        get_products()
        assert mock_stripe.Product.list.call_count == 2

    @patch("backend.membership.services.stripe_service.get_secret")
    @patch("backend.membership.services.stripe_service.stripe")
    def test_stripe_error_returns_cached_data(self, mock_stripe, mock_get_secret):
        """Test that on API failure, stale cached data is returned."""
        mock_get_secret.return_value = {"secret_key": "sk_test_123"}

        # Pre-populate cache
        cached_data = [{"id": "prod_cached", "name": "Cached", "dsb_tier": "FREE"}]
        stripe_service._products_cache["data"] = cached_data
        stripe_service._products_cache["timestamp"] = 0  # Expired

        # Make Stripe call fail
        mock_stripe.Product.list.side_effect = Exception("Stripe API down")

        result = get_products()

        assert result == cached_data

    @patch("backend.membership.services.stripe_service.get_secret")
    @patch("backend.membership.services.stripe_service.stripe")
    def test_stripe_error_no_cache_raises(self, mock_stripe, mock_get_secret):
        """Test that on API failure with no cache, exception is raised."""
        mock_get_secret.return_value = {"secret_key": "sk_test_123"}

        mock_stripe.Product.list.side_effect = Exception("Stripe API down")

        with pytest.raises(Exception, match="Stripe API down"):
            get_products()

    @patch("backend.membership.services.stripe_service.get_secret")
    @patch("backend.membership.services.stripe_service.stripe")
    def test_response_format_keys(self, mock_stripe, mock_get_secret):
        """Test that response contains all required keys."""
        mock_get_secret.return_value = {"secret_key": "sk_test_123"}

        product = _make_product(
            "prod_1", "Full Plan", "BUILDER_ACADEMY", "Full description"
        )
        mock_stripe.Product.list.return_value = MagicMock(data=[product])
        mock_stripe.Price.list.return_value = MagicMock(
            data=[_make_price("price_1", 4999, "usd", "month")]
        )

        result = get_products()

        expected_keys = {
            "id",
            "name",
            "description",
            "price",
            "currency",
            "interval",
            "dsb_tier",
            "price_id",
        }
        assert set(result[0].keys()) == expected_keys


class TestGetSubscriptionStatus:
    """Test the get_subscription_status function.

    Validates: Requirements 3.1, 3.5, 3.6
    """

    @patch("backend.membership.services.stripe_service.membership_db.get_membership")
    def test_no_membership_record_returns_free(self, mock_get_membership):
        """Test that a user with no membership record gets FREE tier with null fields."""
        mock_get_membership.return_value = None

        from backend.membership.services.stripe_service import get_subscription_status

        result = get_subscription_status("user-123")

        assert result == {
            "membership_tier": "FREE",
            "subscription_status": None,
            "current_period_end": None,
            "stripe_subscription_id": None,
        }
        mock_get_membership.assert_called_once_with("user-123")

    @patch("backend.membership.services.stripe_service.membership_db.get_membership")
    def test_free_tier_membership_returns_free_with_nulls(self, mock_get_membership):
        """Test that a FREE tier user with a membership record returns correct data."""
        mock_get_membership.return_value = {
            "PK": {"S": "USER#user-456"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": "user-456"},
            "membership_tier": {"S": "FREE"},
        }

        from backend.membership.services.stripe_service import get_subscription_status

        result = get_subscription_status("user-456")

        assert result["membership_tier"] == "FREE"
        assert result["subscription_status"] is None
        assert result["current_period_end"] is None
        assert result["stripe_subscription_id"] is None

    @patch("backend.membership.services.stripe_service.membership_db.get_membership")
    def test_active_subscription_returns_all_fields(self, mock_get_membership):
        """Test that an active subscriber gets all subscription fields populated."""
        mock_get_membership.return_value = {
            "PK": {"S": "USER#user-789"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": "user-789"},
            "membership_tier": {"S": "BUILDER"},
            "subscription_status": {"S": "active"},
            "current_period_end": {"S": "2025-02-15T00:00:00Z"},
            "stripe_subscription_id": {"S": "sub_abc123"},
            "stripe_customer_id": {"S": "cus_xyz789"},
        }

        from backend.membership.services.stripe_service import get_subscription_status

        result = get_subscription_status("user-789")

        assert result == {
            "membership_tier": "BUILDER",
            "subscription_status": "active",
            "current_period_end": "2025-02-15T00:00:00Z",
            "stripe_subscription_id": "sub_abc123",
        }

    @patch("backend.membership.services.stripe_service.membership_db.get_membership")
    def test_canceled_subscription_returns_status(self, mock_get_membership):
        """Test that a canceled subscription shows the canceled status."""
        mock_get_membership.return_value = {
            "PK": {"S": "USER#user-101"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": "user-101"},
            "membership_tier": {"S": "EXPLORER"},
            "subscription_status": {"S": "canceled"},
            "current_period_end": {"S": "2025-03-01T00:00:00Z"},
            "stripe_subscription_id": {"S": "sub_canceled456"},
        }

        from backend.membership.services.stripe_service import get_subscription_status

        result = get_subscription_status("user-101")

        assert result["membership_tier"] == "EXPLORER"
        assert result["subscription_status"] == "canceled"
        assert result["current_period_end"] == "2025-03-01T00:00:00Z"
        assert result["stripe_subscription_id"] == "sub_canceled456"

    @patch("backend.membership.services.stripe_service.membership_db.get_membership")
    def test_missing_tier_defaults_to_free(self, mock_get_membership):
        """Test that a membership record without membership_tier defaults to FREE."""
        mock_get_membership.return_value = {
            "PK": {"S": "USER#user-edge"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": "user-edge"},
        }

        from backend.membership.services.stripe_service import get_subscription_status

        result = get_subscription_status("user-edge")

        assert result["membership_tier"] == "FREE"
        assert result["subscription_status"] is None
        assert result["current_period_end"] is None
        assert result["stripe_subscription_id"] is None


class TestHandleGetSubscription:
    """Test the handle_get_subscription handler function.

    Validates: Requirements 3.1, 3.5, 3.6
    """

    @patch("backend.membership.services.stripe_service.membership_db.get_membership")
    def test_returns_200_with_subscription_status(self, mock_get_membership):
        """Test successful subscription status retrieval."""
        mock_get_membership.return_value = {
            "PK": {"S": "USER#user-123"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": "user-123"},
            "membership_tier": {"S": "BUILDER"},
            "subscription_status": {"S": "active"},
            "current_period_end": {"S": "2025-02-15T00:00:00Z"},
            "stripe_subscription_id": {"S": "sub_abc123"},
        }

        from backend.membership.services.stripe_service import handle_get_subscription
        import json

        event = {}
        user = {"sub": "user-123"}

        result = handle_get_subscription(event, user)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["membership_tier"] == "BUILDER"
        assert body["subscription_status"] == "active"
        assert body["current_period_end"] == "2025-02-15T00:00:00Z"
        assert body["stripe_subscription_id"] == "sub_abc123"

    def test_returns_401_when_no_user_sub(self):
        """Test that a user without sub claim gets 401."""
        from backend.membership.services.stripe_service import handle_get_subscription

        event = {}
        user = {}  # No "sub" claim

        result = handle_get_subscription(event, user)

        assert result["statusCode"] == 401

    @patch("backend.membership.services.stripe_service.membership_db.get_membership")
    def test_returns_500_on_db_error(self, mock_get_membership):
        """Test that a DynamoDB failure returns 500."""
        mock_get_membership.side_effect = Exception("DynamoDB unavailable")

        from backend.membership.services.stripe_service import handle_get_subscription

        event = {}
        user = {"sub": "user-123"}

        result = handle_get_subscription(event, user)

        assert result["statusCode"] == 500
