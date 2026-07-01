"""Stripe service: product catalog, checkout, webhook, portal, subscription.

Provides Stripe integration for the DSB membership system including:
- Product catalog with in-memory caching (5-minute TTL)
- Checkout session creation for subscription purchases
- Webhook event handling
- Customer portal session creation
- Subscription status retrieval

Validates: Requirements 1.1, 1.2, 1.4–1.7, 1.12, 22.2
"""

import time
import logging
from datetime import datetime, timezone

import stripe

from config.settings import STRIPE_SECRET_NAME, STRIPE_WEBHOOK_SECRET_NAME, FRONTEND_URL
from models.membership import MembershipRecord
from services import membership_db
from services.secrets import get_secret

logger = logging.getLogger(__name__)

# Module-level cache for products
_products_cache = {
    "data": None,
    "timestamp": 0,
}
_CACHE_TTL = 300  # 5 minutes


def _get_stripe_key() -> str:
    """Get the Stripe secret key from Secrets Manager."""
    secret_data = get_secret(STRIPE_SECRET_NAME)
    return secret_data.get("secret_key")


def get_products() -> list[dict]:
    """Fetch active Stripe products with dsb_tier metadata and their prices.

    Returns cached data if within 5-minute TTL. On Stripe API failure,
    returns cached data if available, otherwise raises.

    Returns:
        List of product dicts with keys:
            - id: Stripe product ID
            - name: Product name
            - description: Product description (empty string if None)
            - price: Unit amount in cents
            - currency: Three-letter currency code
            - interval: Recurring interval (e.g. "month") or None for one-time
            - dsb_tier: The DSB membership tier from product metadata
            - price_id: Stripe price ID

    Raises:
        Exception: If Stripe API fails and no cached data is available.
    """
    now = time.time()

    # Return cached data if within TTL
    if (
        _products_cache["data"] is not None
        and (now - _products_cache["timestamp"]) < _CACHE_TTL
    ):
        return _products_cache["data"]

    try:
        stripe.api_key = _get_stripe_key()

        # Fetch active products
        products = stripe.Product.list(active=True)

        # Filter to only products with dsb_tier metadata
        dsb_products = []
        for product in products.data:
            dsb_tier = product.metadata.get("dsb_tier")
            if not dsb_tier:
                continue

            # Fetch active prices for each product
            prices = stripe.Price.list(product=product.id, active=True)
            for price in prices.data:
                dsb_products.append(
                    {
                        "id": product.id,
                        "name": product.name,
                        "description": product.description or "",
                        "price": price.unit_amount,  # in cents
                        "currency": price.currency,
                        "interval": (
                            price.recurring.interval if price.recurring else None
                        ),
                        "dsb_tier": dsb_tier,
                        "price_id": price.id,
                    }
                )

        # Update cache
        _products_cache["data"] = dsb_products
        _products_cache["timestamp"] = now

        return dsb_products

    except Exception as e:
        logger.error(f"Failed to fetch Stripe products: {e}")
        # Return cached data if available
        if _products_cache["data"] is not None:
            logger.info("Returning stale cached products data")
            return _products_cache["data"]
        raise


