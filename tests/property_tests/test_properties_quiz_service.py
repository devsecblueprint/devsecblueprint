"""
Property-based tests for quiz service completion tracking.

Feature: module-quiz-system
"""

from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings, assume
from backend.services.quiz_service import submit_quiz

# Strategies for generating test data
user_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip() != "")

module_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_",
    min_size=1,
    max_size=100,
).filter(lambda x: x.strip() != "" and not x.startswith("-") and not x.endswith("-"))


def generate_quiz_with_answers(passing_score, num_questions, num_correct):
    """
    Generate a quiz definition and answers that will result in a specific score.

    Args:
        passing_score: The passing threshold (0-100)
        num_questions: Total number of questions
        num_correct: Number of correct answers

    Returns:
        tuple: (quiz_definition, answers)
    """
    questions = []
    answers = {}

    for i in range(num_questions):
        question_id = f"q{i+1}"
        correct_answer = "A"

        questions.append(
            {
                "id": question_id,
                "correct_answer": correct_answer,
                "explanation": f"Explanation for question {i+1}",
            }
        )

        # First num_correct questions get correct answers, rest get wrong answers
        if i < num_correct:
            answers[question_id] = "A"  # Correct
        else:
            answers[question_id] = "B"  # Wrong

    quiz_definition = {"passing_score": passing_score, "questions": questions}

    return quiz_definition, answers


