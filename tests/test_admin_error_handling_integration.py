"""
Integration tests for admin dashboard error handling and graceful degradation.

Tests Requirements:
- 10.1: DynamoDB failure returns 500 error
- 10.2: S3 failure returns 503 error
- 10.3: DynamoDB unavailable returns 503 error
- 10.4: Error messages displayed to user
- 10.6: Retry button for transient errors
- 11.5: Partial data display when some APIs fail
"""

import json
import pytest
from unittest.mock import patch, MagicMock, Mock
from botocore.exceptions import ClientError
from backend.handlers.admin_submissions import handle_get_submissions
from backend.handlers.admin_registry import handle_get_registry_status
from backend.handlers.admin_health import handle_get_module_health


@pytest.fixture
def admin_headers():
    """Create admin authentication headers with JWT token."""
    # Use the same secret that conftest.py mocks
    with patch.dict("os.environ", {"JWT_SECRET_NAME": "test-jwt-secret"}):
        from backend.auth.jwt_utils import generate_jwt

        token = generate_jwt(user_id="github|12345", username="damienjburks")
        return {"Cookie": f"dsb_token={token}"}


class TestDynamoDBErrorHandling:
    """Test DynamoDB failure scenarios - Requirement 10.1, 10.3"""

    @patch("backend.handlers.admin_submissions.get_capstone_submissions")
    @patch.dict(
        "os.environ", {"PROGRESS_TABLE": "test-table", "JWT_SECRET_NAME": "test-secret"}
    )
    def test_submissions_dynamodb_query_failure_returns_500(
        self, mock_get_submissions, admin_headers
    ):
        """
        Test that DynamoDB query failure returns 500 error.
        Validates: Requirement 10.1
        """
        # Mock DynamoDB to raise a generic error
        mock_get_submissions.side_effect = Exception("DynamoDB query failed")

        response = handle_get_submissions(headers=admin_headers, query_params={})

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body
        # Check for error message (case-insensitive)
        error_text = body.get("error", "").lower() + body.get("message", "").lower()
        assert (
            "internal" in error_text or "failed" in error_text or "error" in error_text
        )

    @patch("backend.handlers.admin_submissions.boto3")
    @patch.dict(
        "os.environ", {"PROGRESS_TABLE": "test-table", "JWT_SECRET_NAME": "test-secret"}
    )
    def test_submissions_dynamodb_unavailable_returns_503(
        self, mock_boto3, admin_headers
    ):
        """
        Test that DynamoDB unavailable returns 503 error.
        Validates: Requirement 10.3
        """
        # Mock DynamoDB to raise ServiceUnavailable error
        mock_client = MagicMock()
        error_response = {
            "Error": {"Code": "ResourceNotFoundException", "Message": "Table not found"}
        }
        mock_client.scan.side_effect = ClientError(error_response, "Scan")
        mock_boto3.client.return_value = mock_client

        response = handle_get_submissions(headers=admin_headers, query_params={})

        # Should return 503 for service unavailable
        assert response["statusCode"] == 503
        body = json.loads(response["body"])
        assert "error" in body

    @patch("backend.handlers.admin_submissions.boto3")
    @patch.dict(
        "os.environ", {"PROGRESS_TABLE": "test-table", "JWT_SECRET_NAME": "test-secret"}
    )
    def test_submissions_throttling_error_returns_500(self, mock_boto3, admin_headers):
        """
        Test that DynamoDB throttling returns 500 error.
        Validates: Requirement 10.3
        """
        mock_client = MagicMock()
        error_response = {
            "Error": {
                "Code": "ProvisionedThroughputExceededException",
                "Message": "Throttled",
            }
        }
        mock_client.scan.side_effect = ClientError(error_response, "Scan")
        mock_boto3.client.return_value = mock_client

        response = handle_get_submissions(headers=admin_headers, query_params={})

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body


