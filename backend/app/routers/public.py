"""Public credential verification router.

Provides an unauthenticated endpoint for third parties (employers, etc.)
to verify DSB credentials by credential_id.

NEVER exposes: email, user_id, review session details, internal identifiers.

Requirements: 10.1, 10.2, 10.3, 10.4
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings
from app.dependencies import get_settings
from app.models.certification import PublicCredentialResponse
from app.services.certification.db import CertificationDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/credentials/{credential_id}", response_model=PublicCredentialResponse)
async def verify_credential(
    credential_id: str, settings: Settings = Depends(get_settings)
) -> PublicCredentialResponse:
    """Verify a credential by its public credential_id.

    No authentication required. Returns only publicly-safe information:
    holder name, pathway name, issuance/expiration dates, and status.

    Returns 404 if the credential does not exist.
    """
    db = CertificationDB(settings)

    # Look up credential via GSI (no user_id needed)
    credential = db.get_credential_by_id(credential_id)
    if credential is None:
        raise HTTPException(status_code=404, detail="Credential not found")

    # Resolve pathway display name from the active pathway definition
    pathway_id = credential["pathway_id"]
    pathway = db.get_active_pathway(pathway_id)
    if pathway is not None:
        pathway_name = pathway["display_name"]
    else:
        # Fallback: use the pathway_id as a readable name if no active version found
        pathway_name = pathway_id.replace("-", " ").title()

    return PublicCredentialResponse(
        credential_id=credential["credential_id"],
        holder_name=credential["full_name_at_issuance"],
        pathway_name=pathway_name,
        issued_at=credential["issued_at"],
        expires_at=credential["expires_at"],
        credential_status=credential["credential_status"],
    )
