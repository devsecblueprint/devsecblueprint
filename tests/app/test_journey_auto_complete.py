"""Tests for Builder Journey auto-completion logic."""

import pytest

from app.services.journey_auto_complete import compute_auto_completions
from app.config.journey_tasks import (
    PREREQUISITE_CONTENT_IDS,
    PREREQUISITE_QUIZ_IDS,
    WALKTHROUGH_CONTENT_IDS,
)


class TestComputeAutoCompletions:
    """Tests for compute_auto_completions function."""

    def test_journey_started_always_auto_completes(self):
        """explore-builder-dashboard always auto-completes (JOURNEY_STARTED condition)."""
        result = compute_auto_completions(
            user_id="user-1",
            existing_progress=[],
            membership=None,
            capstone_count=0,
        )
        assert "explore-builder-dashboard" in result
        # Only JOURNEY_STARTED tasks should fire with no progress/membership
        for task_id in result:
            if task_id != "explore-builder-dashboard":
                # Any other task that auto-completed must also be JOURNEY_STARTED
                from app.config.journey_tasks import (
                    AUTO_COMPLETE_MAPPINGS,
                    AutoCompleteCondition,
                )

                assert (
                    AUTO_COMPLETE_MAPPINGS[task_id]
                    == AutoCompleteCondition.JOURNEY_STARTED
                )

    def test_discord_connected_auto_completes(self):
        """connect-discord is auto-completed when membership has discord_id."""
        membership = {
            "PK": {"S": "USER#user-1"},
            "SK": {"S": "MEMBERSHIP"},
            "discord_id": {"S": "123456789"},
            "membership_tier": {"S": "BUILDER"},
        }
        result = compute_auto_completions(
            user_id="user-1",
            existing_progress=[],
            membership=membership,
            capstone_count=0,
        )
        assert "connect-discord" in result

    def test_discord_not_connected_when_empty(self):
        """connect-discord is NOT auto-completed when discord_id is empty."""
        membership = {
            "PK": {"S": "USER#user-1"},
            "SK": {"S": "MEMBERSHIP"},
            "discord_id": {"S": ""},
            "membership_tier": {"S": "BUILDER"},
        }
        result = compute_auto_completions(
            user_id="user-1",
            existing_progress=[],
            membership=membership,
            capstone_count=0,
        )
        assert "connect-discord" not in result

    def test_prerequisites_complete_auto_completes(self):
        """complete-prerequisites-path auto-completes when all prereq content done."""
        progress = [
            {"content_id": cid, "status": "complete"}
            for cid in PREREQUISITE_CONTENT_IDS
        ]
        result = compute_auto_completions(
            user_id="user-1",
            existing_progress=progress,
            membership=None,
            capstone_count=0,
        )
        assert "complete-prerequisites-path" in result

    def test_prerequisites_partial_does_not_auto_complete(self):
        """complete-prerequisites-path does NOT auto-complete with partial progress."""
        # Only complete half the prerequisites
        partial = list(PREREQUISITE_CONTENT_IDS)[:2]
        progress = [{"content_id": cid, "status": "complete"} for cid in partial]
        result = compute_auto_completions(
            user_id="user-1",
            existing_progress=progress,
            membership=None,
            capstone_count=0,
        )
        assert "complete-prerequisites-path" not in result

    def test_quizzes_complete_auto_completes(self):
        """complete-prerequisite-quizzes auto-completes when all quiz content done."""
        progress = [
            {"content_id": cid, "status": "complete"} for cid in PREREQUISITE_QUIZ_IDS
        ]
        result = compute_auto_completions(
            user_id="user-1",
            existing_progress=progress,
            membership=None,
            capstone_count=0,
        )
        assert "complete-prerequisite-quizzes" in result

    def test_capstone_submitted_auto_completes(self):
        """submit-first-capstone auto-completes when capstone_count > 0."""
        result = compute_auto_completions(
            user_id="user-1",
            existing_progress=[],
            membership=None,
            capstone_count=1,
        )
        assert "submit-first-capstone" in result

    def test_capstone_zero_does_not_auto_complete(self):
        """submit-first-capstone does NOT auto-complete when capstone_count is 0."""
        result = compute_auto_completions(
            user_id="user-1",
            existing_progress=[],
            membership=None,
            capstone_count=0,
        )
        assert "submit-first-capstone" not in result

    def test_walkthrough_started_auto_completes(self):
        """begin-first-walkthrough auto-completes when any walkthrough is done."""
        first_walkthrough = next(iter(WALKTHROUGH_CONTENT_IDS))
        progress = [{"content_id": first_walkthrough, "status": "complete"}]
        result = compute_auto_completions(
            user_id="user-1",
            existing_progress=progress,
            membership=None,
            capstone_count=0,
        )
        assert "begin-first-walkthrough" in result

    def test_all_conditions_met(self):
        """All auto-completable tasks returned when all conditions met."""
        from app.config.journey_tasks import AUTO_COMPLETE_MAPPINGS

        membership = {
            "discord_id": {"S": "123456789"},
        }
        progress = [
            {"content_id": cid, "status": "complete"}
            for cid in (
                PREREQUISITE_CONTENT_IDS
                | PREREQUISITE_QUIZ_IDS
                | WALKTHROUGH_CONTENT_IDS
            )
        ]
        result = compute_auto_completions(
            user_id="user-1",
            existing_progress=progress,
            membership=membership,
            capstone_count=3,
        )
        assert "connect-discord" in result
        assert "complete-prerequisites-path" in result
        assert "complete-prerequisite-quizzes" in result
        assert "submit-first-capstone" in result
        assert "begin-first-walkthrough" in result
        # With all conditions met, all auto-complete mappings should trigger
        assert len(result) == len(AUTO_COMPLETE_MAPPINGS)


class TestJourneyTaskConfig:
    """Tests for journey task configuration consistency."""

    def test_all_task_ids_are_unique(self):
        """All task IDs across all phases are unique."""
        from app.config.journey_tasks import JOURNEY_PHASES, VALID_TASK_IDS

        all_ids = []
        for phase_tasks in JOURNEY_PHASES.values():
            all_ids.extend(phase_tasks)
        assert len(all_ids) == len(set(all_ids))
        assert len(all_ids) == len(VALID_TASK_IDS)

    def test_task_to_phase_mapping_is_complete(self):
        """Every valid task ID has a phase mapping."""
        from app.config.journey_tasks import VALID_TASK_IDS, TASK_TO_PHASE

        for task_id in VALID_TASK_IDS:
            assert task_id in TASK_TO_PHASE

    def test_total_journey_tasks_count(self):
        """Total task count matches the builder journey phases."""
        from app.config.journey_tasks import TOTAL_JOURNEY_TASKS, BUILDER_JOURNEY_PHASES

        expected = sum(len(tasks) for tasks in BUILDER_JOURNEY_PHASES.values())
        assert TOTAL_JOURNEY_TASKS == expected

    def test_auto_complete_mappings_reference_valid_tasks(self):
        """All auto-complete mapping keys are valid task IDs (across all tiers)."""
        from app.config.journey_tasks import (
            AUTO_COMPLETE_MAPPINGS,
            BUILDER_VALID_TASK_IDS,
            FREE_VALID_TASK_IDS,
        )

        all_valid = BUILDER_VALID_TASK_IDS | FREE_VALID_TASK_IDS
        for task_id in AUTO_COMPLETE_MAPPINGS:
            assert task_id in all_valid, f"{task_id!r} not in any tier's valid task IDs"