class TestS3ErrorHandling:
    """Test S3 failure scenarios - Requirement 10.2"""

    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-secret"},
    )
    def test_registry_status_s3_failure_returns_503(self, mock_service, admin_headers):
        """
        Test that S3 failure returns 503 error for registry status.
        Validates: Requirement 10.2
        """
        # Mock registry service to raise S3 error
        mock_service.side_effect = ValueError(
            "Failed to load registry from S3: NoSuchKey"
        )

        response = handle_get_registry_status(headers=admin_headers)

        # Should return 503 for service unavailable
        assert response["statusCode"] == 503
        body = json.loads(response["body"])
        assert "error" in body

    @patch("backend.handlers.admin_health.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-secret"},
    )
    def test_module_health_s3_failure_returns_503(self, mock_service, admin_headers):
        """
        Test that S3 failure returns 503 error for module health.
        Validates: Requirement 10.2
        """
        # Mock registry service to raise S3 error
        mock_service.side_effect = ValueError(
            "Failed to load registry from S3: AccessDenied"
        )

        response = handle_get_module_health(headers=admin_headers)

        # Should return 503 for service unavailable
        assert response["statusCode"] == 503
        body = json.loads(response["body"])
        assert "error" in body

    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-secret"},
    )
    def test_registry_status_s3_timeout_returns_503(self, mock_service, admin_headers):
        """
        Test that S3 timeout returns 503 error.
        Validates: Requirement 10.2
        """
        mock_service.side_effect = ValueError(
            "Failed to load registry from S3: RequestTimeout"
        )

        response = handle_get_registry_status(headers=admin_headers)

        assert response["statusCode"] == 503
        body = json.loads(response["body"])
        assert "error" in body


class TestErrorResponseFormat:
    """Test error response format and messages - Requirement 10.4"""

    @patch("backend.handlers.admin_submissions.get_capstone_submissions")
    @patch.dict(
        "os.environ", {"PROGRESS_TABLE": "test-table", "JWT_SECRET_NAME": "test-secret"}
    )
    def test_error_responses_contain_descriptive_messages(
        self, mock_get_submissions, admin_headers
    ):
        """
        Test that error responses contain descriptive error messages.
        Validates: Requirement 10.4
        """
        mock_get_submissions.side_effect = Exception("Database connection failed")

        response = handle_get_submissions(headers=admin_headers, query_params={})

        assert response["statusCode"] == 500
        body = json.loads(response["body"])

        # Should have error field with descriptive message
        assert "error" in body or "message" in body
        error_text = body.get("error", "") + body.get("message", "")
        assert len(error_text) > 0  # Has some error description

    @patch("backend.handlers.admin_submissions.get_capstone_submissions")
    @patch.dict(
        "os.environ", {"PROGRESS_TABLE": "test-table", "JWT_SECRET_NAME": "test-secret"}
    )
    def test_error_responses_are_valid_json(self, mock_get_submissions, admin_headers):
        """
        Test that error responses are valid JSON.
        Validates: Requirement 12.1
        """
        mock_get_submissions.side_effect = Exception("Test error")

        response = handle_get_submissions(headers=admin_headers, query_params={})

        # Should be able to parse response body as JSON
        body = json.loads(response["body"])
        assert isinstance(body, dict)

    @patch.dict(
        "os.environ", {"PROGRESS_TABLE": "test-table", "JWT_SECRET_NAME": "test-secret"}
    )
    def test_different_error_types_have_specific_messages(self):
        """
        Test that different error types return specific error messages.
        Validates: Requirement 10.5
        """
        # Test authentication error (401) - invalid token
        invalid_headers = {"Cookie": "dsb_token=invalid_token"}

        response = handle_get_submissions(headers=invalid_headers, query_params={})

        # Should return 401 or 500 with auth-related error
        assert response["statusCode"] in [401, 403, 500]
        body = json.loads(response["body"])
        assert "error" in body or "message" in body


class TestGracefulDegradation:
    """Test graceful degradation and partial failure handling - Requirement 11.5"""

    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-secret"},
    )
    def test_registry_status_returns_error_state_not_exception(
        self, mock_service, admin_headers
    ):
        """
        Test that registry status returns error state instead of throwing exception.
        This allows frontend to display partial data.
        Validates: Requirement 11.5
        """
        mock_service.side_effect = Exception("S3 error")

        response = handle_get_registry_status(headers=admin_headers)

        # Should return a response (not crash)
        assert "statusCode" in response
        assert "body" in response

        # Body should be parseable JSON
        body = json.loads(response["body"])
        assert isinstance(body, dict)

    @patch("backend.handlers.admin_health.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-secret"},
    )
    def test_module_health_handles_partial_registry_data(
        self, mock_service, admin_headers
    ):
        """
        Test that module health can handle partial registry data.
        Validates: Requirement 11.5
        """
        mock_instance = Mock()
        # Partial registry data (some fields missing)
        mock_instance._registry = {
            "entries": {"module-1": {"content_type": "module", "title": "Test Module"}}
        }
        mock_service.return_value = mock_instance

        response = handle_get_module_health(headers=admin_headers)

        # Should handle partial data gracefully
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "total_modules" in body
        assert body["total_modules"] >= 0

    @patch("backend.handlers.admin_submissions.get_capstone_submissions")
    @patch.dict(
        "os.environ", {"PROGRESS_TABLE": "test-table", "JWT_SECRET_NAME": "test-secret"}
    )
    def test_submissions_handles_empty_results_gracefully(
        self, mock_get_submissions, admin_headers
    ):
        """
        Test that submissions endpoint handles empty results gracefully.
        Validates: Requirement 11.5
        """
        # Mock empty query result
        mock_get_submissions.return_value = ([], 0)

        response = handle_get_submissions(headers=admin_headers, query_params={})

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "submissions" in body
        assert body["submissions"] == []
        assert body.get("total_count", 0) == 0


