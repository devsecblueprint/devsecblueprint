"""Pathway definition management service.

Uses hardcoded pathway configurations from pathway_config.py instead of DynamoDB.

Requirements: 1.1, 1.2, 1.5
"""

import logging

from app.models.certification import PathwayDefinition
from app.services.certification.pathway_config import (
    PATHWAY_DEFINITIONS,
    get_all_pathways,
    get_pathway,
)

logger = logging.getLogger(__name__)

# Supported pathway identifiers
SUPPORTED_PATHWAYS = frozenset(PATHWAY_DEFINITIONS.keys())

# Pathway code mapping used for credential IDs and display
PATHWAY_CODES: dict[str, str] = {
    pid: pdef["pathway_code"] for pid, pdef in PATHWAY_DEFINITIONS.items()
}


class PathwayService:
    """Manages pathway definitions from hardcoded config.

    No DynamoDB access needed for pathway lookups.
    """

    def __init__(self, settings=None) -> None:
        # Settings not needed for hardcoded pathways, but accept for API compatibility
        pass

    def get_active_pathway(self, pathway_id: str) -> PathwayDefinition | None:
        """Get the active pathway definition."""
        data = get_pathway(pathway_id)
        if data is None:
            return None
        return PathwayDefinition(
            **data, created_at="2025-01-01T00:00:00Z", created_by="system"
        )

    def list_pathways(self) -> list[PathwayDefinition]:
        """List all active pathway definitions."""
        return [
            PathwayDefinition(
                **p, created_at="2025-01-01T00:00:00Z", created_by="system"
            )
            for p in get_all_pathways()
        ]

    def get_pathway_versions(self, pathway_id: str) -> list[PathwayDefinition]:
        """Get all versions for a pathway (only one version with hardcoded config)."""
        pathway = self.get_active_pathway(pathway_id)
        if pathway is None:
            return []
        return [pathway]
