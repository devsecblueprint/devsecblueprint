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

logger = logging.getLogger(__name__)


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
                dsb_tier = product.metadata.get("dsb_tier")
                if not dsb_tier:
                    continue

                # Fetch active prices for each product
                prices = stripe.Price.list(product=product.id, active=True)
                for price in prices.data:
                    interval = price.recurring.interval if price.recurring else None
                    unit_amount = price.unit_amount or 0
                    monthly_price = round(unit_amount / 12) if interval == "year" else unit_amount

                    dsb_products.append(
                        {
                            "id": product.id,
                            "name": product.name,
                            "description": product.description or "",
                            "price": unit_amount,
                            "monthly_price": monthly_price,
                            "currency": price.currency,
                            "interval": interval,
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

        # Create Checkout Session
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{self._settings.frontend_origin}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{self._settings.frontend_origin}/pricing",
            metadata={"dsb_user_id": user_id},
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
            event = stripe.Webhook.construct_event(
                body, signature_header, webhook_secret
            )
        except stripe.error.SignatureVerificationError as e:
            raise ValueError(f"Invalid webhook signature: {e}")

        event_type = event.get("type", "")
        event_id = event.get("id", "")
        event_obj = event["data"]["object"]

        logger.info("Processing Stripe webhook: type=%s, id=%s", event_type, event_id)

        # Determine user_id from customer
        user_id = None
        customer_id = event_obj.get("customer")

        if customer_id:
            # Look up user by stripe_customer_id in membership table
            user_id = self._resolve_user_from_customer(customer_id)

        # Process event types
        if event_type == "checkout.session.completed":
            # Resolve user from session metadata first (most reliable)
            session_user_id = event_obj.get("metadata", {}).get("dsb_user_id")
            if session_user_id:
                user_id = session_user_id

            subscription_id = event_obj.get("subscription")
            if subscription_id and user_id:
                sub = stripe.Subscription.retrieve(subscription_id)
                tier = self._determine_tier_from_subscription(sub)
                current_period_end = sub.get("current_period_end")
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
                        from app.services.email import send_subscription_welcome_email

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
                current_period_end = event_obj.get("current_period_end")
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
                        from app.services.email import send_subscription_expired_email

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

        Inspects the subscription's items for a product with dsb_tier metadata.
        """
        try:
            items = subscription.get("items", {}).get("data", [])
            if not items:
                return "FREE"
            price = items[0].get("price", {})
            product_id = price.get("product", "")
            if product_id:
                product = stripe.Product.retrieve(product_id)
                tier = product.metadata.get("dsb_tier", "FREE")
                return tier.upper()
        except Exception as e:
            logger.error("Failed to determine tier from subscription: %s", e)
        return "FREE"

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
