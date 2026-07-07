"""Stripe router — /api/stripe/* routes.

Ports all Stripe-related routes from the membership Lambda handler:
- POST /api/stripe/checkout — Create checkout session (authenticated)
- GET /api/stripe/subscription — Get subscription status (authenticated)
- POST /api/stripe/portal — Create customer portal session (authenticated)
- GET /api/stripe/products — List available products (public, no auth)
- POST /api/stripe/webhook — Process Stripe webhook (signature-verified, no JWT)

Authentication:
- checkout, subscription, portal: require JWT via Depends(get_current_user)
- products: public endpoint, no auth required
- webhook: uses Stripe signature verification instead of JWT

Requirements: 4.3, 5.1
"""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth.jwt import get_current_user
from app.background.discord_tasks import enqueue_discord_sync
from app.config import Settings
from app.dependencies import get_settings
from app.services.stripe_service import StripeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stripe", tags=["stripe"])


# ------------------------------------------------------------------
# Request models
# ------------------------------------------------------------------


class CheckoutRequest(BaseModel):
    """Request body for POST /api/stripe/checkout."""

    price_id: str = Field(..., min_length=1)


# ------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------


def get_stripe_service(settings: Settings = Depends(get_settings)) -> StripeService:
    """Provide a StripeService instance."""
    return StripeService(settings)


# ------------------------------------------------------------------
# Public routes (no auth required)
# ------------------------------------------------------------------


@router.get("/products")
async def get_products(
    service: StripeService = Depends(get_stripe_service),
) -> dict[str, Any]:
    """Get available Stripe products with pricing.

    Public endpoint — no authentication required.
    Returns products that have dsb_tier metadata configured.
    """
    try:
        products = service.get_products()
        return {"products": products}
    except Exception as e:
        logger.error("Failed to fetch products: %s", type(e).__name__)
        raise HTTPException(status_code=500, detail="Failed to fetch products")


# ------------------------------------------------------------------
# Authenticated routes (require JWT)
# ------------------------------------------------------------------


@router.post("/checkout")
async def create_checkout(
    body: CheckoutRequest,
    user: dict = Depends(get_current_user),
    service: StripeService = Depends(get_stripe_service),
) -> dict[str, str]:
    """Create a Stripe Checkout Session for subscription purchase.

    Requires authentication. Validates price_id format, checks that the
    user does not already have an active subscription, then creates the
    checkout session.
    """
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Validate price_id format (Stripe price IDs start with "price_")
    if not body.price_id.startswith("price_"):
        raise HTTPException(status_code=400, detail="Invalid price_id format")

    try:
        result = service.create_checkout_session(user_id, body.price_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create checkout session for user %s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.get("/subscription")
async def get_subscription(
    user: dict = Depends(get_current_user),
    service: StripeService = Depends(get_stripe_service),
) -> dict[str, Any]:
    """Get the authenticated user's subscription status.

    Returns membership tier, subscription status, period end, and
    subscription ID.
    """
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        status = service.get_subscription_status(user_id)
        return status
    except Exception as e:
        logger.error("Failed to get subscription status for user %s: %s", user_id, e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve subscription status"
        )


@router.post("/portal")
async def create_portal(
    user: dict = Depends(get_current_user),
    service: StripeService = Depends(get_stripe_service),
) -> dict[str, str]:
    """Create a Stripe Customer Portal session.

    Allows the user to manage their subscription (cancel, update payment
    method, view invoices).
    """
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        result = service.create_portal_session(user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create portal session for user %s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="Failed to create portal session")


# ------------------------------------------------------------------
# Webhook route (signature-verified, no JWT auth)
# ------------------------------------------------------------------


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    service: StripeService = Depends(get_stripe_service),
) -> dict[str, Any]:
    """Process Stripe webhook events.

    No JWT authentication — uses Stripe signature verification instead.
    The raw body is read directly from the request to preserve the exact
    bytes needed for signature verification.

    When the webhook indicates a membership tier change, a Discord role
    sync is enqueued as a background task (replacing the previous SQS
    publish pattern).

    Returns 200 even on processing errors (to avoid Stripe retries for
    non-recoverable issues). Only returns 400 for signature failures.
    """
    # Read raw body for signature verification
    body = (await request.body()).decode("utf-8")

    # Get Stripe-Signature header
    signature_header = request.headers.get("stripe-signature", "")
    if not signature_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        result = service.verify_and_process_webhook(body, signature_header)

        # Trigger Discord sync if the webhook was processed and involves a user.
        # The underlying handle_webhook resolves the user_id and returns it
        # when a tier change occurred. We enqueue a background sync to replace
        # the old SQS publish_sync_event call.
        if result.get("processed") and result.get("user_id"):
            enqueue_discord_sync(
                background_tasks,
                user_id=result["user_id"],
                operation="tier_change",
                reason="Stripe webhook event",
            )

        return result
    except ValueError:
        # Signature verification failed
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    except Exception as e:
        logger.error("Stripe webhook processing error: %s", e, exc_info=True)
        # Return 200 to Stripe even on processing errors to avoid retries
        # for issues we can't fix by retrying (bad data, etc.)
        return {"processed": False, "error": "processing_error"}
