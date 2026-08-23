"""Property tests for video state machine transitions.

Property 2: State machine transition validity
For any Video with a current VideoStatus and any target
VideoStatus, the transition SHALL succeed iff the (current, target)
pair is in the allowed set.

Validates: Requirements 2.2, 2.3, 8.4, 8.5, 8.8
"""

import pytest
from fastapi import HTTPException
from hypothesis import given, settings
from hypothesis import strategies as st

from app.models.videos import ALLOWED_TRANSITIONS, VideoStatus
from app.services.transition_utils import validate_transition

VALID_TRANSITIONS = {
    (VideoStatus.DRAFT, VideoStatus.PROCESSING),
    (VideoStatus.PROCESSING, VideoStatus.READY),
    (VideoStatus.READY, VideoStatus.PUBLISHED),
    (VideoStatus.READY, VideoStatus.ARCHIVED),
    (VideoStatus.PUBLISHED, VideoStatus.ARCHIVED),
}

all_statuses = list(VideoStatus)


@given(
    current=st.sampled_from(all_statuses),
    target=st.sampled_from(all_statuses),
)
@settings(max_examples=200)
def test_transition_validity(
    current: VideoStatus,
    target: VideoStatus,
) -> None:
    """Verify transition succeeds iff pair is in allowed set."""
    pair = (current, target)

    if pair in VALID_TRANSITIONS:
        # Should not raise
        validate_transition(current, target)
    else:
        # Should raise HTTPException with status 400
        with pytest.raises(HTTPException) as exc_info:
            validate_transition(current, target)
        assert exc_info.value.status_code == 400


@given(current=st.sampled_from(all_statuses))
@settings(max_examples=50)
def test_allowed_transitions_dict_consistency(
    current: VideoStatus,
) -> None:
    """Verify ALLOWED_TRANSITIONS dict is consistent with valid set."""
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    for target in all_statuses:
        pair = (current, target)
        if pair in VALID_TRANSITIONS:
            assert target in allowed
        else:
            assert target not in allowed
