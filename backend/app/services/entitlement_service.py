"""Entitlement service for VIDEO_RECORDINGS access control.

Derives the VIDEO_RECORDINGS entitlement from user authentication state
and membership records. Provides both a check method and an enforcement
method that raises HTTPException on failure.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8
"""

import logging
from typing import Any

from fastapi import HTTPException

from app.config import Settings
from app.services.membership_db import MembershipDB

logger = logging.getLogger(__name__)


class EntitlementService:
    """Service for deriving and enforcing the VIDEO_RECORDINGS entitlement."""

    def __init__(self, settings: Settings) -> None:
        self._membership_db = MembershipDB(settings)

    def has_video_recordings_entitlement(
        self,
        user: dict[str, Any],
        membership: dict[str, Any] | None = None,
    ) -> bool:
        """Derive VIDEO_RECORDINGS entitlement.

        Returns True if:
          - user.is_admin is True, OR
          - user has BUILDER tier with active subscription_status

        Args:
            user: Decoded JWT payload dict with is_admin field.
            membership: Raw DynamoDB MEMBERSHIP item, or None to fetch.

        Returns:
            True if the user holds the VIDEO_RECORDINGS entitlement.
        """
        if user.get("is_admin"):
            return True

        if membership is None:
            user_id = user.get("sub", "")
            try:
                membership = self._membership_db.get_membership(user_id)
            except Exception:
                logger.exception(
                    "Failed to retrieve membership for user %s",
                    user_id,
                )
                return False

        if membership is None:
            return False

        tier = membership.get("membership_tier", {}).get("S", "")
        subscription_status = membership.get("subscription_status", {}).get("S", "")

        return tier == "BUILDER" and subscription_status == "active"

    def require_video_recordings(self, user: dict[str, Any]) -> None:
        """Raise HTTPException(403) if entitlement check fails.

        Args:
            user: Decoded JWT payload dict.

        Raises:
            HTTPException: With status 403 if the user lacks entitlement.
        """
        if not self.has_video_recordings_entitlement(user):
            raise HTTPException(
                status_code=403,
                detail="Insufficient entitlement for videos",
            )
