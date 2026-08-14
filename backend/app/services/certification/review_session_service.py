"""Review Session Service for the DSB Certification & Credentialing Program.

Handles capstone submission, combined review session outcome recording,
and revision history retrieval. Supports initial certification and
re-certification flows.

Requirements: 5.1, 5.2, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 8.3, 8.8
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.config import Settings
from app.models.certification import (
    CandidateStatus,
    EligibilityResult,
    ReviewOutcomeRequest,
    ReviewSessionStatus,
)
from app.services.certification.db import CertificationDB
from app.services.certification.eligibility_engine import EligibilityEngine
from app.services.email import (
    send_new_submission_admin_notification,
    send_submission_received_notification,
)

logger = logging.getLogger(__name__)


class ReviewSessionService:
    """Manages capstone submissions, review outcomes, and revision history.

    Coordinates the combined review session workflow:
    1. Learner submits capstone → PENDING_REVIEW
    2. Reviewer records outcome → PASSED / REVISIONS_REQUIRED / FAILED
    3. If PASSED → triggers eligibility evaluation

    Supports re-certification by resetting candidate state for learners
    with expired or expiring credentials.
    """

    def __init__(self, settings: Settings) -> None:
        self._db = CertificationDB(settings)
        self._eligibility_engine = EligibilityEngine(settings)
        self._settings = settings

    def submit_capstone(
        self, user_id: str, pathway_id: str, submission_url: str
    ) -> dict:
        """Record a capstone submission and create a review session.

        Handles both initial submissions and re-certification submissions.

        Args:
            user_id: The learner's user identifier.
            pathway_id: The pathway identifier.
            submission_url: The repository/submission URL.

        Returns:
            Dict containing submission details (pathway_id, revision_number,
            status, submission_url, submitted_at).

        Raises:
            ValueError: If the pathway is not found (no active definition).
        """
        # Step 1: Get the active pathway definition
        pathway = self._db.get_active_pathway(pathway_id)
        if pathway is None:
            raise ValueError(
                f"Pathway '{pathway_id}' not found or has no active version."
            )

        now = datetime.now(timezone.utc).isoformat()

        # Step 2: Get or create the Candidate_Record
        candidate = self._db.get_candidate_record(user_id, pathway_id)

        if candidate is None:
            # New candidate: create record with IN_PROGRESS status
            candidate_record = {
                "pathway_id": pathway_id,
                "pathway_version": pathway["version"],
                "candidate_status": CandidateStatus.IN_PROGRESS.value,
                "review_gate": {
                    "status": ReviewSessionStatus.PENDING_REVIEW.value,
                },
                "started_at": now,
                "updated_at": now,
            }
            self._db.put_candidate_record(user_id, candidate_record)
            logger.info(
                "Created new candidate record for user %s pathway %s",
                user_id,
                pathway_id,
            )

        elif candidate["candidate_status"] in (
            CandidateStatus.EXPIRED.value,
            CandidateStatus.AWARDED.value,
        ):
            # Re-certification: reset candidate to IN_PROGRESS
            # This handles both EXPIRED candidates and AWARDED candidates
            # whose credential is RENEWAL_ELIGIBLE or EXPIRED
            prior_credential_id = candidate.get("credential_id")
            candidate_record = {
                "pathway_id": pathway_id,
                "pathway_version": pathway["version"],
                "candidate_status": CandidateStatus.IN_PROGRESS.value,
                "review_gate": {
                    "status": ReviewSessionStatus.PENDING_REVIEW.value,
                },
                "started_at": now,
                "updated_at": now,
            }
            if prior_credential_id:
                candidate_record["prior_credential_id"] = prior_credential_id
            self._db.put_candidate_record(user_id, candidate_record)
            logger.info(
                "Reset candidate record for re-certification: user %s "
                "pathway %s (prior_credential_id=%s)",
                user_id,
                pathway_id,
                prior_credential_id,
            )

        elif (
            candidate["candidate_status"] == CandidateStatus.IN_PROGRESS.value
            and candidate.get("review_gate", {}).get("status")
            == ReviewSessionStatus.REVISIONS_REQUIRED.value
        ):
            # Resubmission after revisions required
            self._db.update_review_gate(
                user_id,
                pathway_id,
                {"status": ReviewSessionStatus.PENDING_REVIEW.value},
            )
            logger.info(
                "Resubmission after REVISIONS_REQUIRED: user %s pathway %s",
                user_id,
                pathway_id,
            )

        elif candidate["candidate_status"] == CandidateStatus.IN_PROGRESS.value:
            # Already in progress — update review gate to PENDING_REVIEW
            self._db.update_review_gate(
                user_id,
                pathway_id,
                {"status": ReviewSessionStatus.PENDING_REVIEW.value},
            )

        else:
            raise ValueError(
                f"Cannot submit capstone: candidate status is "
                f"'{candidate['candidate_status']}' which does not allow "
                f"new submissions."
            )

        # Step 3: Determine the next revision_number
        latest_session = self._db.get_latest_review_session(user_id, pathway_id)
        if latest_session is not None:
            revision_number = latest_session["revision_number"] + 1
        else:
            revision_number = 1

        # Step 4: Create a new Combined_Review_Session record
        session_record = {
            "pathway_id": pathway_id,
            "revision_number": revision_number,
            "status": ReviewSessionStatus.PENDING_REVIEW.value,
            "rubric_scores": {},
            "evaluation_dimensions": {},
            "submission_url": submission_url,
            "submitted_at": now,
        }
        self._db.put_review_session(user_id, session_record)
        logger.info(
            "Created review session rev %d for user %s pathway %s",
            revision_number,
            user_id,
            pathway_id,
        )

        # Step 5: Send notifications via email service
        pathway_display_name = pathway.get("display_name", pathway_id)
        learner_email = self._db.get_user_email(user_id)
        learner_username = self._db.get_user_username(user_id)

        if learner_email:
            send_submission_received_notification(
                email=learner_email,
                username=learner_username or user_id,
                pathway=pathway_display_name,
            )

        # Notify reviewers/admins of new submission
        reviewer_emails = self._get_reviewer_emails()
        if reviewer_emails:
            send_new_submission_admin_notification(
                reviewer_emails=reviewer_emails,
                candidate_name=learner_username or user_id,
                pathway=pathway_display_name,
                candidate_email=learner_email or "",
            )

        # Step 6: Return submission details
        return {
            "pathway_id": pathway_id,
            "revision_number": revision_number,
            "status": ReviewSessionStatus.PENDING_REVIEW.value,
            "submission_url": submission_url,
            "submitted_at": now,
        }

    def record_review_outcome(
        self,
        reviewer_id: str,
        user_id: str,
        pathway_id: str,
        outcome: ReviewOutcomeRequest,
    ) -> Optional[EligibilityResult]:
        """Record the combined review session outcome.

        Updates the review session record and candidate review gate.
        If the outcome is PASSED, triggers the Eligibility Engine.

        Args:
            reviewer_id: The reviewer's user identifier.
            user_id: The learner's user identifier.
            pathway_id: The pathway identifier.
            outcome: The review outcome request with rubric scores,
                evaluation dimensions, reviewer notes, and status.

        Returns:
            EligibilityResult if the outcome is PASSED (caller handles
            credential issuance), or None if not eligible.

        Raises:
            ValueError: If no review session is found or it's not in
                PENDING_REVIEW status.
        """
        # Step 1: Get the latest review session for user/pathway
        latest_session = self._db.get_latest_review_session(user_id, pathway_id)
        if latest_session is None:
            raise ValueError(
                f"No review session found for user '{user_id}' "
                f"pathway '{pathway_id}'."
            )

        # Step 2: Validate it's in PENDING_REVIEW status
        if latest_session["status"] != ReviewSessionStatus.PENDING_REVIEW.value:
            raise ValueError(
                f"Review session for user '{user_id}' pathway '{pathway_id}' "
                f"is in status '{latest_session['status']}', expected "
                f"'{ReviewSessionStatus.PENDING_REVIEW.value}'."
            )

        now = datetime.now(timezone.utc).isoformat()

        # Step 3: Update the review session record with the outcome
        updated_session = {
            "pathway_id": pathway_id,
            "revision_number": latest_session["revision_number"],
            "status": outcome.status.value,
            "rubric_scores": outcome.rubric_scores,
            "evaluation_dimensions": outcome.evaluation_dimensions,
            "reviewer_id": reviewer_id,
            "reviewer_notes": outcome.reviewer_notes,
            "submission_url": latest_session["submission_url"],
            "submitted_at": latest_session["submitted_at"],
            "reviewed_at": now,
        }
        self._db.put_review_session(user_id, updated_session)
        logger.info(
            "Recorded review outcome %s for user %s pathway %s rev %d",
            outcome.status.value,
            user_id,
            pathway_id,
            latest_session["revision_number"],
        )

        # Step 4: Update the Candidate_Record review_gate with the outcome
        gate_data = {
            "status": outcome.status.value,
            "reviewed_at": now,
            "reviewer_id": reviewer_id,
        }
        self._db.update_review_gate(user_id, pathway_id, gate_data)

        # Step 5: If PASSED, call the EligibilityEngine
        if outcome.status == ReviewSessionStatus.PASSED:
            eligibility_result = self._eligibility_engine.evaluate(user_id, pathway_id)
            logger.info(
                "Eligibility evaluation for user %s pathway %s: eligible=%s",
                user_id,
                pathway_id,
                eligibility_result.eligible,
            )
            return eligibility_result

        # Step 6: If REVISIONS_REQUIRED or FAILED, return None
        logger.info(
            "Review outcome %s for user %s pathway %s — not eligible",
            outcome.status.value,
            user_id,
            pathway_id,
        )
        return None

    def get_revision_history(self, user_id: str, pathway_id: str) -> list[dict]:
        """Get the full revision history for a candidate's review sessions.

        Args:
            user_id: The learner's user identifier.
            pathway_id: The pathway identifier.

        Returns:
            List of review session dicts ordered by revision number (ascending).
        """
        return self._db.get_review_history(user_id, pathway_id)

    def _get_reviewer_emails(self) -> list[str]:
        """Get the list of reviewer/admin notification email addresses.

        Always includes community@devsecblueprint.com as the primary
        notification target. Also appends the configured contact_notify_email
        if set and not already included.

        Returns:
            List of email addresses to notify.
        """
        emails = ["community@devsecblueprint.com"]
        contact_email = self._settings.contact_notify_email
        if contact_email and contact_email not in emails:
            emails.append(contact_email)
        return emails
