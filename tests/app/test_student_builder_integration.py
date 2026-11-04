"""Integration smoke tests for the Student Builder membership feature.

These are a small number (not exhaustive) of example integration tests that
exercise the real service code paths end to end, with only the true external
boundaries mocked: ApyHub (academic-domain check), SES (verification email),
Stripe (product catalog + checkout session), and DynamoDB.

Unlike the per-service unit tests (tests/app/services/test_verification_service.py
and tests/app/services/test_stripe_service.py), which stub each DynamoDB call per
test, the end-to-end flow here shares one small in-memory DynamoDB table between
VerificationService and StripeService so that the token/eligibility records
written by submit()/confirm() are actually read back by
create_student_checkout_session(). This proves the real handoff:

    submit  -> writes STUDENT_VERIFICATION_TOKEN
    confirm -> consumes the token, writes STUDENT_ELIGIBILITY
    checkout -> reads STUDENT_ELIGIBILITY and builds a STUDENT_BUILDER session

The mocking conventions (construct the service under patch("boto3.client") so no
real AWS client is built, then reassign _dynamodb_client; patch the SDK calls per
test) mirror the existing unit tests referenced above.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services import stripe_service as stripe_mod
from app.services import verification_service as verif_mod
from app.services.stripe_service import StripeService
from app.services.verification_service import VerificationService
from app.tiers import STUDENT_BUILDER

# ---------------------------------------------------------------------------
# A tiny in-memory DynamoDB stand-in keyed by (PK, SK).
#
# It implements only the operations the two services use: put_item, get_item,
# and the single conditional update_item that confirm() issues to mark a token
# used (SET #used = :true with ConditionExpression #used = :false).
# ---------------------------------------------------------------------------


class FakeDynamoDB:
    def __init__(self):
        # key: (PK string, SK string) -> item dict (DynamoDB attribute-value form)
        self.store: dict[tuple[str, str], dict] = {}

    @staticmethod
    def _key(key_arg: dict) -> tuple[str, str]:
        return (key_arg["PK"]["S"], key_arg["SK"]["S"])

    def put_item(self, *, TableName, Item, **kwargs):  # noqa: N803 - boto3 kwarg names
        self.store[(Item["PK"]["S"], Item["SK"]["S"])] = dict(Item)
        return {}

    def get_item(self, *, TableName, Key, **kwargs):  # noqa: N803
        item = self.store.get(self._key(Key))
        return {"Item": dict(item)} if item is not None else {}

    def update_item(
        self,
        *,
        TableName,  # noqa: N803
        Key,  # noqa: N803
        UpdateExpression=None,  # noqa: N803
        ConditionExpression=None,  # noqa: N803
        ExpressionAttributeNames=None,  # noqa: N803
        ExpressionAttributeValues=None,  # noqa: N803
        **kwargs,
    ):
        k = self._key(Key)
        item = self.store.get(k)
        if item is None:
            # Nothing to update — create a bare record so SET has a target.
            item = {"PK": Key["PK"], "SK": Key["SK"]}
            self.store[k] = item

        names = ExpressionAttributeNames or {}
        values = ExpressionAttributeValues or {}

        # Honor the single-use guard used by confirm(): #used = :false.
        if ConditionExpression:
            cond = ConditionExpression
            for placeholder, attr in names.items():
                cond = cond.replace(placeholder, attr)
            # cond is now e.g. "used = :false"
            attr_name, _, value_ref = (p.strip() for p in cond.partition("="))
            current = item.get(attr_name)
            expected = values.get(value_ref.strip())
            if current != expected:
                raise stripe_mod.ClientError(
                    {
                        "Error": {
                            "Code": "ConditionalCheckFailedException",
                            "Message": "condition failed",
                        }
                    },
                    "UpdateItem",
                )

        # Apply a simple "SET #attr = :value, #b = :c" update expression.
        if UpdateExpression and UpdateExpression.strip().upper().startswith("SET"):
            assignments = UpdateExpression.strip()[3:].split(",")
            for assignment in assignments:
                target, _, source = assignment.partition("=")
                target = target.strip()
                source = source.strip()
                attr = names.get(target, target)
                item[attr] = values[source]
        return {}


# ---------------------------------------------------------------------------
# Settings + service construction helpers (mirror the unit-test fixtures).
# ---------------------------------------------------------------------------


def _make_settings():
    s = MagicMock()
    s.membership_table = "test-membership"
    s.progress_table = "test-progress"
    s.apyhub_secret_name = "apyhub-secret"
    s.stripe_secret_name = "stripe-secret"
    s.stripe_webhook_secret_name = "stripe-webhook-secret"
    s.frontend_origin = "https://devsecblueprint.com"
    return s


def _make_verification_service(settings, fake_db):
    with patch("boto3.client"):
        svc = VerificationService(settings)
    svc._dynamodb_client = fake_db
    svc._apyhub.is_academic_domain = MagicMock(return_value=True)
    return svc


def _make_stripe_service(settings, fake_db):
    with patch("boto3.client"):
        svc = StripeService(settings)
    svc._dynamodb_client = fake_db
    svc._get_stripe_key = MagicMock(return_value="sk_test")
    svc._get_webhook_secret = MagicMock(return_value="whsec_test")
    return svc


def _reset_product_cache():
    StripeService._products_cache["data"] = None
    StripeService._products_cache["timestamp"] = 0.0


@pytest.fixture(autouse=True)
def _clear_cache():
    _reset_product_cache()
    yield
    _reset_product_cache()


# ---------------------------------------------------------------------------
# 23.1 — End-to-end: verification -> eligibility -> student checkout
# Requirements: 3.1, 4.4, 5.1, 5.6
# ---------------------------------------------------------------------------


class TestStudentBuilderEndToEnd:
    def test_submit_confirm_then_student_checkout_succeeds(self):
        settings = _make_settings()
        fake_db = FakeDynamoDB()

        verification = _make_verification_service(settings, fake_db)
        stripe_svc = _make_stripe_service(settings, fake_db)

        # --- 1. submit(): ApyHub says academic, SES send succeeds. A token
        #        record is written to the shared table. We capture the raw
        #        token from the confirmation link SES would have received.
        sent = {}

        def _capture_email(username, email, confirm_url, *args, **kwargs):
            sent["confirm_url"] = confirm_url
            return True

        with patch.object(
            verif_mod, "send_student_verification_email", side_effect=_capture_email
        ):
            verification.submit("u1", "student@university.edu")

        token_key = ("USER#u1", verif_mod.VERIFICATION_TOKEN_SK)
        assert token_key in fake_db.store  # token persisted (Requirement 3.1/4.1)
        raw_token = sent["confirm_url"].split("token=")[1]

        # --- 2. confirm(): consumes the token and writes eligibility
        #        (Requirement 4.4).
        result = verification.confirm("u1", raw_token)
        assert result["eligible"] is True

        elig_key = ("USER#u1", verif_mod.ELIGIBILITY_SK)
        assert elig_key in fake_db.store
        # The token is now marked used; a second confirm must fail.
        with pytest.raises(verif_mod.InvalidTokenError):
            verification.confirm("u1", raw_token)

        # --- 3. create_student_checkout_session(): the now-eligible user gets a
        #        STUDENT_BUILDER session (Requirements 5.1, 5.6). The checkout
        #        constructs its own VerificationService internally, so patch the
        #        lazily imported symbol to return one backed by the shared table.
        resolved_price_id = "price_student_month"

        def _verification_factory(_settings):
            return verification

        products = [
            {
                "id": "prod_student",
                "dsb_tier": STUDENT_BUILDER,
                "interval": "month",
                "price_id": resolved_price_id,
                "price": 800,
                "monthly_price": 800,
                "currency": "usd",
            }
        ]
        session = MagicMock(url="https://checkout/student-sess")
        customer = MagicMock(id="cus_new")

        with (
            patch.object(verif_mod, "VerificationService", _verification_factory),
            patch.object(stripe_svc, "get_products", return_value=products),
            patch.object(stripe_mod.stripe.Customer, "create", return_value=customer),
            patch.object(
                stripe_mod.stripe.checkout.Session, "create", return_value=session
            ) as sess_create,
        ):
            checkout = stripe_svc.create_student_checkout_session(
                "u1", resolved_price_id, "month"
            )

        assert checkout == {"checkout_url": "https://checkout/student-sess"}

        # The session carries STUDENT_BUILDER metadata and verified eligibility.
        kwargs = sess_create.call_args.kwargs
        assert kwargs["mode"] == "subscription"
        assert kwargs["line_items"] == [{"price": resolved_price_id, "quantity": 1}]
        metadata = kwargs["metadata"]
        assert metadata["dsb_user_id"] == "u1"
        assert metadata["dsb_tier"] == STUDENT_BUILDER
        assert metadata["eligibility_verified"] == "true"
        assert metadata["eligibility_expires_at"] == result["expires_at"]

    def test_checkout_rejected_when_verification_never_completed(self):
        """Without a confirmed eligibility record, checkout is rejected before
        any Stripe call (Requirement 5.1)."""
        settings = _make_settings()
        fake_db = FakeDynamoDB()

        verification = _make_verification_service(settings, fake_db)
        stripe_svc = _make_stripe_service(settings, fake_db)

        def _verification_factory(_settings):
            return verification

        with (
            patch.object(verif_mod, "VerificationService", _verification_factory),
            patch.object(stripe_svc, "get_products") as get_products,
            patch.object(stripe_mod.stripe.checkout.Session, "create") as sess_create,
        ):
            with pytest.raises(stripe_mod.StudentEligibilityError):
                stripe_svc.create_student_checkout_session(
                    "u1", "price_student_month", "month"
                )

        # Rejected before touching the catalog or Stripe.
        get_products.assert_not_called()
        sess_create.assert_not_called()


# ---------------------------------------------------------------------------
# 23.2 — Webhook signature-failure smoke test
# Requirement: 7.6
# ---------------------------------------------------------------------------


class TestWebhookSignatureFailureSmoke:
    def test_router_returns_400_and_no_tier_change(self):
        """A signature-verification failure at the webhook route yields HTTP 400
        and performs no membership tier change."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from app.routers import stripe as stripe_router
        from app.routers.stripe import get_stripe_service

        settings = _make_settings()
        fake_db = FakeDynamoDB()
        stripe_svc = _make_stripe_service(settings, fake_db)
        stripe_svc._activate_subscription = MagicMock()
        stripe_svc._update_subscription_state = MagicMock()

        app = FastAPI()
        app.include_router(stripe_router.router)
        app.dependency_overrides[get_stripe_service] = lambda: stripe_svc

        client = TestClient(app)

        err = stripe_mod.stripe.SignatureVerificationError("bad sig", "sig-header")
        with patch.object(
            stripe_mod.stripe.Webhook, "construct_event", side_effect=err
        ):
            response = client.post(
                "/api/stripe/webhook",
                content=b'{"id": "evt_bad"}',
                headers={"stripe-signature": "t=1,v1=deadbeef"},
            )

        assert response.status_code == 400
        # No tier change of any kind occurred.
        stripe_svc._activate_subscription.assert_not_called()
        stripe_svc._update_subscription_state.assert_not_called()

    def test_service_raises_value_error_and_no_tier_change(self):
        """At the service contract level, an invalid signature raises ValueError
        and performs no membership tier change (Requirement 7.6)."""
        settings = _make_settings()
        fake_db = FakeDynamoDB()
        stripe_svc = _make_stripe_service(settings, fake_db)
        stripe_svc._activate_subscription = MagicMock()
        stripe_svc._update_subscription_state = MagicMock()

        err = stripe_mod.stripe.SignatureVerificationError("bad sig", "sig-header")
        with patch.object(
            stripe_mod.stripe.Webhook, "construct_event", side_effect=err
        ):
            with pytest.raises(ValueError, match="Invalid webhook signature"):
                stripe_svc.verify_and_process_webhook("body", "sig-header")

        stripe_svc._activate_subscription.assert_not_called()
        stripe_svc._update_subscription_state.assert_not_called()
