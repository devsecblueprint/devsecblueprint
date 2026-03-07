"""
Unit tests for capstone.py get capstone submission endpoint handler.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from backend.handlers.capstone import handle_get_capstone_submission


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(
        "os.environ",
        {"JWT_SECRET_NAME": "test-jwt-secret", "PROGRESS_TABLE": "test-progress-table"},
    ):
        yield


@pytest.fixture
def mock_jwt_secret():
    """Mock JWT secret from Secrets Manager."""
    with patch("backend.auth.jwt_utils.get_secret") as mock_get_secret:
        mock_get_secret.return_value = {"secret_key": "test-secret-key-12345"}
        yield mock_get_secret


class TestHandleGetCapstoneSubmission:
    """Test GET /progress/capstone/{content_id} endpoint handler."""

    def test_returns_submission_when_exists(self, mock_env_vars, mock_jwt_secret):
        """Should return capstone submission when it exists."""
        user_id = "12345678"
        content_id = "devsecops-capstone"
        submission_data = {
            "repo_url": "https://github.com/testuser/my-project",
            "github_username": "testuser",
            "repo_name": "my-project",
            "submitted_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
        }

        headers = {"cookie": "dsb_token=valid_token"}

        with patch("backend.handlers.capstone.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch(
                "backend.handlers.capstone.get_capstone_submission"
            ) as mock_get_submission:
                mock_get_submission.return_value = submission_data

                response = handle_get_capstone_submission(headers, content_id)

                # Verify get_capstone_submission was called
                mock_get_submission.assert_called_once_with(user_id, content_id)

                # Verify response
                assert response["statusCode"] == 200
                body_data = json.loads(response["body"])
                assert body_data["repo_url"] == submission_data["repo_url"]
                assert (
                    body_data["github_username"] == submission_data["github_username"]
                )
                assert body_data["repo_name"] == submission_data["repo_name"]

    def test_returns_null_when_no_submission(self, mock_env_vars, mock_jwt_secret):
        """Should return null submission when none exists."""
        user_id = "12345678"
        content_id = "devsecops-capstone"

        headers = {"cookie": "dsb_token=valid_token"}

        with patch("backend.handlers.capstone.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch(
                "backend.handlers.capstone.get_capstone_submission"
            ) as mock_get_submission:
                mock_get_submission.return_value = None

                response = handle_get_capstone_submission(headers, content_id)

                # Verify response
                assert response["statusCode"] == 200
                body_data = json.loads(response["body"])
                assert body_data["submission"] is None

    def test_returns_401_when_jwt_missing(self, mock_env_vars, mock_jwt_secret):
        """Should return 401 when JWT is missing."""
        headers = {}
        content_id = "devsecops-capstone"

        response = handle_get_capstone_submission(headers, content_id)

        assert response["statusCode"] == 401
        body_data = json.loads(response["body"])
        assert "error" in body_data

    def test_returns_401_when_jwt_invalid(self, mock_env_vars, mock_jwt_secret):
        """Should return 401 when JWT is invalid."""
        headers = {"cookie": "dsb_token=invalid_token"}
        content_id = "devsecops-capstone"

        with patch("backend.handlers.capstone.validate_jwt") as mock_validate:
            from jose import JWTError

            mock_validate.side_effect = JWTError("Invalid token")

            response = handle_get_capstone_submission(headers, content_id)

            assert response["statusCode"] == 401
            body_data = json.loads(response["body"])
            assert "error" in body_data

    def test_returns_500_when_dynamodb_fails(self, mock_env_vars, mock_jwt_secret):
        """Should return 500 when DynamoDB operation fails."""
        user_id = "12345678"
        content_id = "devsecops-capstone"

        headers = {"cookie": "dsb_token=valid_token"}

        with patch("backend.handlers.capstone.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch(
                "backend.handlers.capstone.get_capstone_submission",
                side_effect=Exception("DynamoDB error"),
            ):
                response = handle_get_capstone_submission(headers, content_id)

                assert response["statusCode"] == 500
                body_data = json.loads(response["body"])
                assert "error" in body_data

    def test_response_includes_cors_headers(self, mock_env_vars, mock_jwt_secret):
        """Should include CORS headers in response."""
        user_id = "12345678"
        content_id = "devsecops-capstone"

        headers = {"cookie": "dsb_token=valid_token"}

        with patch("backend.handlers.capstone.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch(
                "backend.handlers.capstone.get_capstone_submission"
            ) as mock_get_submission:
                mock_get_submission.return_value = None

                response = handle_get_capstone_submission(headers, content_id)

                assert "headers" in response
                assert "Access-Control-Allow-Origin" in response["headers"]
                assert "Access-Control-Allow-Credentials" in response["headers"]