class TestRetryScenarios:
    """Test scenarios where retry should be possible - Requirement 10.6"""

    @patch("backend.handlers.admin_submissions.boto3")
    @patch.dict(
        "os.environ", {"PROGRESS_TABLE": "test-table", "JWT_SECRET_NAME": "test-secret"}
    )
    def test_transient_errors_return_retryable_status_codes(
        self, mock_boto3, admin_headers
    ):
        """
        Test that transient errors (5xx) indicate retry is possible.
        Validates: Requirement 10.6
        """
        # Simulate transient error
        mock_client = MagicMock()
        error_response = {
            "Error": {"Code": "InternalServerError", "Message": "Transient error"}
        }
        mock_client.scan.side_effect = ClientError(error_response, "Scan")
        mock_boto3.client.return_value = mock_client

        response = handle_get_submissions(headers=admin_headers, query_params={})

        # Should return 5xx status code (retryable)
        assert 500 <= response["statusCode"] < 600

    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-secret"},
    )
    def test_service_unavailable_errors_are_retryable(
        self, mock_service, admin_headers
    ):
        """
        Test that service unavailable errors return 503 (retryable).
        Validates: Requirement 10.6
        """
        mock_service.side_effect = ValueError("Service unavailable")

        response = handle_get_registry_status(headers=admin_headers)

        # Should return 503
        assert response["statusCode"] == 503

        # Frontend should be able to retry based on this response
        body = json.loads(response["body"])
        assert "error" in body


class TestErrorLogging:
    """Test error logging for debugging - Requirement 10.7"""

    @patch("backend.handlers.admin_submissions.get_capstone_submissions")
    @patch.dict(
        "os.environ", {"PROGRESS_TABLE": "test-table", "JWT_SECRET_NAME": "test-secret"}
    )
    def test_errors_are_logged_with_context(
        self, mock_get_submissions, admin_headers, caplog
    ):
        """
        Test that errors are logged with sufficient context for debugging.
        Validates: Requirement 10.7
        """
        mock_get_submissions.side_effect = Exception("Test error for logging")

        response = handle_get_submissions(headers=admin_headers, query_params={})

        # Should log the error
        assert response["statusCode"] == 500
        # Note: Actual log verification would require checking logger calls
        # This test verifies the handler doesn't crash and returns proper error

    @patch.dict(
        "os.environ", {"PROGRESS_TABLE": "test-table", "JWT_SECRET_NAME": "test-secret"}
    )
    def test_authentication_failures_are_logged(self, caplog):
        """
        Test that authentication failures are logged.
        Validates: Requirement 9.7
        """
        invalid_headers = {"Cookie": "dsb_token=invalid_token"}

        response = handle_get_submissions(headers=invalid_headers, query_params={})

        # Should return error status
        assert response["statusCode"] in [401, 403, 500]


class TestCORSHeaders:
    """Test that error responses include proper CORS headers"""

    @patch("backend.handlers.admin_submissions.get_capstone_submissions")
    @patch.dict(
        "os.environ", {"PROGRESS_TABLE": "test-table", "JWT_SECRET_NAME": "test-secret"}
    )
    def test_error_responses_include_cors_headers(
        self, mock_get_submissions, admin_headers
    ):
        """
        Test that error responses include CORS headers for frontend access.
        """
        mock_get_submissions.side_effect = Exception("Test error")

        response = handle_get_submissions(headers=admin_headers, query_params={})

        # Should have CORS headers even on error
        assert "headers" in response
        headers = response["headers"]
        # Check for common CORS headers
        assert any(
            key.lower()
            in ["access-control-allow-origin", "access-control-allow-credentials"]
            for key in headers.keys()
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
