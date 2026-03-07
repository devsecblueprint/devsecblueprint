"""
Unit tests for progress.py progress tracking endpoint handler.
"""

import os
import json
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from jose import jwt, JWTError

from backend.handlers.progress import handle_progress
from backend.auth.jwt_utils import generate_jwt


@pytest.fixture
def mock_jwt_secret():
    """Mock JWT secret from Secrets Manager."""
    return {"secret_key": "test-secret-key-12345"}


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(
        os.environ,
        {"JWT_SECRET_NAME": "test-jwt-secret", "PROGRESS_TABLE": "test-progress-table"},
    ):
        yield


class TestHandleProgress:
    """Test PUT /progress endpoint handler."""

    def test_saves_progress_with_valid_jwt_and_content_id(
        self, mock_env_vars, mock_jwt_secret
    ):
        """Should save progress successfully with valid JWT and content_id."""
        user_id = "12345678"
        content_id = "secure-sdlc/intro"

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"content_id": content_id})

        # Mock JWT validation to return user_id
        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            # Mock save_progress
            with patch("backend.handlers.progress.save_progress") as mock_save:
                response = handle_progress(headers, body)

                # Verify save_progress was called with correct arguments
                mock_save.assert_called_once_with(user_id, content_id)

                # Verify response
                assert response["statusCode"] == 200
                assert "headers" in response
                assert response["headers"]["Content-Type"] == "application/json"

                # Verify response body
                body_data = json.loads(response["body"])
                assert "message" in body_data
                assert body_data["message"] == "Progress saved successfully"

    def test_returns_401_when_jwt_missing(self):
        """Should return 401 when JWT cookie is missing."""
        headers = {}
        body = json.dumps({"content_id": "secure-sdlc/intro"})

        response = handle_progress(headers, body)

        assert response["statusCode"] == 401
        body_data = json.loads(response["body"])
        assert "error" in body_data
        assert body_data["error"] == "Authentication failed"

    def test_returns_401_when_jwt_invalid(self, mock_env_vars, mock_jwt_secret):
        """Should return 401 when JWT signature is invalid."""
        from jose import JWTError

        headers = {"cookie": "dsb_token=invalid.jwt.token"}
        body = json.dumps({"content_id": "secure-sdlc/intro"})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.side_effect = JWTError("Invalid signature")
            response = handle_progress(headers, body)

            assert response["statusCode"] == 401
            body_data = json.loads(response["body"])
            assert "error" in body_data
            assert body_data["error"] == "Authentication failed"

    def test_returns_401_when_jwt_expired(self, mock_env_vars, mock_jwt_secret):
        """Should return 401 when JWT is expired."""
        from jose import JWTError

        headers = {"cookie": "dsb_token=expired_token"}
        body = json.dumps({"content_id": "secure-sdlc/intro"})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.side_effect = JWTError("Token expired")
            response = handle_progress(headers, body)

            assert response["statusCode"] == 401
            body_data = json.loads(response["body"])
            assert "error" in body_data

    def test_returns_400_when_content_id_missing(self, mock_env_vars, mock_jwt_secret):
        """Should return 400 when content_id is missing from request body."""
        user_id = "12345678"

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({})  # Empty body, no content_id

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}
            response = handle_progress(headers, body)

            assert response["statusCode"] == 400
            body_data = json.loads(response["body"])
            assert "error" in body_data
            assert body_data["error"] == "Invalid request"

    def test_returns_400_when_body_is_empty(self, mock_env_vars, mock_jwt_secret):
        """Should return 400 when request body is empty."""
        user_id = "12345678"

        headers = {"cookie": "dsb_token=valid_token"}
        body = ""  # Empty body

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}
            response = handle_progress(headers, body)

            assert response["statusCode"] == 400
            body_data = json.loads(response["body"])
            assert "error" in body_data
            assert body_data["error"] == "Invalid request"

    def test_returns_400_when_body_is_invalid_json(
        self, mock_env_vars, mock_jwt_secret
    ):
        """Should return 400 when request body is not valid JSON."""
        user_id = "12345678"

        headers = {"cookie": "dsb_token=valid_token"}
        body = "not valid json"

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}
            response = handle_progress(headers, body)

            assert response["statusCode"] == 400
            body_data = json.loads(response["body"])
            assert "error" in body_data
            assert body_data["error"] == "Invalid request"

    def test_returns_500_when_dynamodb_fails(self, mock_env_vars, mock_jwt_secret):
        """Should return 500 when DynamoDB write fails."""
        user_id = "12345678"
        content_id = "secure-sdlc/intro"

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"content_id": content_id})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            # Mock save_progress to raise an exception
            with patch(
                "backend.handlers.progress.save_progress",
                side_effect=Exception("DynamoDB error"),
            ):
                response = handle_progress(headers, body)

                assert response["statusCode"] == 500
                body_data = json.loads(response["body"])
                assert "error" in body_data
                assert body_data["error"] == "Service temporarily unavailable"

    def test_validates_jwt_before_processing(self, mock_env_vars, mock_jwt_secret):
        """Should validate JWT before attempting to save progress (no side effects on auth failure)."""
        from jose import JWTError

        headers = {"cookie": "dsb_token=invalid.token"}
        body = json.dumps({"content_id": "secure-sdlc/intro"})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.side_effect = JWTError("Invalid token")

            # Mock save_progress to track if it's called
            with patch("backend.handlers.progress.save_progress") as mock_save:
                response = handle_progress(headers, body)

                # Should return 401
                assert response["statusCode"] == 401

                # save_progress should NOT have been called
                mock_save.assert_not_called()

    def test_response_includes_cors_headers(self, mock_env_vars, mock_jwt_secret):
        """Should include CORS headers in response."""
        user_id = "12345678"
        content_id = "secure-sdlc/intro"

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"content_id": content_id})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch("backend.handlers.progress.save_progress"):
                response = handle_progress(headers, body)

                assert "Access-Control-Allow-Origin" in response["headers"]
                assert (
                    response["headers"]["Access-Control-Allow-Origin"]
                    == "https://devsecblueprint.com"
                )
                assert "Access-Control-Allow-Credentials" in response["headers"]
                assert response["headers"]["Access-Control-Allow-Credentials"] == "true"

    def test_does_not_expose_sensitive_info_in_errors(
        self, mock_env_vars, mock_jwt_secret
    ):
        """Should not expose stack traces or sensitive information in error responses."""
        user_id = "12345678"
        content_id = "secure-sdlc/intro"

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"content_id": content_id})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            # Simulate DynamoDB error with sensitive information
            with patch(
                "backend.handlers.progress.save_progress",
                side_effect=Exception(
                    "AWS DynamoDB internal error: table arn:aws:dynamodb:us-east-1:123456789012:table/progress"
                ),
            ):
                response = handle_progress(headers, body)

                # Should return 500 with generic message
                assert response["statusCode"] == 500
                body_data = json.loads(response["body"])
                assert body_data["error"] == "Service temporarily unavailable"

                # Should not contain internal error details
                assert "AWS" not in body_data["error"]
                assert "arn:aws" not in body_data["error"]
                assert "internal" not in body_data["error"].lower()

    def test_handles_content_id_with_special_characters(
        self, mock_env_vars, mock_jwt_secret
    ):
        """Should handle content_id with special characters."""
        user_id = "12345678"
        content_id = "secure-sdlc/advanced-topics/xss-prevention"

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"content_id": content_id})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch("backend.handlers.progress.save_progress") as mock_save:
                response = handle_progress(headers, body)

                # Verify save_progress was called with the content_id as-is
                mock_save.assert_called_once_with(user_id, content_id)

                assert response["statusCode"] == 200

    def test_handles_multiple_cookies(self, mock_env_vars, mock_jwt_secret):
        """Should extract JWT from multiple cookies correctly."""
        user_id = "87654321"
        content_id = "secure-sdlc/intro"

        headers = {"cookie": "session=abc123; dsb_token=valid_token; other=value"}
        body = json.dumps({"content_id": content_id})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch("backend.handlers.progress.save_progress") as mock_save:
                response = handle_progress(headers, body)

                mock_save.assert_called_once_with(user_id, content_id)
                assert response["statusCode"] == 200

    def test_returns_401_when_sub_claim_missing(self, mock_env_vars, mock_jwt_secret):
        """Should return 401 when JWT doesn't have sub claim."""
        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"content_id": "secure-sdlc/intro"})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {}  # No 'sub' field
            response = handle_progress(headers, body)

            assert response["statusCode"] == 401
            body_data = json.loads(response["body"])
            assert "error" in body_data

    def test_handles_content_id_null_value(self, mock_env_vars, mock_jwt_secret):
        """Should return 400 when content_id is null."""
        user_id = "12345678"

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"content_id": None})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}
            response = handle_progress(headers, body)

            assert response["statusCode"] == 400
            body_data = json.loads(response["body"])
            assert "error" in body_data
            assert body_data["error"] == "Invalid request"

    def test_handles_content_id_empty_string(self, mock_env_vars, mock_jwt_secret):
        """Should return 400 when content_id is empty string."""
        user_id = "12345678"

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"content_id": ""})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}
            response = handle_progress(headers, body)

            assert response["statusCode"] == 400
            body_data = json.loads(response["body"])
            assert "error" in body_data
            assert body_data["error"] == "Invalid request"

    def test_handles_unexpected_exception(self, mock_env_vars, mock_jwt_secret):
        """Should handle unexpected exceptions gracefully."""
        user_id = "12345678"

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"content_id": "secure-sdlc/intro"})

        # Simulate an unexpected error in extract_token_from_cookie
        with patch(
            "backend.handlers.progress.extract_token_from_cookie",
            side_effect=Exception("Unexpected error"),
        ):
            response = handle_progress(headers, body)

            # Should return 500 with generic message
            assert response["statusCode"] == 500
            body_data = json.loads(response["body"])
            assert body_data["error"] == "Service temporarily unavailable"


