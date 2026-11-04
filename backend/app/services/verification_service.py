"""Academic-email verification and Student Builder eligibility.

This module backs the Student Builder academic-email verification flow:

- ``ApyHubClient`` validates whether an email belongs to an academic domain via
  the ApyHub Student Email Verification API (10s timeout, fail-closed).
- ``VerificationService`` (added in later tasks) orchestrates syntactic
  validation, the ApyHub domain check, single-use token issuance + SES email,
  ownership confirmation, and eligibility reads.

Design decisions (see spec ``student-builder-membership``):

- Fail_Closed: any ApyHub error, timeout, or missing/empty API key rejects the
  verification request rather than guessing or granting. All such conditions
  surface as :class:`ApyHubUnavailable`.
- The ApyHub API key is read via the shared cached secret mechanism
  (:func:`app.services.secrets.get_secret`, 15-minute TTL) keyed by
  ``settings.apyhub_secret_name``. The secret JSON holds the key under
  ``secret_key``, matching the ``modules/secrets`` convention used elsewhere.
- No API key is hardcoded in application code.

Requirements: 3.1, 3.5, 3.6, 3.8
"""

import hashlib
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone

import boto3
import httpx
from botocore.exceptions import ClientError

from app.config import Settings
from app.services.email import send_student_verification_email
from app.services.secrets import get_secret

logger = logging.getLogger(__name__)

# Current ApyHub US gateway endpoint for the Student Email Verification API.
# POST with JSON body ``{"email": ...}``, authenticated via the ``apy-token``
# request header. Response is ``{"data": true|false}`` where true means the
# address is an academic/university email.
APYHUB_ACADEMIC_EMAIL_URL = (
    "https://api.us.apyhub.com/apyhub/check-whether-an-email-belongs-to-an-academic"
)

# Request timeout applied to the ApyHub call (Requirement 3.1).
APYHUB_TIMEOUT_SECONDS = 10.0


class VerificationError(Exception):
    """Base class for Student Builder verification failures."""


class ApyHubUnavailable(VerificationError):
    """The ApyHub validation service could not be used (Fail_Closed).

    Raised for any error, timeout, or missing/empty API key encountered while
    performing the academic-domain check. The caller must treat this as a hard
    rejection and must not create or advance any verification record.
    """


class InvalidEmailError(VerificationError):
    """The submitted academic email failed syntactic validation.

    Raised before any ApyHub call and without writing any record
    (Requirement 3.2). Maps to an HTTP 400 at the router boundary.
    """


class NotAcademicError(VerificationError):
    """ApyHub reported the email does not belong to an academic domain.

    Raised when the domain check succeeds but returns a non-academic result
    (Requirement 3.3). No verification record is written. Maps to HTTP 422.
    """


class EmailSendError(VerificationError):
    """The ownership-confirmation email could not be sent.

    Raised when the SES send returns ``False`` after the token record has
    already been written. The token record is retained (Requirement 4.3);
    the user may retry. Maps to an HTTP 502 at the router boundary.
    """


class InvalidTokenError(VerificationError):
    """The submitted ownership-confirmation token is not usable.

    Raised when the token is missing, already used, expired, or its SHA-256
    hash does not match the stored value (Requirement 4.5). No eligibility
    record is created or modified in any of these cases. Maps to an HTTP 400
    at the router boundary.
    """


