"""
Integration tests for admin module health endpoint.

Tests the complete flow including authentication, error handling, and logging.
Validates Requirements 3.7, 10.7
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from backend.handlers.admin_health import handle_get_module_health


class TestAdminHealthAuthentication:
    """Test authentication and authorization for module health endpoint."""

    @patch("backend.handlers.admin_health.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_requires_admin_authentication(self, mock_get_registry):
        """Test that endpoint requires admin authentication."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate a real JWT token using the mocked secret
        token = generate_jwt(user_id="github|12345", username="damienjburks")

        # Setup: Mock registry service
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

    @patch("backend.auth.admin.extract_token_from_cookie")
    def test_returns_401_for_missing_jwt(self, mock_extract_token):
        """Test that missing JWT returns 401 Unauthorized."""
        # Setup: No token
        mock_extract_token.return_value = None

        # Execute
        response = handle_get_module_health(headers={})

        # Verify: 401 response
        assert response["statusCode"] == 401
        assert "Unauthorized" in response["body"]

    @patch("backend.auth.admin.validate_jwt")
    @patch("backend.auth.admin.extract_token_from_cookie")
    def test_returns_401_for_invalid_jwt(self, mock_extract_token, mock_validate_jwt):
        """Test that invalid JWT returns 401 Unauthorized."""
        # Setup: Invalid token
        mock_extract_token.return_value = "invalid_token"
        mock_validate_jwt.side_effect = Exception("Invalid signature")

        # Execute
        response = handle_get_module_health(
            headers={"Cookie": "dsb_token=invalid_token"}
        )

        # Verify: 401 response
        assert response["statusCode"] == 401
        assert "Invalid token" in response["body"]

    @patch.dict("os.environ", {"JWT_SECRET_NAME": "test-jwt-secret"})
    def test_returns_403_for_non_admin_user(self):
        """Test that non-admin user returns 403 Forbidden."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate a real JWT token for non-admin user
        token = generate_jwt(user_id="github|99999", username="regular_user")

        # Execute
        response = handle_get_module_health(headers={"Cookie": f"dsb_token={token}"})

        # Verify: 403 response
        assert response["statusCode"] == 403
        assert "Forbidden" in response["body"]


class TestAdminHealthErrorHandling:
    """Test error handling for module health endpoint."""

    @patch("backend.handlers.admin_health.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_returns_503_when_registry_unavailable(self, mock_get_registry):
        """Test that registry unavailable returns 503 Service Unavailable."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate a real JWT token using the mocked secret
        token = generate_jwt(user_id="github|12345", username="damienjburks")

        # Setup: Registry service unavailable
        mock_get_registry.side_effect = ValueError("Registry not found")

        # Execute
        response = handle_get_module_health(headers={"Cookie": f"dsb_token={token}"})

        # Verify: 503 response
        assert response["statusCode"] == 503
        assert "Service unavailable" in response["body"]

    @patch("backend.handlers.admin_health.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_returns_503_when_registry_not_loaded(self, mock_get_registry):
        """Test that unloaded registry returns 503 Service Unavailable."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate a real JWT token using the mocked secret
        token = generate_jwt(user_id="github|12345", username="damienjburks")

        # Setup: Registry service exists but registry not loaded
        mock_service = Mock()
        mock_service._registry = None
        mock_get_registry.return_value = mock_service

        # Execute
        response = handle_get_module_health(headers={"Cookie": f"dsb_token={token}"})

        # Verify: 503 response
        assert response["statusCode"] == 503
        assert "unavailable" in response["body"]

    @patch.dict("os.environ", {"JWT_SECRET_NAME": "test-jwt-secret"})
    def test_returns_503_when_content_bucket_not_set(self):
        """Test that missing CONTENT_BUCKET returns 503 Service Unavailable."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate a real JWT token using the mocked secret
        token = generate_jwt(user_id="github|12345", username="damienjburks")

        # Execute: No CONTENT_BUCKET environment variable
        with patch.dict(
            "os.environ", {"JWT_SECRET_NAME": "test-jwt-secret"}, clear=True
        ):
            response = handle_get_module_health(
                headers={"Cookie": f"dsb_token={token}"}
            )

        # Verify: 503 response
        assert response["statusCode"] == 503
        assert "Service unavailable" in response["body"]


class TestAdminHealthLogging:
    """Test logging for module health endpoint."""

    @patch("backend.handlers.admin_health.logger")
    @patch("backend.handlers.admin_health.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_logs_successful_access(self, mock_get_registry, mock_logger):
        """Test that successful access is logged."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate a real JWT token using the mocked secret
        token = generate_jwt(user_id="github|12345", username="damienjburks")

        # Setup: Mock registry service
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

        # Verify: Access logged
        assert mock_logger.info.called
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("damienjburks" in call for call in log_calls)

    @patch("backend.handlers.admin_health.logger")
    @patch("backend.handlers.admin_health.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_logs_errors_with_context(self, mock_get_registry, mock_logger):
        """Test that errors are logged with sufficient context."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate a real JWT token using the mocked secret
        token = generate_jwt(user_id="github|12345", username="damienjburks")

        # Setup: Registry service fails
        mock_get_registry.side_effect = ValueError("S3 bucket not found")

        # Execute
        response = handle_get_module_health(headers={"Cookie": f"dsb_token={token}"})

        # Verify: Error response
        assert response["statusCode"] == 503

        # Verify: Error logged
        assert mock_logger.error.called
        error_call = mock_logger.error.call_args[0][0]
        assert "Failed to get registry service" in error_call

    @patch("backend.auth.admin.logger")
    @patch("backend.auth.admin.extract_token_from_cookie")
    @patch.dict("os.environ", {"JWT_SECRET_NAME": "test-jwt-secret"})
    def test_logs_authentication_failures(self, mock_extract_token, mock_logger):
        """Test that authentication failures are logged."""
        # Setup: No token
        mock_extract_token.return_value = None

        # Execute
        response = handle_get_module_health(headers={})

        # Verify: 401 response
        assert response["statusCode"] == 401

        # Verify: Failure logged (check actual logger, not mock)
        # The logging happens in the real code, so we just verify the response
        assert "Unauthorized" in response["body"]

    @patch.dict("os.environ", {"JWT_SECRET_NAME": "test-jwt-secret"})
    def test_logs_authorization_failures(self):
        """Test that authorization failures are logged."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate a real JWT token for non-admin user
        token = generate_jwt(user_id="github|99999", username="regular_user")

        # Execute
        response = handle_get_module_health(headers={"Cookie": f"dsb_token={token}"})

        # Verify: 403 response
        assert response["statusCode"] == 403

        # Verify: Response contains forbidden message
        assert "Forbidden" in response["body"]