class TestValidateGitHubUrl:
    """Test validate_github_url() function."""

    def test_validates_https_url_with_matching_username(self):
        """Should validate HTTPS GitHub URL with matching username."""
        from backend.handlers.progress import validate_github_url

        result = validate_github_url(
            "https://github.com/damienjburks/my-project", "damienjburks"
        )

        assert result["valid"] is True
        assert result["username"] == "damienjburks"
        assert result["repo_name"] == "my-project"

    def test_validates_http_url_with_matching_username(self):
        """Should validate HTTP GitHub URL with matching username."""
        from backend.handlers.progress import validate_github_url

        result = validate_github_url("http://github.com/testuser/test-repo", "testuser")

        assert result["valid"] is True
        assert result["username"] == "testuser"
        assert result["repo_name"] == "test-repo"

    def test_validates_url_with_www_prefix(self):
        """Should validate GitHub URL with www prefix."""
        from backend.handlers.progress import validate_github_url

        result = validate_github_url(
            "https://www.github.com/user123/repo-name", "user123"
        )

        assert result["valid"] is True
        assert result["username"] == "user123"
        assert result["repo_name"] == "repo-name"

    def test_validates_url_with_trailing_slash(self):
        """Should validate GitHub URL with trailing slash."""
        from backend.handlers.progress import validate_github_url

        result = validate_github_url("https://github.com/myuser/myrepo/", "myuser")

        assert result["valid"] is True
        assert result["username"] == "myuser"
        assert result["repo_name"] == "myrepo"

    def test_validates_case_insensitive_username_match(self):
        """Should validate username match case-insensitively."""
        from backend.handlers.progress import validate_github_url

        # URL has uppercase, expected has lowercase
        result = validate_github_url(
            "https://github.com/DamienJBurks/project", "damienjburks"
        )

        assert result["valid"] is True
        assert result["username"] == "DamienJBurks"  # Preserves original case
        assert result["repo_name"] == "project"

        # URL has lowercase, expected has uppercase
        result = validate_github_url("https://github.com/testuser/repo", "TestUser")

        assert result["valid"] is True
        assert result["username"] == "testuser"
        assert result["repo_name"] == "repo"

    def test_rejects_username_mismatch(self):
        """Should reject URL when username doesn't match."""
        from backend.handlers.progress import validate_github_url

        result = validate_github_url("https://github.com/otheruser/project", "myuser")

        assert result["valid"] is False
        assert "error" in result
        assert (
            "Repository must be under your GitHub account (myuser)" == result["error"]
        )

    def test_rejects_invalid_url_format(self):
        """Should reject invalid URL formats."""
        from backend.handlers.progress import validate_github_url

        # Not a URL
        result = validate_github_url("not-a-url", "user")
        assert result["valid"] is False
        assert result["error"] == "Invalid GitHub URL format"

        # Wrong domain
        result = validate_github_url("https://gitlab.com/user/repo", "user")
        assert result["valid"] is False
        assert result["error"] == "Invalid GitHub URL format"

        # Missing username
        result = validate_github_url("https://github.com/repo", "user")
        assert result["valid"] is False
        assert result["error"] == "Invalid GitHub URL format"

        # Missing repo name
        result = validate_github_url("https://github.com/user", "user")
        assert result["valid"] is False
        assert result["error"] == "Invalid GitHub URL format"

        # Extra path segments
        result = validate_github_url("https://github.com/user/repo/extra", "user")
        assert result["valid"] is False
        assert result["error"] == "Invalid GitHub URL format"

    def test_handles_repo_names_with_special_characters(self):
        """Should handle repository names with hyphens, underscores, and periods."""
        from backend.handlers.progress import validate_github_url

        result = validate_github_url(
            "https://github.com/user/my-repo_name.test", "user"
        )

        assert result["valid"] is True
        assert result["username"] == "user"
        assert result["repo_name"] == "my-repo_name.test"

    def test_handles_usernames_with_hyphens(self):
        """Should handle usernames with hyphens."""
        from backend.handlers.progress import validate_github_url

        result = validate_github_url(
            "https://github.com/my-user-name/repo", "my-user-name"
        )

        assert result["valid"] is True
        assert result["username"] == "my-user-name"
        assert result["repo_name"] == "repo"

    def test_rejects_empty_url(self):
        """Should reject empty URL."""
        from backend.handlers.progress import validate_github_url

        result = validate_github_url("", "user")

        assert result["valid"] is False
        assert result["error"] == "Invalid GitHub URL format"


