"""Pathway definition management service.

Provides CRUD operations for certification pathway definitions including
version management, activation/deactivation, and listing.

Requirements: 1.1, 1.2, 1.5
"""

import logging
from datetime import datetime, timezone

from app.config import Settings
from app.models.certification import CreatePathwayVersionRequest, PathwayDefinition
from app.services.certification.db import CertificationDB

logger = logging.getLogger(__name__)

# Supported pathway identifiers
SUPPORTED_PATHWAYS = frozenset(
    [
        "devsecops-engineering",
        "cloud-security-engineering",
        "security-engineering-completionist",
    ]
)

# Pathway code mapping used for credential IDs and display
PATHWAY_CODES: dict[str, str] = {
    "devsecops-engineering": "DSEP",
    "cloud-security-engineering": "CSEP",
    "security-engineering-completionist": "SECP",
}


class PathwayService:
    """Manages pathway definitions and versioning.

    Handles creation of new pathway versions, retrieval of active pathways,
    and listing of all pathway versions. Enforces that only supported
    pathway identifiers are accepted and that at most one version per
    pathway is active at any time.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._db = CertificationDB(settings)

    def create_pathway_version(
        self,
        admin_id: str,
        pathway_id: str,
        request: CreatePathwayVersionRequest,
    ) -> PathwayDefinition:
        """Create a new pathway definition version.

        Deactivates the currently active version (if any) and writes
        the new version as active.

        Args:
            admin_id: The admin user ID creating this version.
            pathway_id: The pathway identifier.
            request: The pathway version creation request.

        Returns:
            The newly created PathwayDefinition.

        Raises:
            ValueError: If pathway_id is not one of the supported pathways.
        """
        self._validate_pathway_id(pathway_id)

        # Deactivate the current active version if one exists
        current_active = self._db.get_active_pathway(pathway_id)
        if current_active is not None:
            self._db.deactivate_pathway_version(pathway_id, current_active["version"])
            logger.info(
                "Deactivated pathway version %s/%s",
                pathway_id,
                current_active["version"],
            )

        # Build the new pathway definition
        now = datetime.now(timezone.utc).isoformat()
        pathway_code = PATHWAY_CODES[pathway_id]

        pathway_data: dict = {
            "pathway_id": pathway_id,
            "version": request.version,
            "display_name": request.display_name,
            "description": request.description,
            "pathway_code": pathway_code,
            "capstone_content_id": request.capstone_content_id,
            "learning_requirements": request.learning_requirements,
            "is_active": True,
            "created_at": now,
            "created_by": admin_id,
        }

        # Write the new version to DynamoDB
        self._db.put_pathway_version(pathway_data)
        logger.info(
            "Created pathway version %s/%s by admin %s",
            pathway_id,
            request.version,
            admin_id,
        )

        return PathwayDefinition(**pathway_data)

    def get_active_pathway(self, pathway_id: str) -> PathwayDefinition | None:
        """Get the currently active version of a pathway.

        Args:
            pathway_id: The pathway identifier.

        Returns:
            The active PathwayDefinition, or None if no active version exists.

        Raises:
            ValueError: If pathway_id is not one of the supported pathways.
        """
        self._validate_pathway_id(pathway_id)

        result = self._db.get_active_pathway(pathway_id)
        if result is None:
            return None

        return PathwayDefinition(**result)

    def get_pathway_versions(self, pathway_id: str) -> list[PathwayDefinition]:
        """Get all versions (active and inactive) for a pathway.

        Args:
            pathway_id: The pathway identifier.

        Returns:
            List of all PathwayDefinition versions for the pathway.

        Raises:
            ValueError: If pathway_id is not one of the supported pathways.
        """
        self._validate_pathway_id(pathway_id)

        # Query all versions by querying PK with SK prefix
        # The DB layer doesn't have a direct "get all versions" method,
        # so we use a targeted query approach
        versions = self._query_all_versions(pathway_id)
        return [PathwayDefinition(**v) for v in versions]

    def list_pathways(self) -> list[PathwayDefinition]:
        """List all active pathway definitions.

        Returns:
            List of all currently active PathwayDefinitions.
        """
        results = self._db.list_active_pathways()
        return [PathwayDefinition(**r) for r in results]

    def _validate_pathway_id(self, pathway_id: str) -> None:
        """Validate that a pathway_id is one of the supported pathways.

        Raises:
            ValueError: If pathway_id is not supported.
        """
        if pathway_id not in SUPPORTED_PATHWAYS:
            raise ValueError(
                f"Invalid pathway_id '{pathway_id}'. "
                f"Supported pathways: {sorted(SUPPORTED_PATHWAYS)}"
            )

    def _query_all_versions(self, pathway_id: str) -> list[dict]:
        """Query all versions for a pathway from DynamoDB.

        Uses the DynamoDB client to query all items with the pathway's
        PK and VERSION# SK prefix.

        Returns:
            List of unmarshalled pathway version dicts.
        """
        try:
            response = self._db._dynamodb.query(
                TableName=self._db._table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"PATHWAY#{pathway_id}"},
                    ":sk_prefix": {"S": "VERSION#"},
                },
            )

            return [
                self._db._unmarshal_pathway(item) for item in response.get("Items", [])
            ]

        except Exception:
            logger.error(
                "Failed to query all versions for pathway %s",
                pathway_id,
                exc_info=True,
            )
            raise
