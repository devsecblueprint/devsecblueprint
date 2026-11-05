"""Verification router — /api/verification/* routes.

Exposes the Student Builder academic-email verification flow backed by
:class:`app.services.verification_service.VerificationService`:

- POST /api/verification/student/submit — begin verification (authenticated)
- POST /api/verification/student/confirm — confirm ownership (authenticated)
- GET  /api/verification/student/eligibility — read eligibility (authenticated)

Authentication:
- All three routes require a JWT via ``Depends(get_current_user)`` and resolve
  the user id from the ``sub`` claim (401 if missing), mirroring ``stripe.py``.

Rate limiting:
- ``submit`` and ``confirm`` are rate-limited per user to blunt email-bombing
  and token-guessing. The contract (see design) is simply "reject with 429 past
  a per-user threshold." No rate-limiting middleware exists in the codebase, so
  this module ships a small, dependency-free in-memory fixed-window limiter
  (:class:`_FixedWindowRateLimiter`). It is intentionally simple: a per-user
  request count within a fixed time window, reset when the window rolls over.
  This is adequate for a single-process guard; a distributed deployment would
  swap in a shared (e.g. DynamoDB) counter behind the same interface.

Error mapping (VerificationService -> HTTP):
- InvalidEmailError  -> 400
- NotAcademicError   -> 422
- ApyHubUnavailable  -> 503
- EmailSendError     -> 502
- InvalidTokenError  -> 400
- unexpected Exception -> 500

Requirements: 3.2, 3.3, 3.4, 3.6, 4.2, 4.3, 4.5, 4.7, 4.8
"""

import logging
import threading
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.jwt import get_current_user
from app.config import Settings
from app.dependencies import get_settings
from app.services.verification_service import (
    ApyHubUnavailable,
    EmailSendError,
    InvalidEmailError,
    InvalidTokenError,
    NotAcademicError,
    VerificationService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/verification", tags=["verification"])


# ------------------------------------------------------------------
# Request / response models
# ------------------------------------------------------------------


class StudentVerifySubmitRequest(BaseModel):
    """Request body for POST /api/verification/student/submit."""

    academic_email: str = Field(..., min_length=1)


class StudentVerifyConfirmRequest(BaseModel):
    """Request body for POST /api/verification/student/confirm."""

    token: str = Field(..., min_length=1)


class StudentEligibilityResponse(BaseModel):
    """Response body for GET /api/verification/student/eligibility."""

    eligible: bool
    expires_at: str | None = None
    academic_email: str | None = None
    verified_at: str | None = None


# ------------------------------------------------------------------
# Rate limiting (lightweight, in-memory, per-user fixed window)
# ------------------------------------------------------------------


class _FixedWindowRateLimiter:
    """A minimal per-key fixed-window request limiter.

    Allows up to ``max_requests`` calls for a given key within each
    ``window_seconds`` window. When a key's window has elapsed, its counter
    resets. This is a single-process, in-memory guard — intentionally simple,
    not a distributed rate limiter. The contract it satisfies is only
    "reject past the per-user threshold" (HTTP 429 at the router).
    """

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._lock = threading.Lock()
        # key -> (window_start_epoch, count_in_window)
        self._state: dict[str, tuple[float, int]] = {}

    def allow(self, key: str) -> bool:
        """Record an attempt for ``key``; return False if over the threshold."""
        now = time.monotonic()
        with self._lock:
            window_start, count = self._state.get(key, (now, 0))
            if now - window_start >= self._window_seconds:
                # Window rolled over: start a fresh window for this key.
                window_start, count = now, 0
            count += 1
            self._state[key] = (window_start, count)
            return count <= self._max_requests


# Per-user thresholds. Submit sends an email, so it is the tighter limit;
# confirm guards against token-guessing. Values are deliberately generous for
# legitimate use while still blunting abuse.
_SUBMIT_RATE_LIMITER = _FixedWindowRateLimiter(max_requests=5, window_seconds=3600)
_CONFIRM_RATE_LIMITER = _FixedWindowRateLimiter(max_requests=10, window_seconds=3600)


def _enforce_rate_limit(limiter: _FixedWindowRateLimiter, user_id: str) -> None:
    """Raise HTTP 429 when ``user_id`` exceeds ``limiter``'s threshold."""
    if not limiter.allow(user_id):
        logger.warning("Rate limit exceeded for user %s", user_id)
        raise HTTPException(status_code=429, detail="Too many requests")


# ------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------


def get_verification_service(
    settings: Settings = Depends(get_settings),
) -> VerificationService:
    """Provide a VerificationService instance."""
    return VerificationService(settings)


# ------------------------------------------------------------------
# Routes (all require JWT)
# ------------------------------------------------------------------


@router.post("/student/submit", status_code=202)
async def submit_student_verification(
    body: StudentVerifySubmitRequest,
    user: dict = Depends(get_current_user),
    service: VerificationService = Depends(get_verification_service),
) -> dict[str, str]:
    """Begin academic-email verification for the authenticated user.

    Returns 202 Accepted on success (a confirmation email has been queued).

    Error mapping:
    - InvalidEmailError  -> 400 (syntactically invalid email)
    - NotAcademicError   -> 422 (not an academic domain)
    - ApyHubUnavailable  -> 503 (validation service unavailable / missing config)
    - EmailSendError     -> 502 (confirmation email could not be sent)
    """
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    _enforce_rate_limit(_SUBMIT_RATE_LIMITER, user_id)

    try:
        service.submit(user_id, body.academic_email)
        return {"status": "accepted"}
    except InvalidEmailError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotAcademicError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ApyHubUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    except EmailSendError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during verification submit for user %s: %s",
            user_id,
            type(e).__name__,
        )
        raise HTTPException(status_code=500, detail="Verification failed")