class TestHandleProgressWithCapstoneSubmission:
    """Test PUT /progress endpoint with capstone submission (repo_url)."""

    def test_saves_capstone_submission_with_valid_repo_url(
        self, mock_env_vars, mock_jwt_secret
    ):
        """Should save capstone submission when repo_url is provided."""
        user_id = "12345678"
        github_username = "damienjburks"
        content_id = "devsecops-capstone"
        repo_url = "https://github.com/damienjburks/my-capstone"

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"content_id": content_id, "repo_url": repo_url})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {
                "sub": user_id,
                "github_login": github_username,
            }

            with patch("backend.handlers.progress.save_progress") as mock_save_progress:
                with patch(
                    "backend.handlers.progress.save_capstone_submission"
                ) as mock_save_submission:
                    response = handle_progress(headers, body)

                    # Verify save_capstone_submission was called
                    mock_save_submission.assert_called_once_with(
                        user_id=user_id,
                        content_id=content_id,
                        repo_url=repo_url,
                        github_username="damienjburks",
                        repo_name="my-capstone",
                    )

                    # Verify save_progress was also called
                    mock_save_progress.assert_called_once_with(user_id, content_id)

                    # Verify response
                    assert response["statusCode"] == 200
                    body_data = json.loads(response["body"])
                    assert "message" in body_data
                    assert "submission" in body_data
                    assert body_data["submission"]["repo_url"] == repo_url
                    assert body_data["submission"]["github_username"] == "damienjburks"
                    assert body_data["submission"]["repo_name"] == "my-capstone"
                    assert "submitted_at" in body_data["submission"]

    def test_returns_400_when_repo_url_username_mismatch(
        self, mock_env_vars, mock_jwt_secret
    ):
        """Should return 400 when repo_url username doesn't match authenticated user."""
        user_id = "12345678"
        github_username = "damienjburks"
        content_id = "devsecops-capstone"
        repo_url = "https://github.com/otheruser/project"

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"content_id": content_id, "repo_url": repo_url})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {
                "sub": user_id,
                "github_login": github_username,
            }

            response = handle_progress(headers, body)

            assert response["statusCode"] == 400
            body_data = json.loads(response["body"])
            assert "error" in body_data
            assert "Repository must be under your GitHub account" in body_data["error"]

    def test_returns_400_when_repo_url_invalid_format(
        self, mock_env_vars, mock_jwt_secret
    ):
        """Should return 400 when repo_url has invalid format."""
        user_id = "12345678"
        github_username = "damienjburks"
        content_id = "devsecops-capstone"
        repo_url = "not-a-valid-url"

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"content_id": content_id, "repo_url": repo_url})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {
                "sub": user_id,
                "github_login": github_username,
            }

            response = handle_progress(headers, body)

            assert response["statusCode"] == 400
            body_data = json.loads(response["body"])
            assert "error" in body_data
            assert body_data["error"] == "Invalid GitHub URL format"

    def test_backward_compatibility_without_repo_url(
        self, mock_env_vars, mock_jwt_secret
    ):
        """Should work normally when repo_url is not provided (backward compatibility)."""
        user_id = "12345678"
        content_id = "secure-sdlc/intro"

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"content_id": content_id})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id, "username": "testuser"}

            with patch("backend.handlers.progress.save_progress") as mock_save_progress:
                with patch(
                    "backend.handlers.progress.save_capstone_submission"
                ) as mock_save_submission:
                    response = handle_progress(headers, body)

                    # Verify save_capstone_submission was NOT called
                    mock_save_submission.assert_not_called()

                    # Verify save_progress was called
                    mock_save_progress.assert_called_once_with(user_id, content_id)

                    # Verify response doesn't include submission metadata
                    assert response["statusCode"] == 200
                    body_data = json.loads(response["body"])
                    assert "message" in body_data
                    assert "submission" not in body_data

    def test_returns_500_when_capstone_submission_fails(
        self, mock_env_vars, mock_jwt_secret
    ):
        """Should return 500 when capstone submission save fails."""
        user_id = "12345678"
        github_username = "damienjburks"
        content_id = "devsecops-capstone"
        repo_url = "https://github.com/damienjburks/my-capstone"

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"content_id": content_id, "repo_url": repo_url})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {
                "sub": user_id,
                "github_login": github_username,
            }

            with patch(
                "backend.handlers.progress.save_capstone_submission",
                side_effect=Exception("DynamoDB error"),
            ):
                response = handle_progress(headers, body)

                assert response["statusCode"] == 500
                body_data = json.loads(response["body"])
                assert "error" in body_data
                assert body_data["error"] == "Service temporarily unavailable"

    def test_validates_repo_url_case_insensitive(self, mock_env_vars, mock_jwt_secret):
        """Should validate repo_url username case-insensitively."""
        user_id = "12345678"
        github_username = "damienjburks"
        content_id = "devsecops-capstone"
        repo_url = "https://github.com/DamienJBurks/my-capstone"  # Different case

        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"content_id": content_id, "repo_url": repo_url})

        with patch("backend.handlers.progress.validate_jwt") as mock_validate:
            mock_validate.return_value = {
                "sub": user_id,
                "github_login": github_username,
            }

            with patch("backend.handlers.progress.save_progress"):
                with patch(
                    "backend.handlers.progress.save_capstone_submission"
                ) as mock_save_submission:
                    response = handle_progress(headers, body)

                    # Should succeed with case-insensitive match
                    assert response["statusCode"] == 200

                    # Verify submission was saved with original case from URL
                    mock_save_submission.assert_called_once()
                    call_args = mock_save_submission.call_args[1]
                    assert (
                        call_args["github_username"] == "DamienJBurks"
                    )  # Preserves URL case
