"""Learner-facing certification router — /certifications/* endpoints.

Handles learner interactions with the certification system: viewing pathways,
enrolling, submitting capstones, checking review history, viewing credentials,
and downloading certificates.

All endpoints require JWT authentication via `get_current_user`.
Learners can only access their own data.

Requirements: 4.7, 5.1, 7.6, 8.1, 8.2, 12.1, 15.1
"""

import logging
from datetime import datetime, timezone

import boto3
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.jwt import get_current_user
from app.config import Settings
from app.dependencies import get_settings
from app.models.certification import (
    CandidateStatus,
    ReviewSessionStatus,
)
from app.services.certification.db import CertificationDB
from app.services.certification.pathway_service import PathwayService
from app.services.certification.review_session_service import ReviewSessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/certifications", tags=["certifications"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class CapstoneSubmissionRequest(BaseModel):
    """Request body for capstone submission."""

    submission_url: str = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# GET /certifications — List all pathways with learner's candidate status
# ---------------------------------------------------------------------------


@router.get("")
async def list_pathways_with_status(
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> list[dict]:
    """List all pathways with the learner's candidate status for each.

    Returns a list of pathway objects with an additional `candidate_status`
    field indicating the learner's progress (or NOT_STARTED if not enrolled).
    """
    user_id = user.get("sub")
    pathway_service = PathwayService(settings)
    db = CertificationDB(settings)

    pathways = pathway_service.list_pathways()
    result = []

    for pathway in pathways:
        candidate = db.get_candidate_record(user_id, pathway.pathway_id)
        candidate_status = (
            candidate["candidate_status"]
            if candidate
            else CandidateStatus.NOT_STARTED.value
        )

        result.append(
            {
                "pathway_id": pathway.pathway_id,
                "display_name": pathway.display_name,
                "description": pathway.description,
                "version": pathway.version,
                "candidate_status": candidate_status,
            }
        )

    return result


# ---------------------------------------------------------------------------
# GET /certifications/{pathway_id} — Get candidate record for a pathway
# ---------------------------------------------------------------------------


@router.get("/{pathway_id}")
async def get_candidate_record(
    pathway_id: str,
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Get the learner's candidate record for a specific pathway.

    Returns 404 if the learner has no candidate record for the pathway.
    """
    user_id = user.get("sub")
    db = CertificationDB(settings)

    candidate = db.get_candidate_record(user_id, pathway_id)
    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail=f"No candidate record found for pathway '{pathway_id}'",
        )

    return candidate


# ---------------------------------------------------------------------------
# POST /certifications/{pathway_id}/enroll — Begin pursuing a pathway
# ---------------------------------------------------------------------------


@router.post("/{pathway_id}/enroll", status_code=201)
async def enroll_in_pathway(
    pathway_id: str,
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Begin pursuing a certification pathway.

    Creates a candidate record with IN_PROGRESS status and review_gate
    set to PENDING_SUBMISSION.

    Returns 409 if the learner is already enrolled.
    """
    user_id = user.get("sub")
    db = CertificationDB(settings)

    # Check if already enrolled
    existing = db.get_candidate_record(user_id, pathway_id)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Already enrolled in pathway '{pathway_id}'",
        )

    # Validate pathway exists
    pathway = db.get_active_pathway(pathway_id)
    if pathway is None:
        raise HTTPException(
            status_code=404,
            detail=f"Pathway '{pathway_id}' not found",
        )

    now = datetime.now(timezone.utc).isoformat()

    candidate_record = {
        "pathway_id": pathway_id,
        "pathway_version": pathway["version"],
        "candidate_status": CandidateStatus.IN_PROGRESS.value,
        "review_gate": {
            "status": ReviewSessionStatus.PENDING_SUBMISSION.value,
        },
        "started_at": now,
        "updated_at": now,
    }

    db.put_candidate_record(user_id, candidate_record)

    logger.info(
        "User %s enrolled in pathway %s",
        user_id,
        pathway_id,
    )

    return candidate_record


# ---------------------------------------------------------------------------
# GET /certifications/{pathway_id}/reviews — Get review session history
# ---------------------------------------------------------------------------


@router.get("/{pathway_id}/reviews")
async def get_review_history(
    pathway_id: str,
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> list[dict]:
    """Get the learner's full review session history for a pathway.

    Returns a list of review session records ordered by revision number.
    """
    user_id = user.get("sub")
    review_service = ReviewSessionService(settings)

    return review_service.get_revision_history(user_id, pathway_id)


# ---------------------------------------------------------------------------
# POST /certifications/{pathway_id}/submit — Submit capstone
# ---------------------------------------------------------------------------


@router.post("/{pathway_id}/submit")
async def submit_capstone(
    pathway_id: str,
    body: CapstoneSubmissionRequest,
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Submit a capstone for initial certification or re-certification.

    Accepts a submission_url and delegates to ReviewSessionService which
    handles both new submissions and re-certification submissions.

    Returns submission details including revision number and status.
    """
    user_id = user.get("sub")
    review_service = ReviewSessionService(settings)

    try:
        result = review_service.submit_capstone(
            user_id, pathway_id, body.submission_url
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


# ---------------------------------------------------------------------------
# GET /certifications/{pathway_id}/credential — Get credential details
# ---------------------------------------------------------------------------


@router.get("/{pathway_id}/credential")
async def get_credential(
    pathway_id: str,
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Get the learner's issued credential for a pathway.

    Reads the candidate record to find the credential_id, then retrieves
    the full credential record. Returns 404 if no credential exists.
    """
    user_id = user.get("sub")
    db = CertificationDB(settings)

    candidate = db.get_candidate_record(user_id, pathway_id)
    if candidate is None or not candidate.get("credential_id"):
        raise HTTPException(
            status_code=404,
            detail=f"No credential found for pathway '{pathway_id}'",
        )

    credential_id = candidate["credential_id"]
    credential = db.get_credential(user_id, credential_id)
    if credential is None:
        raise HTTPException(
            status_code=404,
            detail=f"No credential found for pathway '{pathway_id}'",
        )

    return credential


# ---------------------------------------------------------------------------
# GET /certifications/{pathway_id}/credential/download — Download cert PDF
# ---------------------------------------------------------------------------


@router.get("/{pathway_id}/credential/download")
async def download_certificate(
    pathway_id: str,
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Generate a presigned S3 URL for the learner's certificate PDF.

    Returns the download URL or 404 if no certificate exists.
    """
    user_id = user.get("sub")
    db = CertificationDB(settings)

    candidate = db.get_candidate_record(user_id, pathway_id)
    if candidate is None or not candidate.get("credential_id"):
        raise HTTPException(
            status_code=404,
            detail=f"No credential found for pathway '{pathway_id}'",
        )

    credential_id = candidate["credential_id"]
    credential = db.get_credential(user_id, credential_id)
    if credential is None:
        raise HTTPException(
            status_code=404,
            detail=f"No credential found for pathway '{pathway_id}'",
        )

    s3_key = credential.get("certificate_s3_key")
    if not s3_key:
        raise HTTPException(
            status_code=404,
            detail="Certificate has not been generated yet",
        )

    # Generate a presigned URL for the certificate PDF
    s3_client = boto3.client("s3")
    try:
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.certificate_bucket,
                "Key": s3_key,
            },
            ExpiresIn=3600,  # 1 hour
        )
    except Exception as e:
        logger.error(
            "Failed to generate presigned URL for credential %s: %s",
            credential_id,
            e,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate download URL",
        )

    return {"download_url": presigned_url}