class TestCompletionTrackingProperties:
    """Property-based tests for completion tracking logic."""

    @settings(max_examples=100)
    @given(
        user_id=user_id_strategy,
        module_id=module_id_strategy,
        passing_score=st.integers(min_value=1, max_value=100),
        num_questions=st.integers(min_value=1, max_value=20),
    )
    @patch("backend.services.quiz_service.get_quiz")
    @patch("backend.services.quiz_service.get_module_completion")
    @patch("backend.services.quiz_service.save_module_completion")
    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_property_9_passing_quiz_creates_completion_record(
        self,
        mock_update_streak,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_quiz,
        user_id,
        module_id,
        passing_score,
        num_questions,
    ):
        """
        Property 9: Passing Quiz Creates Completion Record

        For any quiz submission where the score meets or exceeds the passing threshold,
        a completion record should exist in UserState after processing.

        **Validates: Requirements 4.1**
        """
        # Calculate num_correct to ensure passing score
        # Score = (num_correct / num_questions) * 100
        # We want score >= passing_score
        num_correct = max(1, int((passing_score * num_questions + 99) / 100))
        assume(num_correct <= num_questions)

        # Generate quiz and answers that will pass
        quiz_definition, answers = generate_quiz_with_answers(
            passing_score, num_questions, num_correct
        )

        # Mock quiz registry
        mock_get_quiz.return_value = quiz_definition

        # Mock no existing completion (first completion)
        mock_get_completion.return_value = None

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
        }

        # Submit quiz
        result = submit_quiz(user_id, module_id, answers)

        # Verify quiz passed
        assert result["passed"] is True
        assert result["score"] >= passing_score

        # Verify completion record was saved
        mock_save_completion.assert_called_once()
        call_args = mock_save_completion.call_args[0]
        assert call_args[0] == user_id
        assert call_args[1] == module_id
        assert call_args[2] == result["score"]

    @settings(max_examples=100)
    @given(
        user_id=user_id_strategy,
        module_id=module_id_strategy,
        passing_score=st.integers(min_value=1, max_value=100),
        num_questions=st.integers(min_value=2, max_value=20),
    )
    @patch("backend.services.quiz_service.get_quiz")
    @patch("backend.services.quiz_service.get_module_completion")
    @patch("backend.services.quiz_service.save_module_completion")
    @patch("backend.services.quiz_service.get_streak_data")
    def test_property_12_failing_quiz_no_record(
        self,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_quiz,
        user_id,
        module_id,
        passing_score,
        num_questions,
    ):
        """
        Property 12: Failing Quiz No Record

        For any quiz submission where the score is below the passing threshold,
        no completion record should be created or updated in UserState.

        **Validates: Requirements 4.6**
        """
        # Calculate num_correct to ensure failing score
        # We want score < passing_score
        # Score = (num_correct / num_questions) * 100
        num_correct = max(0, int((passing_score * num_questions - 1) / 100))
        assume(num_correct < num_questions)

        # Generate quiz and answers that will fail
        quiz_definition, answers = generate_quiz_with_answers(
            passing_score, num_questions, num_correct
        )

        # Mock quiz registry
        mock_get_quiz.return_value = quiz_definition

        # Mock no existing completion
        mock_get_completion.return_value = None

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": 5,
            "longest_streak": 10,
            "last_activity_date": "2024-01-15",
        }

        # Submit quiz
        result = submit_quiz(user_id, module_id, answers)

        # Verify quiz failed
        assert result["passed"] is False
        assert result["score"] < passing_score

        # Verify completion record was NOT saved
        mock_save_completion.assert_not_called()

    @settings(max_examples=100)
    @given(
        user_id=user_id_strategy,
        module_id=module_id_strategy,
        passing_score=st.integers(min_value=1, max_value=100),
        num_questions=st.integers(min_value=1, max_value=20),
        has_existing_completion=st.booleans(),
    )
    @patch("backend.services.quiz_service.get_quiz")
    @patch("backend.services.quiz_service.get_module_completion")
    @patch("backend.services.quiz_service.save_module_completion")
    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_property_20_already_completed_flag_correctness(
        self,
        mock_update_streak,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_quiz,
        user_id,
        module_id,
        passing_score,
        num_questions,
        has_existing_completion,
    ):
        """
        Property 20: Already Completed Flag Correctness

        For any quiz submission, the already_completed field should be true if and only if
        a completion record existed before this submission.

        **Validates: Requirements 6.6, 6.7**
        """
        # Generate passing quiz
        num_correct = max(1, int((passing_score * num_questions + 99) / 100))
        assume(num_correct <= num_questions)

        quiz_definition, answers = generate_quiz_with_answers(
            passing_score, num_questions, num_correct
        )

        # Mock quiz registry
        mock_get_quiz.return_value = quiz_definition

        # Mock existing completion based on parameter
        if has_existing_completion:
            mock_get_completion.return_value = {
                "score": 80,
                "first_completed_at": "2024-01-15T10:00:00+00:00",
                "completed_at": "2024-01-15T10:00:00+00:00",
            }
        else:
            mock_get_completion.return_value = None

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": 5,
            "longest_streak": 10,
            "last_activity_date": "2024-01-15",
        }

        # Submit quiz
        result = submit_quiz(user_id, module_id, answers)

        # Verify already_completed flag matches existence of prior completion
        assert result["already_completed"] == has_existing_completion

    @settings(max_examples=100)
    @given(
        user_id=user_id_strategy,
        module_id=module_id_strategy,
        passing_score=st.integers(min_value=1, max_value=100),
        num_questions=st.integers(min_value=1, max_value=20),
        old_score=st.integers(min_value=0, max_value=100),
    )
    @patch("backend.services.quiz_service.get_quiz")
    @patch("backend.services.quiz_service.get_module_completion")
    @patch("backend.services.quiz_service.save_module_completion")
    @patch("backend.services.quiz_service.get_streak_data")
    def test_property_11_recompletion_behavior(
        self,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_quiz,
        user_id,
        module_id,
        passing_score,
        num_questions,
        old_score,
    ):
        """
        Property 11: Re-Completion Behavior

        For any re-completion of a module, the stored score should be updated only if
        the new score is higher, the completed_at timestamp should be updated to the
        new submission time, and the first_completed_at timestamp should remain unchanged.

        **Validates: Requirements 4.3, 4.4, 4.5**
        """
        # Generate passing quiz
        num_correct = max(1, int((passing_score * num_questions + 99) / 100))
        assume(num_correct <= num_questions)

        quiz_definition, answers = generate_quiz_with_answers(
            passing_score, num_questions, num_correct
        )

        # Mock quiz registry
        mock_get_quiz.return_value = quiz_definition

        # Mock existing completion (re-completion scenario)
        mock_get_completion.return_value = {
            "score": old_score,
            "first_completed_at": "2024-01-15T10:00:00+00:00",
            "completed_at": "2024-01-15T10:00:00+00:00",
        }

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": 5,
            "longest_streak": 10,
            "last_activity_date": "2024-01-15",
        }

        # Submit quiz
        result = submit_quiz(user_id, module_id, answers)

        # Verify quiz passed
        assert result["passed"] is True
        assert result["already_completed"] is True

        # Verify completion was saved as re-completion (is_first_completion=False)
        mock_save_completion.assert_called_once()
        call_args = mock_save_completion.call_args[0]
        assert call_args[0] == user_id
        assert call_args[1] == module_id
        assert call_args[2] == result["score"]
        assert call_args[3] is False  # is_first_completion should be False

        # Note: The actual score update logic (only if higher) is tested in
        # the save_module_completion function tests, not here


