"""
Unit tests for quiz service business logic.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from backend.services.quiz_service import (
    submit_quiz,
    _update_streak,
    QuizNotFoundError,
    RegistryUnavailableError,
)


class TestSubmitQuiz:
    """Tests for submit_quiz function."""

    @patch("backend.services.quiz_service.get_quiz")
    @patch("backend.services.quiz_service.get_module_completion")
    @patch("backend.services.quiz_service.save_module_completion")
    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_submit_quiz_all_correct_first_completion(
        self,
        mock_update_streak,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_quiz,
    ):
        """Test quiz submission with all correct answers on first completion."""
        # Mock quiz definition
        mock_get_quiz.return_value = {
            "passing_score": 70,
            "questions": [
                {"id": "q1", "correct_answer": "B", "explanation": "Explanation 1"},
                {"id": "q2", "correct_answer": "C", "explanation": "Explanation 2"},
                {"id": "q3", "correct_answer": "A", "explanation": "Explanation 3"},
            ],
        }

        # Mock no existing completion
        mock_get_completion.return_value = None

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
        }

        # Submit quiz with all correct answers
        result = submit_quiz(
            "user123", "secure-sdlc", {"q1": "B", "q2": "C", "q3": "A"}
        )

        # Verify result
        assert result["passed"] is True
        assert result["score"] == 100
        assert result["passing_score"] == 70
        assert result["already_completed"] is False
        assert result["current_streak"] == 1
        assert len(result["results"]) == 3

        # Verify all questions marked correct
        for question_result in result["results"]:
            assert question_result["correct"] is True

        # Verify completion was saved
        mock_save_completion.assert_called_once_with(
            "user123", "secure-sdlc", 100, True
        )

        # Verify streak was updated
        mock_update_streak.assert_called_once()

    @patch("backend.services.quiz_service.get_quiz")
    @patch("backend.services.quiz_service.get_module_completion")
    @patch("backend.services.quiz_service.save_module_completion")
    @patch("backend.services.quiz_service.get_streak_data")
    def test_submit_quiz_all_wrong_no_completion(
        self, mock_get_streak, mock_save_completion, mock_get_completion, mock_get_quiz
    ):
        """Test quiz submission with all wrong answers."""
        # Mock quiz definition
        mock_get_quiz.return_value = {
            "passing_score": 70,
            "questions": [
                {"id": "q1", "correct_answer": "B", "explanation": "Explanation 1"},
                {"id": "q2", "correct_answer": "C", "explanation": "Explanation 2"},
            ],
        }

        # Mock no existing completion
        mock_get_completion.return_value = None

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": 5,
            "longest_streak": 10,
            "last_activity_date": "2024-01-15",
        }

        # Submit quiz with all wrong answers
        result = submit_quiz("user123", "secure-sdlc", {"q1": "A", "q2": "B"})

        # Verify result
        assert result["passed"] is False
        assert result["score"] == 0
        assert result["passing_score"] == 70
        assert result["already_completed"] is False
        assert result["current_streak"] == 5  # Unchanged

        # Verify all questions marked incorrect
        for question_result in result["results"]:
            assert question_result["correct"] is False

        # Verify completion was NOT saved
        mock_save_completion.assert_not_called()

    @patch("backend.services.quiz_service.get_quiz")
    @patch("backend.services.quiz_service.get_module_completion")
    @patch("backend.services.quiz_service.save_module_completion")
    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_submit_quiz_passing_threshold(
        self,
        mock_update_streak,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_quiz,
    ):
        """Test quiz submission at exactly the passing threshold."""
        # Mock quiz definition with 10 questions
        questions = [
            {"id": f"q{i}", "correct_answer": "A", "explanation": f"Explanation {i}"}
            for i in range(1, 11)
        ]
        mock_get_quiz.return_value = {"passing_score": 70, "questions": questions}

        # Mock no existing completion
        mock_get_completion.return_value = None

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
        }

        # Submit quiz with exactly 70% correct (7 out of 10)
        answers = {f"q{i}": "A" for i in range(1, 8)}  # First 7 correct
        answers.update({f"q{i}": "B" for i in range(8, 11)})  # Last 3 wrong

        result = submit_quiz("user123", "secure-sdlc", answers)

        # Verify result
        assert result["passed"] is True
        assert result["score"] == 70
        assert result["passing_score"] == 70

        # Verify completion was saved
        mock_save_completion.assert_called_once()

    @patch("backend.services.quiz_service.get_quiz")
    @patch("backend.services.quiz_service.get_module_completion")
    @patch("backend.services.quiz_service.save_module_completion")
    @patch("backend.services.quiz_service.get_streak_data")
    def test_submit_quiz_recompletion_no_streak_update(
        self, mock_get_streak, mock_save_completion, mock_get_completion, mock_get_quiz
    ):
        """Test quiz re-completion does not update streak."""
        # Mock quiz definition
        mock_get_quiz.return_value = {
            "passing_score": 70,
            "questions": [
                {"id": "q1", "correct_answer": "B", "explanation": "Explanation 1"},
            ],
        }

        # Mock existing completion
        mock_get_completion.return_value = {
            "score": 80,
            "first_completed_at": "2024-01-15T10:00:00+00:00",
            "completed_at": "2024-01-15T10:00:00+00:00",
        }

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": 5,
            "longest_streak": 10,
            "last_activity_date": "2024-01-15",
        }

        # Submit quiz again
        result = submit_quiz("user123", "secure-sdlc", {"q1": "B"})

        # Verify result
        assert result["passed"] is True
        assert result["already_completed"] is True
        assert result["current_streak"] == 5  # Unchanged

        # Verify completion was saved (as re-completion)
        mock_save_completion.assert_called_once_with(
            "user123", "secure-sdlc", 100, False
        )

    @patch("backend.services.quiz_service.get_quiz")
    def test_submit_quiz_invalid_module(self, mock_get_quiz):
        """Test quiz submission with invalid module_id raises QuizNotFoundError."""
        # Mock quiz not found
        mock_get_quiz.return_value = None

        # Verify QuizNotFoundError is raised
        with pytest.raises(QuizNotFoundError) as exc_info:
            submit_quiz("user123", "nonexistent-module", {"q1": "A"})

        assert "Quiz not found" in str(exc_info.value)

    @patch("backend.services.quiz_service.get_quiz")
    def test_submit_quiz_missing_required_questions(self, mock_get_quiz):
        """Test quiz submission with missing required question IDs."""
        # Mock quiz definition
        mock_get_quiz.return_value = {
            "passing_score": 70,
            "questions": [
                {"id": "q1", "correct_answer": "B", "explanation": "Explanation 1"},
                {"id": "q2", "correct_answer": "C", "explanation": "Explanation 2"},
            ],
        }

        # Submit quiz with missing q2
        with pytest.raises(ValueError) as exc_info:
            submit_quiz("user123", "secure-sdlc", {"q1": "B"})

        assert "Missing required question IDs" in str(exc_info.value)

    @patch("backend.services.quiz_service.get_quiz")
    def test_submit_quiz_extra_questions(self, mock_get_quiz):
        """Test quiz submission with extra question IDs not in quiz."""
        # Mock quiz definition
        mock_get_quiz.return_value = {
            "passing_score": 70,
            "questions": [
                {"id": "q1", "correct_answer": "B", "explanation": "Explanation 1"},
            ],
        }

        # Submit quiz with extra question
        with pytest.raises(ValueError) as exc_info:
            submit_quiz("user123", "secure-sdlc", {"q1": "B", "q2": "C"})

        assert "Extra question IDs not in quiz" in str(exc_info.value)

    @patch("backend.services.quiz_service.get_quiz")
    @patch("backend.services.quiz_service.get_module_completion")
    @patch("backend.services.quiz_service.get_streak_data")
    def test_submit_quiz_results_structure(
        self, mock_get_streak, mock_get_completion, mock_get_quiz
    ):
        """Test that results array has correct structure."""
        # Mock quiz definition
        mock_get_quiz.return_value = {
            "passing_score": 70,
            "questions": [
                {"id": "q1", "correct_answer": "B", "explanation": "Explanation 1"},
                {"id": "q2", "correct_answer": "C", "explanation": "Explanation 2"},
            ],
        }

        # Mock no existing completion
        mock_get_completion.return_value = None

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
        }

        # Submit quiz
        result = submit_quiz("user123", "secure-sdlc", {"q1": "B", "q2": "A"})

        # Verify results structure
        assert len(result["results"]) == 2

        for question_result in result["results"]:
            assert "question_id" in question_result
            assert "correct" in question_result
            assert "correct_answer" in question_result
            assert "explanation" in question_result

        # Verify specific results
        q1_result = next(r for r in result["results"] if r["question_id"] == "q1")
        assert q1_result["correct"] is True
        assert q1_result["correct_answer"] == "B"

        q2_result = next(r for r in result["results"] if r["question_id"] == "q2")
        assert q2_result["correct"] is False
        assert q2_result["correct_answer"] == "C"

    @patch.dict(
        os.environ,
        {
            "USE_NEW_REGISTRY_AS_PRIMARY": "true",
            "CONTENT_REGISTRY_BUCKET": "test-bucket",
        },
    )
    @patch("backend.services.quiz_service.CONTENT_REGISTRY_AVAILABLE", True)
    @patch("backend.services.quiz_service.get_registry_service")
    @patch("backend.services.quiz_service.get_quiz")
    def test_submit_quiz_registry_unavailable_no_fallback(
        self, mock_get_quiz, mock_get_registry_service
    ):
        """Test quiz submission when registry is unavailable and no fallback exists."""
        # Mock old registry returns None (no fallback)
        mock_get_quiz.return_value = None

        # Mock new registry raises exception (S3 failure)
        mock_registry = MagicMock()
        mock_registry.get_quiz.side_effect = Exception("S3 connection failed")
        mock_get_registry_service.return_value = mock_registry

        # Verify RegistryUnavailableError is raised
        with pytest.raises(RegistryUnavailableError) as exc_info:
            submit_quiz("user123", "secure-sdlc", {"q1": "A"})

        assert "Content registry unavailable" in str(exc_info.value)

    @patch.dict(
        os.environ,
        {
            "USE_NEW_REGISTRY_AS_PRIMARY": "true",
            "CONTENT_REGISTRY_BUCKET": "test-bucket",
        },
    )
    @patch("backend.services.quiz_service.CONTENT_REGISTRY_AVAILABLE", True)
    @patch("backend.services.quiz_service.get_registry_service")
    @patch("backend.services.quiz_service.get_quiz")
    def test_submit_quiz_schema_version_error_no_fallback(
        self, mock_get_quiz, mock_get_registry_service
    ):
        """Test quiz submission when schema version is incompatible and no fallback exists."""
        from backend.services.content_registry import SchemaVersionError

        # Mock old registry returns None (no fallback)
        mock_get_quiz.return_value = None

        # Mock new registry raises SchemaVersionError
        mock_registry = MagicMock()
        mock_registry.get_quiz.side_effect = SchemaVersionError(
            "Incompatible schema version"
        )
        mock_get_registry_service.return_value = mock_registry

        # Verify RegistryUnavailableError is raised
        with pytest.raises(RegistryUnavailableError) as exc_info:
            submit_quiz("user123", "secure-sdlc", {"q1": "A"})

        # The error message should contain information about the registry being unavailable
        assert "unavailable" in str(exc_info.value).lower()

    @patch.dict(
        os.environ,
        {
            "USE_NEW_REGISTRY_AS_PRIMARY": "true",
            "CONTENT_REGISTRY_BUCKET": "test-bucket",
        },
    )
    @patch("backend.services.quiz_service.CONTENT_REGISTRY_AVAILABLE", True)
    @patch("backend.services.quiz_service.get_registry_service")
    @patch("backend.services.quiz_service.get_quiz")
    @patch("backend.services.quiz_service.get_module_completion")
    @patch("backend.services.quiz_service.save_module_completion")
    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_submit_quiz_registry_unavailable_with_fallback(
        self,
        mock_update_streak,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_quiz,
        mock_get_registry_service,
    ):
        """Test quiz submission falls back to old registry when new registry fails."""
        # Mock new registry raises exception (S3 failure)
        mock_registry = MagicMock()
        mock_registry.get_quiz.side_effect = Exception("S3 connection failed")
        mock_get_registry_service.return_value = mock_registry

        # Mock old registry returns valid quiz (fallback works)
        mock_get_quiz.return_value = {
            "passing_score": 70,
            "questions": [
                {"id": "q1", "correct_answer": "B", "explanation": "Explanation 1"},
            ],
        }

        # Mock no existing completion
        mock_get_completion.return_value = None

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
        }

        # Submit quiz - should succeed using fallback
        result = submit_quiz("user123", "secure-sdlc", {"q1": "B"})

        # Verify result is successful
        assert result["passed"] is True
        assert result["score"] == 100


class TestUpdateStreak:
    """Tests for _update_streak function."""

    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_update_streak_first_completion(self, mock_update_streak, mock_get_streak):
        """Test streak update for first ever completion."""
        # Mock no existing streak
        mock_get_streak.return_value = {
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
        }

        result = _update_streak("user123")

        # Verify streak is set to 1
        assert result == 1

        # Verify update was called with correct values
        mock_update_streak.assert_called_once()
        call_args = mock_update_streak.call_args[0]
        assert call_args[0] == "user123"
        assert call_args[1] == 1  # current_streak
        assert call_args[2] == 1  # longest_streak
        # Verify date is today
        today = datetime.now(timezone.utc).date().isoformat()
        assert call_args[3] == today

    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_update_streak_consecutive_day(self, mock_update_streak, mock_get_streak):
        """Test streak increment for consecutive day completion."""
        # Mock existing streak from yesterday
        yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        mock_get_streak.return_value = {
            "current_streak": 5,
            "longest_streak": 10,
            "last_activity_date": yesterday,
        }

        result = _update_streak("user123")

        # Verify streak incremented
        assert result == 6

        # Verify update was called with incremented streak
        mock_update_streak.assert_called_once()
        call_args = mock_update_streak.call_args[0]
        assert call_args[1] == 6  # current_streak
        assert call_args[2] == 10  # longest_streak unchanged

    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_update_streak_same_day(self, mock_update_streak, mock_get_streak):
        """Test streak unchanged for same day completion."""
        # Mock existing streak from today
        today = datetime.now(timezone.utc).date().isoformat()
        mock_get_streak.return_value = {
            "current_streak": 5,
            "longest_streak": 10,
            "last_activity_date": today,
        }

        result = _update_streak("user123")

        # Verify streak unchanged
        assert result == 5

        # Verify update was called with same streak
        mock_update_streak.assert_called_once()
        call_args = mock_update_streak.call_args[0]
        assert call_args[1] == 5  # current_streak unchanged

    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_update_streak_gap_in_days(self, mock_update_streak, mock_get_streak):
        """Test streak reset for gap in completions."""
        # Mock existing streak from 3 days ago
        three_days_ago = (
            datetime.now(timezone.utc).date() - timedelta(days=3)
        ).isoformat()
        mock_get_streak.return_value = {
            "current_streak": 5,
            "longest_streak": 10,
            "last_activity_date": three_days_ago,
        }

        result = _update_streak("user123")

        # Verify streak reset to 1
        assert result == 1

        # Verify update was called with reset streak
        mock_update_streak.assert_called_once()
        call_args = mock_update_streak.call_args[0]
        assert call_args[1] == 1  # current_streak reset
        assert call_args[2] == 10  # longest_streak unchanged

    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_update_streak_new_longest(self, mock_update_streak, mock_get_streak):
        """Test longest streak update when current exceeds it."""
        # Mock existing streak from yesterday
        yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        mock_get_streak.return_value = {
            "current_streak": 10,
            "longest_streak": 10,
            "last_activity_date": yesterday,
        }

        result = _update_streak("user123")

        # Verify streak incremented and longest updated
        assert result == 11

        # Verify update was called with new longest
        mock_update_streak.assert_called_once()
        call_args = mock_update_streak.call_args[0]
        assert call_args[1] == 11  # current_streak
        assert call_args[2] == 11  # longest_streak updated
