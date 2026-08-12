"""Completionist Service for the DSB Certification & Credentialing Program.

Auto-calculates the security-engineering-completionist credential based on
the status of both primary pathway credentials and learning requirement
completion.

Requirements: 11.1, 11.2, 11.3, 11.4
"""

import logging

from app.config import Settings
from app.models.certification import CredentialStatus
from app.services.certification.credential_lifecycle import CredentialLifecycleService
from app.services.certification.db import CertificationDB

logger = logging.getLogger(__name__)

COMPLETIONIST_PATHWAY_ID = "security-engineering-completionist"
PRIMARY_PATHWAY_IDS = ("devsecops-engineering", "cloud-security-engineering")


class CompletionistService:
    """Auto-calculates the security-engineering-completionist credential.

    Evaluates whether both primary pathway credentials are ACTIVE and all
    learning requirements for the completionist pathway are completed.
    Issues, restores, or expires the completionist credential accordingly.

    Idempotent: calling evaluate() multiple times produces the same result
    without creating duplicates or state oscillation.
    """

    def __init__(self, settings: Settings) -> None:
        self._db = CertificationDB(settings)
        self._settings = settings

    def evaluate(self, user_id: str) -> None:
        """Evaluate and update completionist credential status.

        Checks prerequisites and updates state accordingly. Idempotent.

        Args:
            user_id: The user identifier to evaluate.
        """
        # Step 1: Get the completionist pathway definition
        pathway = self._db.get_active_pathway(COMPLETIONIST_PATHWAY_ID)
        if pathway is None:
            logger.warning(
                "No active pathway definition for '%s'; skipping completionist evaluation",
                COMPLETIONIST_PATHWAY_ID,
            )
            return

        learning_requirements = pathway.get("learning_requirements", [])
        pathway_version = pathway.get("version", "")

        # Step 2: List all credentials for the user
        credentials = self._db.list_user_credentials(user_id)

        # Step 3: Find ACTIVE credentials for both primary pathways
        both_primary_active = self._check_primary_credentials_active(credentials)

        # Step 4: Check learning requirements completion
        learning_complete = self._check_learning_complete(
            user_id, learning_requirements
        )

        # Step 5: Find existing completionist credential (if any)
        completionist_credential = self._find_completionist_credential(credentials)

        # Step 6: Apply rules
        conditions_met = both_primary_active and learning_complete

        if conditions_met:
            self._handle_conditions_met(
                user_id, pathway_version, completionist_credential
            )
        else:
            self._handle_conditions_not_met(user_id, completionist_credential)

    def _check_primary_credentials_active(self, credentials: list[dict]) -> bool:
        """Check if both primary pathway credentials are ACTIVE.

        Args:
            credentials: List of all user credential dicts.

        Returns:
            True if both devsecops-engineering and cloud-security-engineering
            have at least one ACTIVE credential.
        """
        active_pathways: set[str] = set()
        for cred in credentials:
            pathway_id = cred.get("pathway_id", "")
            status = cred.get("credential_status", "")
            if (
                pathway_id in PRIMARY_PATHWAY_IDS
                and status == CredentialStatus.ACTIVE.value
            ):
                active_pathways.add(pathway_id)

        return len(active_pathways) == len(PRIMARY_PATHWAY_IDS)

    def _check_learning_complete(
        self, user_id: str, learning_requirements: list[str]
    ) -> bool:
        """Check if all learning requirements for the completionist pathway are completed.

        Queries the user's CONTENT# records from the progress table and verifies
        all required content IDs are present.

        Args:
            user_id: The user identifier.
            learning_requirements: List of required content IDs.

        Returns:
            True if all learning requirements are completed.
        """
        if not learning_requirements:
            # No learning requirements defined — consider complete
            return True

        try:
            response = self._db._dynamodb.query(
                TableName=self._db._table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk_prefix": {"S": "CONTENT#"},
                },
                Select="ALL_ATTRIBUTES",
            )

            items = response.get("Items", [])
            completed_content_ids = {
                item["SK"]["S"].replace("CONTENT#", "") for item in items
            }

            return all(req in completed_content_ids for req in learning_requirements)

        except Exception:
            logger.error(
                "Failed to query content records for user %s during "
                "completionist evaluation",
                user_id,
                exc_info=True,
            )
            return False

    def _find_completionist_credential(self, credentials: list[dict]) -> dict | None:
        """Find the most recent completionist credential for the user.

        Looks for credentials with pathway_id matching the completionist
        pathway. If multiple exist (e.g., from re-certification), returns
        the one that is most relevant for state evaluation — preferring
        ACTIVE, then RENEWAL_ELIGIBLE, then EXPIRED.

        Args:
            credentials: List of all user credential dicts.

        Returns:
            The completionist credential dict or None if not found.
        """
        completionist_creds = [
            cred
            for cred in credentials
            if cred.get("pathway_id") == COMPLETIONIST_PATHWAY_ID
        ]

        if not completionist_creds:
            return None

        # Prefer ACTIVE, then RENEWAL_ELIGIBLE, then any other
        priority = {
            CredentialStatus.ACTIVE.value: 0,
            CredentialStatus.RENEWAL_ELIGIBLE.value: 1,
            CredentialStatus.EXPIRED.value: 2,
            CredentialStatus.REVOKED.value: 3,
        }

        completionist_creds.sort(
            key=lambda c: priority.get(c.get("credential_status", ""), 99)
        )

        return completionist_creds[0]

    def _handle_conditions_met(
        self,
        user_id: str,
        pathway_version: str,
        completionist_credential: dict | None,
    ) -> None:
        """Handle case where completionist conditions are met.

        Rules:
        - No completionist credential exists → issue one
        - Completionist credential already ACTIVE → do nothing (idempotent)
        - Completionist credential EXPIRED → issue new one (re-certification)

        Args:
            user_id: The user identifier.
            pathway_version: Current active pathway version.
            completionist_credential: Existing completionist credential or None.
        """
        if completionist_credential is None:
            # No completionist credential → issue one
            self._issue_completionist(user_id, pathway_version)
            return

        current_status = completionist_credential.get("credential_status", "")

        if current_status == CredentialStatus.ACTIVE.value:
            # Already ACTIVE → idempotent, do nothing
            logger.debug(
                "Completionist credential already ACTIVE for user %s; no action needed",
                user_id,
            )
            return

        if current_status in (
            CredentialStatus.EXPIRED.value,
            CredentialStatus.RENEWAL_ELIGIBLE.value,
        ):
            # EXPIRED or RENEWAL_ELIGIBLE → issue new credential (re-certification style)
            prior_credential_id = completionist_credential.get("credential_id")
            self._issue_completionist(
                user_id, pathway_version, prior_credential_id=prior_credential_id
            )
            return

        # REVOKED — do not restore revoked credentials automatically
        logger.debug(
            "Completionist credential is REVOKED for user %s; not restoring",
            user_id,
        )

    def _handle_conditions_not_met(
        self,
        user_id: str,
        completionist_credential: dict | None,
    ) -> None:
        """Handle case where completionist conditions are NOT met.

        Rules:
        - Completionist credential ACTIVE → transition to EXPIRED
        - Completionist credential RENEWAL_ELIGIBLE → transition to EXPIRED
        - Otherwise → do nothing

        Args:
            user_id: The user identifier.
            completionist_credential: Existing completionist credential or None.
        """
        if completionist_credential is None:
            return

        current_status = completionist_credential.get("credential_status", "")
        credential_id = completionist_credential.get("credential_id", "")

        if current_status in (
            CredentialStatus.ACTIVE.value,
            CredentialStatus.RENEWAL_ELIGIBLE.value,
        ):
            # Transition to EXPIRED
            try:
                self._db.update_credential_status(
                    user_id, credential_id, CredentialStatus.EXPIRED.value
                )
                logger.info(
                    "Transitioned completionist credential %s to EXPIRED for user %s "
                    "(prerequisites no longer met)",
                    credential_id,
                    user_id,
                )
            except Exception:
                logger.error(
                    "Failed to expire completionist credential %s for user %s",
                    credential_id,
                    user_id,
                    exc_info=True,
                )

    def _issue_completionist(
        self,
        user_id: str,
        pathway_version: str,
        prior_credential_id: str | None = None,
    ) -> None:
        """Issue a completionist credential via CredentialLifecycleService.

        Args:
            user_id: The user identifier.
            pathway_version: The current active pathway version.
            prior_credential_id: Previous credential ID if re-issuing.
        """
        try:
            lifecycle_service = CredentialLifecycleService(self._settings)
            is_recertification = prior_credential_id is not None

            lifecycle_service.issue_credential(
                user_id=user_id,
                pathway_id=COMPLETIONIST_PATHWAY_ID,
                pathway_version=pathway_version,
                is_recertification=is_recertification,
                prior_credential_id=prior_credential_id,
            )
            logger.info(
                "Issued completionist credential for user %s (recert=%s)",
                user_id,
                is_recertification,
            )
        except ValueError as e:
            logger.warning(
                "Cannot issue completionist credential for user %s: %s",
                user_id,
                str(e),
            )
        except Exception:
            logger.error(
                "Failed to issue completionist credential for user %s",
                user_id,
                exc_info=True,
            )
