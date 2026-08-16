"""Admin/reviewer certification router — /admin/certifications/* routes.

Handles pathway management, candidate administration, review outcome recording,
credential granting, and credential revocation for admins and reviewers.

Requirements: 1.5, 5.4, 9.1, 9.2, 9.3, 9.8, 13.1, 13.2, 13.3, 13.4, 13.5, 15.2, 15.3
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.auth.jwt import require_admin, require_reviewer
from app.config import Settings
from app.dependencies import get_settings
from app.models.certification import (
    CertificationStatsResponse,
    CreatePathwayVersionRequest,
    ReviewOutcomeRequest,
    RevokeCredentialRequest,
)
from app.services.certification.certificate_generator import CertificateGenerator
from app.services.certification.completionist import CompletionistService
from app.services.certification.credential_lifecycle import CredentialLifecycleService
from app.services.certification.db import CertificationDB
from app.services.certification.pathway_config import get_pathway as get_pathway_config
from app.services.certification.pathway_service import PathwayService
from app.services.certification.review_session_service import ReviewSessionService
from app.services.email import send_credential_issued_notification
from app.services.progress_db import ProgressDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/certifications", tags=["certification-admin"])


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


@router.get("/stats")
async def get_certification_stats(
    user: dict = Depends(require_reviewer),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get aggregate certification statistics for the admin dashboard.

    Returns candidates grouped by status, credentials grouped by status,
    and the count of pending reviews.

    Requires reviewer or admin role.
    """
    db = CertificationDB(settings)

    # Scan all candidate records to aggregate by status
    candidates_by_status: dict[str, int] = {}
    pending_reviews = 0

    # Paginate through all candidates
    last_key: dict | None = None
    while True:
        candidates, next_key = db.list_candidates(limit=100, last_key=last_key)
        for candidate in candidates:
            status = candidate.get("candidate_status", "UNKNOWN")
            candidates_by_status[status] = candidates_by_status.get(status, 0) + 1
            # Count pending reviews from review_gate
            review_gate = candidate.get("review_gate", {})
            if review_gate.get("status") == "PENDING_REVIEW":
                pending_reviews += 1
        if next_key is None:
            break
        last_key = next_key

    # Scan credentials to aggregate by status
    credentials_by_status: dict[str, int] = {}
    try:
        response = db._dynamodb.scan(
            TableName=db._table_name,
            FilterExpression="begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={":sk_prefix": {"S": "CREDENTIAL#"}},
            ProjectionExpression="credential_status",
        )
        for item in response.get("Items", []):
            cred_status = item.get("credential_status", {}).get("S", "UNKNOWN")
            credentials_by_status[cred_status] = (
                credentials_by_status.get(cred_status, 0) + 1
            )
        # Handle pagination for credentials scan
        while response.get("LastEvaluatedKey"):
            response = db._dynamodb.scan(
                TableName=db._table_name,
                FilterExpression="begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={":sk_prefix": {"S": "CREDENTIAL#"}},
                ProjectionExpression="credential_status",
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            for item in response.get("Items", []):
                cred_status = item.get("credential_status", {}).get("S", "UNKNOWN")
                credentials_by_status[cred_status] = (
                    credentials_by_status.get(cred_status, 0) + 1
                )
    except Exception:
        logger.error("Failed to scan credentials for stats", exc_info=True)

    stats = CertificationStatsResponse(
        candidates_by_status=candidates_by_status,
        credentials_by_status=credentials_by_status,
        pending_reviews=pending_reviews,
    )

    return JSONResponse(status_code=200, content=stats.model_dump())


# ---------------------------------------------------------------------------
# Pathway Management
# ---------------------------------------------------------------------------


@router.post("/pathways")
async def create_pathway(
    body: CreatePathwayVersionRequest,
    pathway_id: str = Query(..., description="The pathway identifier"),
    user: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Create a new pathway definition version.

    Pathway definitions are now managed in code. This endpoint is disabled.
    """
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Pathway definitions are managed in code. Update pathway_config.py and redeploy."
        },
    )


@router.put("/pathways/{pathway_id}")
async def update_pathway(
    pathway_id: str,
    body: CreatePathwayVersionRequest,
    user: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Update a pathway by creating a new version.

    Pathway definitions are now managed in code. This endpoint is disabled.
    """
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Pathway definitions are managed in code. Update pathway_config.py and redeploy."
        },
    )


