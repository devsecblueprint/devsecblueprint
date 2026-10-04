"""Unit tests for app.services.quiz_service.

Covers scoring, validation, completion persistence (first vs. repeat), and
streak day-math. The content registry and DynamoDB are mocked.
"""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import quiz_service as svc
from app.services.quiz_service import (
    QuizNotFoundError,
    RegistryUnavailableError,
)


QUIZ_DEF = {
    "passing_score": 70,
    "questions": [
        {"id": "q1", "correct_answer": "a", "explanation": "because a"},
        {"id": "q2", "correct_answer": "b", "explanation": "because b"},
        {"id": "q3", "correct_answer": "c", "explanation": "because c"},
    ],
}


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


@pytest.fixture
def mock_settings():
    with patch.object(svc, "get_settings") as get_settings:
        get_settings.return_value = MagicMock(
            content_registry_bucket="test-bucket",
            progress_table="test-progress",
        )
        yield get_settings


@pytest.fixture
def mock_registry(mock_settings):
    registry = MagicMock()
    registry.get_quiz.return_value = QUIZ_DEF
    with patch.object(svc, "get_registry_service", return_value=registry):
        yield registry


@pytest.fixture
def mock_dynamodb(mock_registry):
    client = MagicMock()
    # Defaults: no existing completion, no streak record.
    client.get_item.return_value = {}
    with patch.object(svc.boto3, "client", return_value=client):
        yield client


class TestScoring:
    def test_all_correct_passes_with_100(self, mock_dynamodb):
        result = svc.submit_quiz("u", "mod", {"q1": "a", "q2": "b", "q3": "c"})
        assert result["score"] == 100
        assert result["passed"] is True
        assert result["passing_score"] == 70
        assert all(r["correct"] for r in result["results"])

    def test_partial_below_passing_fails(self, mock_dynamodb):
        # 1/3 correct = 33 < 70
        result = svc.submit_quiz("u", "mod", {"q1": "a", "q2": "x", "q3": "y"})
        assert result["score"] == 33
        assert result["passed"] is False

    def test_results_include_explanations(self, mock_dynamodb):
        result = svc.submit_quiz("u", "mod", {"q1": "a", "q2": "b", "q3": "c"})
        exps = {r["question_id"]: r["explanation"] for r in result["results"]}
        assert exps["q1"] == "because a"


class TestValidation:
    def test_missing_question_ids_raises(self, mock_dynamodb):
        with pytest.raises(ValueError, match="Missing required question IDs"):
            svc.submit_quiz("u", "mod", {"q1": "a", "q2": "b"})

    def test_extra_question_ids_raises(self, mock_dynamodb):
        with pytest.raises(ValueError, match="Extra question IDs"):
            svc.submit_quiz("u", "mod", {"q1": "a", "q2": "b", "q3": "c", "q4": "d"})


class TestRegistryErrors:
    def test_quiz_not_found_raises(self, mock_registry, mock_settings):
        mock_registry.get_quiz.return_value = None
        client = MagicMock()
        with patch.object(svc.boto3, "client", return_value=client):
            with pytest.raises(QuizNotFoundError):
                svc.submit_quiz("u", "missing", {"q1": "a"})

    def test_registry_unavailable_raises(self, mock_registry, mock_settings):
        mock_registry.get_quiz.side_effect = RuntimeError("s3 down")
        with pytest.raises(RegistryUnavailableError, match="Content registry unavailable"):
            svc.submit_quiz("u", "mod", {"q1": "a", "q2": "b", "q3": "c"})

    def test_schema_version_error_raises_unavailable(self, mock_registry, mock_settings):
        mock_registry.get_quiz.side_effect = svc.SchemaVersionError("bad version")
        with pytest.raises(RegistryUnavailableError, match="Schema version incompatible"):
            svc.submit_quiz("u", "mod", {"q1": "a", "q2": "b", "q3": "c"})

    def test_no_bucket_configured_is_not_found(self, mock_settings):
        mock_settings.return_value = MagicMock(
            content_registry_bucket="", progress_table="test-progress"
        )
        client = MagicMock()
        with patch.object(svc.boto3, "client", return_value=client):
            with pytest.raises(QuizNotFoundError):
                svc.submit_quiz("u", "mod", {"q1": "a"})


