"""HTTP handler functions for Stripe-related API routes.

These handlers are called from the main Lambda handler (handler.py) after
routing. They handle auth, parse request bodies, call service functions,
and return properly formatted API Gateway responses.

Validates: Requirements 1.4–1.7, 1.12, 3.2, 3.3, 3.4, 3.7, 18.10
"""

import json
import logging

from auth.auth_middleware import require_auth
from services.stripe_service import create_checkout_session, create_portal_session
from utils.responses import json_response, error_response

logger = logging.getLogger(__name__)


def handle_stripe_checkout(event: dict) -> dict:
    """Handle POST /api/stripe/checkout — authenticated.

    Parses price_id from request body, validates auth, and creates
    a Stripe Checkout Session for subscription purchase.

    Args:
        event: API Gateway HTTP API event dict.

    Returns:
        API Gateway response with {checkout_url} on success,
        or appropriate error response.
    """
    # Validate authentication
    user, err = require_auth(event)
    if err:
        return err

    user_id = user.get("sub")
    if not user_id:
        return error_response(401, "Authentication required")

    # Parse request body
    body = event.get("body", "")
    if not body:
        return error_response(400, "Request body is required")

    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return error_response(400, "Invalid JSON body")

    price_id = payload.get("price_id")
    if not price_id:
        return error_response(400, "price_id is required")

    # Validate price_id format (Stripe price IDs start with "price_")
    if not isinstance(price_id, str) or not price_id.startswith("price_"):
        return error_response(400, "Invalid price_id format")

    # Create checkout session
    try:
        result = create_checkout_session(user_id, price_id)
        return json_response(200, result)
    except ValueError as e:
        # User already has active subscription
        return error_response(400, str(e))
    except Exception as e:
        logger.error("Failed to create checkout session for user %s: %s", user_id, e)
        return error_response(500, "Failed to create checkout session")


def handle_stripe_portal(event: dict) -> dict:
    """Handle POST /api/stripe/portal — authenticated.

    Creates a Stripe Customer Portal session so the user can manage their
    subscription (cancel, update payment method, view invoices).

    Args:
        event: API Gateway HTTP API event dict.

    Returns:
        API Gateway response with {portal_url} on success,
        or appropriate error response.

    Validates: Requirements 3.2, 3.3, 3.4, 3.7
    """
    # Validate authentication
    user, err = require_auth(event)
    if err:
        return err

    user_id = user.get("sub")
    if not user_id:
        return error_response(401, "Authentication required")

    try:
        result = create_portal_session(user_id)
        return json_response(200, result)
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        logger.error("Failed to create portal session for user %s: %s", user_id, e)
        return error_response(500, "Failed to create portal session")