def create_checkout_session(user_id: str, price_id: str) -> dict:
    """Create a Stripe Checkout Session for subscription purchase.

    Validates that the user does not already have an active subscription,
    resolves or creates a Stripe Customer, then creates a Checkout Session
    in subscription mode.

    Args:
        user_id: Authenticated DSB user ID.
        price_id: Stripe Price ID to subscribe to.

    Returns:
        dict with key:
            - checkout_url: URL to redirect user to Stripe Checkout

    Raises:
        ValueError: If user already has an active subscription.
        Exception: On Stripe API failure.

    Validates: Requirements 1.4–1.7, 1.12, 18.10
    """
    stripe.api_key = _get_stripe_key()

    # Load user's membership record
    membership_item = membership_db.get_membership(user_id)

    # Check if user already has active subscription
    if membership_item:
        status = membership_item.get("subscription_status", {}).get("S")
        if status in ("active", "past_due"):
            raise ValueError("User already has an active subscription")

    # Get or create Stripe Customer
    stripe_customer_id = None
    if membership_item:
        stripe_customer_id = membership_item.get("stripe_customer_id", {}).get("S")

    if not stripe_customer_id:
        # Create new Stripe Customer
        customer = stripe.Customer.create(metadata={"dsb_user_id": user_id})
        stripe_customer_id = customer.id

        # Store on membership record
        record = MembershipRecord(
            user_id=user_id,
            stripe_customer_id=stripe_customer_id,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        if membership_item:
            # Preserve existing tier when updating
            record.membership_tier = membership_item.get("membership_tier", {}).get(
                "S", "FREE"
            )
        membership_db.put_membership(record.to_dynamo_item())

    # Create Checkout Session
    session = stripe.checkout.Session.create(
        customer=stripe_customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{FRONTEND_URL}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/pricing",
        metadata={"dsb_user_id": user_id},
    )

    return {"checkout_url": session.url}


def get_subscription_status(user_id: str) -> dict:
    """Get the user's current subscription status.

    Loads the MEMBERSHIP record from DynamoDB and returns the relevant
    subscription fields. If no membership record exists (new/FREE user),
    returns tier=FREE with null subscription fields.

    Args:
        user_id: Authenticated DSB user ID.

    Returns:
        dict with keys:
            - membership_tier: str (FREE, EXPLORER, BUILDER, BUILDER_ACADEMY)
            - subscription_status: str | None (active, past_due, canceled, incomplete)
            - current_period_end: str | None (ISO 8601 timestamp)
            - stripe_subscription_id: str | None

    Validates: Requirements 3.1, 3.5, 3.6
    """
    membership_item = membership_db.get_membership(user_id)

    if not membership_item:
        return {
            "membership_tier": "FREE",
            "subscription_status": None,
            "current_period_end": None,
            "stripe_subscription_id": None,
        }

    return {
        "membership_tier": membership_item.get("membership_tier", {}).get("S", "FREE"),
        "subscription_status": membership_item.get("subscription_status", {}).get("S"),
        "current_period_end": membership_item.get("current_period_end", {}).get("S"),
        "stripe_subscription_id": membership_item.get("stripe_subscription_id", {}).get(
            "S"
        ),
    }


def handle_get_subscription(event: dict, user: dict) -> dict:
    """Handler for GET /api/stripe/subscription endpoint.

    Requires authentication. Returns the authenticated user's subscription status.

    Args:
        event: API Gateway HTTP API event dict.
        user: Authenticated user payload from auth middleware (contains 'sub' claim).

    Returns:
        API Gateway response with subscription status body.

    Validates: Requirements 3.1, 3.5, 3.6
    """
    from utils.responses import json_response, error_response

    user_id = user.get("sub")
    if not user_id:
        return error_response(401, "Authentication required")

    try:
        status = get_subscription_status(user_id)
        return json_response(200, status)
    except Exception as e:
        logger.error("Failed to get subscription status for user %s: %s", user_id, e)
        return error_response(500, "Failed to retrieve subscription status")


# ---------------------------------------------------------------------------
# Webhook Processing
# ---------------------------------------------------------------------------


def handle_webhook(body: str, signature_header: str) -> dict:
    """Process a Stripe webhook event.

    Verifies webhook signature, checks idempotency, dispatches to the
    appropriate event handler, marks the event processed, and publishes
    sync events on tier changes.

    Args:
        body: Raw request body string (must not be parsed/modified).
        signature_header: Stripe-Signature header value.

    Returns:
        dict with keys:
            - processed: bool — True if event was handled, False if skipped
            - event_id: str — The Stripe event ID
            - reason: str (optional) — Why the event was skipped

    Raises:
        ValueError: If webhook signature verification fails. The caller
            should return HTTP 400 in this case.

    Validates: Requirements 2.1–2.11, 18.9, 19.10
    """
    # Retrieve webhook signing secret
    webhook_secret = get_secret(STRIPE_WEBHOOK_SECRET_NAME).get("secret_key")

    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(body, signature_header, webhook_secret)
    except stripe.error.SignatureVerificationError:
        logger.warning("Stripe webhook signature verification failed")
        raise ValueError("Invalid webhook signature")

    event_id = event["id"]
    event_type = event["type"]

    logger.info("Processing Stripe webhook: event_id=%s, type=%s", event_id, event_type)

    # Idempotency check — skip if already processed
    if membership_db.check_stripe_event_processed(event_id):
        logger.info("Stripe event %s already processed, skipping", event_id)
        return {"processed": False, "event_id": event_id, "reason": "duplicate"}

    # Dispatch to event-specific handler
    tier_changed = False

    if event_type == "checkout.session.completed":
        tier_changed = _handle_checkout_completed(event)
    elif event_type == "customer.subscription.updated":
        tier_changed = _handle_subscription_updated(event)
    elif event_type == "customer.subscription.deleted":
        tier_changed = _handle_subscription_deleted(event)
    elif event_type == "invoice.payment_failed":
        _handle_payment_failed(event)
    else:
        logger.info("Ignoring unhandled Stripe event type: %s", event_type)

    # Mark event as processed with 7-day TTL
    membership_db.mark_stripe_event_processed(event_id)

    return {"processed": True, "event_id": event_id}


# ---------------------------------------------------------------------------
# Webhook Event Handlers (private)
# ---------------------------------------------------------------------------


def _handle_checkout_completed(event: dict) -> bool:
    """Handle checkout.session.completed — new subscription created.

    Resolves user via GSI2 (stripe_customer_id), extracts dsb_tier from
    product metadata, updates MEMBERSHIP tier, writes audit, and publishes
    sync event.

    Returns True if tier changed.
    """
    from services.audit import write_audit_log
    from services.sqs_publisher import publish_sync_event
    from models.audit_event import AuditEvent, AuditEventType

    session = event["data"]["object"]

    # Only process subscription-mode checkout sessions
    if session.get("mode") != "subscription":
        logger.info("Ignoring non-subscription checkout session")
        return False

    customer_id = session.get("customer")
    subscription_id = session.get("subscription")

    # Resolve user via GSI2
    user_item = membership_db.resolve_stripe_customer(customer_id)
    if not user_item:
        logger.error("Cannot resolve Stripe customer %s to DSB user", customer_id)
        return False

    user_id = _extract_user_id(user_item)
    if not user_id:
        logger.error("Cannot extract user_id for customer %s", customer_id)
        return False

    # Retrieve subscription to extract product metadata
    stripe.api_key = _get_stripe_key()
    subscription = stripe.Subscription.retrieve(
        subscription_id, expand=["items.data.price.product"]
    )

    # Extract dsb_tier from product metadata
    dsb_tier = _extract_tier_from_subscription(subscription)

    # Update membership record
    record = MembershipRecord(
        user_id=user_id,
        membership_tier=dsb_tier,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        subscription_status=subscription.get("status", "active"),
        current_period_end=_timestamp_to_iso(subscription.get("current_period_end")),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    membership_db.put_membership(record.to_dynamo_item())

    # Write audit log
    write_audit_log(
        AuditEvent.build(AuditEventType.SUBSCRIPTION_CREATED, user_id, "stripe")
        .with_stripe(subscription_id=subscription_id, event_id=event["id"])
        .with_state_change("FREE", dsb_tier)
    )

    # Publish sync event for Discord role sync
    publish_sync_event(user_id, "tier_change", dsb_tier)

    logger.info(
        "checkout.session.completed: user=%s tier=%s subscription=%s",
        user_id,
        dsb_tier,
        subscription_id,
    )
    return True


def _handle_subscription_updated(event: dict) -> bool:
    """Handle customer.subscription.updated — plan change or status change.

    Updates tier, subscription_status, and current_period_end. Publishes
    sync event only if tier actually changed.

    Returns True if tier changed.
    """
    from services.audit import write_audit_log
    from services.sqs_publisher import publish_sync_event
    from models.audit_event import AuditEvent, AuditEventType

    subscription = event["data"]["object"]
    customer_id = subscription.get("customer")
    subscription_id = subscription.get("id")

    # Resolve user via GSI2
    user_item = membership_db.resolve_stripe_customer(customer_id)
    if not user_item:
        logger.error("Cannot resolve customer %s for subscription.updated", customer_id)
        return False

    user_id = _extract_user_id(user_item)
    if not user_id:
        return False

    # Get current tier from membership record
    current_item = membership_db.get_membership(user_id)
    previous_tier = (
        current_item.get("membership_tier", {}).get("S", "FREE")
        if current_item
        else "FREE"
    )

    # Extract new tier from subscription product metadata
    stripe.api_key = _get_stripe_key()
    dsb_tier = previous_tier  # Default to current if cannot determine

    for item in subscription.get("items", {}).get("data", []):
        price = item.get("price", {})
        product_id = price.get("product")
        if product_id:
            product = stripe.Product.retrieve(product_id)
            tier = product.get("metadata", {}).get("dsb_tier")
            if tier:
                dsb_tier = tier
                break

    # Update membership record
    record = MembershipRecord(
        user_id=user_id,
        membership_tier=dsb_tier,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        subscription_status=subscription.get("status"),
        current_period_end=_timestamp_to_iso(subscription.get("current_period_end")),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    membership_db.put_membership(record.to_dynamo_item())

    # Write audit log
    write_audit_log(
        AuditEvent.build(AuditEventType.SUBSCRIPTION_UPDATED, user_id, "stripe")
        .with_stripe(subscription_id=subscription_id, event_id=event["id"])
        .with_state_change(previous_tier, dsb_tier)
    )

    # Publish sync event only if tier actually changed
    if dsb_tier != previous_tier:
        publish_sync_event(user_id, "tier_change", dsb_tier)
        logger.info(
            "subscription.updated: user=%s tier %s→%s",
            user_id,
            previous_tier,
            dsb_tier,
        )
        return True

    logger.info(
        "subscription.updated: user=%s tier unchanged (%s), status=%s",
        user_id,
        dsb_tier,
        subscription.get("status"),
    )
    return False


def _handle_subscription_deleted(event: dict) -> bool:
    """Handle customer.subscription.deleted — subscription ended.

    Downgrades user to FREE, clears subscription fields, writes audit,
    and publishes sync event.

    Returns True (tier always changes from paid to FREE).
    """
    from services.audit import write_audit_log
    from services.sqs_publisher import publish_sync_event
    from models.audit_event import AuditEvent, AuditEventType

    subscription = event["data"]["object"]
    customer_id = subscription.get("customer")
    subscription_id = subscription.get("id")

    # Resolve user via GSI2
    user_item = membership_db.resolve_stripe_customer(customer_id)
    if not user_item:
        logger.error("Cannot resolve customer %s for subscription.deleted", customer_id)
        return False

    user_id = _extract_user_id(user_item)
    if not user_id:
        return False

    # Get previous tier
    current_item = membership_db.get_membership(user_id)
    previous_tier = (
        current_item.get("membership_tier", {}).get("S", "FREE")
        if current_item
        else "FREE"
    )

    # Downgrade to FREE, clear subscription fields
    record = MembershipRecord(
        user_id=user_id,
        membership_tier="FREE",
        stripe_customer_id=customer_id,
        # subscription_id, subscription_status, current_period_end intentionally
        # omitted (None) so they are not written to DynamoDB, effectively clearing them
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    membership_db.put_membership(record.to_dynamo_item())

    # Write audit log
    write_audit_log(
        AuditEvent.build(AuditEventType.SUBSCRIPTION_ENDED, user_id, "stripe")
        .with_stripe(subscription_id=subscription_id, event_id=event["id"])
        .with_state_change(previous_tier, "FREE")
    )

    # Publish sync event
    publish_sync_event(user_id, "tier_change", "FREE")

    logger.info(
        "subscription.deleted: user=%s downgraded %s→FREE", user_id, previous_tier
    )
    return True


def _handle_payment_failed(event: dict) -> None:
    """Handle invoice.payment_failed — audit only, no tier change.

    Records the payment failure in the audit log but does not modify
    the user's membership tier. Stripe's dunning process handles retries
    and ultimately fires subscription.deleted if unresolved.
    """
    from services.audit import write_audit_log
    from models.audit_event import AuditEvent, AuditEventType

    invoice = event["data"]["object"]
    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")

    # Resolve user via GSI2
    user_item = membership_db.resolve_stripe_customer(customer_id)
    if not user_item:
        logger.warning(
            "Cannot resolve customer %s for payment_failed event", customer_id
        )
        return

    user_id = _extract_user_id(user_item)
    if not user_id:
        return

    # Write audit log only — no tier change
    write_audit_log(
        AuditEvent.build(AuditEventType.PAYMENT_FAILED, user_id, "stripe").with_stripe(
            subscription_id=subscription_id, event_id=event["id"]
        )
    )

    logger.info(
        "invoice.payment_failed: user=%s subscription=%s", user_id, subscription_id
    )


# ---------------------------------------------------------------------------
# Webhook Utility Helpers (private)
# ---------------------------------------------------------------------------


def _extract_user_id(dynamo_item: dict) -> str | None:
    """Extract user_id from a DynamoDB item returned by GSI2 query.

    Tries the user_id attribute first, then falls back to parsing PK.
    """
    # Direct user_id attribute
    user_id = dynamo_item.get("user_id", {}).get("S")
    if user_id:
        return user_id

    # Fallback: extract from PK (USER#{user_id})
    pk = dynamo_item.get("PK", {}).get("S", "")
    if pk.startswith("USER#"):
        return pk[5:]

    return None


def _extract_tier_from_subscription(subscription: dict) -> str:
    """Extract dsb_tier from a Stripe subscription's product metadata.

    Iterates through subscription items and returns the first dsb_tier
    found in product metadata. Defaults to FREE if not found.
    """
    for item in subscription.get("items", {}).get("data", []):
        product = item.get("price", {}).get("product")
        if product is None:
            continue
        # Product may be expanded (dict) or just an ID (str)
        if isinstance(product, str):
            product = stripe.Product.retrieve(product)
        metadata = product.get("metadata", {}) if isinstance(product, dict) else {}
        tier = metadata.get("dsb_tier")
        if tier:
            return tier

    return "FREE"


def _timestamp_to_iso(unix_timestamp: int | None) -> str | None:
    """Convert a Unix timestamp to ISO 8601 format, or return None."""
    if unix_timestamp is None:
        return None
    return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Webhook Route Handler
# ---------------------------------------------------------------------------


def create_portal_session(user_id: str) -> dict:
    """Create a Stripe Billing Portal session for subscription management.

    Allows user to cancel subscription, update payment method, and view invoices.

    Args:
        user_id: Authenticated DSB user ID.

    Returns:
        dict with key:
            - portal_url: URL to redirect user to Stripe Customer Portal

    Raises:
        ValueError: If user has no stripe_customer_id (never purchased).
        Exception: On Stripe API failure.

    Validates: Requirements 3.2, 3.3, 3.4, 3.7
    """
    stripe.api_key = _get_stripe_key()

    # Load MEMBERSHIP record
    membership_item = membership_db.get_membership(user_id)

    # Get stripe_customer_id
    stripe_customer_id = None
    if membership_item:
        stripe_customer_id = membership_item.get("stripe_customer_id", {}).get("S")

    if not stripe_customer_id:
        raise ValueError("No subscription found. Visit the pricing page to subscribe.")

    # Create Billing Portal session
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{FRONTEND_URL}/settings/subscription",
    )

    return {"portal_url": session.url}


def handle_stripe_webhook(event: dict) -> dict:
    """Lambda route handler for POST /api/stripe/webhook.

    No auth middleware — signature verification provides authentication.
    Extracts raw body and Stripe-Signature header, delegates to handle_webhook.

    Args:
        event: API Gateway HTTP API event dict.

    Returns:
        API Gateway response dict (200 on success, 400 on signature failure).

    Validates: Requirements 2.1, 2.9, 19.10
    """
    from utils.responses import json_response, error_response

    body = event.get("body", "")
    headers = event.get("headers", {})

    # Stripe-Signature header (API Gateway lowercases header names)
    signature_header = headers.get("stripe-signature", "")
    if not signature_header:
        return error_response(400, "Missing Stripe-Signature header")

    try:
        result = handle_webhook(body, signature_header)
        return json_response(200, result)
    except ValueError:
        # Signature verification failed
        return error_response(400, "Invalid webhook signature")
    except Exception as e:
        logger.error("Stripe webhook processing error: %s", e, exc_info=True)
        # Return 200 to Stripe even on processing errors to avoid retries
        # for issues we can't fix by retrying (bad data, etc.)
        # Only signature failures get 400.
        return json_response(200, {"processed": False, "error": "processing_error"})
