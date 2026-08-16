"""Certification system Pydantic models and enums.

Defines all data models for the DSB Certification & Credentialing Program
including candidate state tracking, review sessions, credentials, pathway
definitions, and request/response schemas.

Requirements: 4.2, 5.10, 7.1, 7.6, 9.4, 16.1, 17.4, 17.5
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class CandidateStatus(str, Enum):
    """Lifecycle state of a Candidate within a Pathway."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    ELIGIBLE_FOR_AWARD = "ELIGIBLE_FOR_AWARD"
    AWARDED = "AWARDED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class ReviewSessionStatus(str, Enum):
    """Status of a Combined Review Session."""

    PENDING_SUBMISSION = "PENDING_SUBMISSION"
    PENDING_REVIEW = "PENDING_REVIEW"
    REVISIONS_REQUIRED = "REVISIONS_REQUIRED"
    PASSED = "PASSED"
    FAILED = "FAILED"


class CredentialStatus(str, Enum):
    """Lifecycle state of an issued Credential."""

    ACTIVE = "ACTIVE"
    RENEWAL_ELIGIBLE = "RENEWAL_ELIGIBLE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------


class ReviewGateState(BaseModel):
    """Tracks the state of the single evaluation gate (Combined Review Session)."""

    status: ReviewSessionStatus
    reviewed_at: Optional[str] = None
    reviewer_id: Optional[str] = None


class CandidateRecord(BaseModel):
    """A learner's overall progress and state within a specific Pathway."""

    pathway_id: str
    candidate_status: CandidateStatus
    review_gate: ReviewGateState
    started_at: str
    updated_at: str
    credential_id: Optional[str] = None
    prior_credential_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------


class ProfileUpdateRequest(BaseModel):
    """Request schema for updating a learner's profile (including full_name)."""

    full_name: str = Field(..., min_length=1, max_length=200)


class ReviewOutcomeRequest(BaseModel):
    """Request schema for recording a Combined Review Session outcome."""

    status: ReviewSessionStatus  # PASSED, REVISIONS_REQUIRED, or FAILED only
    rubric_scores: dict[str, dict]  # dimension -> {score, comment}
    evaluation_dimensions: dict[str, str]  # dimension -> assessment (defense portion)
    reviewer_notes: str


class RevokeCredentialRequest(BaseModel):
    """Request schema for revoking a credential."""

    reason: str = Field(..., min_length=5, max_length=500)


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class PublicCredentialResponse(BaseModel):
    """Public verification response — no sensitive data exposed."""

    credential_id: str
    holder_name: str
    pathway_name: str
    issued_at: str
    expires_at: str
    credential_status: CredentialStatus


class EligibilityResult(BaseModel):
    """Result of the Eligibility Engine evaluation."""

    eligible: bool
    blocking_reasons: list[str] = Field(default_factory=list)
    credential_id: Optional[str] = None


class CertificationStatsResponse(BaseModel):
    """Aggregate certification statistics for the admin dashboard."""

    candidates_by_status: dict[str, int]  # CandidateStatus -> count
    credentials_by_status: dict[str, int]  # CredentialStatus -> count
    pending_reviews: int  # Combined_Review_Sessions in PENDING_REVIEW


# ---------------------------------------------------------------------------
# Pathway Models
# ---------------------------------------------------------------------------


class PathwayDefinition(BaseModel):
    """A versionable configuration record for a certification pathway."""

    pathway_id: str
    version: str
    display_name: str
    description: str
    pathway_code: str
    capstone_content_id: str
    learning_requirements: list[str]
    is_active: bool
    created_at: str
    created_by: str


class CreatePathwayVersionRequest(BaseModel):
    """Request schema for creating a new pathway version."""

    version: str
    display_name: str
    description: str
    capstone_content_id: str
    learning_requirements: list[str]


# ---------------------------------------------------------------------------
# Credential Model
# ---------------------------------------------------------------------------


class Credential(BaseModel):
    """An issued certificate record representing successful pathway completion."""

    credential_id: str
    pathway_id: str
    pathway_version: str
    credential_status: CredentialStatus
    issued_at: str
    expires_at: str
    revoked_at: Optional[str] = None
    revocation_reason: Optional[str] = None
    revoked_by: Optional[str] = None
    certificate_s3_key: Optional[str] = None
    full_name_at_issuance: str
    is_recertification: bool = False
    is_grandfathered: bool = False
    prior_credential_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Combined Review Session Model
# ---------------------------------------------------------------------------


class CombinedReviewSession(BaseModel):
    """A single evaluation event record (capstone rubric + live technical defense)."""

    pathway_id: str
    revision_number: int
    status: ReviewSessionStatus
    rubric_scores: dict
    evaluation_dimensions: dict
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    submission_url: str
    submitted_at: str
    reviewed_at: Optional[str] = None