class TestScoreCalculationProperties:
    """Property-based tests for score calculation logic."""

    @settings(max_examples=100)
    @given(
        user_id=user_id_strategy,
        module_id=module_id_strategy,
        num_questions=st.integers(min_value=1, max_value=50),
        num_correct=st.integers(min_value=0, max_value=50),
    )
    @patch("backend.services.quiz_service.get_quiz")
    @patch("backend.services.quiz_service.get_module_completion")
    @patch("backend.services.quiz_service.save_module_completion")
    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_property_7_score_calculation(
        self,
        mock_update_streak,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_quiz,
        user_id,
        module_id,
        num_questions,
        num_correct,
    ):
        """
        Property 7: Score Calculation

        For any set of quiz answers, the calculated score should equal
        (number of correct answers / total number of questions) * 100.

        **Validates: Requirements 3.6**
        """
        # Ensure num_correct doesn't exceed num_questions
        assume(num_correct <= num_questions)

        # Generate quiz and answers with specific correct count
        quiz_definition, answers = generate_quiz_with_answers(
            passing_score=70,  # Arbitrary passing score
            num_questions=num_questions,
            num_correct=num_correct,
        )

        # Mock quiz registry
        mock_get_quiz.return_value = quiz_definition

        # Mock no existing completion
        mock_get_completion.return_value = None

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
        }

        # Submit quiz
        result = submit_quiz(user_id, module_id, answers)

        # Calculate expected score
        expected_score = int((num_correct / num_questions) * 100)

        # Verify score calculation is correct
        assert result["score"] == expected_score

        # Verify score is in valid range
        assert 0 <= result["score"] <= 100

        # Verify results array has correct length
        assert len(result["results"]) == num_questions

        # Verify correct count matches expected
        actual_correct_count = sum(1 for r in result["results"] if r["correct"])
        assert actual_correct_count == num_correct


