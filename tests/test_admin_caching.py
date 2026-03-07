"""
Performance tests for admin registry status caching behavior.

Tests verify that:
1. Registry status endpoint caches data for 60 seconds
2. Multiple requests within 60 seconds reuse cached data (no additional S3 calls)
3. ContentRegistryService cache is reused across requests
4. Cache expires after 60 seconds and data is refreshed

**Validates: Requirements 11.2, 11.3**
"""

import pytest
import json
import time
from unittest.mock import patch, Mock, MagicMock
from backend.handlers.admin_registry import (
    handle_get_registry_status,
    clear_cache,
    _registry_status_cache,
)


class TestRegistryStatusCaching:
    """Test registry status endpoint caching behavior."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear cache before and after each test."""
        clear_cache()
        yield
        clear_cache()

    @patch("backend.handlers.admin_registry.build_registry_status")
    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch("backend.handlers.admin_registry.time.time")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_cache_reduces_s3_calls_within_60_seconds(
        self, mock_time, mock_get_service, mock_build_status
    ):
        """
        Test that registry status cache reduces S3 calls.

        Verifies that multiple requests within 60 seconds reuse cached data
        without making additional S3 calls through the registry service.

        **Validates: Requirement 11.2**
        """
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(user_id="github|123", username="damienjburks")

        # Mock registry service
        mock_service = Mock()
        mock_service._registry = {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "entries": {"quiz1": {"content_type": "quiz"}},
        }
        mock_service.s3_bucket = "test-bucket"
        mock_service.s3_key = "content-registry/latest.json"
        mock_service.cache_ttl_seconds = 300
        mock_service._last_loaded_at = 1000.0
        mock_get_service.return_value = mock_service

        # Mock build_registry_status
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
        body1 = json.loads(response1["body"])
        assert body1["status"] == "healthy"

        # Verify service was called once
        assert mock_get_service.call_count == 1
        assert mock_build_status.call_count == 1

        # Second request at time 1010 (10 seconds later)
        mock_time.return_value = 1010.0
        response2 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response2["statusCode"] == 200
        body2 = json.loads(response2["body"])
        assert body2["status"] == "healthy"

        # Verify service was NOT called again (cache hit)
        assert mock_get_service.call_count == 1
        assert mock_build_status.call_count == 1

        # Third request at time 1030 (30 seconds later)
        mock_time.return_value = 1030.0
        response3 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response3["statusCode"] == 200
        body3 = json.loads(response3["body"])
        assert body3["status"] == "healthy"

        # Verify service was STILL NOT called again (cache hit)
        assert mock_get_service.call_count == 1
        assert mock_build_status.call_count == 1

        # Fourth request at time 1059 (59 seconds later, just before TTL)
        mock_time.return_value = 1059.0
        response4 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response4["statusCode"] == 200
        body4 = json.loads(response4["body"])
        assert body4["status"] == "healthy"

        # Verify service was STILL NOT called again (cache hit)
        assert mock_get_service.call_count == 1
        assert mock_build_status.call_count == 1

        # Verify all responses are identical
        assert body1 == body2 == body3 == body4

    @patch("backend.handlers.admin_registry.build_registry_status")
    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch("backend.handlers.admin_registry.time.time")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_cache_ttl_of_60_seconds(
        self, mock_time, mock_get_service, mock_build_status
    ):
        """
        Test that cache TTL is exactly 60 seconds.

        Verifies that:
        - Requests within 60 seconds use cache
        - Requests at exactly 60 seconds trigger refresh
        - Requests after 60 seconds trigger refresh

        **Validates: Requirement 11.2**
        """
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(user_id="github|123", username="damienjburks")

        # Mock registry service
        mock_service = Mock()
        mock_service._registry = {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "entries": {"quiz1": {"content_type": "quiz"}},
        }
        mock_service.s3_bucket = "test-bucket"
        mock_service.s3_key = "content-registry/latest.json"
        mock_service.cache_ttl_seconds = 300
        mock_service._last_loaded_at = 1000.0
        mock_get_service.return_value = mock_service

        # Mock build_registry_status
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

        # Request at time 1059 (59 seconds later, within TTL)
        mock_time.return_value = 1059.0
        response2 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response2["statusCode"] == 200
        # Should still be 1 call (cache hit)
        assert mock_get_service.call_count == 1
        assert mock_build_status.call_count == 1

        # Request at time 1060 (exactly 60 seconds later, TTL expired)
        mock_time.return_value = 1060.0
        response3 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response3["statusCode"] == 200
        # Should be 2 calls (cache miss, refresh triggered)
        assert mock_get_service.call_count == 2
        assert mock_build_status.call_count == 2

        # Request at time 1070 (10 seconds after refresh, within new TTL)
        mock_time.return_value = 1070.0
        response4 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response4["statusCode"] == 200
        # Should still be 2 calls (cache hit from new cache)
        assert mock_get_service.call_count == 2
        assert mock_build_status.call_count == 2

        # Request at time 1121 (61 seconds after second cache, TTL expired again)
        mock_time.return_value = 1121.0
        response5 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response5["statusCode"] == 200
        # Should be 3 calls (cache miss, refresh triggered again)
        assert mock_get_service.call_count == 3
        assert mock_build_status.call_count == 3

    @patch("backend.handlers.admin_registry.build_registry_status")
    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch("backend.handlers.admin_registry.time.time")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_content_registry_service_cache_reuse(
        self, mock_time, mock_get_service, mock_build_status
    ):
        """
        Test that ContentRegistryService cache is reused across requests.

        Verifies that the singleton ContentRegistryService instance is reused
        and its internal cache is leveraged, avoiding redundant S3 fetches.

        **Validates: Requirement 11.3**
        """
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(user_id="github|123", username="damienjburks")

        # Create a mock service instance that tracks calls
        mock_service = Mock()
        mock_service._registry = {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "entries": {"quiz1": {"content_type": "quiz"}},
        }
        mock_service.s3_bucket = "test-bucket"
        mock_service.s3_key = "content-registry/latest.json"
        mock_service.cache_ttl_seconds = 300
        mock_service._last_loaded_at = 1000.0

        # Mock get_registry_service to return the same instance
        mock_get_service.return_value = mock_service

        # Mock build_registry_status
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

        # Verify get_registry_service was called
        assert mock_get_service.call_count == 1
        first_call_service = mock_get_service.return_value

        # Second request at time 1030 (within cache TTL)
        mock_time.return_value = 1030.0
        response2 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response2["statusCode"] == 200

        # Verify get_registry_service was NOT called again (cache hit)
        assert mock_get_service.call_count == 1

        # Third request at time 1070 (after cache TTL expires)
        mock_time.return_value = 1070.0
        response3 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response3["statusCode"] == 200

        # Verify get_registry_service was called again (cache miss)
        assert mock_get_service.call_count == 2
        second_call_service = mock_get_service.return_value

        # Verify the same service instance is returned (singleton pattern)
        assert first_call_service is second_call_service

    @patch("backend.handlers.admin_registry.build_registry_status")
    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch("backend.handlers.admin_registry.time.time")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_cache_stores_and_reuses_unavailable_status(
        self, mock_time, mock_get_service, mock_build_status
    ):
        """
        Test that cache stores unavailable status to avoid hammering S3.

        Verifies that when the registry is unavailable, the error status
        is cached for 60 seconds to prevent repeated failed S3 calls.

        **Validates: Requirement 11.2**
        """
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(user_id="github|123", username="damienjburks")

        # Mock build_registry_status to raise error
        mock_build_status.side_effect = ValueError("Registry not loaded")

        # First request at time 1000
        mock_time.return_value = 1000.0
        response1 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response1["statusCode"] == 200
        body1 = json.loads(response1["body"])
        assert body1["status"] == "unavailable"
        assert "error" in body1

        # Verify service was called once
        assert mock_get_service.call_count == 1
        assert mock_build_status.call_count == 1

        # Second request at time 1030 (30 seconds later, within TTL)
        mock_time.return_value = 1030.0
        response2 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response2["statusCode"] == 200
        body2 = json.loads(response2["body"])
        assert body2["status"] == "unavailable"

        # Verify service was NOT called again (cached unavailable status)
        assert mock_get_service.call_count == 1
        assert mock_build_status.call_count == 1

        # Third request at time 1070 (70 seconds later, after TTL)
        mock_time.return_value = 1070.0
        response3 = handle_get_registry_status(headers={"cookie": f"dsb_token={token}"})

        assert response3["statusCode"] == 200
        body3 = json.loads(response3["body"])
        assert body3["status"] == "unavailable"

        # Verify service was called again (cache expired, retry)
        assert mock_get_service.call_count == 2
        assert mock_build_status.call_count == 2

    @patch("backend.handlers.admin_registry.time.time")
    def test_cache_data_structure(self, mock_time):
        """
        Test the internal cache data structure.

        Verifies that the cache stores data, timestamp, and TTL correctly.
        """
        mock_time.return_value = 1000.0

        # Initially cache should be empty
        assert _registry_status_cache["data"] is None
        assert _registry_status_cache["timestamp"] is None
        assert _registry_status_cache["ttl_seconds"] == 60

        # Manually populate cache (simulating a request)
        test_data = {"status": "healthy", "total_entries": 5}
        _registry_status_cache["data"] = test_data
        _registry_status_cache["timestamp"] = 1000.0

        # Verify cache is populated
        assert _registry_status_cache["data"] == test_data
        assert _registry_status_cache["timestamp"] == 1000.0

        # Clear cache
        clear_cache()

        # Verify cache is cleared
        assert _registry_status_cache["data"] is None
        assert _registry_status_cache["timestamp"] is None

    @patch("backend.handlers.admin_registry.build_registry_status")
    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch("backend.handlers.admin_registry.time.time")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_multiple_concurrent_requests_use_same_cache(
        self, mock_time, mock_get_service, mock_build_status
    ):
        """
        Test that multiple concurrent requests within TTL use the same cache.

        Simulates the same admin user making multiple requests and verifies
        they all benefit from the shared cache.

        **Validates: Requirement 11.2**
        """
        from backend.auth.jwt_utils import generate_jwt

        # Generate JWT token for admin (using same user for all requests)
        token1 = generate_jwt(user_id="github|123", username="damienjburks")
        token2 = generate_jwt(user_id="github|123", username="damienjburks")
        token3 = generate_jwt(user_id="github|123", username="damienjburks")

        # Mock registry service
        mock_service = Mock()
        mock_service._registry = {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "entries": {"quiz1": {"content_type": "quiz"}},
        }
        mock_service.s3_bucket = "test-bucket"
        mock_service.s3_key = "content-registry/latest.json"
        mock_service.cache_ttl_seconds = 300
        mock_service._last_loaded_at = 1000.0
        mock_get_service.return_value = mock_service

        # Mock build_registry_status
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

        # First admin request at time 1000
        mock_time.return_value = 1000.0
        response1 = handle_get_registry_status(
            headers={"cookie": f"dsb_token={token1}"}
        )

        assert response1["statusCode"] == 200
        assert mock_get_service.call_count == 1

        # Second admin request at time 1001 (1 second later)
        mock_time.return_value = 1001.0
        response2 = handle_get_registry_status(
            headers={"cookie": f"dsb_token={token2}"}
        )

        assert response2["statusCode"] == 200
        # Should still be 1 call (cache hit)
        assert mock_get_service.call_count == 1

        # Third admin request at time 1002 (2 seconds later)
        mock_time.return_value = 1002.0
        response3 = handle_get_registry_status(
            headers={"cookie": f"dsb_token={token3}"}
        )

        assert response3["statusCode"] == 200
        # Should still be 1 call (cache hit)
        assert mock_get_service.call_count == 1

        # Verify all responses are identical
        body1 = json.loads(response1["body"])
        body2 = json.loads(response2["body"])
        body3 = json.loads(response3["body"])
        assert body1 == body2 == body3


