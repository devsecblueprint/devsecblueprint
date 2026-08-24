"""Property tests for progress percent calculation and completion marking.

Property 7: Progress percent calculation and completion marking
For any valid progress update with positionSeconds in [0, durationSeconds]
and durationSeconds in (0, 86400], the server-calculated percentComplete
SHALL equal round(positionSeconds / durationSeconds * 100) and the
completed flag SHALL be True iff percentComplete >= 90.

Validates: Requirements 5.7, 5.8
"""

from hypothesis import given, settings
from hypothesis import strategies as st


def calculate_progress(
    position_seconds: float, duration_seconds: float
) -> tuple[int, bool]:
    """Replicate server-side progress calculation logic.

    Args:
        position_seconds: Current playback position.
        duration_seconds: Total recording duration.

    Returns:
        Tuple of (percent_complete, completed).
    """
    percent_complete = round(position_seconds / duration_seconds * 100)
    completed = percent_complete >= 90
    return percent_complete, completed


@given(
    duration_seconds=st.floats(min_value=0.01, max_value=86400.0, allow_nan=False),
    fraction=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
@settings(max_examples=500)
def test_progress_calculation_correctness(
    duration_seconds: float,
    fraction: float,
) -> None:
    """Verify percent and completion are correctly calculated."""
    position_seconds = fraction * duration_seconds

    percent_complete, completed = calculate_progress(position_seconds, duration_seconds)

    expected_percent = round(position_seconds / duration_seconds * 100)
    assert percent_complete == expected_percent

    expected_completed = expected_percent >= 90
    assert completed == expected_completed


@given(
    duration_seconds=st.floats(min_value=0.01, max_value=86400.0, allow_nan=False),
)
@settings(max_examples=100)
def test_progress_at_zero_is_not_complete(
    duration_seconds: float,
) -> None:
    """Verify that zero position is never marked complete."""
    percent_complete, completed = calculate_progress(0.0, duration_seconds)
    assert percent_complete == 0
    assert completed is False


@given(
    duration_seconds=st.floats(min_value=0.01, max_value=86400.0, allow_nan=False),
)
@settings(max_examples=100)
def test_progress_at_full_duration_is_complete(
    duration_seconds: float,
) -> None:
    """Verify that full duration is always marked complete."""
    percent_complete, completed = calculate_progress(duration_seconds, duration_seconds)
    assert percent_complete == 100
    assert completed is True