class ApyHubClient:
    """Thin client for the ApyHub academic-email validation API.

    The API key is resolved lazily (per call) from Secrets Manager through the
    shared TTL-cached :func:`app.services.secrets.get_secret` helper, so the key
    is never held in application memory beyond the cache and never hardcoded.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _get_api_key(self) -> str:
        """Return the ApyHub API key, or raise :class:`ApyHubUnavailable`.

        Fail_Closed (Requirement 3.6) when the secret name is unset, the secret
        cannot be retrieved/parsed, or the ``secret_key`` value is missing/empty.
        """
        secret_name = self._settings.apyhub_secret_name
        if not secret_name:
            logger.error("ApyHub secret name is not configured")
            raise ApyHubUnavailable("ApyHub secret name is not configured")

        try:
            secret_data = get_secret(secret_name)
        except Exception as exc:  # noqa: BLE001 - normalize all secret errors
            logger.error("Failed to retrieve ApyHub secret: %s", exc)
            raise ApyHubUnavailable("ApyHub secret could not be retrieved") from exc

        api_key = (secret_data or {}).get("secret_key", "")
        if not api_key:
            logger.error("ApyHub secret does not contain a usable API key")
            raise ApyHubUnavailable("ApyHub API key is missing or empty")

        return api_key

    def is_academic_domain(self, email: str) -> bool:
        """Return True iff ApyHub reports ``email`` as an academic-domain address.

        Calls the ApyHub academic-email validation API with a 10-second timeout
        (Requirement 3.1). Any transport error, timeout, non-success status, or
        unparseable response raises :class:`ApyHubUnavailable` (Fail_Closed,
        Requirement 3.4). A missing/empty API key likewise fails closed
        (Requirement 3.6).

        Args:
            email: The academic email address to validate.

        Returns:
            True if the email belongs to an academic domain, False otherwise.

        Raises:
            ApyHubUnavailable: On any error, timeout, or missing/empty key.
        """
        api_key = self._get_api_key()

        try:
            response = httpx.post(
                APYHUB_ACADEMIC_EMAIL_URL,
                headers={"apy-token": api_key},
                json={"email": email},
                timeout=APYHUB_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            logger.error("ApyHub academic-email validation failed: %s", exc)
            raise ApyHubUnavailable("ApyHub request failed or timed out") from exc
        except ValueError as exc:  # JSON decode error
            logger.error("ApyHub returned an unparseable response: %s", exc)
            raise ApyHubUnavailable("ApyHub returned an invalid response") from exc

        # ApyHub returns the boolean under ``data``; accept ``academic`` as a
        # tolerant fallback so the result mapping is easy to adjust if the
        # response shape changes.
        if not isinstance(payload, dict):
            logger.error("ApyHub response was not a JSON object: %r", payload)
            raise ApyHubUnavailable("ApyHub returned an unexpected response shape")

        result = payload.get("data", payload.get("academic"))
        return bool(result)


# Syntactic email pattern, matching the convention used elsewhere in the app
# (see ``routers/contact.py``): a non-empty local part, a single ``@``, and a
# dotted domain with no whitespace. This is a cheap pre-filter run BEFORE any
# ApyHub call; ApyHub performs the authoritative academic-domain check.
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# Verification token lifetime: 24 hours, in seconds (Requirement 4.1).
TOKEN_TTL_SECONDS = 86400

# Single range-key for the per-user outstanding verification token. Writing to
# this fixed SK means a new submission overwrites (supersedes) any prior token
# for the user (Requirement 4.1).
VERIFICATION_TOKEN_SK = "STUDENT_VERIFICATION_TOKEN"

# Range-key for the per-user Student Builder eligibility record written on a
# successful ownership confirmation (Requirement 4.4).
ELIGIBILITY_SK = "STUDENT_ELIGIBILITY"

# Eligibility window: 365 days, in seconds. ``expires_at`` on the eligibility
# record is an ISO-8601 timestamp this far past ``verified_at`` (Requirement
# 4.4); eligibility is active iff that timestamp is strictly after now
# (Requirements 4.7/4.8). Unlike the token's 24h epoch TTL, DynamoDB does NOT
# auto-delete the eligibility item — expiry is enforced only at read time.
ELIGIBILITY_TTL_SECONDS = 365 * 86400


def _hash_token(raw_token: str) -> str:
    """Return the hex SHA-256 digest of ``raw_token``.

    Only the hash is ever persisted, so a table read never exposes a usable
    token (Requirement 4.1). Confirmation hashes the submitted token and
    compares against the stored value.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class VerificationService:
    """Orchestrates academic-email verification for Student Builder eligibility.

    ``submit`` performs syntactic validation, the ApyHub academic-domain check
    (Fail_Closed), issues a single-use hashed token with a 24-hour TTL that
    supersedes any prior outstanding token, and emails an ownership-confirmation
    link carrying the raw token. ``confirm``/``get_eligibility`` are added in a
    later task.

    Creates its own boto3 DynamoDB client, mirroring ``StripeService``.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._apyhub = ApyHubClient(settings)
        self._dynamodb_client = boto3.client("dynamodb")

    def submit(self, user_id: str, academic_email: str) -> None:
        """Begin academic-email verification for ``user_id``.

        Flow (Requirements 3.1–3.4, 4.1–4.3):

        1. Syntactic validation first. An empty or malformed address raises
           :class:`InvalidEmailError` BEFORE any ApyHub call and without writing
           any record (Requirement 3.2).
        2. ApyHub academic-domain check. ``False`` raises
           :class:`NotAcademicError` with no record written (Requirement 3.3);
           an unavailable service propagates as :class:`ApyHubUnavailable`
           (Fail_Closed, Requirements 3.4/3.6).
        3. On success, generate a high-entropy token, persist only its SHA-256
           hash in a ``STUDENT_VERIFICATION_TOKEN`` item (TTL = now + 86400),
           superseding any prior outstanding token for this user
           (Requirement 4.1).
        4. Send the ownership-confirmation email with the raw token in the
           link. If the send fails, the token record is retained and an
           :class:`EmailSendError` is raised (Requirement 4.3).

        Args:
            user_id: The DSB user id initiating verification.
            academic_email: The academic email address to verify.

        Raises:
            InvalidEmailError: Syntactically invalid/empty email.
            NotAcademicError: ApyHub reports a non-academic domain.
            ApyHubUnavailable: ApyHub error/timeout/missing key (Fail_Closed).
            EmailSendError: The confirmation email could not be sent.
        """
        # 1. Syntactic validation BEFORE any ApyHub call or record write.
        email = (academic_email or "").strip()
        if not email or not _EMAIL_PATTERN.match(email):
            logger.info("Rejecting syntactically invalid academic email")
            raise InvalidEmailError("Invalid email address")

        # 2. ApyHub academic-domain check (10s, Fail_Closed). A non-academic
        #    result is a clean rejection with no record written; any
        #    ApyHubUnavailable propagates unchanged (fail-closed).
        if not self._apyhub.is_academic_domain(email):
            logger.info("Rejecting non-academic email for user %s", user_id)
            raise NotAcademicError("Email is not an academic-domain address")

        # 3. Generate a high-entropy token and persist ONLY its hash. Writing to
        #    the fixed single SK supersedes any prior outstanding token.
        raw_token = secrets.token_urlsafe(32)
        token_hash = _hash_token(raw_token)

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        expiry_epoch = int(now.timestamp()) + TOKEN_TTL_SECONDS

        try:
            self._dynamodb_client.put_item(
                TableName=self._settings.membership_table,
                Item={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": VERIFICATION_TOKEN_SK},
                    "token_hash": {"S": token_hash},
                    "academic_email": {"S": email},
                    "used": {"BOOL": False},
                    "created_at": {"S": now_iso},
                    # DynamoDB TTL auto-expiry: the dsb-platform-membership
                    # table configures TTL on the ``expires_at`` attribute (see
                    # terraform/modules/dynamodb_membership), so the epoch value
                    # lives there to get a real auto-sweep. ``ttl`` is also
                    # written to match the design's documented attribute name.
                    # Read-time expiry (task 9.3) is enforced regardless, so a
                    # slow sweep never grants a stale token.
                    "expires_at": {"N": str(expiry_epoch)},
                    "ttl": {"N": str(expiry_epoch)},
                },
            )
        except ClientError as exc:
            logger.error(
                "Failed to write verification token for user %s: %s",
                user_id,
                exc.response.get("Error", {}).get("Code"),
            )
            raise

        # 4. Send the ownership-confirmation email. The raw token appears only
        #    in the link; it is never persisted.
        confirm_url = (
            f"{self._settings.frontend_origin}/verify/confirm?token={raw_token}"
        )
        username = self._get_username(user_id) or "there"

        sent = send_student_verification_email(username, email, confirm_url)
        if not sent:
            # Retain the token record (Requirement 4.3) so the user can retry;
            # surface a send-failure error for the router to map to 502.
            logger.error(
                "Verification email send failed for user %s; token retained",
                user_id,
            )
            raise EmailSendError("Verification email could not be sent")

    def confirm(self, user_id: str, raw_token: str) -> dict:
        """Confirm academic-email ownership and grant Student Builder eligibility.

        Flow (Requirements 4.4, 4.5; Property 11):

        1. Read the user's ``STUDENT_VERIFICATION_TOKEN`` item. A missing item
           is an invalid token.
        2. Validate the token at READ TIME, independent of the DynamoDB TTL
           sweep: it must be unused (``used == false``), unexpired (the stored
           epoch in ``expires_at`` must be strictly after now), and
           ``sha256(raw_token)`` must equal the stored ``token_hash``.
        3. Any failure raises :class:`InvalidTokenError` and makes NO
           eligibility change (Requirement 4.5).
        4. On success, conditionally mark the token used with a DynamoDB
           ``used = false`` guard so two concurrent confirmations cannot both
           succeed (single-use, Property 11). A lost race also surfaces as
           :class:`InvalidTokenError`.
        5. Write a ``STUDENT_ELIGIBILITY`` item carrying the token's
           ``academic_email``, ``verified_at = now`` (ISO-8601), and
           ``expires_at = now + 365d`` (ISO-8601). Unlike the token, this item
           has no DynamoDB TTL; its window is enforced at read time only.

        Args:
            user_id: The DSB user id confirming ownership.
            raw_token: The raw token carried by the confirmation link.

        Returns:
            ``{"eligible": True, "expires_at": <iso>}`` on success.

        Raises:
            InvalidTokenError: Missing, used, expired, or hash-mismatched token.
        """
        table_name = self._settings.membership_table

        try:
            response = self._dynamodb_client.get_item(
                TableName=table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": VERIFICATION_TOKEN_SK},
                },
            )
        except ClientError as exc:
            logger.error(
                "Failed to read verification token for user %s: %s",
                user_id,
                exc.response.get("Error", {}).get("Code"),
            )
            raise

        item = response.get("Item")
        if not item:
            logger.info("No verification token on file for user %s", user_id)
            raise InvalidTokenError("Invalid or expired verification token")

        # Already consumed — single-use (Requirement 4.5).
        if item.get("used", {}).get("BOOL", False):
            logger.info("Verification token already used for user %s", user_id)
            raise InvalidTokenError("Invalid or expired verification token")

        # Read-time expiry check against the stored 24h epoch, regardless of the
        # DynamoDB TTL sweep latency (Requirement 4.5).
        now = datetime.now(timezone.utc)
        expiry_epoch_raw = item.get("expires_at", {}).get("N")
        try:
            expiry_epoch = int(expiry_epoch_raw) if expiry_epoch_raw is not None else 0
        except (TypeError, ValueError):
            expiry_epoch = 0
        if expiry_epoch <= int(now.timestamp()):
            logger.info("Verification token expired for user %s", user_id)
            raise InvalidTokenError("Invalid or expired verification token")

        # Hash comparison: only the hash is stored, so hash the submitted token
        # and compare in constant time.
        stored_hash = item.get("token_hash", {}).get("S", "")
        if not stored_hash or not secrets.compare_digest(
            _hash_token(raw_token), stored_hash
        ):
            logger.info("Verification token hash mismatch for user %s", user_id)
            raise InvalidTokenError("Invalid or expired verification token")

        # Conditionally mark the token used. The ``used = false`` guard means a
        # concurrent double-confirm can mark it used at most once; the loser of
        # the race gets a ConditionalCheckFailed and is treated as invalid.
        try:
            self._dynamodb_client.update_item(
                TableName=table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": VERIFICATION_TOKEN_SK},
                },
                UpdateExpression="SET #used = :true",
                ConditionExpression="#used = :false",
                ExpressionAttributeNames={"#used": "used"},
                ExpressionAttributeValues={
                    ":true": {"BOOL": True},
                    ":false": {"BOOL": False},
                },
            )
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code == "ConditionalCheckFailedException":
                # Lost the single-use race: another confirmation already
                # consumed this token. No eligibility change here.
                logger.info("Verification token concurrently used for user %s", user_id)
                raise InvalidTokenError(
                    "Invalid or expired verification token"
                ) from exc
            logger.error(
                "Failed to mark verification token used for user %s: %s",
                user_id,
                code,
            )
            raise

        # Grant eligibility: expires_at is an ISO-8601 timestamp 365 days out.
        # This item carries NO DynamoDB TTL — the window is enforced at read
        # time only (see get_eligibility).
        academic_email = item.get("academic_email", {}).get("S", "")
        verified_at = now.isoformat()
        expires_at = (now + timedelta(seconds=ELIGIBILITY_TTL_SECONDS)).isoformat()

        eligibility_item = {
            "PK": {"S": f"USER#{user_id}"},
            "SK": {"S": ELIGIBILITY_SK},
            "verified_at": {"S": verified_at},
            "expires_at": {"S": expires_at},
            "updated_at": {"S": verified_at},
        }
        if academic_email:
            eligibility_item["academic_email"] = {"S": academic_email}

        try:
            self._dynamodb_client.put_item(
                TableName=table_name,
                Item=eligibility_item,
            )
        except ClientError as exc:
            logger.error(
                "Failed to write eligibility record for user %s: %s",
                user_id,
                exc.response.get("Error", {}).get("Code"),
            )
            raise

        logger.info("Student Builder eligibility granted for user %s", user_id)
        return {"eligible": True, "expires_at": expires_at}

    def get_eligibility(self, user_id: str) -> dict | None:
        """Return the user's active Student Builder eligibility, or ``None``.

        Reads the ``STUDENT_ELIGIBILITY`` item and returns a plain dict with
        ``academic_email``, ``verified_at``, and ``expires_at`` only when
        ``expires_at`` is strictly later than now (Requirements 4.7/4.8). The
        comparison is enforced at read time; the eligibility item has no
        DynamoDB TTL, so a record whose window has passed returns ``None``
        rather than relying on auto-deletion.

        Args:
            user_id: The DSB user id to look up.

        Returns:
            The eligibility record as a dict when active, otherwise ``None``.
        """
        try:
            response = self._dynamodb_client.get_item(
                TableName=self._settings.membership_table,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": ELIGIBILITY_SK},
                },
            )
        except ClientError as exc:
            logger.error(
                "Failed to read eligibility record for user %s: %s",
                user_id,
                exc.response.get("Error", {}).get("Code"),
            )
            raise

        item = response.get("Item")
        if not item:
            return None

        expires_at = item.get("expires_at", {}).get("S")
        if not expires_at:
            return None

        # Read-time expiry: active iff expires_at is strictly after now.
        try:
            expires_dt = datetime.fromisoformat(expires_at)
        except ValueError:
            logger.warning(
                "Unparseable eligibility expires_at for user %s: %r",
                user_id,
                expires_at,
            )
            return None

        if expires_dt.tzinfo is None:
            expires_dt = expires_dt.replace(tzinfo=timezone.utc)

        if expires_dt <= datetime.now(timezone.utc):
            return None

        return {
            "academic_email": item.get("academic_email", {}).get("S"),
            "verified_at": item.get("verified_at", {}).get("S"),
            "expires_at": expires_at,
        }

    def _get_username(self, user_id: str) -> str | None:
        """Return the user's display name from their PROFILE record, or None.

        Mirrors ``StripeService._get_user_display_name``: the PROFILE record
        lives in the progress table under ``USER#{user_id}`` / ``PROFILE``. Any
        read failure is swallowed so a missing profile never blocks sending the
        verification email (the caller falls back to a generic greeting).
        """
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