class TestContentRegistryServiceCaching:
    """Test ContentRegistryService internal caching behavior."""

    @patch("backend.services.content_registry.boto3.client")
    def test_registry_service_singleton_pattern(self, mock_boto_client):
        """
        Test that get_registry_service returns singleton instance.

        Verifies that multiple calls to get_registry_service return
        the same instance, ensuring cache reuse.

        **Validates: Requirement 11.3**
        """
        from backend.services.content_registry import (
            get_registry_service,
            _registry_service,
        )

        # Reset singleton
        import backend.services.content_registry as registry_module

        registry_module._registry_service = None

        # Mock S3 client
        mock_s3 = Mock()
        mock_s3.get_object.return_value = {
            "Body": Mock(
                read=lambda: json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "last_updated": "2024-01-15T08:00:00Z",
                        "entries": {},
                    }
                ).encode("utf-8")
            )
        }
        mock_boto_client.return_value = mock_s3

        # First call
        service1 = get_registry_service("test-bucket")
        assert service1 is not None

        # Second call (should return same instance)
        service2 = get_registry_service()
        assert service2 is service1

        # Third call (should return same instance)
        service3 = get_registry_service("test-bucket")
        assert service3 is service1

        # Verify S3 was only called once (during first initialization)
        assert mock_s3.get_object.call_count == 1

        # Reset singleton for other tests
        registry_module._registry_service = None

    @patch("backend.services.content_registry.boto3.client")
    @patch("backend.services.content_registry.time.time")
    def test_registry_service_cache_ttl(self, mock_time, mock_boto_client):
        """
        Test that ContentRegistryService respects cache TTL.

        Verifies that the service's internal cache refreshes after TTL expires.

        **Validates: Requirement 11.3**
        """
        from backend.services.content_registry import ContentRegistryService

        # Mock S3 client
        mock_s3 = Mock()
        mock_s3.get_object.return_value = {
            "Body": Mock(
                read=lambda: json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "last_updated": "2024-01-15T08:00:00Z",
                        "entries": {"quiz1": {"content_type": "quiz"}},
                    }
                ).encode("utf-8")
            )
        }
        mock_boto_client.return_value = mock_s3

        # Create service with 60-second TTL
        mock_time.return_value = 1000.0
        service = ContentRegistryService(s3_bucket="test-bucket", cache_ttl_seconds=60)

        # Verify initial load
        assert service._registry is not None
        assert service._last_loaded_at == 1000.0
        assert mock_s3.get_object.call_count == 1

        # Access entry at time 1030 (within TTL)
        mock_time.return_value = 1030.0
        entry = service.get_entry("quiz1")
        assert entry is not None
        # Should still be 1 S3 call (cache hit)
        assert mock_s3.get_object.call_count == 1

        # Access entry at time 1070 (after TTL expires)
        mock_time.return_value = 1070.0
        entry = service.get_entry("quiz1")
        assert entry is not None
        # Should be 2 S3 calls (cache refresh)
        assert mock_s3.get_object.call_count == 2
        assert service._last_loaded_at == 1070.0