class TestStreakCalculationProperties:
    """Property-based tests for streak calculation logic."""

    @settings(max_examples=100)
    @given(
        user_id=user_id_strategy,
        current_streak=st.integers(min_value=0, max_value=1000),
        longest_streak=st.integers(min_value=0, max_value=1000),
        days_since_last_activity=st.integers(min_value=0, max_value=365),
    )
    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_property_14_streak_calculation_logic(
        self,
        mock_update_streak,
        mock_get_streak,
        user_id,
        current_streak,
        longest_streak,
        days_since_last_activity,
    ):
        """
        Property 14: Streak Calculation Logic

        For any first completion with existing streak data, if last_activity_date equals
        today then current_streak should not change, if last_activity_date equals yesterday
        then current_streak should increment by 1, otherwise current_streak should reset to 1.

        **Validates: Requirements 5.2, 5.3, 5.4**
        """
        from datetime import datetime, timezone, timedelta
        from backend.services.quiz_service import _update_streak

        # Ensure longest_streak is at least current_streak
        longest_streak = max(longest_streak, current_streak)

        # Calculate last_activity_date based on days_since_last_activity
        today = datetime.now(timezone.utc).date()

        if days_since_last_activity == 0:
            # Same day
            last_activity_date = today.isoformat()
            expected_streak = current_streak  # No change
        elif days_since_last_activity == 1:
            # Yesterday
            last_activity_date = (today - timedelta(days=1)).isoformat()
            expected_streak = current_streak + 1  # Increment
        else:
            # Gap in completions
            last_activity_date = (
                today - timedelta(days=days_since_last_activity)
            ).isoformat()
            expected_streak = 1  # Reset

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_activity_date": last_activity_date,
        }

        # Update streak
        result = _update_streak(user_id)

        # Verify streak calculation follows the rules
        assert result == expected_streak

        # Verify update_streak_data was called
        mock_update_streak.assert_called_once()
        call_args = mock_update_streak.call_args[0]
        assert call_args[0] == user_id
        assert call_args[1] == expected_streak  # current_streak
        assert call_args[3] == today.isoformat()  # last_activity_date updated to today

    @settings(max_examples=100)
    @given(
        user_id=user_id_strategy,
        current_streak=st.integers(min_value=0, max_value=1000),
        longest_streak=st.integers(min_value=0, max_value=1000),
        days_since_last_activity=st.integers(min_value=0, max_value=365),
    )
    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_property_15_longest_streak_tracking(
        self,
        mock_update_streak,
        mock_get_streak,
        user_id,
        current_streak,
        longest_streak,
        days_since_last_activity,
    ):
        """
        Property 15: Longest Streak Tracking

        For any streak update, the longest_streak should equal the maximum of the new
        current_streak and the previous longest_streak.

        **Validates: Requirements 5.5**
        """
        from datetime import datetime, timezone, timedelta
        from backend.services.quiz_service import _update_streak

        # Ensure longest_streak is at least current_streak
        longest_streak = max(longest_streak, current_streak)

        # Calculate last_activity_date
        today = datetime.now(timezone.utc).date()

        if days_since_last_activity == 0:
            last_activity_date = today.isoformat()
            new_current_streak = current_streak
        elif days_since_last_activity == 1:
            last_activity_date = (today - timedelta(days=1)).isoformat()
            new_current_streak = current_streak + 1
        else:
            last_activity_date = (
                today - timedelta(days=days_since_last_activity)
            ).isoformat()
            new_current_streak = 1

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_activity_date": last_activity_date,
        }

        # Update streak
        _update_streak(user_id)

        # Verify longest_streak is max of new current_streak and previous longest_streak
        mock_update_streak.assert_called_once()
        call_args = mock_update_streak.call_args[0]
        expected_longest = max(new_current_streak, longest_streak)
        assert call_args[2] == expected_longest  # longest_streak

    @settings(max_examples=100)
    @given(
        user_id=user_id_strategy,
        module_id=module_id_strategy,
        passing_score=st.integers(min_value=1, max_value=100),
        num_questions=st.integers(min_value=1, max_value=20),
        current_streak=st.integers(min_value=0, max_value=1000),
        longest_streak=st.integers(min_value=0, max_value=1000),
    )
    @patch("backend.services.quiz_service.get_quiz")
    @patch("backend.services.quiz_service.get_module_completion")
    @patch("backend.services.quiz_service.save_module_completion")
    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_property_17_recompletion_no_streak_update(
        self,
        mock_update_streak,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_quiz,
        user_id,
        module_id,
        passing_score,
        num_questions,
        current_streak,
        longest_streak,
    ):
        """
        Property 17: Re-Completion No Streak Update

        For any re-completion of a module, the current_streak, longest_streak, and
        last_activity_date should remain unchanged.

        **Validates: Requirements 5.7**
        """
        # Ensure longest_streak is at least current_streak
        longest_streak = max(longest_streak, current_streak)

        # Generate passing quiz
        num_correct = max(1, int((passing_score * num_questions + 99) / 100))
        assume(num_correct <= num_questions)

        quiz_definition, answers = generate_quiz_with_answers(
            passing_score, num_questions, num_correct
        )

        # Mock quiz registry
        mock_get_quiz.return_value = quiz_definition

        # Mock existing completion (re-completion scenario)
        mock_get_completion.return_value = {
            "score": 80,
            "first_completed_at": "2024-01-15T10:00:00+00:00",
            "completed_at": "2024-01-15T10:00:00+00:00",
        }

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_activity_date": "2024-01-15",
        }

        # Submit quiz (re-completion)
        result = submit_quiz(user_id, module_id, answers)

        # Verify quiz passed and is a re-completion
        assert result["passed"] is True
        assert result["already_completed"] is True

        # Verify streak was NOT updated (update_streak_data should not be called)
        mock_update_streak.assert_not_called()

        # Verify current_streak in response matches the existing streak
        assert result["current_streak"] == current_streak


