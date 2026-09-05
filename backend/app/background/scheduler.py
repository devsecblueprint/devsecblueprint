"""APScheduler setup and Discord reconciliation job.

The scheduler is started/stopped by the FastAPI lifespan context manager
in main.py. The reconciliation job runs hourly. For each active member it
first reconciles the membership tier against Stripe (source of truth, so
missed subscription webhooks self-heal) and then syncs Discord roles to
match. Real-time changes are handled by event-driven webhook syncs; this
sweep is the periodic safety net.

The credential expiry check job runs every 24 hours, transitioning
ACTIVE credentials approaching expiry to RENEWAL_ELIGIBLE and
RENEWAL_ELIGIBLE credentials past expiry to EXPIRED.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 7.3, 7.4, 14.5, 14.6
"""

import logging
from datetime import datetime, timezone, timedelta

from app.dependencies import get_settings
from app.models.certification import CandidateStatus, CredentialStatus
from app.services.certification.completionist import CompletionistService
from app.services.certification.db import CertificationDB
from app.services.email import (
    send_credential_expired_notification,
    send_credential_renewal_notification,
)
from app.services.discord_sync import reconcile_all_members

logger = logging.getLogger("app.scheduler")


async def run_reconciliation() -> None:
    """Run Discord role reconciliation.

    Compares DynamoDB membership records against actual Discord roles
    and syncs any differences. Called by apscheduler hourly.

    On success, logs a summary of roles added, removed, or unchanged.
    On failure, logs the error without re-raising so the scheduler
    continues running on the next interval.

    Requirements: 6.1, 6.2, 6.4, 6.5
    """
    try:
        result = await reconcile_all_members()
        logger.info(
            "Reconciliation completed",
            extra={
                "roles_added": result.get("added", 0),
                "roles_removed": result.get("removed", 0),
                "unchanged": result.get("unchanged", 0),
                "skipped": result.get("skipped", 0),
                "failed": result.get("failed", 0),
                "stripe_reconciled": result.get("stripe_reconciled", 0),
                "stripe_changed": result.get("stripe_changed", 0),
            },
        )
    except Exception as exc:
        logger.error(
            "Reconciliation failed",
            extra={"error": str(exc), "error_type": type(exc).__name__},
        )


async def run_credential_expiry_check() -> None:
    """Run credential expiry background check.

    Queries credentials using the CredentialExpiry GSI to find:
    1. ACTIVE credentials within 30 days of expiry → transition to RENEWAL_ELIGIBLE
    2. RENEWAL_ELIGIBLE credentials past expiry → transition to EXPIRED

    For each transition:
    - Updates the credential status
    - For EXPIRED: updates the associated Candidate_Record status to EXPIRED
    - Triggers CompletionistService.evaluate() for affected users
    - Sends appropriate notification emails

    On failure, logs the error without re-raising so the scheduler
    continues running on the next interval.

    Requirements: 7.3, 7.4, 14.5, 14.6
    """
    try:
        settings = get_settings()
        db = CertificationDB(settings)
        completionist_service = CompletionistService(settings)

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        renewal_threshold_iso = (now + timedelta(days=30)).isoformat()

        renewed_count = 0
        expired_count = 0

        # Step 1: ACTIVE credentials where expires_at <= now + 30 days
        # → transition to RENEWAL_ELIGIBLE
        active_approaching_expiry = db.query_credentials_by_status_and_expiry(
            status=CredentialStatus.ACTIVE.value,
            expires_before=renewal_threshold_iso,
        )

        for credential in active_approaching_expiry:
            credential_id = credential.get("credential_id", "")
            user_id = credential.get("user_id", "")
            pathway_id = credential.get("pathway_id", "")
            expires_at = credential.get("expires_at", "")

            # Check if already past expiry — should go straight to EXPIRED
            if expires_at and expires_at <= now_iso:
                # This credential has already expired — handle in step 2
                continue

            try:
                db.update_credential_status(
                    user_id,
                    credential_id,
                    CredentialStatus.RENEWAL_ELIGIBLE.value,
                )
                renewed_count += 1

                # Send renewal notification email
                _send_renewal_email(db, user_id, pathway_id, credential_id, expires_at)

                # Trigger completionist re-evaluation
                completionist_service.evaluate(user_id)

            except Exception:
                logger.error(
                    "Failed to transition credential %s to RENEWAL_ELIGIBLE",
                    credential_id,
                    exc_info=True,
                )

        # Step 2: RENEWAL_ELIGIBLE credentials where expires_at <= now
        # → transition to EXPIRED
        renewal_past_expiry = db.query_credentials_by_status_and_expiry(
            status=CredentialStatus.RENEWAL_ELIGIBLE.value,
            expires_before=now_iso,
        )

        # Also handle ACTIVE credentials that are already past expiry
        # (caught by the filter in step 1 but skipped there)
        active_past_expiry = [
            c for c in active_approaching_expiry if c.get("expires_at", "") <= now_iso
        ]
        all_past_expiry = renewal_past_expiry + active_past_expiry

        for credential in all_past_expiry:
            credential_id = credential.get("credential_id", "")
            user_id = credential.get("user_id", "")
            pathway_id = credential.get("pathway_id", "")

            try:
                db.update_credential_status(
                    user_id,
                    credential_id,
                    CredentialStatus.EXPIRED.value,
                )
                expired_count += 1

                # Update the associated Candidate_Record status to EXPIRED
                try:
                    db.update_candidate_status(
                        user_id,
                        pathway_id,
                        CandidateStatus.EXPIRED.value,
                    )
                except Exception:
                    logger.error(
                        "Failed to update candidate status to EXPIRED for "
                        "user %s pathway %s",
                        user_id,
                        pathway_id,
                        exc_info=True,
                    )

                # Send expired notification email
                _send_expired_email(db, user_id, pathway_id, credential_id)

                # Trigger completionist re-evaluation
                completionist_service.evaluate(user_id)

            except Exception:
                logger.error(
                    "Failed to transition credential %s to EXPIRED",
                    credential_id,
                    exc_info=True,
                )

        logger.info(
            "Credential expiry check completed",
            extra={
                "renewed": renewed_count,
                "expired": expired_count,
            },
        )

    except Exception as exc:
        logger.error(
            "Credential expiry check failed",
            extra={"error": str(exc), "error_type": type(exc).__name__},
        )


