"""
AWS Lambda handler with manual routing for the DSB Membership service.

This module provides the main entry point for the membership Lambda, implementing
event source detection (SQS, EventBridge, HTTP) and dictionary-based routing for
HTTP requests. Supports Stripe, Discord identity, Discord sync, and admin endpoints.

Validates: Requirements 18.7, 19.11, 20.1, 20.11, 21.15-21.19
"""

import logging
import re
from typing import Any, Dict

from auth.auth_middleware import require_admin, require_auth
from utils.responses import error_response, json_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# CORS preflight response
# ---------------------------------------------------------------------------


def _cors_preflight_response() -> Dict[str, Any]:
    """Return 200 with CORS headers for OPTIONS preflight requests."""
    from utils.responses import add_cors_headers

    headers = add_cors_headers()
    headers["Access-Control-Max-Age"] = "300"
    return {"statusCode": 200, "headers": headers, "body": ""}


# ---------------------------------------------------------------------------
# Admin route path patterns (compiled once at module load)
# ---------------------------------------------------------------------------

_ADMIN_ROUTE_PATTERNS = [
    (
        re.compile(r"^/admin/discord/users/([^/]+)/sync$"),
        "POST",
        "handle_admin_sync",
    ),
    (
        re.compile(r"^/admin/discord/users/([^/]+)/disconnect$"),
        "DELETE",
        "handle_admin_disconnect",
    ),
    (
        re.compile(r"^/admin/discord/users/([^/]+)/audit$"),
        "GET",
        "handle_admin_audit",
    ),
    (
        re.compile(r"^/admin/discord/users/([^/]+)$"),
        "GET",
        "handle_admin_user_detail",
    ),
]


# ---------------------------------------------------------------------------
# Admin route handler wrappers
# ---------------------------------------------------------------------------


def _handle_admin_user_detail(event: Dict, user: Dict, user_id: str) -> Dict[str, Any]:
    """Handle GET /admin/discord/users/{user_id}."""
    from services.admin_discord import get_admin_user_detail

    result = get_admin_user_detail(user_id)
    if result is None:
        return error_response(404, "User not found")
    return json_response(200, result)


def _handle_admin_sync(event: Dict, user: Dict, user_id: str) -> Dict[str, Any]:
    """Handle POST /admin/discord/users/{user_id}/sync."""
    import json as json_mod

    from services.admin_discord import admin_trigger_sync

    body = event.get("body", "")
    reason = "Admin triggered"
    if body:
        try:
            payload = json_mod.loads(body)
            reason = payload.get("reason", reason)
        except (json_mod.JSONDecodeError, TypeError):
            pass

    admin_user_id = user.get("sub", "unknown")
    result = admin_trigger_sync(admin_user_id, user_id, reason)
    return json_response(200, result)


def _handle_admin_disconnect(event: Dict, user: Dict, user_id: str) -> Dict[str, Any]:
    """Handle DELETE /admin/discord/users/{user_id}/disconnect."""
    import json as json_mod

    from services.admin_discord import admin_disconnect

    body = event.get("body", "")
    reason = ""
    if body:
        try:
            payload = json_mod.loads(body)
            reason = payload.get("reason", "")
        except (json_mod.JSONDecodeError, TypeError):
            pass

    if not reason:
        return error_response(400, "Reason is required")

    admin_user_id = user.get("sub", "unknown")
    try:
        result = admin_disconnect(admin_user_id, user_id, reason)
        return json_response(200, result)
    except ValueError as e:
        return error_response(400, str(e))


def _handle_admin_audit(event: Dict, user: Dict, user_id: str) -> Dict[str, Any]:
    """Handle GET /admin/discord/users/{user_id}/audit."""
    from services.admin_discord import get_admin_audit_log

    result = get_admin_audit_log(user_id)
    return json_response(200, {"entries": result})


_ADMIN_DISPATCH = {
    "handle_admin_user_detail": _handle_admin_user_detail,
    "handle_admin_sync": _handle_admin_sync,
    "handle_admin_disconnect": _handle_admin_disconnect,
    "handle_admin_audit": _handle_admin_audit,
}


