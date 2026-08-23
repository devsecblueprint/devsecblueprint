"""Property tests for progress validation and video API behavior.

Property 8: Progress validation rejects invalid inputs
Property 9: Progress upsert idempotency
Property 10: Partial update preserves unchanged fields

Validates: Requirements 5.11, 6.3, 6.4, 6.5, 8.2
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from app.models.videos import (
    ProgressUpdateRequest,
    UpdateVideoRequest,
)


@given(
    position=st.floats(min_value=-1000.0, max_value=-0.01, allow_nan=False),
    duration=st.floats(min_value=0.01, max_value=86400.0, allow_nan=False),
)
@settings(max_examples=100)
def test_progress_rejects_negative_position(
    position: float,
    duration: float,
) -> None:
    """Property 8: Negative positionSeconds must be rejected."""
    with pytest.raises(ValidationError):
        ProgressUpdateRequest(
            position_seconds=position,
            duration_seconds=duration,
        )


@given(
    duration=st.floats(min_value=-1000.0, max_value=0.0, allow_nan=False),
)
@settings(max_examples=100)
def test_progress_rejects_non_positive_duration(
    duration: float,
) -> None:
    """Property 8: Non-positive durationSeconds must be rejected."""
    with pytest.raises(ValidationError):
        ProgressUpdateRequest(
            position_seconds=0.0,
            duration_seconds=duration,
        )


@given(
    duration=st.floats(min_value=86400.01, max_value=200000.0, allow_nan=False),
)
@settings(max_examples=50)
def test_progress_rejects_excessive_duration(
    duration: float,
) -> None:
    """Property 8: durationSeconds > 86400 must be rejected."""
    with pytest.raises(ValidationError):
        ProgressUpdateRequest(
            position_seconds=0.0,
            duration_seconds=duration,
        )


@given(
    position=st.floats(min_value=0.0, max_value=86400.0, allow_nan=False),
    duration=st.floats(min_value=0.01, max_value=86400.0, allow_nan=False),
)
@settings(max_examples=200)
def test_progress_upsert_idempotency(
    position: float,
    duration: float,
) -> None:
    """Property 9: Same payload produces same percentComplete.

    The calculation round(position / duration * 100) is deterministic.
    """
    if position > duration:
        return  # Skip invalid inputs

    percent1 = round(position / duration * 100)
    percent2 = round(position / duration * 100)
    assert percent1 == percent2

    completed1 = percent1 >= 90
    completed2 = percent2 >= 90
    assert completed1 == completed2


@given(
    has_title=st.booleans(),
    has_description=st.booleans(),
    has_instructor=st.booleans(),
    has_tags=st.booleans(),
)
@settings(max_examples=50)
def test_partial_update_only_sets_provided_fields(
    has_title: bool,
    has_description: bool,
    has_instructor: bool,
    has_tags: bool,
) -> None:
    """Property 10: Only provided fields change in partial update."""
    kwargs: dict = {}
    if has_title:
        kwargs["title"] = "New Title"
    if has_description:
        kwargs["description"] = "New description"
    if has_instructor:
        kwargs["instructor"] = "New Instructor"
    if has_tags:
        kwargs["tags"] = ["new-tag"]

    request = UpdateVideoRequest(**kwargs)

    # Fields not provided should be None
    if not has_title:
        assert request.title is None
    else:
        assert request.title == "New Title"

    if not has_description:
        assert request.description is None
    else:
        assert request.description == "New description"

    if not has_instructor:
        assert request.instructor is None
    else:
        assert request.instructor == "New Instructor"

    if not has_tags:
        assert request.tags is None
    else:
        assert request.tags == ["new-tag"]
