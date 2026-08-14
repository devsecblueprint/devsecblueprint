"""Credential Lifecycle Service for the DSB Certification & Credentialing Program.

Handles credential issuance, expiry checking, revocation, re-certification,
and admin-initiated grandfathering. All credential state transitions are
managed through this service.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 8.4, 8.5, 9.1, 9.2, 9.3,
              9.4, 9.5, 9.6, 9.7, 9.8
"""

import logging
import secrets
from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta

from app.config import Settings
from app.models.certification import (
    CandidateStatus,
    Credential,
    CredentialStatus,
)
from app.services.certification.db import CertificationDB
from app.services.certification.pathway_config import get_pathway as get_pathway_config

logger = logging.getLogger(__name__)


class CredentialLifecycleService:
    """Manages the full lifecycle of certification credentials.

    Responsibilities:
    - Issue credentials upon eligibility confirmation
    - Grant credentials directly (admin grandfathering)
    - Check expiry status for background jobs
    - Revoke credentials with audit trail
    - Handle re-certification (new credential, old untouched)
    """

    def __init__(self, settings: Settings) -> None:
        self._db = CertificationDB(settings)
        self._credential_validity_months = settings.credential_validity_months

    def issue_credential(
        self,
        user_id: str,
        pathway_id: str,
        pathway_version: str,
        is_recertification: bool = False,
        prior_credential_id: str | None = None,
    ) -> Credential:
        """Issue a new credential for a user who has passed eligibility.

        Generates a unique Credential_ID, computes expiration from config,
        and writes the credential record with a conditional put to prevent
        duplicates. If a duplicate is detected (ConditionalCheckFailedException),
        the existing credential is returned (idempotent).

        Args:
            user_id: The user identifier.
            pathway_id: The pathway identifier.
            pathway_version: The pathway definition version at time of issuance.
            is_recertification: Whether this is a re-certification issuance.
            prior_credential_id: The previous credential ID if re-certifying.

        Returns:
            The issued (or existing) Credential model instance.

        Raises:
            ValueError: If the pathway has no active definition or user has
                no valid full_name.
        """
        # Step 1: Get the pathway config to obtain the pathway_code
        pathway = get_pathway_config(pathway_id)
        if pathway is None:
            raise ValueError(f"No pathway definition found for '{pathway_id}'")
        pathway_code = pathway["pathway_code"]

        # Step 2: Generate a unique Credential_ID
        credential_id = self._generate_credential_id(pathway_code)

        # Step 3: Compute timestamps
        issued_at = datetime.now(timezone.utc).isoformat()
        expires_at = self._compute_expires_at(issued_at)

        # Step 4: Get the user's full_name for the credential record
        full_name = self._db.get_user_full_name(user_id)
        if full_name is None or full_name.strip() == "":
            raise ValueError(f"User '{user_id}' does not have a valid full_name set")

        # Step 5: Build the credential dict
        credential_data: dict = {
            "credential_id": credential_id,
            "pathway_id": pathway_id,
            "pathway_version": pathway_version,
            "credential_status": CredentialStatus.ACTIVE.value,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "full_name_at_issuance": full_name,
            "is_recertification": is_recertification,
            "is_grandfathered": False,
        }

        if prior_credential_id:
            credential_data["prior_credential_id"] = prior_credential_id

        # Step 6: Write credential with conditional put (prevent duplicates)
        try:
            self._db.put_credential(user_id, credential_data)
        except Exception as e:
            # Handle ConditionalCheckFailedException (duplicate)
            error_code = getattr(getattr(e, "response", None), "get", lambda *_: None)
            if hasattr(e, "response") and isinstance(e.response, dict):
                error_code = e.response.get("Error", {}).get("Code", "")
            else:
                error_code = ""

            if error_code == "ConditionalCheckFailedException":
                logger.info(
                    "Credential %s already exists for user %s — returning existing",
                    credential_id,
                    user_id,
                )
                existing = self._db.get_credential(user_id, credential_id)
                if existing:
                    return Credential(**existing)
            raise

        # Step 7: Update the Candidate_Record: set status to AWARDED, set credential_id
        try:
            self._db.put_candidate_record(
                user_id,
                {
                    "pathway_id": pathway_id,
                    "pathway_version": pathway_version,
                    "candidate_status": CandidateStatus.AWARDED.value,
                    "review_gate": {"status": "PASSED"},
                    "started_at": issued_at,
                    "updated_at": issued_at,
                    "credential_id": credential_id,
                    "prior_credential_id": prior_credential_id,
                },
            )
        except Exception:
            logger.error(
                "Failed to update candidate record for user %s pathway %s "
                "after credential issuance %s",
                user_id,
                pathway_id,
                credential_id,
                exc_info=True,
            )
            # Credential was already written; log but don't fail the issuance

        logger.info(
            "Issued credential %s for user %s pathway %s (recert=%s)",
            credential_id,
            user_id,
            pathway_id,
            is_recertification,
        )

        # Step 8: Return a Credential model instance
        return Credential(**credential_data)

    def grant_credential(
        self,
        admin_id: str,
        user_id: str,
        pathway_id: str,
    ) -> Credential:
        """Issue a credential directly via admin grandfathering.

        Bypasses the Combined_Review_Session requirement. Validates that
        the target user has a valid full_name and that an active pathway
        definition exists.

        Args:
            admin_id: The admin user ID performing the grant.
            user_id: The target user to receive the credential.
            pathway_id: The pathway to grant the credential for.

        Returns:
            The issued Credential model instance.

        Raises:
            ValueError: If user has no valid full_name or pathway not found.
        """
        # Step 1: Validate user has a valid full_name set
        full_name = self._db.get_user_full_name(user_id)
        if full_name is None or full_name.strip() == "":
            raise ValueError(
                "Learner must set full name before credential can be issued"
            )

        # Step 2: Verify course completion
        is_complete, missing = self.verify_course_completion(user_id, pathway_id)
        if not is_complete:
            raise ValueError(
                f"Learner has not completed all required content for pathway '{pathway_id}'. "
                f"Missing: {', '.join(missing[:5])}"
                + (f" and {len(missing) - 5} more" if len(missing) > 5 else "")
            )

        # Step 3: Get the pathway definition from config
        pathway = get_pathway_config(pathway_id)
        if pathway is None:
            raise ValueError(f"No pathway definition found for '{pathway_id}'")

        pathway_code = pathway["pathway_code"]
        pathway_version = pathway["version"]

        # Step 4: Generate Credential_ID and compute expires_at
        credential_id = self._generate_credential_id(pathway_code)
        issued_at = datetime.now(timezone.utc).isoformat()
        expires_at = self._compute_expires_at(issued_at)

        # Step 5: Build credential dict with is_grandfathered=True
        credential_data: dict = {
            "credential_id": credential_id,
            "pathway_id": pathway_id,
            "pathway_version": pathway_version,
            "credential_status": CredentialStatus.ACTIVE.value,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "full_name_at_issuance": full_name,
            "is_recertification": False,
            "is_grandfathered": True,
        }

        # Step 6: Write credential via conditional put
        try:
            self._db.put_credential(user_id, credential_data)
        except Exception as e:
            error_code = ""
            if hasattr(e, "response") and isinstance(e.response, dict):
                error_code = e.response.get("Error", {}).get("Code", "")

            if error_code == "ConditionalCheckFailedException":
                logger.info(
                    "Grandfathered credential %s already exists for user %s",
                    credential_id,
                    user_id,
                )
                existing = self._db.get_credential(user_id, credential_id)
                if existing:
                    return Credential(**existing)
            raise

        # Step 7: Create or update Candidate_Record with status=AWARDED directly
        now = datetime.now(timezone.utc).isoformat()
        self._db.put_candidate_record(
            user_id,
            {
                "pathway_id": pathway_id,
                "pathway_version": pathway_version,
                "candidate_status": CandidateStatus.AWARDED.value,
                "review_gate": {"status": "PASSED"},
                "started_at": now,
                "updated_at": now,
                "credential_id": credential_id,
            },
        )

        logger.info(
            "Admin %s granted credential %s to user %s for pathway %s",
            admin_id,
            credential_id,
            user_id,
            pathway_id,
        )

        # Step 8: Return Credential model instance
        return Credential(**credential_data)

    def check_expiry(self, credential_id: str) -> str | None:
        """Check if a credential's status needs updating based on current time.

        For background job use: looks up the credential, determines if a
        status transition is needed based on current time vs expires_at.

        This method does NOT perform writes — the background job handles
        the actual status update.

        Args:
            credential_id: The credential identifier to check.

        Returns:
            The new status string if a transition is needed, None if no change.
        """
        credential = self._db.get_credential_by_id(credential_id)
        if credential is None:
            logger.warning("Credential %s not found for expiry check", credential_id)
            return None

        current_status = credential.get("credential_status")
        expires_at_str = credential.get("expires_at")

        # Only check ACTIVE and RENEWAL_ELIGIBLE credentials
        if current_status not in (
            CredentialStatus.ACTIVE.value,
            CredentialStatus.RENEWAL_ELIGIBLE.value,
        ):
            return None

        if not expires_at_str:
            return None

        now = datetime.now(timezone.utc)
        expires_at = datetime.fromisoformat(expires_at_str)

        # Ensure timezone-aware comparison
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        # Check if expired
        if now >= expires_at:
            if current_status != CredentialStatus.EXPIRED.value:
                return CredentialStatus.EXPIRED.value
            return None

        # Check if within 30-day renewal window
        renewal_threshold = expires_at - relativedelta(days=30)
        if now >= renewal_threshold:
            if current_status != CredentialStatus.RENEWAL_ELIGIBLE.value:
                return CredentialStatus.RENEWAL_ELIGIBLE.value
            return None

        return None

    def revoke_credential(
        self,
        credential_id: str,
        reason: str,
        admin_id: str,
    ) -> Credential:
        """Revoke a credential with reason and audit trail.

        Looks up the credential by credential_id (using GSI), validates
        it's not already revoked, and updates both the credential and
        candidate records.

        Args:
            credential_id: The credential identifier to revoke.
            reason: The reason for revocation.
            admin_id: The admin user ID performing the revocation.

        Returns:
            The updated Credential model instance.

        Raises:
            ValueError: If credential not found or already revoked.
        """
        # Step 1: Look up the credential by credential_id (using GSI)
        credential = self._db.get_credential_by_id(credential_id)
        if credential is None:
            raise ValueError(f"Credential '{credential_id}' not found")

        # Step 2: Validate it's not already REVOKED
        if credential.get("credential_status") == CredentialStatus.REVOKED.value:
            raise ValueError(f"Credential '{credential_id}' is already revoked")

        # Step 3: Update credential: set status, revoked_at, reason, revoked_by
        now = datetime.now(timezone.utc).isoformat()
        user_id = credential.get("user_id")

        if not user_id:
            raise ValueError(
                f"Cannot determine user_id for credential '{credential_id}'"
            )

        # Update the credential record with revocation details
        try:
            self._db._dynamodb.update_item(
                TableName=self._db._table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": f"CREDENTIAL#{credential_id}"},
                },
                UpdateExpression=(
                    "SET credential_status = :revoked, "
                    "revoked_at = :revoked_at, "
                    "revocation_reason = :reason, "
                    "revoked_by = :admin_id, "
                    "GSI_EXPIRY_PK = :revoked"
                ),
                ExpressionAttributeValues={
                    ":revoked": {"S": CredentialStatus.REVOKED.value},
                    ":revoked_at": {"S": now},
                    ":reason": {"S": reason},
                    ":admin_id": {"S": admin_id},
                },
            )
        except Exception:
            logger.error(
                "Failed to revoke credential %s for user %s",
                credential_id,
                user_id,
                exc_info=True,
            )
            raise

        # Step 4: Update the Candidate_Record: set candidate_status=REVOKED
        pathway_id = credential.get("pathway_id")
        if pathway_id:
            try:
                self._db.update_candidate_status(
                    user_id, pathway_id, CandidateStatus.REVOKED.value
                )
            except Exception:
                logger.error(
                    "Failed to update candidate status to REVOKED for "
                    "user %s pathway %s",
                    user_id,
                    pathway_id,
                    exc_info=True,
                )

        logger.info(
            "Admin %s revoked credential %s for user %s (reason: %s)",
            admin_id,
            credential_id,
            user_id,
            reason,
        )

        # Step 5: Return updated Credential
        credential["credential_status"] = CredentialStatus.REVOKED.value
        credential["revoked_at"] = now
        credential["revocation_reason"] = reason
        credential["revoked_by"] = admin_id

        # Remove non-model fields before constructing Credential
        credential.pop("user_id", None)

        return Credential(**credential)

    # ------------------------------------------------------------------
    # Course completion verification
    # ------------------------------------------------------------------

    def verify_course_completion(
        self, user_id: str, pathway_id: str
    ) -> tuple[bool, list[str]]:
        """Verify the learner has completed all required content for the pathway.

        Checks the user's CONTENT# progress records against the pathway's
        learning_requirements list.

        Args:
            user_id: User identifier.
            pathway_id: Pathway identifier.

        Returns:
            Tuple of (is_complete, missing_content_ids).
            If is_complete is True, missing_content_ids is empty.
        """
        pathway = get_pathway_config(pathway_id)
        if pathway is None:
            # No pathway definition exists — skip completion check
            logger.warning(
                "No pathway definition for '%s'; skipping course completion check",
                pathway_id,
            )
            return True, []

        learning_requirements = pathway.get("learning_requirements", [])
        if not learning_requirements:
            # No requirements defined — consider complete
            return True, []

        # Query user's completed content
        completed_content_ids = self._get_user_completed_content(user_id)

        # Find missing requirements
        missing = [
            req for req in learning_requirements if req not in completed_content_ids
        ]

        return len(missing) == 0, missing

    def _get_user_completed_content(self, user_id: str) -> set[str]:
        """Get the set of content IDs the user has completed."""
        try:
            response = self._db._dynamodb.query(
                TableName=self._db._table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk_prefix": {"S": "CONTENT#"},
                },
                ProjectionExpression="SK",
            )
            return {
                item["SK"]["S"].replace("CONTENT#", "")
                for item in response.get("Items", [])
            }
        except Exception:
            logger.error(
                "Failed to query content progress for user %s", user_id, exc_info=True
            )
            return set()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_credential_id(self, pathway_code: str) -> str:
        """Generate a unique Credential_ID.

        Format: DSB-{PATHWAY_CODE}-{8 uppercase hex characters}

        Args:
            pathway_code: The short pathway code (e.g., "DSEP", "CSEP").

        Returns:
            A credential ID string like "DSB-DSEP-8F4C92A1".
        """
        hex_suffix = secrets.token_hex(4).upper()
        return f"DSB-{pathway_code}-{hex_suffix}"

    def _compute_expires_at(self, issued_at: str) -> str:
        """Compute the expiration date from an issuance date.

        Adds credential_validity_months (from settings) to the issued_at
        timestamp.

        Args:
            issued_at: ISO 8601 timestamp string of the issuance date.

        Returns:
            ISO 8601 timestamp string of the expiration date.
        """
        issued_dt = datetime.fromisoformat(issued_at)
        expires_dt = issued_dt + relativedelta(months=self._credential_validity_months)
        return expires_dt.isoformat()
