"""Contact form router — handles public contact submissions.

Accepts a POST with form data, validates it, and sends a notification
email to the DSB team via SES. No authentication required.
"""

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.services.email import send_contact_notification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contact", tags=["contact"])

InquiryType = Literal[
    "membership-support",
    "technical-support",
    "contributions",
    "partnerships",
    "speaking-media",
    "general-inquiry",
]


class ContactRequest(BaseModel):
    """Validated contact form submission."""

    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., max_length=254)
    organization: str = Field(default="", max_length=100)
    inquiry_type: InquiryType
    subject: str = Field(..., min_length=1, max_length=150)
    message: str = Field(..., min_length=10, max_length=2000)


class ContactResponse(BaseModel):
    """Response after successful submission."""

    success: bool
    message: str


@router.post("", response_model=ContactResponse)
async def submit_contact_form(body: ContactRequest) -> ContactResponse:
    """Handle a public contact form submission.

    Validates the input and sends a notification email to the DSB support team.
    """
    logger.info(
        "Contact form submission: type=%s, from=%s",
        body.inquiry_type,
        body.email,
    )

    success = send_contact_notification(
        full_name=body.full_name,
        email=body.email,
        organization=body.organization,
        inquiry_type=body.inquiry_type,
        subject=body.subject,
        message=body.message,
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to send your message. Please try again later.",
        )

    return ContactResponse(
        success=True,
        message="Your message has been sent. We'll get back to you soon.",
    )
