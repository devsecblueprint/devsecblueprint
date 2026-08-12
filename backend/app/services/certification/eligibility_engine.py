"""Eligibility Engine for the DSB Certification & Credentialing Program.

Evaluates whether a candidate is eligible for credential issuance based on
a single-gate check: review_gate PASSED + valid full_name.

This service is read-only evaluation — it does NOT issue credentials or
perform DynamoDB writes. Credential issuance is handled by the caller
(the review session service or router layer).

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

import logging

from app.config import Settings
from app.models.certification import (
    CandidateStatus,
    EligibilityResult,
    ReviewSessionStatus,
)
from app.services.certification.db import CertificationDB

logger = logging.getLogger(__name__)


class EligibilityEngine:
    """Evaluates candidate eligibility for credential issuance.

    Single-gate logic:
    1. Check review_gate.status == PASSED
    2. Check full_name is valid (non-empty, non-whitespace)
    3. Check if already AWARDED (idempotent return)
    4. If all checks pass, return eligible=True

    This engine is synchronous, triggered when a review outcome is recorded.
    It does NOT call credential issuance — that responsibility belongs to
    the caller (review session service or router).
    """

    def __init__(self, settings: Settings) -> None:
        self._db = CertificationDB(settings)

    def evaluate(self, user_id: str, pathway_id: str) -> EligibilityResult:
        """Evaluate whether a candidate is eligible for credential issuance.

        Args:
            user_id: The user identifier.
            pathway_id: The pathway identifier.

        Returns:
            EligibilityResult indicating eligibility status, blocking reasons,
            or existing credential_id if already awarded.
        """
        # Step 1: Read the Candidate_Record from DynamoDB
        candidate = self._db.get_candidate_record(user_id, pathway_id)

        if candidate is None:
            logger.warning(
                "No candidate record found for user %s pathway %s",
                user_id,
                pathway_id,
            )
            return EligibilityResult(
                eligible=False,
                blocking_reasons=["candidate_record_not_found"],
            )

        # Step 2: Check if review_gate.status == PASSED
        review_gate_status = candidate.get("review_gate", {}).get("status")

        if review_gate_status != ReviewSessionStatus.PASSED.value:
            logger.info(
                "User %s pathway %s: review gate not passed (status=%s)",
                user_id,
                pathway_id,
                review_gate_status,
            )
            return EligibilityResult(
                eligible=False,
                blocking_reasons=["review_session_not_passed"],
            )

        # Step 3: Read the user's profile to check full_name
        full_name = self._db.get_user_full_name(user_id)

        if full_name is None or full_name.strip() == "":
            logger.info(
                "User %s pathway %s: full_name not set or empty",
                user_id,
                pathway_id,
            )
            return EligibilityResult(
                eligible=False,
                blocking_reasons=["full_name_required"],
            )

        # Step 4: Check if the candidate is already AWARDED (idempotent)
        candidate_status = candidate.get("candidate_status")

        if candidate_status == CandidateStatus.AWARDED.value:
            existing_credential_id = candidate.get("credential_id")
            logger.info(
                "User %s pathway %s: already AWARDED with credential %s",
                user_id,
                pathway_id,
                existing_credential_id,
            )
            return EligibilityResult(
                eligible=True,
                credential_id=existing_credential_id,
            )

        # Step 5: All checks passed — candidate is eligible
        logger.info(
            "User %s pathway %s: eligible for credential issuance",
            user_id,
            pathway_id,
        )
        return EligibilityResult(eligible=True, blocking_reasons=[])