def _get_user_email(db: CertificationDB, user_id: str) -> str | None:
    """Read the user's email from their PROFILE record.

    Args:
        db: CertificationDB instance (used for its DynamoDB client).
        user_id: User identifier.

    Returns:
        Email string or None if not found.
    """
    try:
        response = db._dynamodb.get_item(
            TableName=db._table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "PROFILE"},
            },
            ProjectionExpression="email, username",
        )
        item = response.get("Item")
        if not item:
            return None
        return item.get("email", {}).get("S")
    except Exception:
        logger.error("Failed to read email for user %s", user_id, exc_info=True)
        return None


def _get_user_username(db: CertificationDB, user_id: str) -> str:
    """Read the user's username from their PROFILE record.

    Args:
        db: CertificationDB instance.
        user_id: User identifier.

    Returns:
        Username string or empty string if not found.
    """
    try:
        response = db._dynamodb.get_item(
            TableName=db._table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "PROFILE"},
            },
            ProjectionExpression="username",
        )
        item = response.get("Item")
        if not item:
            return ""
        return item.get("username", {}).get("S", "")
    except Exception:
        logger.error("Failed to read username for user %s", user_id, exc_info=True)
        return ""


def _get_pathway_display_name(db: CertificationDB, pathway_id: str) -> str:
    """Get the display name for a pathway.

    Args:
        db: CertificationDB instance.
        pathway_id: Pathway identifier.

    Returns:
        Display name string or the pathway_id as fallback.
    """
    try:
        pathway = db.get_active_pathway(pathway_id)
        if pathway:
            return pathway.get("display_name", pathway_id)
    except Exception:
        logger.error(
            "Failed to get pathway display name for %s", pathway_id, exc_info=True
        )
    return pathway_id


def _send_renewal_email(
    db: CertificationDB,
    user_id: str,
    pathway_id: str,
    credential_id: str,
    expires_at: str,
) -> None:
    """Send a renewal reminder email for a credential approaching expiry.

    Failures are logged but never block the expiry check.
    """
    try:
        email = _get_user_email(db, user_id)
        if not email:
            return

        username = _get_user_username(db, user_id)
        pathway_name = _get_pathway_display_name(db, pathway_id)

        send_credential_renewal_notification(
            email=email,
            username=username,
            pathway=pathway_name,
            credential_id=credential_id,
            expires_at=expires_at,
        )
    except Exception:
        logger.error(
            "Failed to send renewal email for credential %s",
            credential_id,
            exc_info=True,
        )


def _send_expired_email(
    db: CertificationDB,
    user_id: str,
    pathway_id: str,
    credential_id: str,
) -> None:
    """Send an expiration notification email for a credential that has expired.

    Failures are logged but never block the expiry check.
    """
    try:
        email = _get_user_email(db, user_id)
        if not email:
            return

        username = _get_user_username(db, user_id)
        pathway_name = _get_pathway_display_name(db, pathway_id)

        send_credential_expired_notification(
            email=email,
            username=username,
            pathway=pathway_name,
            credential_id=credential_id,
        )
    except Exception:
        logger.error(
            "Failed to send expired email for credential %s",
            credential_id,
            exc_info=True,
        )
