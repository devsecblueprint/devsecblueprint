"""
Unit tests for walkthroughs.py API endpoint handlers.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock
from jose import JWTError

from backend.handlers.walkthroughs import (
    handle_get_walkthroughs,
    handle_get_walkthrough,
    handle_update_progress,
)


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(
        os.environ,
        {
            "JWT_SECRET_NAME": "test-jwt-secret",
            "USER_STATE_TABLE": "test-user-state-table",
        },
    ):
        yield


class TestHandleGetWalkthroughs:
    """Test GET /api/walkthroughs endpoint handler."""

    def test_returns_walkthroughs_with_valid_jwt(self, mock_env_vars):
        """Should return walkthroughs successfully with valid JWT."""
        user_id = "12345678"
        headers = {"cookie": "dsb_token=valid_token"}
        query_params = {}

        mock_walkthroughs = [
            {
                "id": "test-walkthrough",
                "title": "Test Walkthrough",
                "description": "Test description",
                "difficulty": "Beginner",
                "topics": ["Testing"],
                "estimatedTime": 30,
                "prerequisites": [],
                "repository": "walkthroughs/test-walkthrough",
            }
        ]

        with patch("backend.handlers.walkthroughs.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch("backend.handlers.walkthroughs.get_walkthroughs") as mock_get:
                mock_get.return_value = mock_walkthroughs

                with patch(
                    "backend.handlers.walkthroughs.get_walkthrough_progress"
                ) as mock_progress:
                    mock_progress.return_value = {
                        "status": "not_started",
                        "started_at": None,
                        "completed_at": None,
                    }

                    response = handle_get_walkthroughs(headers, query_params)

                    assert response["statusCode"] == 200
                    body_data = json.loads(response["body"])
                    assert "walkthroughs" in body_data
                    assert len(body_data["walkthroughs"]) == 1
                    assert body_data["walkthroughs"][0]["id"] == "test-walkthrough"
                    assert "progress" in body_data["walkthroughs"][0]

    def test_returns_401_when_jwt_missing(self):
        """Should return 401 when JWT cookie is missing."""
        headers = {}
        query_params = {}

        response = handle_get_walkthroughs(headers, query_params)

        assert response["statusCode"] == 401
        body_data = json.loads(response["body"])
        assert "error" in body_data
        assert body_data["error"] == "Authentication failed"

    def test_applies_difficulty_filter(self, mock_env_vars):
        """Should apply difficulty filter from query parameters."""
        user_id = "12345678"
        headers = {"cookie": "dsb_token=valid_token"}
        query_params = {"difficulty": "Intermediate"}

        with patch("backend.handlers.walkthroughs.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch("backend.handlers.walkthroughs.get_walkthroughs") as mock_get:
                mock_get.return_value = []

                with patch("backend.handlers.walkthroughs.get_walkthrough_progress"):
                    response = handle_get_walkthroughs(headers, query_params)

                    # Verify get_walkthroughs was called with difficulty filter
                    mock_get.assert_called_once_with(
                        difficulty="Intermediate", topics=None, search=None
                    )
                    assert response["statusCode"] == 200

    def test_applies_topics_filter(self, mock_env_vars):
        """Should parse and apply topics filter from comma-separated string."""
        user_id = "12345678"
        headers = {"cookie": "dsb_token=valid_token"}
        query_params = {"topics": "CI/CD,Security"}

        with patch("backend.handlers.walkthroughs.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch("backend.handlers.walkthroughs.get_walkthroughs") as mock_get:
                mock_get.return_value = []

                with patch("backend.handlers.walkthroughs.get_walkthrough_progress"):
                    response = handle_get_walkthroughs(headers, query_params)

                    # Verify topics were parsed correctly
                    mock_get.assert_called_once_with(
                        difficulty=None, topics=["CI/CD", "Security"], search=None
                    )
                    assert response["statusCode"] == 200

    def test_applies_search_filter(self, mock_env_vars):
        """Should apply search filter from query parameters."""
        user_id = "12345678"
        headers = {"cookie": "dsb_token=valid_token"}
        query_params = {"search": "security"}

        with patch("backend.handlers.walkthroughs.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch("backend.handlers.walkthroughs.get_walkthroughs") as mock_get:
                mock_get.return_value = []

                with patch("backend.handlers.walkthroughs.get_walkthrough_progress"):
                    response = handle_get_walkthroughs(headers, query_params)

                    mock_get.assert_called_once_with(
                        difficulty=None, topics=None, search="security"
                    )
                    assert response["statusCode"] == 200


class TestHandleGetWalkthrough:
    """Test GET /api/walkthroughs/[id] endpoint handler."""

    def test_returns_walkthrough_with_readme(self, mock_env_vars):
        """Should return walkthrough with README content."""
        user_id = "12345678"
        walkthrough_id = "test-walkthrough"
        headers = {"cookie": "dsb_token=valid_token"}

        mock_walkthrough = {
            "id": walkthrough_id,
            "title": "Test Walkthrough",
            "description": "Test description",
            "difficulty": "Beginner",
            "topics": ["Testing"],
            "estimatedTime": 30,
            "prerequisites": [],
            "repository": "walkthroughs/test-walkthrough",
        }

        with patch("backend.handlers.walkthroughs.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch(
                "backend.handlers.walkthroughs.get_walkthrough_by_id"
            ) as mock_get:
                mock_get.return_value = mock_walkthrough

                with patch("backend.handlers.walkthroughs.load_readme") as mock_readme:
                    mock_readme.return_value = "# Test README"

                    with patch(
                        "backend.handlers.walkthroughs.get_walkthrough_progress"
                    ) as mock_progress:
                        mock_progress.return_value = {
                            "status": "not_started",
                            "started_at": None,
                            "completed_at": None,
                        }

                        response = handle_get_walkthrough(headers, walkthrough_id)

                        assert response["statusCode"] == 200
                        body_data = json.loads(response["body"])
                        assert body_data["id"] == walkthrough_id
                        assert body_data["readme"] == "# Test README"
                        assert "progress" in body_data

    def test_returns_404_when_walkthrough_not_found(self, mock_env_vars):
        """Should return 404 when walkthrough does not exist."""
        user_id = "12345678"
        walkthrough_id = "nonexistent"
        headers = {"cookie": "dsb_token=valid_token"}

        with patch("backend.handlers.walkthroughs.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch(
                "backend.handlers.walkthroughs.get_walkthrough_by_id"
            ) as mock_get:
                mock_get.return_value = None

                response = handle_get_walkthrough(headers, walkthrough_id)

                assert response["statusCode"] == 404
                body_data = json.loads(response["body"])
                assert body_data["error"] == "Walkthrough not found"

    def test_returns_404_when_readme_not_found(self, mock_env_vars):
        """Should return 404 when README.md does not exist."""
        user_id = "12345678"
        walkthrough_id = "test-walkthrough"
        headers = {"cookie": "dsb_token=valid_token"}

        mock_walkthrough = {"id": walkthrough_id, "title": "Test Walkthrough"}

        with patch("backend.handlers.walkthroughs.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch(
                "backend.handlers.walkthroughs.get_walkthrough_by_id"
            ) as mock_get:
                mock_get.return_value = mock_walkthrough

                with patch("backend.handlers.walkthroughs.load_readme") as mock_readme:
                    mock_readme.side_effect = FileNotFoundError("README not found")

                    response = handle_get_walkthrough(headers, walkthrough_id)

                    assert response["statusCode"] == 404
                    body_data = json.loads(response["body"])
                    assert body_data["error"] == "README not found"

    def test_returns_401_when_jwt_missing(self):
        """Should return 401 when JWT cookie is missing."""
        headers = {}
        walkthrough_id = "test-walkthrough"

        response = handle_get_walkthrough(headers, walkthrough_id)

        assert response["statusCode"] == 401
        body_data = json.loads(response["body"])
        assert body_data["error"] == "Authentication failed"


class TestHandleUpdateProgress:
    """Test POST /api/walkthroughs/[id]/progress endpoint handler."""

    def test_updates_progress_successfully(self, mock_env_vars):
        """Should update progress with valid status."""
        user_id = "12345678"
        walkthrough_id = "test-walkthrough"
        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"status": "in_progress"})

        with patch("backend.handlers.walkthroughs.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch(
                "backend.handlers.walkthroughs.update_walkthrough_progress"
            ) as mock_update:
                response = handle_update_progress(headers, walkthrough_id, body)

                mock_update.assert_called_once_with(
                    user_id, walkthrough_id, "in_progress"
                )
                assert response["statusCode"] == 200
                body_data = json.loads(response["body"])
                assert body_data["message"] == "Progress updated successfully"

    def test_returns_400_when_status_invalid(self, mock_env_vars):
        """Should return 400 when status value is invalid."""
        user_id = "12345678"
        walkthrough_id = "test-walkthrough"
        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({"status": "invalid_status"})

        with patch("backend.handlers.walkthroughs.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            with patch(
                "backend.handlers.walkthroughs.update_walkthrough_progress"
            ) as mock_update:
                mock_update.side_effect = ValueError("Invalid status")

                response = handle_update_progress(headers, walkthrough_id, body)

                assert response["statusCode"] == 400
                body_data = json.loads(response["body"])
                assert body_data["error"] == "Invalid status value"

    def test_returns_400_when_status_missing(self, mock_env_vars):
        """Should return 400 when status field is missing."""
        user_id = "12345678"
        walkthrough_id = "test-walkthrough"
        headers = {"cookie": "dsb_token=valid_token"}
        body = json.dumps({})

        with patch("backend.handlers.walkthroughs.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            response = handle_update_progress(headers, walkthrough_id, body)

            assert response["statusCode"] == 400
            body_data = json.loads(response["body"])
            assert body_data["error"] == "Invalid request"

    def test_returns_400_when_body_invalid_json(self, mock_env_vars):
        """Should return 400 when body is not valid JSON."""
        user_id = "12345678"
        walkthrough_id = "test-walkthrough"
        headers = {"cookie": "dsb_token=valid_token"}
        body = "not valid json"

        with patch("backend.handlers.walkthroughs.validate_jwt") as mock_validate:
            mock_validate.return_value = {"sub": user_id}

            response = handle_update_progress(headers, walkthrough_id, body)

            assert response["statusCode"] == 400
            body_data = json.loads(response["body"])
            assert body_data["error"] == "Invalid request"

    def test_returns_401_when_jwt_missing(self):
        """Should return 401 when JWT cookie is missing."""
        headers = {}
        walkthrough_id = "test-walkthrough"
        body = json.dumps({"status": "completed"})

        response = handle_update_progress(headers, walkthrough_id, body)

        assert response["statusCode"] == 401
        body_data = json.loads(response["body"])
        assert body_data["error"] == "Authentication failed"

    def test_returns_401_when_jwt_invalid(self, mock_env_vars):
        """Should return 401 when JWT is invalid."""
        headers = {"cookie": "dsb_token=invalid_token"}
        walkthrough_id = "test-walkthrough"
        body = json.dumps({"status": "completed"})

        with patch("backend.handlers.walkthroughs.validate_jwt") as mock_validate:
            mock_validate.side_effect = JWTError("Invalid token")

            response = handle_update_progress(headers, walkthrough_id, body)

            assert response["statusCode"] == 401
            body_data = json.loads(response["body"])
            assert body_data["error"] == "Authentication failed"
