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
from app.models.videos import AccessTier
from app.services.membership_db import MembershipDB
from app.tiers import is_builder_equivalent

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

        The CONTRIBUTOR_ROLE no longer grants Builder-equivalent access. That
        perk was time-limited and expired on 2026-11-01; contributors are now
        entitled solely through their own membership tier (or admin status).
        The role itself is retained for recognition, admin filtering, and
        Discord sync — it simply carries no entitlement.

        Args:
            user: Decoded JWT payload dict with is_admin field.
            membership: Raw DynamoDB MEMBERSHIP item, or None to fetch.

        Returns:
            True if the user holds the VIDEO_RECORDINGS entitlement.
        """
        if user.get("is_admin"):
            return True

        user_id = user.get("sub", "")

        if membership is None:
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

        return is_builder_equivalent(tier) and subscription_status == "active"

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

    def require_video_access(
        self,
        user: dict[str, Any],
        access_tier: AccessTier,
    ) -> None:
        """Raise HTTPException(403) unless the user may watch this video.

        FREE videos only need an authenticated user (enforced upstream by
        get_current_user). BUILDER videos require the video entitlement.

        Args:
            user: Decoded JWT payload dict.
            access_tier: The video's access tier.

        Raises:
            HTTPException: With status 403 if the video is BUILDER and the
                user lacks entitlement.
        """
        if access_tier == AccessTier.FREE:
            return
        self.require_video_recordings(user)
