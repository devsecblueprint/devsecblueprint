"""Unit tests for the membership Lambda handler (handler.py)."""

import json
import os
from unittest.mock import patch, MagicMock

import pytest

# Set required env vars before importing the module
os.environ.setdefault("MEMBERSHIP_TABLE", "test-membership-table")
os.environ.setdefault("FRONTEND_URL", "https://staging.devsecblueprint.com")
os.environ.setdefault("JWT_SECRET_NAME", "test-jwt-secret")
os.environ.setdefault("ADMIN_USERS", "github:admin_user")
os.environ.setdefault("DISCORD_SECRET_NAME", "test-discord-secret")
os.environ.setdefault("DISCORD_BOT_SECRET_NAME", "test-bot-secret")
os.environ.setdefault("STRIPE_SECRET_NAME", "test-stripe-secret")
os.environ.setdefault("DISCORD_GUILD_ID", "12345678901234567")

from handler import main, _cors_preflight_response


def _make_http_event(method: str, path: str, headers=None, body="", query_params=None):
    """Helper to build an API Gateway HTTP API v2 event."""
    return {
        "requestContext": {"http": {"method": method, "path": path}},
        "headers": headers or {},
        "body": body,
        "queryStringParameters": query_params,
    }


class TestEventSourceDetection:
    """Tests for event source routing (SQS, EventBridge, HTTP)."""

    @patch("handlers.sync_handlers.handle_sqs_event")
    def test_sqs_event_dispatches_to_handle_sqs_event(self, mock_sqs):
        """Events with 'Records' key dispatch to SQS handler."""
        mock_sqs.return_value = {"statusCode": 200, "body": "ok"}
        event = {"Records": [{"body": '{"user_id": "user123"}'}]}

        result = main(event, None)

        mock_sqs.assert_called_once_with(event)
        assert result["statusCode"] == 200

    @patch("handlers.sync_handlers.handle_reconciliation")
    def test_eventbridge_source_scheduler(self, mock_reconcile):
        """Events with source=scheduler dispatch to reconciliation."""
        mock_reconcile.return_value = {"statusCode": 200, "body": "done"}
        event = {"source": "scheduler"}

        result = main(event, None)

        mock_reconcile.assert_called_once_with(event)
        assert result["statusCode"] == 200

    @patch("handlers.sync_handlers.handle_reconciliation")
    def test_eventbridge_action_reconciliation(self, mock_reconcile):
        """Events with action=reconciliation dispatch to reconciliation."""
        mock_reconcile.return_value = {"statusCode": 200, "body": "done"}
        event = {"action": "reconciliation"}

        result = main(event, None)

        mock_reconcile.assert_called_once_with(event)
        assert result["statusCode"] == 200


class TestOptionsPreflightHandler:
    """Tests for CORS OPTIONS preflight handling."""

    def test_options_returns_200_with_cors_headers(self):
        """OPTIONS requests return 200 with CORS headers."""
        event = _make_http_event("OPTIONS", "/api/discord/status")

        result = main(event, None)

        assert result["statusCode"] == 200
        assert "Access-Control-Allow-Origin" in result["headers"]
        assert "Access-Control-Allow-Methods" in result["headers"]
        assert "Access-Control-Allow-Credentials" in result["headers"]

    def test_options_returns_max_age(self):
        """OPTIONS preflight includes Access-Control-Max-Age."""
        event = _make_http_event("OPTIONS", "/any/path")

        result = main(event, None)

        assert result["headers"]["Access-Control-Max-Age"] == "300"