@router.get("/pathways")
async def list_pathways(
    user: dict = Depends(require_reviewer),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """List all active pathway definitions.

    Requires reviewer or admin role.
    """
    service = PathwayService(settings)
    pathways = service.list_pathways()
    return JSONResponse(
        status_code=200,
        content=[p.model_dump() for p in pathways],
    )


@router.get("/pathways/{pathway_id}")
async def get_pathway_versions(
    pathway_id: str,
    user: dict = Depends(require_reviewer),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get a pathway definition with all its versions.

    Requires reviewer or admin role.
    """
    service = PathwayService(settings)

    try:
        versions = service.get_pathway_versions(pathway_id)
        return JSONResponse(
            status_code=200,
            content=[v.model_dump() for v in versions],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Candidate Management
# ---------------------------------------------------------------------------


@router.get("/candidates")
async def list_candidates(
    pathway: Optional[str] = Query(None, description="Filter by pathway ID"),
    status: Optional[str] = Query(None, description="Filter by candidate status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    user: dict = Depends(require_reviewer),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """List all certification candidates with optional filters and pagination.

    Requires reviewer or admin role.
    """
    db = CertificationDB(settings)

    candidates, next_key = db.list_candidates(
        pathway_id=pathway,
        status=status,
        limit=limit,
    )

    # Enrich candidates with display_name and pathway_display_name
    # Build a map of user_id -> username for display
    user_ids = list({c["user_id"] for c in candidates})
    display_name_map: dict[str, str] = {}
    for uid in user_ids:
        name = db.get_user_full_name(uid)
        if not name:
            name = db.get_user_username(uid)
        display_name_map[uid] = name or uid[:8]

    # Map pathway_id -> display_name from config
    pathway_name_map: dict[str, str] = {}
    for candidate in candidates:
        pid = candidate.get("pathway_id", "")
        if pid and pid not in pathway_name_map:
            pw = get_pathway_config(pid)
            pathway_name_map[pid] = pw["display_name"] if pw else pid

    # Build enriched response
    enriched = []
    for candidate in candidates:
        uid = candidate["user_id"]
        pid = candidate.get("pathway_id", "")
        review_gate = candidate.get("review_gate", {})
        enriched.append(
            {
                "user_id": uid,
                "display_name": display_name_map.get(uid, uid[:8]),
                "pathway_id": pid,
                "pathway_display_name": pathway_name_map.get(pid, pid),
                "candidate_status": candidate.get("candidate_status", ""),
                "review_session_status": review_gate.get(
                    "status", "PENDING_SUBMISSION"
                ),
                "updated_at": candidate.get("updated_at", ""),
            }
        )

    return JSONResponse(
        status_code=200,
        content={
            "candidates": enriched,
            "page": page,
            "limit": limit,
            "has_more": next_key is not None,
        },
    )


@router.get("/candidates/{user_id}/{pathway_id}")
async def get_candidate_detail(
    user_id: str,
    pathway_id: str,
    user: dict = Depends(require_reviewer),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get detailed candidate information including review history and credential.

    Requires reviewer or admin role.
    """
    db = CertificationDB(settings)

    # Get candidate record
    candidate = db.get_candidate_record(user_id, pathway_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Get review history
    review_history = db.get_review_history(user_id, pathway_id)

    # Get credential if awarded
    credential = None
    credential_id = candidate.get("credential_id")
    if credential_id:
        credential = db.get_credential(user_id, credential_id)

    return JSONResponse(
        status_code=200,
        content={
            "candidate": candidate,
            "review_history": review_history,
            "credential": credential,
        },
    )


# ---------------------------------------------------------------------------
# Review Outcome
# ---------------------------------------------------------------------------


@router.post("/candidates/{user_id}/{pathway_id}/review-outcome")
async def record_review_outcome(
    user_id: str,
    pathway_id: str,
    body: ReviewOutcomeRequest,
    user: dict = Depends(require_reviewer),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Record a combined review session outcome for a candidate.

    If the outcome results in eligibility (PASSED + eligible), issues
    a credential and triggers completionist evaluation.

    Requires reviewer or admin role.
    """
    reviewer_id = user.get("sub", "unknown")
    review_service = ReviewSessionService(settings)

    try:
        eligibility_result = review_service.record_review_outcome(
            reviewer_id=reviewer_id,
            user_id=user_id,
            pathway_id=pathway_id,
            outcome=body,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # If eligible and no existing credential, issue one
    if eligibility_result is not None and eligibility_result.eligible:
        if eligibility_result.credential_id is None:
            # Get the pathway version from config for issuance
            db = CertificationDB(settings)
            pathway = get_pathway_config(pathway_id)
            pathway_version = pathway["version"] if pathway else "unknown"

            # Check if this is a re-certification
            candidate = db.get_candidate_record(user_id, pathway_id)
            prior_credential_id = (
                candidate.get("prior_credential_id") if candidate else None
            )
            is_recertification = prior_credential_id is not None

            credential_service = CredentialLifecycleService(settings)
            try:
                credential = credential_service.issue_credential(
                    user_id=user_id,
                    pathway_id=pathway_id,
                    pathway_version=pathway_version,
                    is_recertification=is_recertification,
                    prior_credential_id=prior_credential_id,
                )

                # Post-issuance: generate certificate PDF
                certificate_generator = CertificateGenerator(settings)
                s3_key = certificate_generator.generate(
                    credential_id=credential.credential_id,
                    full_name=credential.full_name_at_issuance,
                    pathway_display_name=pathway.get("display_name", pathway_id),
                    pathway_description=pathway.get("description", ""),
                    issued_at=credential.issued_at,
                    expires_at=credential.expires_at,
                )
                if s3_key:
                    db.update_certificate_s3_key(
                        user_id, credential.credential_id, s3_key
                    )

                # Post-issuance: send credential issued notification email
                learner_email = db.get_user_email(user_id)
                learner_username = db.get_user_username(user_id)
                if learner_email:
                    send_credential_issued_notification(
                        email=learner_email,
                        username=learner_username or user_id,
                        pathway=pathway.get("display_name", pathway_id),
                        credential_id=credential.credential_id,
                    )

                # Trigger completionist evaluation
                completionist_service = CompletionistService(settings)
                completionist_service.evaluate(user_id)

                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "credential_issued",
                        "credential_id": credential.credential_id,
                        "eligibility": eligibility_result.model_dump(),
                    },
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        # Credential already exists (idempotent case)
        return JSONResponse(
            status_code=200,
            content={
                "status": "already_awarded",
                "credential_id": eligibility_result.credential_id,
                "eligibility": eligibility_result.model_dump(),
            },
        )

    # Not eligible (REVISIONS_REQUIRED, FAILED, or blocking reasons)
    return JSONResponse(
        status_code=200,
        content={
            "status": "review_recorded",
            "eligibility": (
                eligibility_result.model_dump() if eligibility_result else None
            ),
        },
    )


# ---------------------------------------------------------------------------
# Grant Credential (Admin Grandfathering)
# ---------------------------------------------------------------------------


@router.post("/candidates/{user_id}/{pathway_id}/grant")
async def grant_credential(
    user_id: str,
    pathway_id: str,
    user: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Grant a credential directly to a user (admin grandfathering).

    Bypasses the Combined Review Session requirement. Requires the target
    user to have a valid full_name set.

    Requires admin role.
    """
    admin_id = user.get("sub", "unknown")
    credential_service = CredentialLifecycleService(settings)

    try:
        credential = credential_service.grant_credential(
            admin_id=admin_id,
            user_id=user_id,
            pathway_id=pathway_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Post-issuance: generate certificate PDF
    db = CertificationDB(settings)
    pathway = get_pathway_config(pathway_id)
    certificate_generator = CertificateGenerator(settings)
    s3_key = certificate_generator.generate(
        credential_id=credential.credential_id,
        full_name=credential.full_name_at_issuance,
        pathway_display_name=(
            pathway.get("display_name", pathway_id) if pathway else pathway_id
        ),
        pathway_description=pathway.get("description", "") if pathway else "",
        issued_at=credential.issued_at,
        expires_at=credential.expires_at,
    )
    if s3_key:
        db.update_certificate_s3_key(user_id, credential.credential_id, s3_key)

    # Post-issuance: send credential issued notification email
    learner_email = db.get_user_email(user_id)
    learner_username = db.get_user_username(user_id)
    if learner_email:
        send_credential_issued_notification(
            email=learner_email,
            username=learner_username or user_id,
            pathway=pathway.get("display_name", pathway_id) if pathway else pathway_id,
            credential_id=credential.credential_id,
        )

    # Trigger completionist evaluation after issuance
    completionist_service = CompletionistService(settings)
    completionist_service.evaluate(user_id)

    return JSONResponse(
        status_code=200,
        content={
            "status": "credential_granted",
            "credential_id": credential.credential_id,
            "credential": credential.model_dump(),
        },
    )


# ---------------------------------------------------------------------------
# Revoke Credential
# ---------------------------------------------------------------------------


@router.post("/credentials/{credential_id}/revoke")
async def revoke_credential(
    credential_id: str,
    body: RevokeCredentialRequest,
    user: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Revoke an issued credential.

    Requires admin role. Stores the revocation reason and admin ID.

    Triggers completionist evaluation after revocation to update
    the completionist credential status if needed.
    """
    admin_id = user.get("sub", "unknown")
    credential_service = CredentialLifecycleService(settings)

    try:
        credential = credential_service.revoke_credential(
            credential_id=credential_id,
            reason=body.reason,
            admin_id=admin_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Get user_id from the credential to trigger completionist evaluation
    # The credential model doesn't have user_id, but we can get it from the DB
    db = CertificationDB(settings)
    cred_lookup = db.get_credential_by_id(credential_id)
    if cred_lookup and cred_lookup.get("user_id"):
        completionist_service = CompletionistService(settings)
        completionist_service.evaluate(cred_lookup["user_id"])

    return JSONResponse(
        status_code=200,
        content={
            "status": "credential_revoked",
            "credential_id": credential.credential_id,
            "credential": credential.model_dump(),
        },
    )


# ---------------------------------------------------------------------------
# Uncomplete Content (Admin - for Fail/Revisions Required)
# ---------------------------------------------------------------------------


@router.post("/candidates/{user_id}/uncomplete-content")
async def uncomplete_content(
    user_id: str,
    content_id: str = Query(..., description="The content_id to uncomplete"),
    user: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Remove a content completion record (e.g., uncomplete a capstone on fail/revisions).

    Requires admin role.
    """
    progress_db = ProgressDB(settings)
    try:
        progress_db.delete_progress(user_id, content_id)
        return JSONResponse(
            status_code=200,
            content={"status": "uncompleted", "content_id": content_id},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Certificate Preview (Admin)
# ---------------------------------------------------------------------------


@router.get("/credentials/{credential_id}/preview")
async def admin_preview_certificate(
    credential_id: str,
    user: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Return a presigned S3 URL for the certificate image (admin view).

    Looks up the credential by ID using the GSI, retrieves the cached
    certificate from S3, and returns a time-limited presigned URL.
    If not cached, generates the certificate on-the-fly via Templated.io.

    Requires admin role.
    """
    db = CertificationDB(settings)

    # Look up credential via the CredentialLookup GSI
    credential = db.get_credential_by_id(credential_id)
    if credential is None:
        raise HTTPException(
            status_code=404,
            detail=f"Credential '{credential_id}' not found",
        )

    # Get pathway info for display name
    pathway_id = credential.get("pathway_id", "")
    pathway = get_pathway_config(pathway_id)
    pathway_display_name = pathway["display_name"] if pathway else pathway_id
    pathway_description = pathway.get("description", "") if pathway else ""

    # Generate presigned URL (serves from S3 cache or generates via Templated.io)
    generator = CertificateGenerator(settings)
    preview_url = generator.generate_svg_content(
        credential_id=credential["credential_id"],
        full_name=credential.get("full_name_at_issuance", ""),
        pathway_display_name=pathway_display_name,
        pathway_description=pathway_description,
        issued_at=credential.get("issued_at", ""),
        expires_at=credential.get("expires_at", ""),
    )

    if preview_url is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate certificate preview",
        )

    return JSONResponse(
        status_code=200,
        content={
            "preview_url": preview_url,
            "credential_id": credential_id,
            "pathway_id": pathway_id,
            "full_name": credential.get("full_name_at_issuance", ""),
            "issued_at": credential.get("issued_at", ""),
            "expires_at": credential.get("expires_at", ""),
        },
    )
