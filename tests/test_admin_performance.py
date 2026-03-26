"""
Performance tests for admin endpoints.

Tests that all admin endpoints respond within 2 seconds under normal load.
Validates Requirement 11.6
"""

import pytest
import time
from unittest.mock import Mock, patch
from backend.handlers.admin_submissions import handle_get_submissions
from backend.handlers.admin_registry import handle_get_registry_status
from backend.handlers.admin_health import handle_get_module_health


class TestAdminEndpointPerformance:
    """Test response times for admin endpoints."""

    @patch("backend.handlers.admin_submissions.boto3")
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_submissions_endpoint_response_time(self, mock_boto3):
        """Test that submissions endpoint responds within 2 seconds."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock DynamoDB response with realistic data
        mock_dynamodb = Mock()
        mock_boto3.client.return_value = mock_dynamodb

        # Create 50 mock submissions (default page size)
        mock_items = []
        for i in range(50):
            mock_items.append(
                {
                    "PK": {"S": f"USER#github|{12345 + i}"},
                    "SK": {"S": f"CAPSTONE_SUBMISSION#capstone-{i}"},
                    "github_username": {"S": f"learner{i}"},
                    "repo_url": {"S": f"https://github.com/learner{i}/capstone"},
                    "submitted_at": {"S": f"2024-01-{15 + (i % 15):02d}T10:30:00Z"},
                    "updated_at": {"S": f"2024-01-{15 + (i % 15):02d}T10:30:00Z"},
                }
            )

        mock_dynamodb.scan.return_value = {"Items": mock_items, "Count": 50}

        # Execute and measure time
        start_time = time.time()
        response = handle_get_submissions(headers={"Cookie": f"dsb_token={token}"})
        elapsed_time = time.time() - start_time

        # Verify: Response is successful
        assert response["statusCode"] == 200

        # Verify: Response time is under 2 seconds
        assert elapsed_time < 2.0, f"Response took {elapsed_time:.3f}s, expected < 2.0s"

        print(f"✓ Submissions endpoint responded in {elapsed_time:.3f}s")

    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_registry_status_endpoint_response_time(self, mock_get_registry):
        """Test that registry status endpoint responds within 2 seconds."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock registry service with realistic data
        mock_service = Mock()
        mock_service._registry = {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "entries": {f"module-{i}": {"title": f"Module {i}"} for i in range(156)},
        }
        mock_service.cache_ttl_seconds = 300
        mock_service._last_loaded_at = time.time() - 120  # Loaded 2 minutes ago
        mock_service.s3_bucket = "test-bucket"
        mock_service.s3_key = "content-registry/latest.json"
        mock_get_registry.return_value = mock_service

        # Clear cache to ensure fresh request
        from backend.handlers.admin_registry import clear_cache

        clear_cache()

        # Execute and measure time
        start_time = time.time()
        response = handle_get_registry_status(headers={"Cookie": f"dsb_token={token}"})
        elapsed_time = time.time() - start_time

        # Verify: Response is successful
        assert response["statusCode"] == 200

        # Verify: Response time is under 2 seconds
        assert elapsed_time < 2.0, f"Response took {elapsed_time:.3f}s, expected < 2.0s"

        print(f"✓ Registry status endpoint responded in {elapsed_time:.3f}s")

    @patch("backend.handlers.admin_health.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_module_health_endpoint_response_time(self, mock_get_registry):
        """Test that module health endpoint responds within 2 seconds."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock registry service with realistic data (156 modules)
        mock_entries = {}
        for i in range(156):
            content_type = ["quiz", "module", "capstone", "walkthrough"][i % 4]
            mock_entries[f"topic-{i}"] = {
                "content_type": content_type,
                "title": f"Test {content_type.title()} {i}",
                "description": f"Description for {content_type} {i}",
            }

            # Add content-type specific fields
            if content_type == "quiz":
                mock_entries[f"topic-{i}"]["quiz"] = {
                    "passing_score": 80,
                    "questions": [{"question": "Test?", "answer": "Yes"}],
                }
            elif content_type == "walkthrough":
                mock_entries[f"topic-{i}"]["walkthrough"] = {"steps": []}
            elif content_type == "capstone":
                mock_entries[f"topic-{i}"]["capstone"] = {"requirements": []}

        mock_service = Mock()
        mock_service._registry = {"entries": mock_entries}
        mock_get_registry.return_value = mock_service

        # Execute and measure time
        start_time = time.time()
        response = handle_get_module_health(headers={"Cookie": f"dsb_token={token}"})
        elapsed_time = time.time() - start_time

        # Verify: Response is successful
        assert response["statusCode"] == 200

        # Verify: Response time is under 2 seconds
        assert elapsed_time < 2.0, f"Response took {elapsed_time:.3f}s, expected < 2.0s"

        print(f"✓ Module health endpoint responded in {elapsed_time:.3f}s")

    @patch("backend.handlers.admin_submissions.boto3")
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
    def test_all_endpoints_respond_within_2_seconds(
        self, mock_health_registry, mock_status_registry, mock_boto3
    ):
        """Test that all three admin endpoints respond within 2 seconds."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock DynamoDB for submissions
        mock_dynamodb = Mock()
        mock_boto3.client.return_value = mock_dynamodb
        mock_items = []
        for i in range(50):
            mock_items.append(
                {
                    "PK": {"S": f"USER#github|{12345 + i}"},
                    "SK": {"S": f"CAPSTONE_SUBMISSION#capstone-{i}"},
                    "github_username": {"S": f"learner{i}"},
                    "repo_url": {"S": f"https://github.com/learner{i}/capstone"},
                    "submitted_at": {"S": f"2024-01-{15 + (i % 15):02d}T10:30:00Z"},
                    "updated_at": {"S": f"2024-01-{15 + (i % 15):02d}T10:30:00Z"},
                }
            )
        mock_dynamodb.scan.return_value = {"Items": mock_items, "Count": 50}

        # Setup: Mock registry service for status
        mock_status_service = Mock()
        mock_status_service._registry = {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "entries": {f"module-{i}": {"title": f"Module {i}"} for i in range(156)},
        }
        mock_status_service.cache_ttl_seconds = 300
        mock_status_service._last_loaded_at = time.time() - 120
        mock_status_service.s3_bucket = "test-bucket"
        mock_status_service.s3_key = "content-registry/latest.json"
        mock_status_registry.return_value = mock_status_service

        # Setup: Mock registry service for health
        mock_entries = {}
        for i in range(156):
            content_type = ["quiz", "module", "capstone", "walkthrough"][i % 4]
            mock_entries[f"topic-{i}"] = {
                "content_type": content_type,
                "title": f"Test {content_type.title()} {i}",
                "description": f"Description for {content_type} {i}",
            }
            if content_type == "quiz":
                mock_entries[f"topic-{i}"]["quiz"] = {
                    "passing_score": 80,
                    "questions": [{"question": "Test?"}],
                }
        mock_health_service = Mock()
        mock_health_service._registry = {"entries": mock_entries}
        mock_health_registry.return_value = mock_health_service

        # Clear registry cache
        from backend.handlers.admin_registry import clear_cache

        clear_cache()

        # Test each endpoint
        endpoints = [
            (
                "submissions",
                lambda: handle_get_submissions(
                    headers={"Cookie": f"dsb_token={token}"}
                ),
            ),
            (
                "registry-status",
                lambda: handle_get_registry_status(
                    headers={"Cookie": f"dsb_token={token}"}
                ),
            ),
            (
                "module-health",
                lambda: handle_get_module_health(
                    headers={"Cookie": f"dsb_token={token}"}
                ),
            ),
        ]

        results = []
        for endpoint_name, handler in endpoints:
            start_time = time.time()
            response = handler()
            elapsed_time = time.time() - start_time

            # Verify response is successful
            assert (
                response["statusCode"] == 200
            ), f"{endpoint_name} returned {response['statusCode']}"

            # Verify response time
            assert (
                elapsed_time < 2.0
            ), f"{endpoint_name} took {elapsed_time:.3f}s, expected < 2.0s"

            results.append((endpoint_name, elapsed_time))
            print(f"✓ {endpoint_name} responded in {elapsed_time:.3f}s")

        # Summary
        total_time = sum(t for _, t in results)
        avg_time = total_time / len(results)
        print(f"\n✓ All endpoints passed performance requirements")
        print(f"  Average response time: {avg_time:.3f}s")
        print(f"  Total sequential time: {total_time:.3f}s")