class TestPublicRoutes:
    """Tests for routes that require no authentication."""

    @patch("services.stripe_service.get_products")
    def test_get_stripe_products_returns_products(self, mock_products):
        """GET /api/stripe/products returns product list without auth."""
        mock_products.return_value = [{"id": "prod_1", "name": "Explorer"}]
        event = _make_http_event("GET", "/api/stripe/products")

        result = main(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["products"] == [{"id": "prod_1", "name": "Explorer"}]

    @patch("services.stripe_service.get_products")
    def test_get_stripe_products_handles_error(self, mock_products):
        """GET /api/stripe/products returns 500 on service error."""
        mock_products.side_effect = Exception("Stripe API error")
        event = _make_http_event("GET", "/api/stripe/products")

        result = main(event, None)

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert body["error"] == "Failed to fetch products"


class TestSpecialAuthRoutes:
    """Tests for routes with their own auth mechanisms."""

    @patch("services.stripe_service.handle_stripe_webhook")
    def test_stripe_webhook_no_jwt_required(self, mock_webhook):
        """POST /api/stripe/webhook does not require JWT auth."""
        mock_webhook.return_value = {"statusCode": 200, "body": '{"received": true}'}
        event = _make_http_event(
            "POST",
            "/api/stripe/webhook",
            headers={"stripe-signature": "sig_test"},
            body="raw_body",
        )

        result = main(event, None)

        mock_webhook.assert_called_once_with(event)
        assert result["statusCode"] == 200

    @patch("services.discord_identity.handle_callback")
    def test_discord_callback_state_validated(self, mock_callback):
        """GET /auth/discord/callback uses state validation, not JWT."""
        mock_callback.return_value = "20100558"  # Returns user_id, not a URL
        event = _make_http_event(
            "GET",
            "/auth/discord/callback",
            query_params={"code": "test_code", "state": "test_state"},
        )

        result = main(event, None)

        mock_callback.assert_called_once_with("test_code", "test_state")
        assert result["statusCode"] == 302
        assert "discord=pending" in result["headers"]["Location"]
        assert "/settings/connected-accounts" in result["headers"]["Location"]

    @patch("services.discord_identity.handle_callback")
    def test_discord_callback_failure_redirects_with_error(self, mock_callback):
        """GET /auth/discord/callback redirects with error on exception."""
        mock_callback.side_effect = ValueError("Invalid state")
        event = _make_http_event(
            "GET",
            "/auth/discord/callback",
            query_params={"code": "test_code", "state": "bad_state"},
        )

        result = main(event, None)

        assert result["statusCode"] == 302
        assert "discord=error" in result["headers"]["Location"]
        assert "/settings/connected-accounts" in result["headers"]["Location"]

    def test_discord_callback_missing_params_redirects_with_error(self):
        """GET /auth/discord/callback without code/state redirects with error."""
        event = _make_http_event(
            "GET",
            "/auth/discord/callback",
            query_params={},
        )

        result = main(event, None)

        assert result["statusCode"] == 302
        assert "discord=error" in result["headers"]["Location"]


class TestAuthenticatedRoutes:
    """Tests for routes requiring JWT authentication."""

    @patch("auth.auth_middleware.require_auth")
    def test_unauthenticated_returns_401(self, mock_auth):
        """Authenticated routes return 401 when no valid token."""
        mock_auth.return_value = (
            None,
            {
                "statusCode": 401,
                "headers": {},
                "body": '{"error": "Authentication required"}',
            },
        )
        event = _make_http_event("GET", "/api/discord/status")

        result = main(event, None)

        assert result["statusCode"] == 401

    @patch("services.discord_identity.get_status")
    @patch("auth.auth_middleware.require_auth")
    def test_discord_status_authenticated(self, mock_auth, mock_status):
        """GET /api/discord/status returns status when authenticated."""
        mock_auth.return_value = ({"sub": "user123", "is_admin": False}, None)
        mock_status.return_value = {"connected": True, "discord_username": "testuser"}
        event = _make_http_event("GET", "/api/discord/status")

        result = main(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["connected"] is True

    @patch("services.discord_identity.confirm_identity")
    @patch("auth.auth_middleware.require_auth")
    def test_discord_confirm_authenticated(self, mock_auth, mock_confirm):
        """POST /api/discord/confirm works with valid auth."""
        mock_auth.return_value = ({"sub": "user123", "is_admin": False}, None)
        mock_confirm.return_value = {"platform_state": "Discord_Verified"}
        event = _make_http_event("POST", "/api/discord/confirm")

        result = main(event, None)

        assert result["statusCode"] == 200
        mock_confirm.assert_called_once_with("user123")

    @patch("services.discord_identity.disconnect")
    @patch("auth.auth_middleware.require_auth")
    def test_discord_disconnect_authenticated(self, mock_auth, mock_disconnect):
        """DELETE /api/discord/disconnect works with valid auth."""
        mock_auth.return_value = ({"sub": "user123", "is_admin": False}, None)
        mock_disconnect.return_value = {"cleanup_status": "completed"}
        event = _make_http_event("DELETE", "/api/discord/disconnect")

        result = main(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["cleanup_status"] == "completed"

    @patch("services.discord_identity.start_oauth")
    @patch("auth.auth_middleware.require_auth")
    def test_discord_start_redirects(self, mock_auth, mock_start):
        """GET /auth/discord/start redirects to Discord OAuth URL."""
        mock_auth.return_value = ({"sub": "user123", "is_admin": False}, None)
        mock_start.return_value = "https://discord.com/oauth2/authorize?client_id=123"
        event = _make_http_event("GET", "/auth/discord/start")

        result = main(event, None)

        assert result["statusCode"] == 302
        assert "discord.com" in result["headers"]["Location"]


class TestAdminRoutes:
    """Tests for admin routes requiring JWT + admin check."""

    @patch("auth.auth_middleware.require_admin")
    def test_admin_route_returns_401_unauthenticated(self, mock_admin):
        """Admin routes return 401 for unauthenticated requests."""
        mock_admin.return_value = (
            None,
            {
                "statusCode": 401,
                "headers": {},
                "body": '{"error": "Authentication required"}',
            },
        )
        event = _make_http_event("GET", "/admin/discord/users/user123")

        result = main(event, None)

        assert result["statusCode"] == 401

    @patch("auth.auth_middleware.require_admin")
    def test_admin_route_returns_403_non_admin(self, mock_admin):
        """Admin routes return 403 for non-admin users."""
        mock_admin.return_value = (
            None,
            {
                "statusCode": 403,
                "headers": {},
                "body": '{"error": "Admin access required"}',
            },
        )
        event = _make_http_event("GET", "/admin/discord/users/user123")

        result = main(event, None)

        assert result["statusCode"] == 403

    @patch("services.admin_discord.get_admin_user_detail")
    @patch("auth.auth_middleware.require_admin")
    def test_admin_user_detail(self, mock_admin, mock_detail):
        """GET /admin/discord/users/{user_id} returns user detail."""
        mock_admin.return_value = ({"sub": "admin1", "is_admin": True}, None)
        mock_detail.return_value = {
            "user_id": "user123",
            "membership_tier": "BUILDER",
            "discord_connected": True,
        }
        event = _make_http_event("GET", "/admin/discord/users/user123")

        result = main(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["user_id"] == "user123"
        mock_detail.assert_called_once_with("user123")

    @patch("services.admin_discord.get_admin_user_detail")
    @patch("auth.auth_middleware.require_admin")
    def test_admin_user_detail_not_found(self, mock_admin, mock_detail):
        """GET /admin/discord/users/{user_id} returns 404 for unknown user."""
        mock_admin.return_value = ({"sub": "admin1", "is_admin": True}, None)
        mock_detail.return_value = None
        event = _make_http_event("GET", "/admin/discord/users/unknown_user")

        result = main(event, None)

        assert result["statusCode"] == 404

    @patch("services.admin_discord.admin_trigger_sync")
    @patch("auth.auth_middleware.require_admin")
    def test_admin_sync_trigger(self, mock_admin, mock_sync):
        """POST /admin/discord/users/{user_id}/sync triggers sync."""
        mock_admin.return_value = ({"sub": "admin1", "is_admin": True}, None)
        mock_sync.return_value = {"success": True, "user_id": "user123"}
        event = _make_http_event(
            "POST",
            "/admin/discord/users/user123/sync",
            body=json.dumps({"reason": "Testing sync"}),
        )

        result = main(event, None)

        assert result["statusCode"] == 200
        mock_sync.assert_called_once_with("admin1", "user123", "Testing sync")

    @patch("services.admin_discord.admin_disconnect")
    @patch("auth.auth_middleware.require_admin")
    def test_admin_disconnect(self, mock_admin, mock_disconnect):
        """DELETE /admin/discord/users/{user_id}/disconnect works."""
        mock_admin.return_value = ({"sub": "admin1", "is_admin": True}, None)
        mock_disconnect.return_value = {
            "cleanup_status": "completed",
            "user_id": "user123",
        }
        event = _make_http_event(
            "DELETE",
            "/admin/discord/users/user123/disconnect",
            body=json.dumps({"reason": "Policy violation detected"}),
        )

        result = main(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["cleanup_status"] == "completed"

    @patch("auth.auth_middleware.require_admin")
    def test_admin_disconnect_missing_reason(self, mock_admin):
        """DELETE /admin/discord/users/{user_id}/disconnect rejects missing reason."""
        mock_admin.return_value = ({"sub": "admin1", "is_admin": True}, None)
        event = _make_http_event(
            "DELETE",
            "/admin/discord/users/user123/disconnect",
            body="",
        )

        result = main(event, None)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Reason" in body["error"] or "reason" in body["error"].lower()

    @patch("services.admin_discord.get_admin_audit_log")
    @patch("auth.auth_middleware.require_admin")
    def test_admin_audit_log(self, mock_admin, mock_audit):
        """GET /admin/discord/users/{user_id}/audit returns audit entries."""
        mock_admin.return_value = ({"sub": "admin1", "is_admin": True}, None)
        mock_audit.return_value = [
            {"event_type": "CONNECTED", "timestamp": "2024-01-01T00:00:00Z"}
        ]
        event = _make_http_event("GET", "/admin/discord/users/user123/audit")

        result = main(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert len(body["entries"]) == 1
        mock_audit.assert_called_once_with("user123")


class TestUnknownRoutes:
    """Tests for 404 handling."""

    def test_unknown_route_returns_404(self):
        """Unknown routes return 404."""
        event = _make_http_event("GET", "/unknown/path")

        result = main(event, None)

        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert body["error"] == "Not found"

    def test_unknown_admin_route_returns_404(self):
        """Unknown admin sub-routes return 404 (after admin auth)."""
        with patch("auth.auth_middleware.require_admin") as mock_admin:
            mock_admin.return_value = ({"sub": "admin1", "is_admin": True}, None)
            event = _make_http_event("GET", "/admin/unknown/path")

            result = main(event, None)

            assert result["statusCode"] == 404


class TestErrorSanitization:
    """Tests for error sanitization — no internal details exposed."""

    @patch("auth.auth_middleware.require_auth")
    def test_unhandled_exception_returns_generic_500(self, mock_auth):
        """Unhandled exceptions return generic 500 without stack traces."""
        # Force an unexpected error during route dispatch
        mock_auth.side_effect = RuntimeError("Database connection pool exhausted")
        event = _make_http_event("GET", "/api/discord/status")

        result = main(event, None)

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        # Must NOT contain internal error details
        assert "Database" not in body["error"]
        assert "pool" not in body["error"]
        assert body["error"] == "Internal server error"

    def test_malformed_event_returns_500(self):
        """Malformed events (no requestContext) return 500."""
        event = {}

        result = main(event, None)

        # Should not crash — returns 404 or 500
        assert result["statusCode"] in (404, 500)

    @patch("services.stripe_service.get_products")
    def test_products_error_does_not_expose_details(self, mock_products):
        """Product fetch error returns safe message, no internal details."""
        mock_products.side_effect = Exception("Stripe API key invalid: sk_test_abc123")
        event = _make_http_event("GET", "/api/stripe/products")

        result = main(event, None)

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "sk_test" not in body["error"]
        assert "API key" not in body["error"]
        assert body["error"] == "Failed to fetch products"


class TestRequestLogging:
    """Tests verifying request logging behavior."""

    @patch("handler.logger")
    def test_logs_incoming_request(self, mock_logger):
        """Handler logs method and path for debugging."""
        event = _make_http_event("GET", "/api/discord/status")

        # Will fail on auth, but logging should still happen
        with patch("auth.auth_middleware.require_auth") as mock_auth:
            mock_auth.return_value = (
                None,
                {
                    "statusCode": 401,
                    "headers": {},
                    "body": '{"error": "Auth required"}',
                },
            )
            main(event, None)

        # Verify the log call was made with method and path
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any(
            "GET" in call and "/api/discord/status" in call for call in log_calls
        )
