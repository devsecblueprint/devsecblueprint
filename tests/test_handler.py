"""
Unit tests for Lambda handler with routing.

Tests the main lambda_handler function to ensure proper routing to all endpoints,
error handling, and response formatting.
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.handler import main as lambda_handler, sanitize_error_message


def create_test_event(
    method: str, path: str, headers=None, query_params=None, body=None
):
    """Helper to create API Gateway HTTP API event."""
    return {
        "requestContext": {"http": {"method": method, "path": path}},
        "headers": headers or {},
        "queryStringParameters": query_params,
        "body": body,
    }


class TestLambdaHandlerRouting:
    """Test routing logic in lambda_handler."""

    @patch("backend.handler.start_oauth")
    def test_route_github_start(self, mock_start_oauth):
        """Test routing to GET /auth/github/start."""
        mock_start_oauth.return_value = {"statusCode": 302}

        event = create_test_event("GET", "/auth/github/start")
        response = lambda_handler(event, None)

        mock_start_oauth.assert_called_once()
        assert response["statusCode"] == 302

    @patch("backend.handler.handle_callback")
    def test_route_github_callback_with_code(self, mock_handle_callback):
        """Test routing to GET /auth/github/callback with code parameter."""
        mock_handle_callback.return_value = {"statusCode": 302}

        event = create_test_event(
            "GET", "/auth/github/callback", query_params={"code": "test_code"}
        )
        response = lambda_handler(event, None)

        mock_handle_callback.assert_called_once_with("test_code")
        assert response["statusCode"] == 302

    def test_route_github_callback_missing_code(self):
        """Test GET /auth/github/callback without code parameter returns 400."""
        event = create_test_event("GET", "/auth/github/callback", query_params={})
        response = lambda_handler(event, None)

        assert response["statusCode"] == 400
        assert "error" in response["body"]

    @patch("backend.handler.verify_user")
    def test_route_me(self, mock_verify_user):
        """Test routing to GET /me."""
        mock_verify_user.return_value = {"statusCode": 200}

        headers = {"cookie": "dsb_token=test_token"}
        event = create_test_event("GET", "/me", headers=headers)
        response = lambda_handler(event, None)

        mock_verify_user.assert_called_once_with(headers)
        assert response["statusCode"] == 200

    @patch("backend.handler.handle_progress")
    def test_route_progress(self, mock_handle_progress):
        """Test routing to PUT /progress."""
        mock_handle_progress.return_value = {"statusCode": 200}

        headers = {"cookie": "dsb_token=test_token"}
        body = '{"content_id": "test-content"}'
        event = create_test_event("PUT", "/progress", headers=headers, body=body)
        response = lambda_handler(event, None)

        mock_handle_progress.assert_called_once_with(headers, body)
        assert response["statusCode"] == 200

    def test_unknown_route_returns_404(self):
        """Test that unknown routes return 404."""
        event = create_test_event("GET", "/unknown/path")
        response = lambda_handler(event, None)

        assert response["statusCode"] == 404
        assert "error" in response["body"]

    def test_unsupported_method_returns_404(self):
        """Test that unsupported HTTP methods return 404."""
        event = create_test_event("POST", "/auth/github/start")
        response = lambda_handler(event, None)

        assert response["statusCode"] == 404
        assert "error" in response["body"]


class TestLambdaHandlerErrorHandling:
    """Test error handling in lambda_handler."""

    @patch("backend.handler.start_oauth")
    def test_exception_handling_returns_500(self, mock_start_oauth):
        """Test that unhandled exceptions return 500 with generic error."""
        mock_start_oauth.side_effect = Exception("Unexpected error")

        event = create_test_event("GET", "/auth/github/start")
        response = lambda_handler(event, None)

        assert response["statusCode"] == 500
        assert "error" in response["body"]
        # Ensure no stack trace or sensitive info in response
        assert "Unexpected error" not in response["body"]

    @patch("backend.handler.logger")
    @patch("backend.handler.start_oauth")
    def test_exception_logging_with_sanitization(self, mock_start_oauth, mock_logger):
        """Test that exceptions are logged with sanitized messages."""
        # Simulate an exception with sensitive data
        mock_start_oauth.side_effect = Exception(
            "Error with token abc123def456ghi789jkl012mno345pqr678"
        )

        event = create_test_event("GET", "/auth/github/start")
        response = lambda_handler(event, None)

        # Verify error response
        assert response["statusCode"] == 500

        # Verify logging was called
        mock_logger.error.assert_called_once()

        # Verify the logged message contains sanitized content
        logged_message = mock_logger.error.call_args[0][0]
        assert "[REDACTED_TOKEN]" in logged_message
        assert "abc123def456ghi789jkl012mno345pqr678" not in logged_message

    @patch("backend.handler.logger")
    @patch("backend.handler.start_oauth")
    def test_exception_logging_sanitizes_secrets(self, mock_start_oauth, mock_logger):
        """Test that secret values are sanitized in error logs."""
        mock_start_oauth.side_effect = Exception(
            "API error: api_key=sk_live_1234567890abcdef"
        )

        event = create_test_event("GET", "/auth/github/start")
        response = lambda_handler(event, None)

        assert response["statusCode"] == 500

        # Verify the logged message has sanitized secrets
        logged_message = mock_logger.error.call_args[0][0]
        assert "api_key=[REDACTED]" in logged_message
        assert "sk_live_1234567890abcdef" not in logged_message

    def test_missing_request_context(self):
        """Test handling of malformed event without requestContext."""
        event = {"headers": {}}
        response = lambda_handler(event, None)

        # Should handle gracefully and return 404 for empty method/path
        assert response["statusCode"] == 404

    def test_none_query_parameters(self):
        """Test handling when queryStringParameters is None."""
        event = create_test_event("GET", "/auth/github/callback", query_params=None)
        response = lambda_handler(event, None)

        # Should handle None gracefully and return 400 for missing code
        assert response["statusCode"] == 400


class TestSanitizeErrorMessage:
    """Test the sanitize_error_message function."""

    def test_sanitize_long_tokens(self):
        """Test that long token-like strings are redacted."""
        error = Exception(
            "Authentication failed with token: abc123def456ghi789jkl012mno345pqr678"
        )
        sanitized = sanitize_error_message(error)

        # The word "token:" is treated as a key, so it becomes "token=[REDACTED]"
        assert "token=[REDACTED]" in sanitized
        assert "abc123def456ghi789jkl012mno345pqr678" not in sanitized

    def test_sanitize_api_keys(self):
        """Test that API keys are redacted."""
        error = Exception("Failed to connect: api_key=sk_live_1234567890")
        sanitized = sanitize_error_message(error)

        assert "api_key=[REDACTED]" in sanitized
        assert "sk_live_1234567890" not in sanitized

    def test_sanitize_secrets(self):
        """Test that secret values are redacted."""
        error = Exception("Secret validation failed: secret=my_secret_value_123")
        sanitized = sanitize_error_message(error)

        assert "secret=[REDACTED]" in sanitized
        assert "my_secret_value_123" not in sanitized

    def test_sanitize_passwords(self):
        """Test that passwords are redacted."""
        error = Exception("Auth error: password='MyP@ssw0rd123'")
        sanitized = sanitize_error_message(error)

        assert "password=[REDACTED]" in sanitized
        assert "MyP@ssw0rd123" not in sanitized

    def test_sanitize_file_paths_unix(self):
        """Test that Unix file paths are redacted."""
        error = Exception("File not found: /home/user/secrets/config.json")
        sanitized = sanitize_error_message(error)

        assert "[REDACTED_PATH]" in sanitized
        assert "/home/user/secrets/config.json" not in sanitized

    def test_sanitize_file_paths_windows(self):
        """Test that Windows file paths are redacted."""
        error = Exception("File error: C:\\Users\\Admin\\secrets\\config.json")
        sanitized = sanitize_error_message(error)

        assert "[REDACTED_PATH]" in sanitized
        assert "C:\\Users\\Admin\\secrets\\config.json" not in sanitized

    def test_sanitize_environment_variables(self):
        """Test that environment variable values are redacted."""
        error = Exception("Config error: env=production_secret_key_123")
        sanitized = sanitize_error_message(error)

        assert "env=[REDACTED]" in sanitized
        assert "production_secret_key_123" not in sanitized

    def test_sanitize_preserves_safe_content(self):
        """Test that safe error messages are preserved."""
        error = Exception("Connection timeout after 30 seconds")
        sanitized = sanitize_error_message(error)

        assert "Connection timeout" in sanitized
        assert "30 seconds" in sanitized


class TestLambdaHandlerResponseFormat:
    """Test response formatting from lambda_handler."""

    @patch("backend.handler.start_oauth")
    def test_response_includes_cors_headers(self, mock_start_oauth):
        """Test that all responses include CORS headers."""
        mock_start_oauth.return_value = {
            "statusCode": 302,
            "headers": {
                "Location": "https://github.com",
                "Access-Control-Allow-Origin": "https://devsecblueprint.com",
            },
            "body": "",
        }

        event = create_test_event("GET", "/auth/github/start")
        response = lambda_handler(event, None)

        assert "Access-Control-Allow-Origin" in response["headers"]

    def test_error_response_format(self):
        """Test that error responses are properly formatted."""
        event = create_test_event("GET", "/unknown")
        response = lambda_handler(event, None)

        assert "statusCode" in response
        assert "headers" in response
        assert "body" in response
        assert response["statusCode"] == 404


class TestWalkthroughRouting:
    """Test routing for walkthrough endpoints."""

    @patch("backend.handler.handle_get_walkthroughs")
    def test_route_get_walkthroughs(self, mock_handler):
        """Test routing to GET /api/walkthroughs."""
        mock_handler.return_value = {"statusCode": 200, "body": '{"walkthroughs": []}'}

        headers = {"cookie": "dsb_token=test_token"}
        query_params = {"difficulty": "Beginner"}
        event = create_test_event(
            "GET", "/api/walkthroughs", headers=headers, query_params=query_params
        )
        response = lambda_handler(event, None)

        mock_handler.assert_called_once_with(headers, query_params)
        assert response["statusCode"] == 200

    @patch("backend.handler.handle_get_walkthrough")
    def test_route_get_walkthrough_by_id(self, mock_handler):
        """Test routing to GET /api/walkthroughs/{id}."""
        mock_handler.return_value = {
            "statusCode": 200,
            "body": '{"id": "test-walkthrough"}',
        }

        headers = {"cookie": "dsb_token=test_token"}
        event = create_test_event(
            "GET", "/api/walkthroughs/test-walkthrough", headers=headers
        )
        response = lambda_handler(event, None)

        mock_handler.assert_called_once_with(headers, "test-walkthrough")
        assert response["statusCode"] == 200

    @patch("backend.handler.handle_walkthrough_progress")
    def test_route_update_walkthrough_progress(self, mock_handler):
        """Test routing to POST /api/walkthroughs/{id}/progress."""
        mock_handler.return_value = {
            "statusCode": 200,
            "body": '{"message": "Progress updated"}',
        }

        headers = {"cookie": "dsb_token=test_token"}
        body = '{"status": "completed"}'
        event = create_test_event(
            "POST",
            "/api/walkthroughs/test-walkthrough/progress",
            headers=headers,
            body=body,
        )
        response = lambda_handler(event, None)

        mock_handler.assert_called_once_with(headers, "test-walkthrough", body)
        assert response["statusCode"] == 200

    def test_walkthrough_route_with_special_characters_in_id(self):
        """Test that walkthrough IDs with hyphens and underscores work."""
        with patch("backend.handler.handle_get_walkthrough") as mock_handler:
            mock_handler.return_value = {"statusCode": 200, "body": "{}"}

            headers = {"cookie": "dsb_token=test_token"}
            event = create_test_event(
                "GET", "/api/walkthroughs/secure-cicd_pipeline-v2", headers=headers
            )
            response = lambda_handler(event, None)

            mock_handler.assert_called_once_with(headers, "secure-cicd_pipeline-v2")
            assert response["statusCode"] == 200

    def test_invalid_walkthrough_route_returns_404(self):
        """Test that invalid walkthrough routes return 404."""
        event = create_test_event("GET", "/api/walkthroughs/test-id/invalid")
        response = lambda_handler(event, None)

        assert response["statusCode"] == 404
