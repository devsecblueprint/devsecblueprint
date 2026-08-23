"""State machine transition validation for video status.

Provides a utility function to validate that a video status transition
is permitted according to the defined allowed transitions map.

Requirements: 2.2, 2.3, 8.8
"""

from fastapi import HTTPException

from app.models.videos import ALLOWED_TRANSITIONS, VideoStatus


def validate_transition(
    current: VideoStatus,
    target: VideoStatus,
) -> None:
    """Validate that a video status transition is allowed.

    Args:
        current: The current status of the video.
        target: The desired target status.

    Raises:
        HTTPException: With status 400 if the transition is not permitted.
    """
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        allowed_values = [s.value for s in allowed]
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot transition from {current.value} to"
                f" {target.value}. Allowed transitions from"
                f" {current.value}: {allowed_values}"
            ),
        )
