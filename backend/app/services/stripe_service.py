"""Stripe service: product catalog, checkout, webhook, portal, subscription.

Encapsulates all Stripe API interactions for the DSB Platform. Ported from
the Lambda-based service (backend/membership/services/stripe_service.py).

Provides:
- Product catalog with in-memory caching (5-minute TTL)
- Checkout session creation for subscription purchases
- Webhook event verification and dispatch
- Customer portal session creation
- Subscription status retrieval

Uses the centralized Settings for secret names and URLs rather than
module-level config imports.

Requirements: 4.3
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

import boto3
import stripe
from botocore.exceptions import ClientError

from app.config import Settings
from app.services.builder_activation import record_builder_activation
from app.services.email import (
    send_payment_failed_email,
    send_subscription_expired_email,
    send_subscription_welcome_email,
)
from app.services.progress_db import ProgressDB
from app.tiers import STUDENT_BUILDER, is_builder_equivalent

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Student Builder checkout errors
# ----------------------------------------------------------------------
#
# Distinct ValueError subclasses so the router (task 15) can map each failure
# mode to the correct HTTP status without parsing messages:
#   - StudentEligibilityError  -> 403 (user not active-eligible)
#   - DuplicateSubscriptionError -> 400 (active/past_due subscription exists)
#   - InvalidPriceSelectionError -> 400 (client price_id != resolved price_id)
#   - EligibilityReadError       -> 503 (eligibility/membership read failure)
# The Fail_Closed ValueError raised by get_student_builder_product() /
# select_price_for_interval() (no matching / ambiguous price) propagates as a
# plain ValueError the router maps to 400.


class StudentCheckoutError(ValueError):
    """Base class for Student Builder checkout failures (Requirement 5)."""


class StudentEligibilityError(StudentCheckoutError):
    """The user does not hold active Student Builder eligibility.

    Raised before resolving a Stripe customer or creating a session
    (Requirements 5.1, 5.2). Maps to HTTP 403 at the router boundary.
    """


class DuplicateSubscriptionError(StudentCheckoutError):
    """The user already has an active or past_due subscription.

    Raised to prevent duplicate active memberships (Requirement 5.7). Maps to
    HTTP 400 at the router boundary.
    """


class InvalidPriceSelectionError(StudentCheckoutError):
    """The client-supplied price_id does not match the resolved price.

    Raised when a client substitutes an arbitrary product/price identifier
    (Requirement 5.5). Maps to HTTP 400 at the router boundary.
    """


class EligibilityReadError(StudentCheckoutError):
    """The eligibility or membership record could not be retrieved.

    Raised so the request is rejected without creating a session and the
    membership state is left unchanged (Requirement 5.9). Maps to HTTP 503 at
    the router boundary.
    """


class StripeService:
    """Stripe operations for the DSB Platform.

    Accepts a Settings instance to resolve secret names, URLs, and table names.
    Creates its own boto3 client for Secrets Manager and DynamoDB access.
    """

    # Module-level cache for products (shared across instances)
    _products_cache: dict[str, Any] = {
        "data": None,
        "timestamp": 0.0,
    }
    _CACHE_TTL = 300  # 5 minutes

    # Cache for secrets (shared across instances)
    _secrets_cache: dict[str, Any] = {}
    _SECRETS_TTL = 900  # 15 minutes

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._secrets_client = boto3.client("secretsmanager")
        self._dynamodb_client = boto3.client("dynamodb")

    # ------------------------------------------------------------------
    # Secret retrieval (with caching)
    # ------------------------------------------------------------------

    def _get_secret(self, secret_name: str) -> dict[str, Any]:
        """Retrieve a secret from Secrets Manager with caching.

        Args:
            secret_name: The Secrets Manager secret ID/name.

        Returns:
            Parsed JSON secret data as a dict.
        """
        now = time.time()
        cached = self._secrets_cache.get(secret_name)
        if cached and (now - cached["fetched_at"]) < self._SECRETS_TTL:
            return cached["data"]

        try:
            response = self._secrets_client.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(response["SecretString"])
        except (ClientError, json.JSONDecodeError, KeyError) as exc:
            logger.error("Failed to retrieve secret %s: %s", secret_name, exc)
            raise

        self._secrets_cache[secret_name] = {
            "data": secret_data,
            "fetched_at": now,
        }
        return secret_data

    def _get_stripe_key(self) -> str:
        """Get the Stripe secret key from Secrets Manager."""
        secret_data = self._get_secret(self._settings.stripe_secret_name)
        return secret_data.get("secret_key", "")

    def _get_webhook_secret(self) -> str:
        """Get the Stripe webhook signing secret from Secrets Manager."""
        secret_data = self._get_secret(self._settings.stripe_webhook_secret_name)
        return secret_data.get("secret_key", "")

    # ------------------------------------------------------------------
    # Products (public, cached)
    # ------------------------------------------------------------------

    def get_products(self) -> list[dict[str, Any]]:
        """Fetch active Stripe products with dsb_tier metadata and their prices.

        Returns cached data if within 5-minute TTL. On Stripe API failure,
        returns cached data if available, otherwise raises.

        Returns:
            List of product dicts with keys: id, name, description, price,
            currency, interval, dsb_tier, price_id.
        """
        now = time.time()

        # Return cached data if within TTL
        if (
            self._products_cache["data"] is not None
            and (now - self._products_cache["timestamp"]) < self._CACHE_TTL
        ):
            return self._products_cache["data"]

        try:
            stripe.api_key = self._get_stripe_key()

            # Fetch active products
            products = stripe.Product.list(active=True)

            logger.info(
                "Stripe products fetched: count=%d, ids=%s",
                len(products.data),
                [p.id for p in products.data],
            )

            # Filter to only products with dsb_tier metadata
            dsb_products = []
            for product in products.data:
                # stripe-python v13+ returns metadata as a StripeObject, which
                # no longer supports dict-style .get(). Use membership + index
                # access, which works across SDK versions.
                dsb_tier = (
                    product.metadata["dsb_tier"]
                    if "dsb_tier" in product.metadata
                    else None
                )
                if not dsb_tier:
                    continue

                # Fetch active prices for each product
                prices = stripe.Price.list(product=product.id, active=True)
                for price in prices.data:
                    # stripe-python v13+ returns price.recurring as a
                    # StripeObject whose attribute access (.interval) can come
                    # back empty/None depending on access style. Read the
                    # interval/interval_count with the same StripeObject-safe
                    # membership + index pattern used for product.metadata
                    # above so a StripeObject returns the real "month"/"year"
                    # string instead of None.
                    recurring = price.recurring
                    if not recurring:
                        # Non-recurring (one-time) price: no billing interval.
                        # Exclude it as before — it is not a recurring price.
                        continue

                    interval = (
                        recurring["interval"] if "interval" in recurring else None
                    )
                    interval_count = (
                        recurring["interval_count"]
                        if "interval_count" in recurring
                        else 1
                    ) or 1

                    # If the interval could not be classified even after the
                    # defensive read, this is a recurring price we cannot label
                    # as a clean month/year row. Skip it rather than letting a
                    # None interval fall into the monthly branch below and
                    # mislabel the amount (that was the student-builder bug).
                    if interval is None:
                        logger.warning(
                            "Skipping price %s on product %s: recurring interval "
                            "could not be resolved",
                            price.id,
                            product.id,
                        )
                        continue

                    unit_amount = price.unit_amount or 0
                    # `price` is the price's own amount for its own interval.
                    # `monthly_price` is a derived convenience: for a yearly
                    # price it is the per-month equivalent, otherwise the amount
                    # itself. Only interval == "year" divides; a None interval
                    # can never reach here (skipped above).
                    monthly_price = (
                        round(unit_amount / 12) if interval == "year" else unit_amount
                    )

                    dsb_products.append(
                        {
                            "id": product.id,
                            "name": product.name,
                            "description": product.description or "",
                            "price": unit_amount,
                            "monthly_price": monthly_price,
                            "currency": price.currency,
                            "interval": interval,
                            "interval_count": interval_count,
                            "dsb_tier": dsb_tier,
                            "price_id": price.id,
                        }
                    )

            logger.info("Filtered products with dsb_tier: count=%d", len(dsb_products))

            # Update cache
            self._products_cache["data"] = dsb_products
            self._products_cache["timestamp"] = now

            return dsb_products

        except Exception as e:
            logger.error("Failed to fetch Stripe products: %s", e)
            # Return cached data if available
            if self._products_cache["data"] is not None:
                logger.info("Returning stale cached products data")
                return self._products_cache["data"]
            raise

    # ------------------------------------------------------------------
    # Student Builder product/price discovery (Fail_Closed)
    # ------------------------------------------------------------------

    def get_student_builder_product(self) -> list[dict[str, Any]]:
        """Resolve the unique active STUDENT_BUILDER product from the catalog.

        Reads ``get_products()`` (cache-first) and groups the returned rows by
        ``dsb_tier``. Because ``get_products()`` returns one row per active
        recurring price, a single Student Builder product with monthly and
        annual prices yields two rows that share the same product ``id``.

        Fail_Closed behaviour (Requirement 2.6, 2.7):
        - Raises ``ValueError`` if zero distinct STUDENT_BUILDER products are
          present, or if more than one distinct product id is present among the
          STUDENT_BUILDER rows.
        - Raises ``ValueError`` if the uniquely identified product has no active
          recurring price row.
        - Never selects a fallback product and never writes the result to any
          cache (the only cache is the one ``get_products()`` maintains).

        Returns:
            The list of price rows belonging to the single STUDENT_BUILDER
            product. Every returned row is an active recurring price.

        Raises:
            ValueError: When the Student Builder product cannot be uniquely
                identified or has no active recurring price.
        """
        products = self.get_products()

        # Group rows by dsb_tier, matching the canonical upper-cased value.
        student_rows = [
            row
            for row in products
            if (row.get("dsb_tier") or "").upper() == STUDENT_BUILDER
        ]

        if not student_rows:
            raise ValueError(
                "Student Builder product could not be uniquely identified: no "
                "active product carries dsb_tier=STUDENT_BUILDER."
            )

        # "More than one distinct product" means more than one distinct product
        # id among the STUDENT_BUILDER rows (not more than one price row).
        distinct_product_ids = {row.get("id") for row in student_rows}
        if len(distinct_product_ids) > 1:
            raise ValueError(
                "Student Builder product could not be uniquely identified: "
                f"{len(distinct_product_ids)} active products carry "
                "dsb_tier=STUDENT_BUILDER; expected exactly one."
            )

        # get_products() only emits rows for active recurring prices (it sets
        # interval from price.recurring.interval), so a row with a recurring
        # interval confirms an active recurring price exists.
        recurring_rows = [
            row for row in student_rows if row.get("interval") in ("month", "year")
        ]
        if not recurring_rows:
            raise ValueError(
                "No active recurring Student Builder price was found for the "
                "configured STUDENT_BUILDER product."
            )

        return recurring_rows

    def select_price_for_interval(
        self, rows: list[dict[str, Any]], interval: str
    ) -> dict[str, Any]:
        """Return the single active recurring price row matching ``interval``.

        Uses only the Stripe-reported ``interval`` on each row; it never applies
        a fallback. Fail_Closed (Requirement 2.3, 2.7): raises ``ValueError`` if
        no row matches the requested interval.

        Args:
            rows: Price rows for a single product (e.g. from
                ``get_student_builder_product()``).
            interval: The requested billing interval, ``'month'`` or ``'year'``.

        Returns:
            The single price row whose ``interval`` equals ``interval``.

        Raises:
            ValueError: If ``interval`` is not a supported value, or if no row
                matches the requested interval.
        """
        if interval not in ("month", "year"):
            raise ValueError(
                f"Unsupported billing interval '{interval}'; expected "
                "'month' or 'year'."
            )

        matching = [row for row in rows if row.get("interval") == interval]

        if not matching:
            raise ValueError(
                f"No active recurring Student Builder price found for interval "
                f"'{interval}'."
            )

        # A product should expose at most one active recurring price per
        # interval; if Stripe is misconfigured with duplicates, Fail_Closed
        # rather than silently picking one.
        if len(matching) > 1:
            raise ValueError(
                f"Multiple active recurring Student Builder prices found for "
                f"interval '{interval}'; expected exactly one."
            )

        return matching[0]

    # ------------------------------------------------------------------
    # Checkout session (authenticated)
    # ------------------------------------------------------------------

    def create_checkout_session(self, user_id: str, price_id: str) -> dict[str, str]:
        """Create a Stripe Checkout Session for subscription purchase.

        Validates that the user does not already have an active subscription,
        resolves or creates a Stripe Customer, then creates a Checkout Session
        in subscription mode.

        Args:
            user_id: Authenticated DSB user ID.
            price_id: Stripe Price ID to subscribe to.

        Returns:
            dict with key checkout_url.

        Raises:
            ValueError: If user already has an active subscription or
                price_id is invalid.
        """
        stripe.api_key = self._get_stripe_key()

        # Load user's membership record
        membership_item = self._get_membership(user_id)

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
            customer = stripe.Customer.create(metadata={"dsb_user_id": user_id})
            stripe_customer_id = customer.id

            # Store on membership record
            self._put_membership(
                user_id=user_id,
                stripe_customer_id=stripe_customer_id,
                membership_tier=(
                    membership_item.get("membership_tier", {}).get("S", "FREE")
                    if membership_item
                    else "FREE"
                ),
            )

        # Let Stripe Dashboard settings determine eligible payment methods.
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{self._settings.frontend_origin}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{self._settings.frontend_origin}/pricing",
            metadata={"dsb_user_id": user_id},
        )

        return {"checkout_url": session.url}

    # ------------------------------------------------------------------
    # Student Builder checkout (authenticated, eligibility-gated)
    # ------------------------------------------------------------------

    def create_student_checkout_session(
        self, user_id: str, price_id: str, interval: str
    ) -> dict[str, str]:
        """Create an eligibility-gated Student Builder Checkout Session.

        Mirrors ``create_checkout_session`` (customer resolve/create, session
        shape, success/cancel URLs) but adds the Student Builder eligibility
        gate and price-selection safeguards (Requirement 5).

        Order of operations (the eligibility check runs strictly BEFORE any
        Stripe call so a non-eligible user never touches Stripe — 5.1/5.2):

        1. Load eligibility + membership. A read failure on either leaves the
           membership state unchanged and raises :class:`EligibilityReadError`
           (router → 503, Requirement 5.9).
        2. If the user does not hold active eligibility, raise
           :class:`StudentEligibilityError` BEFORE resolving a Stripe customer
           or creating a session (router → 403, Requirements 5.1, 5.2).
        3. If the membership ``subscription_status`` is ``active`` or
           ``past_due``, raise :class:`DuplicateSubscriptionError`
           (router → 400, Requirement 5.7).
        4. Resolve the Student Builder price for ``interval`` from the cached
           catalog. A missing/ambiguous price fails closed via a plain
           ``ValueError`` from the catalog helpers (router → 400,
           Requirements 5.3, 5.4).
        5. If the client-supplied ``price_id`` does not exactly match the
           resolved price, raise :class:`InvalidPriceSelectionError`
           (router → 400, Requirement 5.5).
        6. Resolve-or-create the Stripe customer via the same path as
           ``create_checkout_session`` and create a subscription-mode Checkout
           Session carrying the eligibility snapshot in metadata
           (Requirements 5.6, 5.11).

        Args:
            user_id: Authenticated DSB user ID.
            price_id: Client-supplied Stripe Price ID (must match the resolved
                Student Builder price for ``interval``).
            interval: Requested billing interval, ``'month'`` or ``'year'``.

        Returns:
            dict with key ``checkout_url``.

        Raises:
            EligibilityReadError: Eligibility/membership read failure (→ 503).
            StudentEligibilityError: User is not active-eligible (→ 403).
            DuplicateSubscriptionError: Active/past_due subscription (→ 400).
            InvalidPriceSelectionError: price_id mismatch (→ 400).
            ValueError: No matching / ambiguous Student Builder price (→ 400).
        """
        # 1. Load eligibility + membership BEFORE any Stripe call. A read
        #    failure must leave membership state unchanged (Requirement 5.9).
        #    Import VerificationService lazily to avoid an import cycle
        #    (stripe_service <-> verification_service).
        from app.services.verification_service import VerificationService

        try:
            eligibility = VerificationService(self._settings).get_eligibility(user_id)
        except Exception as exc:  # noqa: BLE001 - normalize to a 503 signal
            logger.error(
                "Student checkout aborted: eligibility read failed for user %s: %s",
                user_id,
                exc,
            )
            raise EligibilityReadError(
                "Could not process the request; please try again later."
            ) from exc

        try:
            membership_item = self._get_membership(user_id)
        except Exception as exc:  # noqa: BLE001 - normalize to a 503 signal
            logger.error(
                "Student checkout aborted: membership read failed for user %s: %s",
                user_id,
                exc,
            )
            raise EligibilityReadError(
                "Could not process the request; please try again later."
            ) from exc

        # 2. Not active-eligible → reject BEFORE resolving a customer or
        #    creating a session (Requirements 5.1, 5.2). get_eligibility()
        #    already enforces the read-time expiry window, so None means the
        #    user is not currently eligible.
        if not eligibility:
            logger.info(
                "Student checkout rejected: user %s is not active-eligible", user_id
            )
            raise StudentEligibilityError(
                "You are not eligible for Student Builder. "
                "Please complete academic-email verification first."
            )

        # 3. Duplicate-membership guard (Requirement 5.7).
        if membership_item:
            status = membership_item.get("subscription_status", {}).get("S")
            if status in ("active", "past_due"):
                logger.info(
                    "Student checkout rejected: user %s already has a %s subscription",
                    user_id,
                    status,
                )
                raise DuplicateSubscriptionError(
                    "You already have an active subscription."
                )

        # 4. Resolve the Student Builder price for the requested interval from
        #    the cached catalog. Fail_Closed ValueError propagates (5.3, 5.4).
        rows = self.get_student_builder_product()
        resolved = self.select_price_for_interval(rows, interval)
        resolved_price_id = resolved["price_id"]

        # 5. Refuse arbitrary client-supplied price substitutions (5.5).
        if price_id != resolved_price_id:
            logger.info(
                "Student checkout rejected: price mismatch for user %s "
                "(supplied=%s, resolved=%s)",
                user_id,
                price_id,
                resolved_price_id,
            )
            raise InvalidPriceSelectionError(
                "The selected price is not valid for Student Builder."
            )

        # 6. Only now touch Stripe: resolve-or-create the customer using the
        #    same path as create_checkout_session, then create the session.
        stripe.api_key = self._get_stripe_key()

        stripe_customer_id = None
        if membership_item:
            stripe_customer_id = membership_item.get("stripe_customer_id", {}).get("S")

        if not stripe_customer_id:
            customer = stripe.Customer.create(metadata={"dsb_user_id": user_id})
            stripe_customer_id = customer.id

            # Persist the new customer id on the membership record.
            self._put_membership(
                user_id=user_id,
                stripe_customer_id=stripe_customer_id,
                membership_tier=(
                    membership_item.get("membership_tier", {}).get("S", "FREE")
                    if membership_item
                    else "FREE"
                ),
            )

        # Record the active-eligibility snapshot at session-creation time
        # (Requirement 5.11). Let Stripe Dashboard settings determine eligible
        # payment methods, matching create_checkout_session.
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            line_items=[{"price": resolved_price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{self._settings.frontend_origin}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{self._settings.frontend_origin}/pricing",
            metadata={
                "dsb_user_id": user_id,
                "dsb_tier": STUDENT_BUILDER,
                "eligibility_verified": "true",
                "eligibility_expires_at": eligibility.get("expires_at", ""),
            },
        )

        return {"checkout_url": session.url}

    # ------------------------------------------------------------------
    # Subscription status (authenticated)
    # ------------------------------------------------------------------

    def get_subscription_status(self, user_id: str) -> dict[str, Any]:
        """Get the user's current subscription status.

        Args:
            user_id: Authenticated DSB user ID.

        Returns:
            dict with keys: membership_tier, subscription_status,
            current_period_end, stripe_subscription_id, subscription_started_at.
        """
        membership_item = self._get_membership(user_id)

        if not membership_item:
            return {
                "membership_tier": "FREE",
                "subscription_status": None,
                "current_period_end": None,
                "stripe_subscription_id": None,
                "subscription_started_at": None,
            }

        return {
            "membership_tier": membership_item.get("membership_tier", {}).get(
                "S", "FREE"
            ),
            "subscription_status": membership_item.get("subscription_status", {}).get(
                "S"
            ),
            "current_period_end": membership_item.get("current_period_end", {}).get(
                "S"
            ),
            "stripe_subscription_id": membership_item.get(
                "stripe_subscription_id", {}
            ).get("S"),
            "subscription_started_at": membership_item.get(
                "subscription_started_at", {}
            ).get("S"),
        }

    # ------------------------------------------------------------------
    # Reconciliation against Stripe (source of truth)
    # ------------------------------------------------------------------

    def reconcile_subscription_from_stripe(self, user_id: str) -> dict[str, Any]:
        """Reconcile a user's DynamoDB membership tier against live Stripe state.

        Unlike webhook processing (which reacts to events), this actively pulls
        the user's current subscription from Stripe and writes the authoritative
        tier/status back to DynamoDB. Intended for admin-triggered syncs and
        recovery from missed webhooks.

        Behaviour:
        - No stripe_customer_id on file: user has never checked out. Left as-is
          (no Stripe truth to apply) and reported as "no_customer".
        - Customer has an active/trialing/past_due subscription: tier is derived
          from the subscription product's dsb_tier metadata and written to
          DynamoDB. First-time activation records the start date; otherwise the
          subscription state is updated.
        - Customer has no active subscription: tier is downgraded to FREE.

        Args:
            user_id: DSB user identifier.

        Returns:
            dict with keys: reconciled (bool), reason (str), and when reconciled,
            tier (str), status (str), changed (bool), previous_tier (str).
        """
        membership_item = self._get_membership(user_id)
        stripe_customer_id = None
        if membership_item:
            stripe_customer_id = membership_item.get("stripe_customer_id", {}).get("S")

        previous_tier = (
            membership_item.get("membership_tier", {}).get("S", "FREE")
            if membership_item
            else "FREE"
        )

        if not stripe_customer_id:
            logger.info(
                "Stripe reconcile skipped for user %s: no stripe_customer_id", user_id
            )
            return {"reconciled": False, "reason": "no_customer"}

        try:
            stripe.api_key = self._get_stripe_key()

            # Fetch the customer's most relevant subscription. We ask for all
            # statuses so we can distinguish "canceled" from "never subscribed".
            subscriptions = stripe.Subscription.list(
                customer=stripe_customer_id,
                status="all",
                limit=10,
            ).to_dict()
        except Exception as e:  # noqa: BLE001 - surface as failed reconcile
            logger.error(
                "Stripe reconcile failed to list subscriptions for user %s: %s",
                user_id,
                e,
            )
            return {"reconciled": False, "reason": "stripe_error"}

        # Statuses that grant an entitlement. Stripe considers "past_due" still
        # active until it is fully canceled/unpaid; keep parity with checkout.
        active_statuses = {"active", "trialing", "past_due"}
        sub_data = subscriptions.get("data", [])

        active_sub = next(
            (s for s in sub_data if s.get("status") in active_statuses), None
        )

        if active_sub is None:
            # No entitlement-granting subscription — ensure user is FREE.
            if previous_tier == "FREE":
                logger.info(
                    "Stripe reconcile: user %s already FREE, no change", user_id
                )
                return {
                    "reconciled": True,
                    "reason": "no_active_subscription",
                    "tier": "FREE",
                    "status": "canceled",
                    "changed": False,
                    "previous_tier": previous_tier,
                }
            # Downgrade to FREE, preserving the last known subscription id.
            sub_id = (
                membership_item.get("stripe_subscription_id", {}).get("S", "")
                if membership_item
                else ""
            )
            self._update_subscription_state(user_id, "FREE", sub_id, "canceled")
            logger.info(
                "Stripe reconcile: user %s downgraded %s -> FREE (no active sub)",
                user_id,
                previous_tier,
            )
            return {
                "reconciled": True,
                "reason": "downgraded_to_free",
                "tier": "FREE",
                "status": "canceled",
                "changed": True,
                "previous_tier": previous_tier,
            }

        # Entitlement-granting subscription found — derive tier and persist.
        tier = self._determine_tier_from_subscription(active_sub)
        status = active_sub.get("status", "active")
        sub_id = active_sub.get("id", "")
        current_period_end = self._extract_current_period_end(active_sub)

        if previous_tier == "FREE":
            # First-time activation from FREE — record start date and Builder
            # activation via the existing activation path.
            self._activate_subscription(
                user_id, tier, sub_id, status, current_period_end
            )
        else:
            self._update_subscription_state(
                user_id, tier, sub_id, status, current_period_end
            )

        changed = tier != previous_tier
        logger.info(
            "Stripe reconcile: user %s tier %s -> %s (status=%s, changed=%s)",
            user_id,
            previous_tier,
            tier,
            status,
            changed,
        )
        return {
            "reconciled": True,
            "reason": "synced_from_stripe",
            "tier": tier,
            "status": status,
            "changed": changed,
            "previous_tier": previous_tier,
        }

    # ------------------------------------------------------------------
    # Customer portal (authenticated)
    # ------------------------------------------------------------------

    def create_portal_session(self, user_id: str) -> dict[str, str]:
        """Create a Stripe Billing Portal session for subscription management.

        Args:
            user_id: Authenticated DSB user ID.

        Returns:
            dict with key portal_url.

        Raises:
            ValueError: If user has no stripe_customer_id.
        """
        stripe.api_key = self._get_stripe_key()

        membership_item = self._get_membership(user_id)

        stripe_customer_id = None
        if membership_item:
            stripe_customer_id = membership_item.get("stripe_customer_id", {}).get("S")

        if not stripe_customer_id:
            raise ValueError(
                "No subscription found. Visit the pricing page to subscribe."
            )

        frontend_origin = self._settings.frontend_origin
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=f"{frontend_origin}/settings/subscription",
        )

        return {"portal_url": session.url}

    # ------------------------------------------------------------------
    # Cancel-for-switch (immediate cancellation)
    # ------------------------------------------------------------------

    def cancel_subscription_for_switch(self, user_id: str) -> dict[str, str]:
        """Immediately cancel the user's subscription to allow a tier switch.

        Unlike an ordinary cancellation (which users perform through the Stripe
        Billing Portal and which cancels at period end), a switch cancellation
        cancels the Stripe subscription *immediately* (Requirements 6.5, 6.6).
        An immediate cancel makes Stripe emit ``customer.subscription.deleted``
        promptly; the existing webhook path handles the DynamoDB downgrade to
        ``FREE`` and clears ``subscription_status``. Once that status clears,
        the duplicate-membership guard in checkout no longer blocks the member
        from immediately subscribing to the other tier.

        This method only triggers the immediate cancel. It deliberately does
        NOT write the tier/status change itself — that is driven by the
        ``customer.subscription.deleted`` webhook to keep a single source of
        truth for downgrades.

        Args:
            user_id: Authenticated DSB user ID.

        Returns:
            dict with key ``status`` set to ``"canceled"``.

        Raises:
            ValueError: If the user has no active subscription to cancel.
        """
        membership_item = self._get_membership(user_id)

        subscription_id = None
        status = None
        if membership_item:
            subscription_id = membership_item.get("stripe_subscription_id", {}).get("S")
            status = membership_item.get("subscription_status", {}).get("S")

        if not subscription_id or status not in ("active", "past_due"):
            raise ValueError(
                "No active subscription to cancel. Visit the pricing page to "
                "subscribe."
            )

        stripe.api_key = self._get_stripe_key()

        # Immediate cancellation (NOT cancel_at_period_end). Stripe emits
        # customer.subscription.deleted promptly, and the existing webhook path
        # performs the downgrade to FREE / clears subscription_status.
        stripe.Subscription.cancel(subscription_id)

        return {"status": "canceled"}

    # ------------------------------------------------------------------
    # Webhook handling
    # ------------------------------------------------------------------

    def verify_and_process_webhook(
        self, body: str, signature_header: str
    ) -> dict[str, Any]:
        """Verify Stripe webhook signature and process the event.

        Handles webhook events directly:
        - checkout.session.completed: Activate subscription
        - customer.subscription.updated: Update tier
        - customer.subscription.deleted: Downgrade to FREE

        Args:
            body: Raw request body string.
            signature_header: Stripe-Signature header value.

        Returns:
            dict with keys: processed (bool), event_id (str),
            user_id (str, optional), and optionally reason (str).

        Raises:
            ValueError: If webhook signature verification fails.
        """
        webhook_secret = self._get_webhook_secret()
        stripe.api_key = self._get_stripe_key()

        try:
            event_obj_raw = stripe.Webhook.construct_event(
                body, signature_header, webhook_secret
            )
        except stripe.SignatureVerificationError as e:
            raise ValueError(f"Invalid webhook signature: {e}")

        # stripe-python v13+ returns StripeObjects that no longer support
        # dict-style .get(). Convert to a plain (recursively nested) dict so
        # the rest of this handler can use ordinary dict access.
        event = event_obj_raw.to_dict()

        event_type = event.get("type", "")
        event_id = event.get("id", "")
        event_obj = event["data"]["object"]

        logger.info("Processing Stripe webhook: type=%s, id=%s", event_type, event_id)

        # Determine user_id. Prefer the authoritative dsb_user_id metadata
        # (on the event object or the Stripe Customer) over a membership-table
        # scan by customer id, which misses when the customer id was never
        # persisted on a membership record.
        customer_id = event_obj.get("customer")
        user_id = self._resolve_user_id(event_obj, customer_id)

        # Process event types
        if event_type == "checkout.session.completed":
            # Resolve user from session metadata first (most reliable)
            session_user_id = event_obj.get("metadata", {}).get("dsb_user_id")
            if session_user_id:
                user_id = session_user_id

            subscription_id = event_obj.get("subscription")
            if subscription_id and user_id:
                sub = stripe.Subscription.retrieve(subscription_id).to_dict()
                tier = self._determine_tier_from_subscription(sub)
                current_period_end = self._extract_current_period_end(sub)

                # Activation re-verification (Requirements 5.8, 5.12; Property
                # 10). For a Student Builder checkout, re-read the user's
                # STUDENT_ELIGIBILITY at activation time: eligibility may have
                # lapsed or been revoked between session creation and this
                # event. If it is no longer active, DO NOT grant
                # STUDENT_BUILDER — log loudly and write a
                # ``student_activation_blocked`` audit event (reusing the
                # PAYMENT#{ts} shape) for ops follow-up. The Stripe
                # subscription still exists; refund/cancel is handled out of
                # band. The webhook is still treated as processed (an
                # activation block is a handled outcome, not an error).
                if tier == STUDENT_BUILDER:
                    # Import VerificationService lazily to avoid an import
                    # cycle, matching create_student_checkout_session.
                    from app.services.verification_service import VerificationService

                    # Fail closed: an eligibility read failure means we cannot
                    # confirm active eligibility, so treat it like "no longer
                    # eligible" and block the grant rather than granting on an
                    # unverified state.
                    try:
                        eligibility = VerificationService(
                            self._settings
                        ).get_eligibility(user_id)
                    except Exception as exc:  # noqa: BLE001 - fail closed
                        logger.error(
                            "Student Builder activation re-verify: eligibility "
                            "read failed for user %s (subscription=%s, event=%s): "
                            "%s; failing closed",
                            user_id,
                            subscription_id,
                            event_id,
                            exc,
                        )
                        eligibility = None
                    if not eligibility:
                        logger.error(
                            "Student Builder activation BLOCKED: user %s no longer "
                            "holds active eligibility at activation time "
                            "(subscription=%s, event=%s); NOT granting "
                            "STUDENT_BUILDER",
                            user_id,
                            subscription_id,
                            event_id,
                        )
                        # Preserve the membership's unchanged tier on the audit
                        # record; do not alter membership_tier.
                        existing = self._get_membership(user_id)
                        unchanged_tier = (
                            existing.get("membership_tier", {}).get("S", "")
                            if existing
                            else ""
                        )
                        self._record_payment_event(
                            user_id,
                            "student_activation_blocked",
                            unchanged_tier,
                            subscription_id,
                            event_id,
                        )
                        # Handled, not an error: report processed without a
                        # tier change (skip the welcome email / Discord sync).
                        return {
                            "processed": True,
                            "event_id": event_id,
                            "user_id": user_id,
                            "reason": "student_activation_blocked",
                        }

                self._activate_subscription(
                    user_id, tier, subscription_id, "active", current_period_end
                )
                self._record_payment_event(
                    user_id, "subscription_activated", tier, subscription_id, event_id
                )

                # Send subscription welcome email (fire-and-forget)
                try:
                    user_email = self._get_user_email(user_id)
                    user_display_name = self._get_user_display_name(user_id)
                    if user_email:
                        send_subscription_welcome_email(
                            username=user_display_name or "there",
                            email=user_email,
                            tier=tier,
                        )
                except Exception as e:
                    logger.error(
                        "Failed to send subscription welcome email for user %s: %s",
                        user_id,
                        e,
                    )

        elif event_type == "customer.subscription.updated":
            if user_id:
                status = event_obj.get("status", "")
                tier = self._determine_tier_from_subscription(event_obj)
                sub_id = event_obj.get("id", "")
                current_period_end = self._extract_current_period_end(event_obj)
                self._update_subscription_state(
                    user_id, tier, sub_id, status, current_period_end
                )
                self._record_payment_event(
                    user_id, "subscription_updated", tier, sub_id, event_id
                )

        elif event_type == "customer.subscription.deleted":
            if user_id:
                sub_id = event_obj.get("id", "")
                # Get previous tier before downgrading
                previous_membership = self._get_membership(user_id)
                previous_tier = (
                    previous_membership.get("membership_tier", {}).get("S", "")
                    if previous_membership
                    else ""
                )

                self._update_subscription_state(user_id, "FREE", sub_id, "canceled")
                self._record_payment_event(
                    user_id, "subscription_canceled", "FREE", sub_id, event_id
                )

                # Send expiration email (fire-and-forget)
                try:
                    user_email = self._get_user_email(user_id)
                    user_display_name = self._get_user_display_name(user_id)
                    if user_email:
                        send_subscription_expired_email(
                            username=user_display_name or "there",
                            email=user_email,
                            previous_tier=previous_tier,
                        )
                except Exception as e:
                    logger.error(
                        "Failed to send expiration email for user %s: %s", user_id, e
                    )

        elif event_type == "invoice.payment_succeeded":
            # Record successful payment for renewal tracking
            if user_id:
                sub_id = event_obj.get("subscription", "")
                self._record_payment_event(
                    user_id, "payment_succeeded", "", sub_id, event_id
                )

        elif event_type == "invoice.payment_failed":
            # A renewal (or other) charge failed. We do NOT change the tier or
            # revoke access here — Stripe keeps the subscription in a grace
            # period (past_due) and will retry, ultimately emitting
            # customer.subscription.deleted if it never recovers. We record the
            # event for the audit trail and notify the user to update their
            # payment method. No tier change means no Discord role sync, so
            # user_id is intentionally omitted from the result below.
            if user_id:
                sub_id = event_obj.get("subscription", "")
                self._record_payment_event(
                    user_id, "payment_failed", "", sub_id, event_id
                )

                # Notify the user (fire-and-forget). Derive the tier from the
                # current membership record for a friendlier message.
                try:
                    membership = self._get_membership(user_id)
                    tier = (
                        membership.get("membership_tier", {}).get("S", "")
                        if membership
                        else ""
                    )
                    user_email = self._get_user_email(user_id)
                    user_display_name = self._get_user_display_name(user_id)
                    if user_email:
                        send_payment_failed_email(
                            username=user_display_name or "there",
                            email=user_email,
                            tier=tier,
                        )
                    else:
                        logger.warning(
                            "payment_failed: no email on profile for user %s "
                            "(event %s); payment-failed email NOT sent",
                            user_id,
                            event_id,
                        )
                except Exception as e:
                    logger.error(
                        "Failed to send payment failed email for user %s: %s",
                        user_id,
                        e,
                    )
            else:
                # Could not map this invoice to a DSB user via metadata or the
                # customer-id scan. Log loudly so the miss is visible rather
                # than silently returning processed=true.
                logger.warning(
                    "payment_failed: could not resolve DSB user for customer %s "
                    "(event %s); no notification sent",
                    customer_id,
                    event_id,
                )

            # Processed, but no tier change → skip the Discord sync.
            return {"processed": True, "event_id": event_id}

        else:
            logger.info("Unhandled webhook event type: %s", event_type)
            return {
                "processed": False,
                "event_id": event_id,
                "reason": "unhandled_type",
            }

        result: dict[str, Any] = {"processed": True, "event_id": event_id}
        if user_id:
            result["user_id"] = user_id
        return result

    # ------------------------------------------------------------------
    # DynamoDB helpers (membership table)
    # ------------------------------------------------------------------

    def _get_membership(self, user_id: str) -> dict[str, Any] | None:
        """Get the MEMBERSHIP record for a user from DynamoDB.

        Returns:
            Raw DynamoDB item dict, or None if not found.
        """
        table_name = self._settings.membership_table
        try:
            response = self._dynamodb_client.get_item(
                TableName=table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": "MEMBERSHIP"},
                },
            )
            return response.get("Item")
        except ClientError as e:
            logger.error(
                "Failed to get membership for user %s: %s",
                user_id,
                e.response["Error"]["Code"],
            )
            return None

    def _put_membership(
        self,
        user_id: str,
        stripe_customer_id: str,
        membership_tier: str = "FREE",
    ) -> None:
        """Write/update the MEMBERSHIP record in DynamoDB.

        Performs an update that sets stripe_customer_id and membership_tier
        without overwriting other fields.
        """
        table_name = self._settings.membership_table
        updated_at = datetime.now(timezone.utc).isoformat()

        try:
            self._dynamodb_client.update_item(
                TableName=table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": "MEMBERSHIP"},
                },
                UpdateExpression=(
                    "SET stripe_customer_id = :cid, "
                    "membership_tier = :tier, "
                    "updated_at = :ts"
                ),
                ExpressionAttributeValues={
                    ":cid": {"S": stripe_customer_id},
                    ":tier": {"S": membership_tier},
                    ":ts": {"S": updated_at},
                },
            )
        except ClientError as e:
            logger.error(
                "Failed to update membership for user %s: %s",
                user_id,
                e.response["Error"]["Code"],
            )
            raise

    def _resolve_user_id(
        self, event_obj: dict[str, Any], customer_id: str | None
    ) -> str | None:
        """Resolve the DSB user_id for a webhook event, most-reliable first.

        Resolution order:
          1. ``dsb_user_id`` in the event object's own metadata (present on
             checkout sessions).
          2. The ``customer`` id on the event, matched against the stored
             ``stripe_customer_id`` on a membership record. Because every
             subscriber goes through the DSB checkout flow, which persists the
             customer id at customer-creation time, this is the authoritative
             mapping for events such as ``invoice.payment_failed``.

        The invoice's ``customer_email`` is deliberately NOT used: it is the
        payment email on file with Stripe, which can differ from the user's DSB
        account email, so matching on it would resolve the wrong user (or none).

        Returns the user_id, or ``None`` if it cannot be resolved.
        """
        # 1. Event object metadata (e.g. checkout.session.completed).
        obj_metadata = event_obj.get("metadata") or {}
        metadata_user_id = obj_metadata.get("dsb_user_id")
        if metadata_user_id:
            return metadata_user_id

        # 2. Look up by the customer id from the payload against the DB.
        if customer_id:
            return self._resolve_user_from_customer(customer_id)

        return None

    def _resolve_user_from_customer(self, customer_id: str) -> str | None:
        """Look up the DSB user_id for a Stripe customer ID.

        Scans the membership table for a record with the given stripe_customer_id.
        """
        table_name = self._settings.membership_table
        try:
            response = self._dynamodb_client.scan(
                TableName=table_name,
                FilterExpression="stripe_customer_id = :cid AND SK = :sk",
                ExpressionAttributeValues={
                    ":cid": {"S": customer_id},
                    ":sk": {"S": "MEMBERSHIP"},
                },
                Limit=1,
            )
            items = response.get("Items", [])
            if items:
                pk = items[0].get("PK", {}).get("S", "")
                if pk.startswith("USER#"):
                    return pk[5:]
        except ClientError as e:
            logger.error("Failed to resolve customer %s: %s", customer_id, e)
        return None

    def _determine_tier_from_subscription(self, subscription: Any) -> str:
        """Determine the DSB tier from a Stripe subscription object.

        Inspects the subscription's items for a product, then resolves that
        product's dsb_tier from the cached product catalog (get_products())
        by matching product_id. Only on a cache miss (the product id is not
        present in the catalog) does this fall back to a direct
        stripe.Product.retrieve, preserving correctness while avoiding a
        per-event Stripe API call. The resolved dsb_tier is upper-cased and
        defaults to FREE when no recognized dsb_tier is found or on any error.
        """
        try:
            items = subscription.get("items", {}).get("data", [])
            if not items:
                return "FREE"
            price = items[0].get("price", {})
            product_id = price.get("product", "")
            if not product_id:
                return "FREE"

            # Catalog-backed resolution: match the product_id against the
            # cached catalog rows from get_products(). Each row carries the
            # product id under "id" and its dsb_tier under "dsb_tier".
            try:
                for product in self.get_products():
                    if product.get("id") == product_id:
                        tier = product.get("dsb_tier") or "FREE"
                        return tier.upper()
            except Exception as e:
                # A catalog read failure (e.g. Stripe list error with no cache)
                # must not break tier resolution. Fall through to the direct
                # Product.retrieve fallback below.
                logger.warning(
                    "Catalog lookup failed during tier resolution, "
                    "falling back to Product.retrieve: %s",
                    e,
                )

            # Cache miss (or catalog read failure): fall back to a direct
            # retrieve so a newly added product not yet in the cache still
            # resolves correctly.
            metadata = stripe.Product.retrieve(product_id).metadata
            # StripeObject metadata does not support dict-style .get() in
            # stripe-python v13+; use membership + index access instead.
            tier = metadata["dsb_tier"] if "dsb_tier" in metadata else "FREE"
            return tier.upper()
        except Exception as e:
            logger.error("Failed to determine tier from subscription: %s", e)
        return "FREE"

    @staticmethod
    def _extract_current_period_end(subscription: dict[str, Any]) -> int | None:
        """Read current_period_end from a subscription dict.

        The Stripe API version bundled with stripe-python v13+ moved
        current_period_end/current_period_start off the subscription root and
        onto each subscription item. Prefer the item value; fall back to the
        root for older API versions.
        """
        items = subscription.get("items", {}).get("data", [])
        if items:
            item_period_end = items[0].get("current_period_end")
            if item_period_end is not None:
                return item_period_end
        return subscription.get("current_period_end")

    def _update_subscription_state(
        self,
        user_id: str,
        tier: str,
        subscription_id: str,
        status: str,
        current_period_end: int | None = None,
    ) -> None:
        """Update a user's membership tier, subscription status, and period info."""
        table_name = self._settings.membership_table
        now = datetime.now(timezone.utc).isoformat()

        update_parts = [
            "membership_tier = :tier",
            "subscription_status = :status",
            "stripe_subscription_id = :sub_id",
            "updated_at = :ts",
        ]
        expr_values: dict = {
            ":tier": {"S": tier},
            ":status": {"S": status},
            ":sub_id": {"S": subscription_id},
            ":ts": {"S": now},
        }

        if current_period_end:
            period_end_iso = datetime.fromtimestamp(
                current_period_end, tz=timezone.utc
            ).isoformat()
            update_parts.append("current_period_end = :cpe")
            expr_values[":cpe"] = {"S": period_end_iso}

        try:
            self._dynamodb_client.update_item(
                TableName=table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": "MEMBERSHIP"},
                },
                UpdateExpression="SET " + ", ".join(update_parts),
                ExpressionAttributeValues=expr_values,
            )
            logger.info(
                "Updated subscription state: user=%s tier=%s status=%s",
                user_id,
                tier,
                status,
            )
        except ClientError as e:
            logger.error(
                "Failed to update subscription state for user %s: %s",
                user_id,
                e.response["Error"]["Code"],
            )

    def _activate_subscription(
        self,
        user_id: str,
        tier: str,
        subscription_id: str,
        status: str,
        current_period_end: int | None = None,
    ) -> None:
        """Activate a subscription for the first time, recording the start date."""
        table_name = self._settings.membership_table
        now = datetime.now(timezone.utc).isoformat()

        # Get previous tier before updating (for Builder activation detection)
        previous_tier = "FREE"
        try:
            existing = self._get_membership(user_id)
            if existing:
                previous_tier = existing.get("membership_tier", {}).get("S", "FREE")
        except Exception:
            pass  # Default to FREE if we can't read

        update_parts = [
            "membership_tier = :tier",
            "subscription_status = :status",
            "stripe_subscription_id = :sub_id",
            "subscription_started_at = :started",
            "updated_at = :ts",
        ]
        expr_values: dict = {
            ":tier": {"S": tier},
            ":status": {"S": status},
            ":sub_id": {"S": subscription_id},
            ":started": {"S": now},
            ":ts": {"S": now},
        }

        if current_period_end:
            period_end_iso = datetime.fromtimestamp(
                current_period_end, tz=timezone.utc
            ).isoformat()
            update_parts.append("current_period_end = :cpe")
            expr_values[":cpe"] = {"S": period_end_iso}

        try:
            self._dynamodb_client.update_item(
                TableName=table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": "MEMBERSHIP"},
                },
                UpdateExpression="SET " + ", ".join(update_parts),
                ExpressionAttributeValues=expr_values,
            )
            logger.info(
                "Activated subscription: user=%s tier=%s sub_id=%s",
                user_id,
                tier,
                subscription_id,
            )

            # Initialize Builder Journey meta on subscription activation
            if is_builder_equivalent(tier):
                try:
                    progress_db = ProgressDB(self._settings)
                    progress_db.save_journey_meta(user_id)
                    logger.info("Initialized Builder Journey for user %s", user_id)
                except Exception as e:
                    logger.error(
                        "Failed to initialize journey for user %s: %s",
                        user_id,
                        e,
                    )

                # Record Builder activation event (FREE→BUILDER or EXPLORER→BUILDER)
                if not is_builder_equivalent(previous_tier):
                    try:
                        record_builder_activation(
                            user_id=user_id,
                            activation_source="STRIPE_SUBSCRIPTION",
                            previous_tier=previous_tier,
                            settings=self._settings,
                        )
                    except Exception as e:
                        logger.error(
                            "Failed to record builder activation for user %s: %s",
                            user_id,
                            e,
                        )
        except ClientError as e:
            logger.error(
                "Failed to activate subscription for user %s: %s",
                user_id,
                e.response["Error"]["Code"],
            )

    def _get_user_email(self, user_id: str) -> str | None:
        """Get user's email from their PROFILE record in the progress table."""
        try:
            response = self._dynamodb_client.get_item(
                TableName=self._settings.progress_table,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": "PROFILE"},
                },
                ProjectionExpression="email",
            )
            item = response.get("Item")
            return item.get("email", {}).get("S") if item else None
        except ClientError:
            return None

    def _get_user_display_name(self, user_id: str) -> str | None:
        """Get user's display name from their PROFILE record."""
        try:
            response = self._dynamodb_client.get_item(
                TableName=self._settings.progress_table,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": "PROFILE"},
                },
                ProjectionExpression="username",
            )
            item = response.get("Item")
            return item.get("username", {}).get("S") if item else None
        except ClientError:
            return None

    def _record_payment_event(
        self,
        user_id: str,
        event_type: str,
        tier: str,
        subscription_id: str,
        stripe_event_id: str,
    ) -> None:
        """Write a payment event record for audit trail."""
        table_name = self._settings.membership_table
        now = datetime.now(timezone.utc).isoformat()

        try:
            self._dynamodb_client.put_item(
                TableName=table_name,
                Item={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": f"PAYMENT#{now}"},
                    "event_type": {"S": event_type},
                    "membership_tier": {"S": tier},
                    "stripe_subscription_id": {"S": subscription_id},
                    "stripe_event_id": {"S": stripe_event_id},
                    "timestamp": {"S": now},
                },
            )
        except ClientError as e:
            logger.error("Failed to record payment event: %s", e)
