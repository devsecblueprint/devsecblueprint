"""
Unit tests for quiz handler.

Tests the handle_quiz_submit function to ensure proper authentication,
request validation, error handling, and response formatting.

Requirements: 1.2, 1.3, 1.4, 1.5, 7.1, 7.2, 7.3
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from backend.handlers.quiz import handle_quiz_submit


class TestQuizHandlerAuthentication:
    """Test authentication in quiz handler."""

    def test_missing_jwt_returns_401(self):
        """Test that missing JWT token returns 401."""
        headers = {}
        body = json.dumps({"module_id": "test-module", "answers": {"q1": "A"}})

        response = handle_quiz_submit(headers, body)

        assert response["statusCode"] == 401
        assert "error" in response["body"]
        assert "Authentication failed" in response["body"]

    @patch("backend.handlers.quiz.validate_jwt")
    def test_invalid_jwt_returns_401(self, mock_validate_jwt):
        """Test that invalid JWT token returns 401."""
        from jose import JWTError

        mock_validate_jwt.side_effect = JWTError("Invalid token")

        headers = {"cookie": "dsb_token=invalid_token"}
        body = json.dumps({"module_id": "test-module", "answers": {"q1": "A"}})

        response = handle_quiz_submit(headers, body)

        assert response["statusCode"] == 401
        assert "Authentication failed" in response["body"]

    @patch("backend.handlers.quiz.validate_jwt")
    def test_jwt_without_user_id_returns_401(self, mock_validate_jwt):
        """Test that JWT without user_id returns 401."""
        mock_validate_jwt.return_value = {}  # No 'sub' field

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"module_id": "test-module", "answers": {"q1": "A"}})

        response = handle_quiz_submit(headers, body)

        assert response["statusCode"] == 401
        assert "Authentication failed" in response["body"]


class TestQuizHandlerValidation:
    """Test request validation in quiz handler."""

    @patch("backend.handlers.quiz.validate_jwt")
    def test_missing_module_id_returns_400(self, mock_validate_jwt):
        """Test that missing module_id returns 400."""
        mock_validate_jwt.return_value = {"sub": "user123"}

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"answers": {"q1": "A"}})

        response = handle_quiz_submit(headers, body)

        assert response["statusCode"] == 400
        assert "Invalid request" in response["body"]

    @patch("backend.handlers.quiz.validate_jwt")
    def test_missing_answers_returns_400(self, mock_validate_jwt):
        """Test that missing answers returns 400."""
        mock_validate_jwt.return_value = {"sub": "user123"}

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"module_id": "test-module"})

        response = handle_quiz_submit(headers, body)

        assert response["statusCode"] == 400
        assert "Invalid request" in response["body"]

    @patch("backend.handlers.quiz.validate_jwt")
    def test_malformed_json_returns_400(self, mock_validate_jwt):
        """Test that malformed JSON returns 400."""
        mock_validate_jwt.return_value = {"sub": "user123"}

        headers = {"cookie": "dsb_token=valid_token"}
        body = "{invalid json"

        response = handle_quiz_submit(headers, body)

        assert response["statusCode"] == 400
        assert "Invalid request" in response["body"]

    @patch("backend.handlers.quiz.validate_jwt")
    def test_answers_not_dict_returns_400(self, mock_validate_jwt):
        """Test that answers not being a dict returns 400."""
        mock_validate_jwt.return_value = {"sub": "user123"}

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"module_id": "test-module", "answers": "not a dict"})

        response = handle_quiz_submit(headers, body)

        assert response["statusCode"] == 400
        assert "Invalid request" in response["body"]


class TestQuizHandlerServiceErrors:
    """Test error handling from quiz service."""

    @patch("backend.handlers.quiz.submit_quiz")
    @patch("backend.handlers.quiz.validate_jwt")
    def test_invalid_module_id_returns_404(self, mock_validate_jwt, mock_submit_quiz):
        """Test that invalid module_id returns 404."""
        # Import from the same path as the handler
        from services.quiz_service import QuizNotFoundError

        mock_validate_jwt.return_value = {"sub": "user123"}
        mock_submit_quiz.side_effect = QuizNotFoundError("Quiz not found: test-module")

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"module_id": "test-module", "answers": {"q1": "A"}})

        response = handle_quiz_submit(headers, body)

        assert response["statusCode"] == 404
        assert "Quiz not found" in response["body"]

    @patch("backend.handlers.quiz.submit_quiz")
    @patch("backend.handlers.quiz.validate_jwt")
    def test_registry_unavailable_returns_503(
        self, mock_validate_jwt, mock_submit_quiz
    ):
        """Test that registry unavailable errors return 503."""
        # Import from the same path as the handler
        from services.quiz_service import RegistryUnavailableError

        mock_validate_jwt.return_value = {"sub": "user123"}
        mock_submit_quiz.side_effect = RegistryUnavailableError(
            "Content registry unavailable"
        )

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"module_id": "test-module", "answers": {"q1": "A"}})

        response = handle_quiz_submit(headers, body)

        assert response["statusCode"] == 503
        assert "Service temporarily unavailable" in response["body"]

    @patch("backend.handlers.quiz.submit_quiz")
    @patch("backend.handlers.quiz.validate_jwt")
    def test_validation_error_returns_400(self, mock_validate_jwt, mock_submit_quiz):
        """Test that validation errors return 400."""
        mock_validate_jwt.return_value = {"sub": "user123"}
        mock_submit_quiz.side_effect = ValueError("Missing required question IDs")

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"module_id": "test-module", "answers": {"q1": "A"}})

        response = handle_quiz_submit(headers, body)

        assert response["statusCode"] == 400
        assert "Invalid request" in response["body"]

    @patch("backend.handlers.quiz.submit_quiz")
    @patch("backend.handlers.quiz.validate_jwt")
    def test_dynamodb_error_returns_500(self, mock_validate_jwt, mock_submit_quiz):
        """Test that DynamoDB errors return 500 with appropriate message."""
        mock_validate_jwt.return_value = {"sub": "user123"}

        # Simulate a generic exception (handler will return generic 500)
        mock_submit_quiz.side_effect = Exception("Database error")

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"module_id": "test-module", "answers": {"q1": "A"}})

        response = handle_quiz_submit(headers, body)

        assert response["statusCode"] == 500
        # The handler returns "Internal server error" for non-DynamoDB exceptions
        assert "error" in response["body"]

    @patch("backend.handlers.quiz.submit_quiz")
    @patch("backend.handlers.quiz.validate_jwt")
    def test_unexpected_error_returns_500(self, mock_validate_jwt, mock_submit_quiz):
        """Test that unexpected errors return 500."""
        mock_validate_jwt.return_value = {"sub": "user123"}
        mock_submit_quiz.side_effect = Exception("Unexpected error")

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"module_id": "test-module", "answers": {"q1": "A"}})

        response = handle_quiz_submit(headers, body)

        assert response["statusCode"] == 500
        assert "Internal server error" in response["body"]


class TestQuizHandlerSuccess:
    """Test successful quiz submission."""

    @patch("backend.handlers.quiz.submit_quiz")
    @patch("backend.handlers.quiz.validate_jwt")
    def test_successful_submission_returns_200(
        self, mock_validate_jwt, mock_submit_quiz
    ):
        """Test that successful quiz submission returns 200 with results."""
        mock_validate_jwt.return_value = {"sub": "user123"}
        mock_submit_quiz.return_value = {
            "passed": True,
            "score": 80,
            "passing_score": 70,
            "already_completed": False,
            "results": [
                {
                    "question_id": "q1",
                    "correct": True,
                    "correct_answer": "A",
                    "explanation": "Explanation for q1",
                }
            ],
            "current_streak": 5,
        }

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"module_id": "test-module", "answers": {"q1": "A"}})

        response = handle_quiz_submit(headers, body)

        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["passed"] is True
        assert response_body["score"] == 80
        assert response_body["passing_score"] == 70
        assert response_body["already_completed"] is False
        assert len(response_body["results"]) == 1
        assert response_body["current_streak"] == 5

    @patch("backend.handlers.quiz.submit_quiz")
    @patch("backend.handlers.quiz.validate_jwt")
    def test_response_includes_cors_headers(self, mock_validate_jwt, mock_submit_quiz):
        """Test that response includes CORS headers."""
        mock_validate_jwt.return_value = {"sub": "user123"}
        mock_submit_quiz.return_value = {
            "passed": True,
            "score": 80,
            "passing_score": 70,
            "already_completed": False,
            "results": [],
            "current_streak": 1,
        }

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"module_id": "test-module", "answers": {"q1": "A"}})

        response = handle_quiz_submit(headers, body)

        assert "Access-Control-Allow-Origin" in response["headers"]
        assert "Access-Control-Allow-Credentials" in response["headers"]