class TestCompletionPersistence:
    def test_first_pass_saves_completion_and_starts_streak(self, mock_dynamodb):
        # No existing MODULE# or STREAK records (get_item -> {}).
        result = svc.submit_quiz("u", "mod", {"q1": "a", "q2": "b", "q3": "c"})
        assert result["already_completed"] is False
        assert result["current_streak"] == 1
        # put_item called for MODULE# and STREAK.
        assert mock_dynamodb.put_item.call_count == 2

    def test_repeat_pass_marks_already_completed(self, mock_dynamodb):
        # Existing MODULE# completion present on first get_item.
        def get_item(**kwargs):
            sk = kwargs["Key"]["SK"]["S"]
            if sk.startswith("MODULE#"):
                return {"Item": {"score": {"N": "80"}, "first_completed_at": {"S": "2026-01-01"}, "completed_at": {"S": "2026-01-01"}}}
            if sk == "STREAK":
                return {"Item": {"current_streak": {"N": "5"}, "longest_streak": {"N": "9"}, "last_activity_date": {"S": "2026-01-01"}}}
            return {}

        mock_dynamodb.get_item.side_effect = get_item
        result = svc.submit_quiz("u", "mod", {"q1": "a", "q2": "b", "q3": "c"})
        assert result["already_completed"] is True
        # Streak unchanged on repeat; reflects existing streak record.
        assert result["current_streak"] == 5

    def test_failing_does_not_save_completion(self, mock_dynamodb):
        result = svc.submit_quiz("u", "mod", {"q1": "x", "q2": "y", "q3": "z"})
        assert result["passed"] is False
        mock_dynamodb.put_item.assert_not_called()


class TestStreakMath:
    def test_consecutive_day_increments(self, mock_dynamodb):
        yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()

        def get_item(**kwargs):
            sk = kwargs["Key"]["SK"]["S"]
            if sk == "STREAK":
                return {"Item": {"current_streak": {"N": "3"}, "longest_streak": {"N": "3"}, "last_activity_date": {"S": yesterday}}}
            return {}

        mock_dynamodb.get_item.side_effect = get_item
        result = svc.submit_quiz("u", "mod", {"q1": "a", "q2": "b", "q3": "c"})
        assert result["current_streak"] == 4

    def test_gap_resets_streak_to_one(self, mock_dynamodb):
        old = (datetime.now(timezone.utc).date() - timedelta(days=5)).isoformat()

        def get_item(**kwargs):
            sk = kwargs["Key"]["SK"]["S"]
            if sk == "STREAK":
                return {"Item": {"current_streak": {"N": "7"}, "longest_streak": {"N": "7"}, "last_activity_date": {"S": old}}}
            return {}

        mock_dynamodb.get_item.side_effect = get_item
        result = svc.submit_quiz("u", "mod", {"q1": "a", "q2": "b", "q3": "c"})
        assert result["current_streak"] == 1


class TestHelpers:
    def test_get_module_completion_handles_client_error(self):
        client = MagicMock()
        client.get_item.side_effect = _client_error("InternalServerError")
        assert svc._get_module_completion(client, "t", "u", "m") is None

    def test_save_completion_raises_on_client_error(self):
        client = MagicMock()
        client.put_item.side_effect = _client_error("ValidationException")
        with pytest.raises(Exception, match="Failed to save module completion"):
            svc._save_module_completion(client, "t", "u", "m", 90, True)

    def test_update_streak_swallows_put_error(self):
        # Streak persistence failure should not raise (logged only).
        client = MagicMock()
        client.get_item.return_value = {}
        client.put_item.side_effect = _client_error("InternalServerError")
        streak = svc._update_streak(client, "t", "u")
        assert streak == 1

    def test_get_streak_data_defaults_on_client_error(self):
        client = MagicMock()
        client.get_item.side_effect = _client_error("InternalServerError")
        data = svc._get_streak_data(client, "t", "u")
        assert data["current_streak"] == 0