@router.post("/student/confirm")
async def confirm_student_verification(
    body: StudentVerifyConfirmRequest,
    user: dict = Depends(get_current_user),
    service: VerificationService = Depends(get_verification_service),
) -> dict:
    """Confirm academic-email ownership and grant Student Builder eligibility.

    Returns 200 with ``{eligible, expires_at}`` on success.

    Error mapping:
    - InvalidTokenError -> 400 (missing, used, expired, or mismatched token)
    """
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    _enforce_rate_limit(_CONFIRM_RATE_LIMITER, user_id)

    try:
        result = service.confirm(user_id, body.token)
        return {
            "eligible": result.get("eligible", False),
            "expires_at": result.get("expires_at"),
        }
    except InvalidTokenError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during verification confirm for user %s: %s",
            user_id,
            type(e).__name__,
        )
        raise HTTPException(status_code=500, detail="Confirmation failed")


@router.get("/student/eligibility", response_model=StudentEligibilityResponse)
async def get_student_eligibility(
    user: dict = Depends(get_current_user),
    service: VerificationService = Depends(get_verification_service),
) -> StudentEligibilityResponse:
    """Return the authenticated user's Student Builder eligibility.

    Eligibility is active iff an unexpired eligibility record exists
    (Requirements 4.7/4.8). When active, the response also carries the
    registered ``academic_email`` and ``verified_at`` from the record so the
    dashboard Membership card can show them. Returns
    ``{eligible: false, expires_at: null, academic_email: null,
    verified_at: null}`` when there is no active record.
    """
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        record = service.get_eligibility(user_id)
    except Exception as e:
        logger.error(
            "Unexpected error reading eligibility for user %s: %s",
            user_id,
            type(e).__name__,
        )
        raise HTTPException(status_code=500, detail="Failed to read eligibility")

    if record and record.get("expires_at"):
        return StudentEligibilityResponse(
            eligible=True,
            expires_at=record["expires_at"],
            academic_email=record.get("academic_email"),
            verified_at=record.get("verified_at"),
        )
    return StudentEligibilityResponse(
        eligible=False, expires_at=None, academic_email=None, verified_at=None
    )