# ---------------------------------------------------------------------------
# Authenticated route handlers (wrappers)
# ---------------------------------------------------------------------------


def _handle_discord_start(event: Dict, user: Dict) -> Dict[str, Any]:
    """Handle GET /auth/discord/start — authenticated."""
    from services.discord_identity import start_oauth
    from utils.responses import redirect_response

    user_id = user.get("sub")
    try:
        redirect_url = start_oauth(user_id)
        return redirect_response(redirect_url)
    except ValueError as e:
        return error_response(400, str(e))


def _handle_discord_callback(event: Dict) -> Dict[str, Any]:
    """Handle GET /auth/discord/callback — state-validated, not JWT."""
    from services.discord_identity import handle_callback
    from utils.responses import redirect_response

    query_params = event.get("queryStringParameters") or {}
    code = query_params.get("code", "")
    state = query_params.get("state", "")

    if not code or not state:
        from config.settings import FRONTEND_URL

        return redirect_response(
            f"{FRONTEND_URL}/settings/connected-accounts?discord=error"
        )

    redirect_url = handle_callback(code, state)
    return redirect_response(redirect_url)


def _handle_discord_confirm(event: Dict, user: Dict) -> Dict[str, Any]:
    """Handle POST /api/discord/confirm — authenticated."""
    from services.discord_identity import confirm_identity

    user_id = user.get("sub")
    try:
        result = confirm_identity(user_id)
        return json_response(200, result)
    except ValueError as e:
        return error_response(400, str(e))


def _handle_discord_disconnect(event: Dict, user: Dict) -> Dict[str, Any]:
    """Handle DELETE /api/discord/disconnect — authenticated."""
    from services.discord_identity import disconnect

    user_id = user.get("sub")
    try:
        result = disconnect(user_id)
        return json_response(200, result)
    except ValueError as e:
        return error_response(400, str(e))


def _handle_discord_status(event: Dict, user: Dict) -> Dict[str, Any]:
    """Handle GET /api/discord/status — authenticated."""
    from services.discord_identity import get_status

    user_id = user.get("sub")
    result = get_status(user_id)
    return json_response(200, result)


def _handle_stripe_checkout(event: Dict, user: Dict) -> Dict[str, Any]:
    """Handle POST /api/stripe/checkout — authenticated."""
    from handlers.stripe_handlers import handle_stripe_checkout

    return handle_stripe_checkout(event)


def _handle_stripe_subscription(event: Dict, user: Dict) -> Dict[str, Any]:
    """Handle GET /api/stripe/subscription — authenticated."""
    from services.stripe_service import handle_get_subscription

    return handle_get_subscription(event, user)


def _handle_stripe_portal(event: Dict, user: Dict) -> Dict[str, Any]:
    """Handle POST /api/stripe/portal — authenticated."""
    from handlers.stripe_handlers import handle_stripe_portal

    return handle_stripe_portal(event)


# ---------------------------------------------------------------------------
# Public/special route handlers (no auth required)
# ---------------------------------------------------------------------------


def _handle_stripe_products(event: Dict) -> Dict[str, Any]:
    """Handle GET /api/stripe/products — public, no auth."""
    from services.stripe_service import get_products

    try:
        products = get_products()
        return json_response(200, {"products": products})
    except Exception as e:
        logger.error("Failed to fetch products: %s", type(e).__name__)
        return error_response(500, "Failed to fetch products")


def _handle_stripe_webhook(event: Dict) -> Dict[str, Any]:
    """Handle POST /api/stripe/webhook — signature-verified, no JWT auth."""
    from services.stripe_service import handle_stripe_webhook

    return handle_stripe_webhook(event)


# ---------------------------------------------------------------------------
# Route tables
# ---------------------------------------------------------------------------

# Routes that require NO authentication
_PUBLIC_ROUTES = {
    ("GET", "/api/stripe/products"): _handle_stripe_products,
}

