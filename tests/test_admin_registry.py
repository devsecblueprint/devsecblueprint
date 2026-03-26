"""
Unit tests for admin registry status handler.

Tests the handle_get_registry_status endpoint.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, Mock
from backend.handlers.admin_registry import build_registry_status, log_error


class TestBuildRegistryStatus:
    """Test the build_registry_status function."""

    def test_builds_status_with_all_fields(self):
        """Test that build_registry_status includes all required fields."""
        mock_service = Mock()
        mock_service._registry = {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "entries": {
                "quiz1": {"content_type": "quiz"},
                "module1": {"content_type": "module"},
                "capstone1": {"content_type": "capstone"},
            },
        }
        mock_service.s3_bucket = "test-bucket"
        mock_service.s3_key = "content-registry/latest.json"
        mock_service.cache_ttl_seconds = 300
        mock_service._last_loaded_at = 1000.0

        with patch("backend.handlers.admin_registry.time.time", return_value=1150.0):
            status = build_registry_status(mock_service)

        assert status["schema_version"] == "1.0.0"
        assert status["last_updated"] == "2024-01-15T08:00:00Z"
        assert status["total_entries"] == 3
        assert status["cache_status"] == "loaded"
        assert status["cache_ttl_seconds"] == 300
        assert status["cache_expires_in_seconds"] == 150  # 300 - 150
        assert status["s3_bucket"] == "test-bucket"
        assert status["s3_key"] == "content-registry/latest.json"
        assert status["status"] == "healthy"

    def test_raises_error_when_registry_not_loaded(self):
        """Test that build_registry_status raises error when registry is None."""
        mock_service = Mock()
        mock_service._registry = None

        with pytest.raises(ValueError, match="Registry not loaded"):
            build_registry_status(mock_service)

    def test_handles_no_cache_ttl(self):
        """Test that build_registry_status handles None cache_ttl_seconds."""
        mock_service = Mock()
        mock_service._registry = {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "entries": {},
        }
        mock_service.s3_bucket = "test-bucket"
        mock_service.s3_key = "content-registry/latest.json"
        mock_service.cache_ttl_seconds = None
        mock_service._last_loaded_at = 1000.0

        status = build_registry_status(mock_service)

        assert status["cache_ttl_seconds"] is None
        assert status["cache_expires_in_seconds"] is None

    def test_cache_expires_in_never_negative(self):
        """Test that cache_expires_in_seconds is never negative."""
        mock_service = Mock()
        mock_service._registry = {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "entries": {},
        }
        mock_service.s3_bucket = "test-bucket"
        mock_service.s3_key = "content-registry/latest.json"
        mock_service.cache_ttl_seconds = 300
        mock_service._last_loaded_at = 1000.0

        # Time has passed beyond TTL
        with patch("backend.handlers.admin_registry.time.time", return_value=1500.0):
            status = build_registry_status(mock_service)

        assert status["cache_expires_in_seconds"] == 0  # Should be 0, not negative


class TestLogError:
    """Test the log_error function."""

    @patch("backend.handlers.admin_registry.logger")
    def test_logs_error_with_all_fields(self, mock_logger):
        """Test that log_error creates structured log entry."""
        log_error(
            endpoint="handle_get_registry_status",
            error_type="ClientError",
            error_message="NoSuchKey",
            username="damienjburks",
            user_id="github|12345",
            context={"bucket": "test-bucket"},
        )

        assert mock_logger.error.called
        call_args = mock_logger.error.call_args

        # Check log message
        log_message = call_args[0][0]
        assert "handle_get_registry_status" in log_message
        assert "ClientError" in log_message

        # Check extra data
        extra = call_args[1]["extra"]
        assert extra["event"] == "admin_endpoint_error"
        assert extra["endpoint"] == "handle_get_registry_status"
        assert extra["error_type"] == "ClientError"
        assert extra["username"] == "damienjburks"
        assert extra["context"]["bucket"] == "test-bucket"


class TestCacheBehavior:
    """Test the 60-second caching behavior."""

    @patch("backend.handlers.admin_registry.build_registry_status")
    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch("backend.handlers.admin_registry.time.time")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_cache_returns_cached_data_within_ttl(
        self, mock_time, mock_get_service, mock_build_status
    ):
        """Test that cache returns cached data within 60-second TTL."""
        from backend.handlers.admin_registry import (
            handle_get_registry_status,
            clear_cache,
        )
        from backend.auth.jwt_utils import generate_jwt

        # Clear cache before test
        clear_cache()

        # Generate a real JWT token using the mocked secret
        token = generate_jwt(
            user_id="github|123",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Mock build_registry_status to return test data
        test_status = {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "total_entries": 1,
            "cache_status": "loaded",
            "cache_ttl_seconds": 300,
            "cache_expires_in_seconds": 150,
            "s3_bucket": "test-bucket",
            "s3_key": "content-registry/latest.json",
            "status": "healthy",
        }
        mock_build_status.return_value = test_status

        # First request at time 1000
        mock_time.return_value = 1000.0

        response1 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response1["statusCode"] == 200
        assert mock_get_service.call_count == 1
        assert mock_build_status.call_count == 1

        # Second request at time 1030 (30 seconds later, within 60s TTL)
        mock_time.return_value = 1030.0

        response2 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response2["statusCode"] == 200
        # Should still be 1 call - cache was used
        assert mock_get_service.call_count == 1
        assert mock_build_status.call_count == 1

        # Verify both responses are identical
        assert json.loads(response1["body"]) == json.loads(response2["body"])

    @patch("backend.handlers.admin_registry.build_registry_status")
    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch("backend.handlers.admin_registry.time.time")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_cache_refreshes_after_ttl_expires(
        self, mock_time, mock_get_service, mock_build_status
    ):
        """Test that cache refreshes after 60-second TTL expires."""
        from backend.handlers.admin_registry import (
            handle_get_registry_status,
            clear_cache,
        )
        from backend.auth.jwt_utils import generate_jwt

        # Clear cache before test
        clear_cache()

        # Generate a real JWT token using the mocked secret
        token = generate_jwt(
            user_id="github|123",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Mock build_registry_status to return test data
        test_status = {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "total_entries": 1,
            "cache_status": "loaded",
            "cache_ttl_seconds": 300,
            "cache_expires_in_seconds": 150,
            "s3_bucket": "test-bucket",
            "s3_key": "content-registry/latest.json",
            "status": "healthy",
        }
        mock_build_status.return_value = test_status

        # First request at time 1000
        mock_time.return_value = 1000.0

        response1 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response1["statusCode"] == 200
        assert mock_get_service.call_count == 1
        assert mock_build_status.call_count == 1

        # Second request at time 1070 (70 seconds later, beyond 60s TTL)
        mock_time.return_value = 1070.0

        response2 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response2["statusCode"] == 200
        # Should be 2 calls - cache expired and refreshed
        assert mock_get_service.call_count == 2
        assert mock_build_status.call_count == 2

    @patch("backend.handlers.admin_registry.build_registry_status")
    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch("backend.handlers.admin_registry.time.time")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_cache_stores_unavailable_status(
        self, mock_time, mock_get_service, mock_build_status
    ):
        """Test that cache stores unavailable status to avoid hammering S3."""
        from backend.handlers.admin_registry import (
            handle_get_registry_status,
            clear_cache,
        )
        from backend.auth.jwt_utils import generate_jwt

        # Clear cache before test
        clear_cache()

        # Generate a real JWT token using the mocked secret
        token = generate_jwt(
            user_id="github|123",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Mock build_registry_status to raise error (registry not loaded)
        mock_build_status.side_effect = ValueError("Registry not loaded")

        # First request at time 1000
        mock_time.return_value = 1000.0

        response1 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response1["statusCode"] == 200
        body1 = json.loads(response1["body"])
        assert body1["status"] == "unavailable"
        assert mock_get_service.call_count == 1
        assert mock_build_status.call_count == 1

        # Second request at time 1030 (30 seconds later, within 60s TTL)
        mock_time.return_value = 1030.0

        response2 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response2["statusCode"] == 200
        body2 = json.loads(response2["body"])
        assert body2["status"] == "unavailable"
        # Should still be 1 call - cached unavailable status was used
        assert mock_get_service.call_count == 1
        assert mock_build_status.call_count == 1

    def test_clear_cache_resets_cache(self):
        """Test that clear_cache resets the cache."""
        from backend.handlers.admin_registry import clear_cache, _registry_status_cache

        # Set cache data
        _registry_status_cache["data"] = {"test": "data"}
        _registry_status_cache["timestamp"] = 1000.0

        # Clear cache
        clear_cache()

        # Verify cache is cleared
        assert _registry_status_cache["data"] is None
        assert _registry_status_cache["timestamp"] is None