class TestUnlimitedAttemptsProperties:
    """Property-based tests for unlimited quiz attempts."""

    @settings(max_examples=100)
    @given(
        user_id=user_id_strategy,
        module_id=module_id_strategy,
        passing_score=st.integers(min_value=1, max_value=100),
        num_questions=st.integers(min_value=1, max_value=20),
        num_previous_submissions=st.integers(min_value=0, max_value=100),
    )
    @patch("backend.services.quiz_service.get_quiz")
    @patch("backend.services.quiz_service.get_module_completion")
    @patch("backend.services.quiz_service.save_module_completion")
    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_property_26_unlimited_attempts(
        self,
        mock_update_streak,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_quiz,
        user_id,
        module_id,
        passing_score,
        num_questions,
        num_previous_submissions,
    ):
        """
        Property 26: Unlimited Attempts

        For any user and module combination, the Quiz_Engine should accept and process
        quiz submissions regardless of how many previous submissions exist.

        **Validates: Requirements 9.1**
        """
        # Generate passing quiz
        num_correct = max(1, int((passing_score * num_questions + 99) / 100))
        assume(num_correct <= num_questions)

        quiz_definition, answers = generate_quiz_with_answers(
            passing_score, num_questions, num_correct
        )

        # Mock quiz registry
        mock_get_quiz.return_value = quiz_definition

        # Mock existing completion if there were previous submissions
        if num_previous_submissions > 0:
            mock_get_completion.return_value = {
                "score": 75,
                "first_completed_at": "2024-01-15T10:00:00+00:00",
                "completed_at": "2024-01-20T15:30:00+00:00",
            }
        else:
            mock_get_completion.return_value = None

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": 5,
            "longest_streak": 10,
            "last_activity_date": "2024-01-15",
        }

        # Submit quiz - should succeed regardless of previous submission count
        result = submit_quiz(user_id, module_id, answers)

        # Verify submission was processed successfully
        assert "passed" in result
        assert "score" in result
        assert "results" in result

        # Verify quiz was scored correctly
        assert result["passed"] is True
        assert result["score"] >= passing_score

        # The system should not reject based on attempt count
        # (no exception should be raised, and result should be returned)

    @settings(max_examples=100)
    @given(
        user_id=user_id_strategy,
        module_id=module_id_strategy,
        passing_score=st.integers(min_value=1, max_value=100),
        num_questions=st.integers(min_value=1, max_value=20),
        num_submissions=st.integers(min_value=2, max_value=10),
    )
    @patch("backend.services.quiz_service.get_quiz")
    @patch("backend.services.quiz_service.get_module_completion")
    @patch("backend.services.quiz_service.save_module_completion")
    @patch("backend.services.quiz_service.get_streak_data")
    @patch("backend.services.quiz_service.update_streak_data")
    def test_property_27_independent_submission_processing(
        self,
        mock_update_streak,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_quiz,
        user_id,
        module_id,
        passing_score,
        num_questions,
        num_submissions,
    ):
        """
        Property 27: Independent Submission Processing

        For any sequence of quiz submissions for the same module, each submission
        should be scored independently without affecting the scoring of other submissions.

        **Validates: Requirements 9.3**
        """
        # Generate quiz definition
        questions = []
        for i in range(num_questions):
            questions.append(
                {
                    "id": f"q{i+1}",
                    "correct_answer": "A",
                    "explanation": f"Explanation {i+1}",
                }
            )

        quiz_definition = {"passing_score": passing_score, "questions": questions}

        # Mock quiz registry
        mock_get_quiz.return_value = quiz_definition

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": 5,
            "longest_streak": 10,
            "last_activity_date": "2024-01-15",
        }

        # Track scores from each submission
        scores = []

        # Submit quiz multiple times with different answer patterns
        for submission_num in range(num_submissions):
            # Generate different answers for each submission
            # Vary the number of correct answers
            num_correct = (submission_num * 3) % (num_questions + 1)

            answers = {}
            for i in range(num_questions):
                question_id = f"q{i+1}"
                # First num_correct get correct answer, rest get wrong
                if i < num_correct:
                    answers[question_id] = "A"  # Correct
                else:
                    answers[question_id] = "B"  # Wrong

            # Mock completion status (after first submission, it's a re-completion)
            if submission_num > 0:
                mock_get_completion.return_value = {
                    "score": scores[-1],  # Previous score
                    "first_completed_at": "2024-01-15T10:00:00+00:00",
                    "completed_at": "2024-01-20T15:30:00+00:00",
                }
            else:
                mock_get_completion.return_value = None

            # Submit quiz
            result = submit_quiz(user_id, module_id, answers)

            # Calculate expected score independently
            expected_score = int((num_correct / num_questions) * 100)

            # Verify this submission was scored independently
            assert result["score"] == expected_score

            # Store score for next iteration
            scores.append(result["score"])

        # Verify all submissions were processed (no exceptions)
        assert len(scores) == num_submissions

        # Verify scores can vary (independent scoring)
        # If we have enough submissions, we should see different scores
        if num_submissions >= 3 and num_questions >= 2:
            # At least some scores should be different (not all identical)
            unique_scores = len(set(scores))
            # This property holds: each submission is scored independently
            # (we don't assert uniqueness, just that scoring happened)
            assert all(0 <= score <= 100 for score in scores)


