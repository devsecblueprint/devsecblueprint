"""
Integration tests for admin authentication flow across all endpoints.

Tests the complete authentication flow for all three admin endpoints:
- GET /admin/submissions
- GET /admin/registry-status
- GET /admin/module-health

Validates Requirements 9.1, 9.2, 9.3, 9.4, 9.5
"""

import pytest
from unittest.mock import Mock, patch
from backend.handlers.admin_submissions import handle_get_submissions
from backend.handlers.admin_registry import handle_get_registry_status
from backend.handlers.admin_health import handle_get_module_health


class TestAdminAuthenticationFlow:
    """Test authentication flow for all admin endpoints."""

    @patch("backend.handlers.admin_submissions.get_capstone_submissions")
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_admin_user_can_access_submissions_endpoint(self, mock_get_submissions):
        """Test that admin user can successfully access submissions endpoint."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Mock submissions data
        mock_get_submissions.return_value = (
            [
                {
                    "user_id": "github|99999",
                    "github_username": "learner1",
                    "repo_url": "https://github.com/learner1/capstone",
                    "submitted_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                }
            ],
            1,
        )

        # Execute
        response = handle_get_submissions(
            headers={"Cookie": f"dsb_token={token}"},
            query_params={"page": "1", "page_size": "50"},
        )

        # Verify: Success response
        assert response["statusCode"] == 200
        assert "submissions" in response["body"]

    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_admin_user_can_access_registry_status_endpoint(self, mock_get_registry):
        """Test that admin user can successfully access registry status endpoint."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Mock registry service
        mock_service = Mock()
        mock_service._registry = {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "entries": {"module1": {"content_type": "module"}},
        }
        mock_service.cache_ttl_seconds = 300
        mock_service._last_loaded_at = None
        mock_service.s3_bucket = "test-bucket"
        mock_service.s3_key = "content-registry/latest.json"
        mock_get_registry.return_value = mock_service

        # Execute
        response = handle_get_registry_status(headers={"Cookie": f"dsb_token={token}"})

        # Verify: Success response
        assert response["statusCode"] == 200
        assert "schema_version" in response["body"]

    @patch("backend.handlers.admin_health.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_admin_user_can_access_module_health_endpoint(self, mock_get_registry):
        """Test that admin user can successfully access module health endpoint."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Mock registry service
        mock_service = Mock()
        mock_service._registry = {
            "entries": {
                "module1": {
                    "content_type": "module",
                    "title": "Test Module",
                    "description": "Test description",
                }
            }
        }
        mock_get_registry.return_value = mock_service

        # Execute
        response = handle_get_module_health(headers={"Cookie": f"dsb_token={token}"})

        # Verify: Success response
        assert response["statusCode"] == 200
        assert "total_modules" in response["body"]


class TestNonAdminUserAccess:
    """Test that non-admin users receive 403 errors."""

    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_non_admin_receives_403_for_submissions(self):
        """Test that non-admin user receives 403 for submissions endpoint."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate non-admin JWT token
        token = generate_jwt(user_id="github|99999", username="regular_user")

        # Execute
        response = handle_get_submissions(
            headers={"Cookie": f"dsb_token={token}"}, query_params={}
        )

        # Verify: 403 Forbidden
        assert response["statusCode"] == 403
        assert "Forbidden" in response["body"]

    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_non_admin_receives_403_for_registry_status(self):
        """Test that non-admin user receives 403 for registry status endpoint."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate non-admin JWT token
        token = generate_jwt(user_id="github|99999", username="regular_user")

        # Execute
        response = handle_get_registry_status(headers={"Cookie": f"dsb_token={token}"})

        # Verify: 403 Forbidden
        assert response["statusCode"] == 403
        assert "Forbidden" in response["body"]

    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_non_admin_receives_403_for_module_health(self):
        """Test that non-admin user receives 403 for module health endpoint."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate non-admin JWT token
        token = generate_jwt(user_id="github|99999", username="regular_user")

        # Execute
        response = handle_get_module_health(headers={"Cookie": f"dsb_token={token}"})

        # Verify: 403 Forbidden
        assert response["statusCode"] == 403
        assert "Forbidden" in response["body"]


class TestMissingJWTAccess:
    """Test that missing JWT returns 401 errors."""

    def test_missing_jwt_returns_401_for_submissions(self):
        """Test that missing JWT returns 401 for submissions endpoint."""
        # Execute with no cookie header
        response = handle_get_submissions(headers={}, query_params={})

        # Verify: 401 Unauthorized
        assert response["statusCode"] == 401
        assert "Unauthorized" in response["body"]

    def test_missing_jwt_returns_401_for_registry_status(self):
        """Test that missing JWT returns 401 for registry status endpoint."""
        # Execute with no cookie header
        response = handle_get_registry_status(headers={})

        # Verify: 401 Unauthorized
        assert response["statusCode"] == 401
        assert "Unauthorized" in response["body"]

    def test_missing_jwt_returns_401_for_module_health(self):
        """Test that missing JWT returns 401 for module health endpoint."""
        # Execute with no cookie header
        response = handle_get_module_health(headers={})

        # Verify: 401 Unauthorized
        assert response["statusCode"] == 401
        assert "Unauthorized" in response["body"]


class TestInvalidJWTAccess:
    """Test that invalid JWT returns 401 errors."""

    @patch("backend.auth.admin.validate_jwt")
    @patch("backend.auth.admin.extract_token_from_cookie")
    def test_invalid_jwt_returns_401_for_submissions(self, mock_extract, mock_validate):
        """Test that invalid JWT returns 401 for submissions endpoint."""
        # Mock invalid token
        mock_extract.return_value = "invalid_token"
        mock_validate.side_effect = Exception("Invalid signature")

        # Execute
        response = handle_get_submissions(
            headers={"Cookie": "dsb_token=invalid_token"}, query_params={}
        )

        # Verify: 401 Unauthorized
        assert response["statusCode"] == 401
        assert "Invalid token" in response["body"]

    @patch("backend.auth.admin.validate_jwt")
    @patch("backend.auth.admin.extract_token_from_cookie")
    def test_invalid_jwt_returns_401_for_registry_status(
        self, mock_extract, mock_validate
    ):
        """Test that invalid JWT returns 401 for registry status endpoint."""
        # Mock invalid token
        mock_extract.return_value = "invalid_token"
        mock_validate.side_effect = Exception("Invalid signature")

        # Execute
        response = handle_get_registry_status(
            headers={"Cookie": "dsb_token=invalid_token"}
        )

        # Verify: 401 Unauthorized
        assert response["statusCode"] == 401
        assert "Invalid token" in response["body"]

    @patch("backend.auth.admin.validate_jwt")
    @patch("backend.auth.admin.extract_token_from_cookie")
    def test_invalid_jwt_returns_401_for_module_health(
        self, mock_extract, mock_validate
    ):
        """Test that invalid JWT returns 401 for module health endpoint."""
        # Mock invalid token
        mock_extract.return_value = "invalid_token"
        mock_validate.side_effect = Exception("Invalid signature")

        # Execute
        response = handle_get_module_health(
            headers={"Cookie": "dsb_token=invalid_token"}
        )

        # Verify: 401 Unauthorized
        assert response["statusCode"] == 401
        assert "Invalid token" in response["body"]


class TestCrossEndpointConsistency:
    """Test that authentication behavior is consistent across all endpoints."""

    @patch.dict("os.environ", {"JWT_SECRET_NAME": "test-jwt-secret"})
    def test_all_endpoints_reject_non_admin_consistently(self):
        """Test that all endpoints reject non-admin users with 403."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate non-admin JWT token
        token = generate_jwt(user_id="github|99999", username="regular_user")
        headers = {"Cookie": f"dsb_token={token}"}

        # Test all three endpoints
        submissions_response = handle_get_submissions(headers=headers, query_params={})
        registry_response = handle_get_registry_status(headers=headers)
        health_response = handle_get_module_health(headers=headers)

        # Verify: All return 403
        assert submissions_response["statusCode"] == 403
        assert registry_response["statusCode"] == 403
        assert health_response["statusCode"] == 403

    def test_all_endpoints_reject_missing_jwt_consistently(self):
        """Test that all endpoints reject missing JWT with 401."""
        headers = {}

        # Test all three endpoints
        submissions_response = handle_get_submissions(headers=headers, query_params={})
        registry_response = handle_get_registry_status(headers=headers)
        health_response = handle_get_module_health(headers=headers)

        # Verify: All return 401
        assert submissions_response["statusCode"] == 401
        assert registry_response["statusCode"] == 401
        assert health_response["statusCode"] == 401

    @patch("backend.handlers.admin_submissions.get_capstone_submissions")
    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch("backend.handlers.admin_health.get_registry_service")
    @patch.dict(
        "os.environ",
        {
            "PROGRESS_TABLE": "test-progress-table",
            "CONTENT_BUCKET": "test-bucket",
            "JWT_SECRET_NAME": "test-jwt-secret",
        },
    )
    def test_all_endpoints_accept_admin_consistently(
        self, mock_health_registry, mock_status_registry, mock_get_submissions
    ):
        """Test that all endpoints accept admin users with 200."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )
        headers = {"Cookie": f"dsb_token={token}"}

        # Mock data for submissions
        mock_get_submissions.return_value = ([], 0)

        # Mock registry service for status endpoint
        mock_status_service = Mock()
        mock_status_service._registry = {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "entries": {},
        }
        mock_status_service.cache_ttl_seconds = 300
        mock_status_service._last_loaded_at = None
        mock_status_service.s3_bucket = "test-bucket"
        mock_status_service.s3_key = "content-registry/latest.json"
        mock_status_registry.return_value = mock_status_service

        # Mock registry service for health endpoint
        mock_health_service = Mock()
        mock_health_service._registry = {"entries": {}}
        mock_health_registry.return_value = mock_health_service

        # Test all three endpoints
        submissions_response = handle_get_submissions(headers=headers, query_params={})
        registry_response = handle_get_registry_status(headers=headers)
        health_response = handle_get_module_health(headers=headers)

        # Verify: All return 200
        assert submissions_response["statusCode"] == 200
        assert registry_response["statusCode"] == 200
        assert health_response["statusCode"] == 200