# Routes that use their own auth mechanism (not JWT)
_SPECIAL_AUTH_ROUTES = {
    ("POST", "/api/stripe/webhook"): _handle_stripe_webhook,
    ("GET", "/auth/discord/callback"): _handle_discord_callback,
}

# Routes that require JWT authentication
_AUTHENTICATED_ROUTES = {
    ("GET", "/auth/discord/start"): _handle_discord_start,
    ("POST", "/api/discord/confirm"): _handle_discord_confirm,
    ("DELETE", "/api/discord/disconnect"): _handle_discord_disconnect,
    ("GET", "/api/discord/status"): _handle_discord_status,
    ("POST", "/api/stripe/checkout"): _handle_stripe_checkout,
    ("GET", "/api/stripe/subscription"): _handle_stripe_subscription,
    ("POST", "/api/stripe/portal"): _handle_stripe_portal,
}


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------


def main(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler function with event source detection and routing.

    Detects the event source and dispatches accordingly:
    - SQS records → handle_sqs_event
    - EventBridge scheduler → handle_reconciliation
    - HTTP API Gateway → dictionary-based route matching

    Args:
        event: Lambda event (SQS, EventBridge, or API Gateway HTTP API).
        context: Lambda context object (not used).

    Returns:
        dict: Response in API Gateway format for HTTP events, or processing
        result for SQS/EventBridge events.
    """
    try:
        # -----------------------------------------------------------------
        # 1. Event source detection
        # -----------------------------------------------------------------

        # SQS event source
        if "Records" in event:
            from handlers.sync_handlers import handle_sqs_event

            return handle_sqs_event(event)

        # EventBridge Scheduler event
        if (
            event.get("source") == "scheduler"
            or event.get("action") == "reconciliation"
        ):
            from handlers.sync_handlers import handle_reconciliation

            return handle_reconciliation(event)

        # -----------------------------------------------------------------
        # 2. HTTP routing
        # -----------------------------------------------------------------
        method = event.get("requestContext", {}).get("http", {}).get("method", "")
        path = event.get("requestContext", {}).get("http", {}).get("path", "")

        # Log incoming request for debugging
        logger.info("Incoming request: method=%s, path=%s", method, path)

        # -----------------------------------------------------------------
        # 3. OPTIONS preflight
        # -----------------------------------------------------------------
        if method == "OPTIONS":
            return _cors_preflight_response()

        # -----------------------------------------------------------------
        # 4. Route matching
        # -----------------------------------------------------------------

        # 4a. Public routes (no auth)
        handler = _PUBLIC_ROUTES.get((method, path))
        if handler:
            return handler(event)

        # 4b. Special auth routes (own auth mechanism)
        handler = _SPECIAL_AUTH_ROUTES.get((method, path))
        if handler:
            return handler(event)

        # 4c. Authenticated routes (require JWT)
        handler = _AUTHENTICATED_ROUTES.get((method, path))
        if handler:
            user, err = require_auth(event)
            if err:
                return err
            return handler(event, user)

        # 4d. Admin routes (require JWT + admin)
        if path.startswith("/admin/"):
            user, err = require_admin(event)
            if err:
                return err

            for pattern, expected_method, handler_name in _ADMIN_ROUTE_PATTERNS:
                if method != expected_method:
                    continue
                match = pattern.match(path)
                if match:
                    target_user_id = match.group(1)
                    dispatch_fn = _ADMIN_DISPATCH[handler_name]
                    return dispatch_fn(event, user, target_user_id)

            # Admin path but no matching route
            return error_response(404, "Not found")

        # -----------------------------------------------------------------
        # 5. Unknown route
        # -----------------------------------------------------------------
        return error_response(404, "Not found")

    except Exception as e:
        # Global exception handler — never expose internal details
        logger.error(
            "Unhandled exception: %s: %s", type(e).__name__, str(e), exc_info=True
        )
        return error_response(500, "Internal server error")
