"""Tests for the stripe router — /api/stripe/*.

- GET  /api/stripe/products       (public)
- POST /api/stripe/checkout       (auth)
- GET  /api/stripe/subscription   (auth)
- POST /api/stripe/portal         (auth)
- POST /api/stripe/webhook        (signature-verified, no JWT)

StripeService is injected via get_stripe_service, overridden with a mock.
The webhook enqueues a Discord sync background task; we patch
enqueue_discord_sync at the router import site.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import Settings
from app.main import app

TEST_SETTINGS = Settings(
    membership_table="test-membership",
    progress_table="test-progress",
    user_state_table="test-user-state",
    testimonials_table="test-testimonials",
    notifications_table="test-notifications",
    discord_secret_name="test-discord",
    discord_bot_secret_name="test-discord-bot",
    stripe_secret_name="test-stripe",
    stripe_webhook_secret_name="test-stripe-webhook",
    jwt_secret_name="test-jwt-secret",
    github_secret_name="test-github",
    gitlab_secret_name="test-gitlab",
    bitbucket_secret_name="test-bitbucket",
    discord_guild_id="123456",
    discord_role_free_id="111",
    discord_role_explorer_id="222",
    discord_role_builder_id="333",
    discord_role_builder_academy_id="444",
    discord_callback_url="https://example.com/callback",
    frontend_url="https://example.com",
    frontend_origin="https://example.com",
    github_callback_url="https://example.com/auth/github/callback",
    gitlab_callback_url="https://example.com/auth/gitlab/callback",
    bitbucket_callback_url="https://example.com/auth/bitbucket/callback",
    session_token_lifetime_hours=8,
)

TEST_SECRET_KEY = "test-secret-key-for-jwt-signing-32chars"


def _make_token(sub: str = "user-123") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "avatar": "https://avatar.url",
        "name": "Test User",
        "provider": "github",
        "github_login": "testuser",
        "is_admin": False,
        "iat": now,
        "exp": now + timedelta(hours=8),
    }
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")


@pytest.fixture
def mock_auth():
    from app.auth.jwt import _jwt_secret_cache

    _jwt_secret_cache["secret_key"] = TEST_SECRET_KEY
    _jwt_secret_cache["fetched_at"] = 9999999999.0
    yield
    _jwt_secret_cache["secret_key"] = None
    _jwt_secret_cache["fetched_at"] = 0.0


@pytest.fixture
def mock_service():
    return MagicMock()


@pytest.fixture
def client(mock_service):
    from app.dependencies import get_settings as dep_get_settings
    from app.routers.stripe import get_stripe_service

    app.dependency_overrides[dep_get_settings] = lambda: TEST_SETTINGS
    app.dependency_overrides[get_stripe_service] = lambda: mock_service
    yield TestClient(app)
    app.dependency_overrides.clear()


def _auth_header():
    return {"Authorization": f"Bearer {_make_token()}"}


# ---------------------------------------------------------------------------
# GET /api/stripe/products (public)
# ---------------------------------------------------------------------------


class TestProducts:
    def test_success(self, client, mock_service):
        mock_service.get_products.return_value = [
            {"id": "prod_1", "tier": "BUILDER", "price": 1000}
        ]
        response = client.get("/api/stripe/products")
        assert response.status_code == 200
        data = response.json()
        assert data["products"][0]["id"] == "prod_1"

    def test_no_auth_required(self, client, mock_auth, mock_service):
        mock_service.get_products.return_value = []
        response = client.get("/api/stripe/products")
        assert response.status_code == 200
        assert response.json() == {"products": []}

    def test_service_error_returns_500(self, client, mock_service):
        mock_service.get_products.side_effect = RuntimeError("stripe down")
        response = client.get("/api/stripe/products")
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to fetch products"


# ---------------------------------------------------------------------------
# POST /api/stripe/checkout (auth)
# ---------------------------------------------------------------------------


class TestCheckout:
    def test_requires_auth(self, client, mock_auth):
        response = client.post("/api/stripe/checkout", json={"price_id": "price_123"})
        assert response.status_code == 401

    def test_success(self, client, mock_auth, mock_service):
        mock_service.create_checkout_session.return_value = {
            "checkout_url": "https://checkout.stripe.com/abc"
        }
        response = client.post(
            "/api/stripe/checkout",
            headers=_auth_header(),
            json={"price_id": "price_123"},
        )
        assert response.status_code == 200
        assert response.json()["checkout_url"] == "https://checkout.stripe.com/abc"
        mock_service.create_checkout_session.assert_called_once_with(
            "user-123", "price_123"
        )

    def test_invalid_price_id_format_400(self, client, mock_auth, mock_service):
        response = client.post(
            "/api/stripe/checkout",
            headers=_auth_header(),
            json={"price_id": "notaprice"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid price_id format"
        mock_service.create_checkout_session.assert_not_called()

    def test_empty_price_id_422(self, client, mock_auth):
        response = client.post(
            "/api/stripe/checkout", headers=_auth_header(), json={"price_id": ""}
        )
        assert response.status_code == 422

    def test_value_error_returns_400(self, client, mock_auth, mock_service):
        mock_service.create_checkout_session.side_effect = ValueError(
            "already subscribed"
        )
        response = client.post(
            "/api/stripe/checkout",
            headers=_auth_header(),
            json={"price_id": "price_123"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "already subscribed"

    def test_unexpected_error_returns_500(self, client, mock_auth, mock_service):
        mock_service.create_checkout_session.side_effect = RuntimeError("boom")
        response = client.post(
            "/api/stripe/checkout",
            headers=_auth_header(),
            json={"price_id": "price_123"},
        )
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to create checkout session"


# ---------------------------------------------------------------------------
# GET /api/stripe/subscription (auth)
# ---------------------------------------------------------------------------


class TestSubscription:
    def test_requires_auth(self, client, mock_auth):
        assert client.get("/api/stripe/subscription").status_code == 401

    def test_success(self, client, mock_auth, mock_service):
        mock_service.get_subscription_status.return_value = {
            "membership_tier": "BUILDER",
            "subscription_status": "active",
            "current_period_end": "2025-01-01",
            "subscription_id": "sub_1",
        }
        response = client.get("/api/stripe/subscription", headers=_auth_header())
        assert response.status_code == 200
        data = response.json()
        assert data["membership_tier"] == "BUILDER"
        assert data["subscription_status"] == "active"

    def test_error_returns_500(self, client, mock_auth, mock_service):
        mock_service.get_subscription_status.side_effect = RuntimeError("boom")
        response = client.get("/api/stripe/subscription", headers=_auth_header())
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to retrieve subscription status"


# ---------------------------------------------------------------------------
# POST /api/stripe/portal (auth)
# ---------------------------------------------------------------------------


class TestPortal:
    def test_requires_auth(self, client, mock_auth):
        assert client.post("/api/stripe/portal").status_code == 401

    def test_success(self, client, mock_auth, mock_service):
        mock_service.create_portal_session.return_value = {
            "portal_url": "https://billing.stripe.com/xyz"
        }
        response = client.post("/api/stripe/portal", headers=_auth_header())
        assert response.status_code == 200
        assert response.json()["portal_url"] == "https://billing.stripe.com/xyz"

    def test_value_error_returns_400(self, client, mock_auth, mock_service):
        mock_service.create_portal_session.side_effect = ValueError("no customer")
        response = client.post("/api/stripe/portal", headers=_auth_header())
        assert response.status_code == 400
        assert response.json()["detail"] == "no customer"

    def test_error_returns_500(self, client, mock_auth, mock_service):
        mock_service.create_portal_session.side_effect = RuntimeError("boom")
        response = client.post("/api/stripe/portal", headers=_auth_header())
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to create portal session"


# ---------------------------------------------------------------------------
# POST /api/stripe/webhook (signature-verified)
# ---------------------------------------------------------------------------


class TestWebhook:
    def test_missing_signature_header_400(self, client, mock_service):
        response = client.post("/api/stripe/webhook", content=b"{}")
        assert response.status_code == 400
        assert response.json()["detail"] == "Missing Stripe-Signature header"

    def test_success_enqueues_sync_on_tier_change(self, client, mock_service):
        mock_service.verify_and_process_webhook.return_value = {
            "processed": True,
            "user_id": "user-999",
        }
        with patch("app.routers.stripe.enqueue_discord_sync") as mock_enqueue:
            response = client.post(
                "/api/stripe/webhook",
                content=b'{"type":"customer.subscription.updated"}',
                headers={"stripe-signature": "t=1,v1=abc"},
            )

        assert response.status_code == 200
        assert response.json()["processed"] is True
        mock_enqueue.assert_called_once()
        _, kwargs = mock_enqueue.call_args
        assert kwargs["user_id"] == "user-999"
        assert kwargs["operation"] == "tier_change"

    def test_success_without_user_no_enqueue(self, client, mock_service):
        mock_service.verify_and_process_webhook.return_value = {"processed": False}
        with patch("app.routers.stripe.enqueue_discord_sync") as mock_enqueue:
            response = client.post(
                "/api/stripe/webhook",
                content=b"{}",
                headers={"stripe-signature": "sig"},
            )

        assert response.status_code == 200
        assert response.json()["processed"] is False
        mock_enqueue.assert_not_called()

    def test_invalid_signature_400(self, client, mock_service):
        mock_service.verify_and_process_webhook.side_effect = ValueError("bad sig")
        response = client.post(
            "/api/stripe/webhook",
            content=b"{}",
            headers={"stripe-signature": "sig"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid webhook signature"

    def test_processing_error_returns_200(self, client, mock_service):
        """Non-signature errors return 200 to avoid Stripe retries."""
        mock_service.verify_and_process_webhook.side_effect = RuntimeError("boom")
        response = client.post(
            "/api/stripe/webhook",
            content=b"{}",
            headers={"stripe-signature": "sig"},
        )
        assert response.status_code == 200
        assert response.json() == {"processed": False, "error": "processing_error"}


# ---------------------------------------------------------------------------
# Dependency provider
# ---------------------------------------------------------------------------


def test_get_stripe_service_builds_instance():
    from app.routers.stripe import get_stripe_service
    from app.services.stripe_service import StripeService

    with patch("app.services.stripe_service.boto3.client"):
        svc = get_stripe_service(TEST_SETTINGS)
    assert isinstance(svc, StripeService)