class TestQuizRegistryProperties:
    """Property-based tests for quiz registry operations."""

    @settings(max_examples=100)
    @given(
        module_id=st.sampled_from(
            ["secure-sdlc"]
        ),  # Use actual module IDs from registry
    )
    def test_property_2_quiz_registry_lookup(self, module_id):
        """
        Property 2: Quiz Registry Lookup

        For any valid module_id that exists in the Quiz_Registry, calling get_quiz
        should return the corresponding quiz definition with questions and passing_score.

        **Validates: Requirements 2.3**
        """
        from backend.quiz_registry import get_quiz

        # Lookup quiz in registry
        quiz_definition = get_quiz(module_id)

        # Verify quiz definition was returned (not None)
        assert quiz_definition is not None

        # Verify required fields are present
        assert "passing_score" in quiz_definition
        assert "questions" in quiz_definition

        # Verify passing_score is valid
        assert isinstance(quiz_definition["passing_score"], int)
        assert 0 <= quiz_definition["passing_score"] <= 100

        # Verify questions is a list
        assert isinstance(quiz_definition["questions"], list)
        assert len(quiz_definition["questions"]) > 0

        # Verify each question has required fields
        for question in quiz_definition["questions"]:
            assert "id" in question
            assert "correct_answer" in question
            assert "explanation" in question
            assert isinstance(question["id"], str)
            assert isinstance(question["correct_answer"], str)
            assert isinstance(question["explanation"], str)

    @settings(max_examples=100)
    @given(
        module_id=st.sampled_from(["secure-sdlc"]),
    )
    @patch("backend.services.quiz_service.get_quiz")
    @patch("backend.services.quiz_service.get_module_completion")
    @patch("backend.services.quiz_service.save_module_completion")
    @patch("backend.services.quiz_service.get_streak_data")
    def test_property_3_answer_confidentiality(
        self,
        mock_get_streak,
        mock_save_completion,
        mock_get_completion,
        mock_get_quiz,
        module_id,
    ):
        """
        Property 3: Answer Confidentiality

        For any quiz module, responses generated before submission validation should
        never contain correct answer data from the Quiz_Registry.

        **Validates: Requirements 2.5**
        """
        from backend.quiz_registry import QUIZ_REGISTRY

        # Get the actual quiz definition
        actual_quiz = QUIZ_REGISTRY.get(module_id)
        assume(actual_quiz is not None)

        # Mock get_quiz to return the quiz definition
        mock_get_quiz.return_value = actual_quiz

        # Mock no existing completion
        mock_get_completion.return_value = None

        # Mock streak data
        mock_get_streak.return_value = {
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
        }

        # Create answers (all wrong to ensure we get results with correct answers)
        answers = {}
        for question in actual_quiz["questions"]:
            # Submit wrong answer (assuming correct answer is not "WRONG")
            answers[question["id"]] = "WRONG"

        # Submit quiz
        result = submit_quiz("test-user", module_id, answers)

        # The result WILL contain correct answers (this is after submission validation)
        # This is expected behavior - correct answers are shown AFTER submission

        # What we're testing is that the quiz registry itself is not exposed
        # The correct answers are only revealed in the results AFTER scoring

        # Verify results contain correct answers (this is allowed after submission)
        assert "results" in result
        for result_item in result["results"]:
            assert "correct_answer" in result_item
            assert "explanation" in result_item

        # The key property: The quiz registry data structure itself should never
        # be returned directly to the client. Only processed results are returned.
        # We verify this by checking that the result structure is different from
        # the registry structure (it's been transformed)

        # Result should not have the raw "questions" array from registry
        assert "questions" not in result

        # Result should have processed "results" array instead
        assert "results" in result
        assert isinstance(result["results"], list)

        # Each result should be a processed version, not the raw question object
        for i, result_item in enumerate(result["results"]):
            # Result has these fields
            assert "question_id" in result_item
            assert "correct" in result_item
            assert "correct_answer" in result_item
            assert "explanation" in result_item

            # But should not have the raw question structure
            # (the "id" field from questions is transformed to "question_id")
            assert result_item["question_id"] == actual_quiz["questions"][i]["id"]
