"""
Test parallel operation mode for quiz service.

This test verifies that the quiz service can read from both old and new registries
and compare results correctly.

Requirements: 10.6, 10.7
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from services.quiz_service import (
    submit_quiz,
    _compare_quiz_definitions,
    _compare_validation_results,
)


class TestParallelOperationMode:
    """Test parallel operation mode functionality."""

    def test_compare_quiz_definitions_matching(self, caplog):
        """Test that matching quiz definitions don't log discrepancies."""
        old_quiz = {
            "passing_score": 70,
            "questions": [
                {"id": "q1", "correct_answer": "A", "explanation": "Test 1"},
                {"id": "q2", "correct_answer": "B", "explanation": "Test 2"},
            ],
        }

        new_quiz = {
            "passing_score": 70,
            "questions": [
                {"id": "q1", "correct_answer": "A", "explanation": "Test 1"},
                {"id": "q2", "correct_answer": "B", "explanation": "Test 2"},
            ],
        }

        with caplog.at_level("INFO"):
            _compare_quiz_definitions(old_quiz, new_quiz, "test-module")

        # Should log success message
        assert any(
            "Quiz definitions match" in record.message for record in caplog.records
        )
        assert not any(
            "discrepancies detected" in record.message for record in caplog.records
        )

    def test_compare_quiz_definitions_passing_score_mismatch(self, caplog):
        """Test that passing score mismatches are logged."""
        old_quiz = {"passing_score": 70, "questions": []}

        new_quiz = {"passing_score": 80, "questions": []}

        with caplog.at_level("ERROR"):
            _compare_quiz_definitions(old_quiz, new_quiz, "test-module")

        # Should log error with discrepancy
        assert any(
            "discrepancies detected" in record.message for record in caplog.records
        )
        # Check the extra field contains the discrepancy details
        assert any("discrepancies" in record.__dict__ for record in caplog.records)

    def test_compare_quiz_definitions_question_count_mismatch(self, caplog):
        """Test that question count mismatches are logged."""
        old_quiz = {
            "passing_score": 70,
            "questions": [{"id": "q1", "correct_answer": "A", "explanation": "Test 1"}],
        }

        new_quiz = {
            "passing_score": 70,
            "questions": [
                {"id": "q1", "correct_answer": "A", "explanation": "Test 1"},
                {"id": "q2", "correct_answer": "B", "explanation": "Test 2"},
            ],
        }

        with caplog.at_level("ERROR"):
            _compare_quiz_definitions(old_quiz, new_quiz, "test-module")

        # Should log error with discrepancy
        assert any(
            "discrepancies detected" in record.message for record in caplog.records
        )

    def test_compare_quiz_definitions_answer_mismatch(self, caplog):
        """Test that correct answer mismatches are logged."""
        old_quiz = {
            "passing_score": 70,
            "questions": [{"id": "q1", "correct_answer": "A", "explanation": "Test 1"}],
        }

        new_quiz = {
            "passing_score": 70,
            "questions": [{"id": "q1", "correct_answer": "B", "explanation": "Test 1"}],
        }

        with caplog.at_level("ERROR"):
            _compare_quiz_definitions(old_quiz, new_quiz, "test-module")

        # Should log error with discrepancy
        assert any(
            "discrepancies detected" in record.message for record in caplog.records
        )

    def test_compare_validation_results_matching(self, caplog):
        """Test that matching validation results don't log discrepancies."""
        old_results = {
            "score": 80,
            "passed": True,
            "results": [
                {"question_id": "q1", "correct": True},
                {"question_id": "q2", "correct": False},
            ],
        }

        new_results = {
            "score": 80,
            "passed": True,
            "results": [
                {"question_id": "q1", "correct": True},
                {"question_id": "q2", "correct": False},
            ],
        }

        with caplog.at_level("INFO"):
            _compare_validation_results(
                old_results, new_results, "test-module", {"q1": "A", "q2": "B"}
            )

        # Should log success message
        assert any(
            "Validation results match" in record.message for record in caplog.records
        )
        assert not any(
            "discrepancies detected" in record.message for record in caplog.records
        )

    def test_compare_validation_results_score_mismatch(self, caplog):
        """Test that score mismatches are logged."""
        old_results = {"score": 80, "passed": True, "results": []}

        new_results = {"score": 70, "passed": True, "results": []}

        with caplog.at_level("ERROR"):
            _compare_validation_results(old_results, new_results, "test-module", {})

        # Should log error with discrepancy
        assert any(
            "discrepancies detected" in record.message for record in caplog.records
        )

    def test_compare_validation_results_passed_mismatch(self, caplog):
        """Test that passed status mismatches are logged."""
        old_results = {"score": 80, "passed": True, "results": []}

        new_results = {"score": 80, "passed": False, "results": []}

        with caplog.at_level("ERROR"):
            _compare_validation_results(old_results, new_results, "test-module", {})

        # Should log error with discrepancy
        assert any(
            "discrepancies detected" in record.message for record in caplog.records
        )

    @patch.dict(
        os.environ,
        {
            "CONTENT_REGISTRY_BUCKET": "test-bucket",
            "USE_NEW_REGISTRY_AS_PRIMARY": "true",
        },
    )
    @patch("services.quiz_service.PARALLEL_MODE_ENABLED", True)
    @patch("services.quiz_service.CONTENT_REGISTRY_AVAILABLE", True)
    @patch("services.quiz_service.get_quiz")
    @patch("services.quiz_service.get_registry_service")
    @patch("services.quiz_service.get_module_completion")
    @patch("services.quiz_service.save_module_completion")
    @patch("services.quiz_service.get_streak_data")
    @patch("services.quiz_service.update_streak_data")
    def test_submit_quiz_parallel_mode_enabled(
        self,
        mock_update_streak,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_registry_service,
        mock_get_quiz,
        caplog,
    ):
        """Test that parallel mode fetches from both registries."""
        # Setup old registry
        old_quiz = {
            "passing_score": 70,
            "questions": [{"id": "q1", "correct_answer": "A", "explanation": "Test 1"}],
        }
        mock_get_quiz.return_value = old_quiz

        # Setup new registry
        mock_registry_service = MagicMock()
        mock_registry_service.get_quiz.return_value = old_quiz

        mock_validation_result = MagicMock()
        mock_validation_result.score = 100.0
        mock_validation_result.passed = True
        mock_validation_result.per_question = {"q1": True}
        mock_registry_service.validate_quiz_submission.return_value = (
            mock_validation_result
        )

        mock_get_registry_service.return_value = mock_registry_service

        # Setup completion data
        mock_get_completion.return_value = None
        mock_get_streak.return_value = {
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
        }

        # Submit quiz
        with caplog.at_level("INFO"):
            result = submit_quiz("user123", "test-module", {"q1": "A"})

        # Verify both registries were accessed
        # Note: get_quiz is called twice now - once for fallback check and once for parallel comparison
        assert mock_get_quiz.call_count == 2
        mock_registry_service.get_quiz.assert_called_with("test-module")
        mock_registry_service.validate_quiz_submission.assert_called_once_with(
            "test-module", {"q1": "A"}
        )

        # Verify comparison was logged
        assert any(
            "Parallel mode: fetched quiz from both registries" in record.message
            for record in caplog.records
        )

        # Verify result is from new registry (primary source)
        assert result["score"] == 100
        assert result["passed"] is True

    @patch.dict(os.environ, {"ENABLE_PARALLEL_REGISTRY_MODE": "false"})
    @patch("services.quiz_service.get_quiz")
    @patch("services.quiz_service.get_module_completion")
    @patch("services.quiz_service.save_module_completion")
    @patch("services.quiz_service.get_streak_data")
    @patch("services.quiz_service.update_streak_data")
    def test_submit_quiz_parallel_mode_disabled(
        self,
        mock_update_streak,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_quiz,
    ):
        """Test that parallel mode is skipped when disabled."""
        # Setup old registry
        old_quiz = {
            "passing_score": 70,
            "questions": [{"id": "q1", "correct_answer": "A", "explanation": "Test 1"}],
        }
        mock_get_quiz.return_value = old_quiz

        # Setup completion data
        mock_get_completion.return_value = None
        mock_get_streak.return_value = {
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
        }

        # Submit quiz
        result = submit_quiz("user123", "test-module", {"q1": "A"})

        # Verify only old registry was accessed
        mock_get_quiz.assert_called_once_with("test-module")

        # Verify result is correct
        assert result["score"] == 100
        assert result["passed"] is True

    @patch.dict(
        os.environ,
        {
            "CONTENT_REGISTRY_BUCKET": "test-bucket",
            "USE_NEW_REGISTRY_AS_PRIMARY": "true",
            "ENABLE_PARALLEL_REGISTRY_MODE": "false",
        },
    )
    @patch("services.quiz_service.CONTENT_REGISTRY_AVAILABLE", True)
    @patch("services.quiz_service.get_quiz")
    @patch("services.quiz_service.get_registry_service")
    @patch("services.quiz_service.get_module_completion")
    @patch("services.quiz_service.save_module_completion")
    @patch("services.quiz_service.get_streak_data")
    @patch("services.quiz_service.update_streak_data")
    def test_submit_quiz_new_registry_as_primary(
        self,
        mock_update_streak,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_registry_service,
        mock_get_quiz,
        caplog,
    ):
        """Test that new registry is used as primary source when USE_NEW_REGISTRY_AS_PRIMARY=true."""
        # Setup new registry (primary)
        new_quiz = {
            "passing_score": 80,
            "questions": [
                {
                    "id": "q1",
                    "correct_answer": "B",
                    "explanation": "New registry answer",
                }
            ],
        }

        mock_registry_service = MagicMock()
        mock_registry_service.get_quiz.return_value = new_quiz
        mock_get_registry_service.return_value = mock_registry_service

        # Setup old registry (should not be used)
        old_quiz = {
            "passing_score": 70,
            "questions": [
                {
                    "id": "q1",
                    "correct_answer": "A",
                    "explanation": "Old registry answer",
                }
            ],
        }
        mock_get_quiz.return_value = old_quiz

        # Setup completion data
        mock_get_completion.return_value = None
        mock_get_streak.return_value = {
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
        }

        # Submit quiz with answer from new registry
        with caplog.at_level("INFO"):
            result = submit_quiz("user123", "test-module", {"q1": "B"})

        # Verify new registry was used as primary
        mock_registry_service.get_quiz.assert_called_with("test-module")

        # Verify result uses new registry's passing score and validation
        assert result["score"] == 100
        assert result["passed"] is True
        assert result["passing_score"] == 80

        # Verify log message indicates new registry as primary
        assert any(
            "Using ContentRegistryService as primary source" in record.message
            for record in caplog.records
        )

    @patch.dict(
        os.environ,
        {
            "CONTENT_REGISTRY_BUCKET": "test-bucket",
            "USE_NEW_REGISTRY_AS_PRIMARY": "true",
            "ENABLE_PARALLEL_REGISTRY_MODE": "false",
        },
    )
    @patch("services.quiz_service.CONTENT_REGISTRY_AVAILABLE", True)
    @patch("services.quiz_service.get_quiz")
    @patch("services.quiz_service.get_registry_service")
    @patch("services.quiz_service.get_module_completion")
    @patch("services.quiz_service.save_module_completion")
    @patch("services.quiz_service.get_streak_data")
    @patch("services.quiz_service.update_streak_data")
    def test_submit_quiz_fallback_to_old_registry(
        self,
        mock_update_streak,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_registry_service,
        mock_get_quiz,
        caplog,
    ):
        """Test that old registry is used as fallback when new registry fails."""
        # Setup new registry to return None (quiz not found)
        mock_registry_service = MagicMock()
        mock_registry_service.get_quiz.return_value = None
        mock_get_registry_service.return_value = mock_registry_service

        # Setup old registry (fallback)
        old_quiz = {
            "passing_score": 70,
            "questions": [
                {
                    "id": "q1",
                    "correct_answer": "A",
                    "explanation": "Old registry answer",
                }
            ],
        }
        mock_get_quiz.return_value = old_quiz

        # Setup completion data
        mock_get_completion.return_value = None
        mock_get_streak.return_value = {
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
        }

        # Submit quiz
        with caplog.at_level("WARNING"):
            result = submit_quiz("user123", "test-module", {"q1": "A"})

        # Verify new registry was tried first
        mock_registry_service.get_quiz.assert_called_with("test-module")

        # Verify old registry was used as fallback
        mock_get_quiz.assert_called_with("test-module")

        # Verify result uses old registry
        assert result["score"] == 100
        assert result["passed"] is True
        assert result["passing_score"] == 70

        # Verify log message indicates fallback
        assert any(
            "falling back to hardcoded registry" in record.message
            for record in caplog.records
        )

    @patch.dict(
        os.environ,
        {
            "CONTENT_REGISTRY_BUCKET": "test-bucket",
            "USE_NEW_REGISTRY_AS_PRIMARY": "false",
            "ENABLE_PARALLEL_REGISTRY_MODE": "false",
        },
    )
    @patch("services.quiz_service.USE_NEW_REGISTRY_AS_PRIMARY", False)
    @patch("services.quiz_service.CONTENT_REGISTRY_AVAILABLE", True)
    @patch("services.quiz_service.get_quiz")
    @patch("services.quiz_service.get_registry_service")
    @patch("services.quiz_service.get_module_completion")
    @patch("services.quiz_service.save_module_completion")
    @patch("services.quiz_service.get_streak_data")
    @patch("services.quiz_service.update_streak_data")
    def test_submit_quiz_old_registry_as_primary(
        self,
        mock_update_streak,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_registry_service,
        mock_get_quiz,
        caplog,
    ):
        """Test that old registry is used as primary source when USE_NEW_REGISTRY_AS_PRIMARY=false."""
        # Setup old registry (primary)
        old_quiz = {
            "passing_score": 70,
            "questions": [
                {
                    "id": "q1",
                    "correct_answer": "A",
                    "explanation": "Old registry answer",
                }
            ],
        }
        mock_get_quiz.return_value = old_quiz

        # Setup new registry (should not be used)
        new_quiz = {
            "passing_score": 80,
            "questions": [
                {
                    "id": "q1",
                    "correct_answer": "B",
                    "explanation": "New registry answer",
                }
            ],
        }

        mock_registry_service = MagicMock()
        mock_registry_service.get_quiz.return_value = new_quiz
        mock_get_registry_service.return_value = mock_registry_service

        # Setup completion data
        mock_get_completion.return_value = None
        mock_get_streak.return_value = {
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
        }

        # Submit quiz with answer from old registry
        with caplog.at_level("INFO"):
            result = submit_quiz("user123", "test-module", {"q1": "A"})

        # Verify old registry was used as primary
        mock_get_quiz.assert_called_with("test-module")

        # Verify result uses old registry's passing score and validation
        assert result["score"] == 100
        assert result["passed"] is True
        assert result["passing_score"] == 70

        # Verify log message indicates old registry as primary
        assert any(
            "Using hardcoded quiz_registry as primary source" in record.message
            for record in caplog.records
        )
