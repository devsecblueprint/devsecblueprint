"""
Integration tests for admin dashboard data flow from backend to frontend.

Tests the complete data flow for all three admin monitoring sections:
- Capstone submissions: Backend API → Frontend component display
- Registry status: Backend API → Frontend component display with cache info
- Module health: Backend API → Frontend component display with validation metrics

Validates Requirements 4.2, 5.2, 6.2
"""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from backend.handlers.admin_submissions import handle_get_submissions
from backend.handlers.admin_registry import handle_get_registry_status
from backend.handlers.admin_health import handle_get_module_health


class TestCapstoneSubmissionsDataFlow:
    """Test data flow from backend to frontend for capstone submissions."""

    @patch("backend.handlers.admin_submissions.get_capstone_submissions")
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_submissions_display_correctly_in_dashboard(self, mock_get_submissions):
        """
        Test that submissions data flows correctly from backend to frontend.

        Validates Requirement 4.2: Dashboard fetches and displays submission data
        """
        from backend.auth.jwt_utils import generate_jwt

        # Setup: Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock submissions data with all required fields
        mock_submissions = [
            {
                "user_id": "github|11111",
                "github_username": "learner1",
                "repo_url": "https://github.com/learner1/capstone-project",
                "submitted_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            },
            {
                "user_id": "github|22222",
                "github_username": "learner2",
                "repo_url": "https://github.com/learner2/my-capstone",
                "submitted_at": "2024-01-14T15:45:00Z",
                "updated_at": "2024-01-14T15:45:00Z",
            },
            {
                "user_id": "github|33333",
                "github_username": "learner3",
                "repo_url": "https://github.com/learner3/final-project",
                "submitted_at": "2024-01-13T09:20:00Z",
                "updated_at": "2024-01-13T09:20:00Z",
            },
        ]
        mock_get_submissions.return_value = (mock_submissions, 3)

        # Execute: Call backend endpoint
        response = handle_get_submissions(
            headers={"Cookie": f"dsb_token={token}"},
            query_params={"page": "1", "page_size": "50"},
        )

        # Verify: Response is successful
        assert response["statusCode"] == 200

        # Verify: Parse response body (simulating frontend parsing)
        body = json.loads(response["body"])

        # Verify: All required fields are present for frontend display
        assert "submissions" in body
        assert "total_count" in body
        assert body["total_count"] == 3
        assert len(body["submissions"]) == 3

        # Verify: Each submission has all fields needed for frontend display
        for submission in body["submissions"]:
            # Requirement 4.3: Display github_username, repo_url, submitted_at
            assert "github_username" in submission
            assert "repo_url" in submission
            assert "submitted_at" in submission

            # Verify field types for frontend consumption
            assert isinstance(submission["github_username"], str)
            assert isinstance(submission["repo_url"], str)
            assert isinstance(submission["submitted_at"], str)

            # Requirement 4.4: repo_url should be a valid URL for clickable links
            assert submission["repo_url"].startswith("https://github.com/")

            # Requirement 4.5: submitted_at should be ISO 8601 for relative time formatting
            # Verify it can be parsed as a datetime
            datetime.fromisoformat(submission["submitted_at"].replace("Z", "+00:00"))

        # Verify: Submissions are sorted by submitted_at descending (most recent first)
        # Requirement 1.3: Sorted by timestamp descending
        timestamps = [s["submitted_at"] for s in body["submissions"]]
        assert timestamps == sorted(timestamps, reverse=True)

        # Verify: First submission is the most recent
        assert body["submissions"][0]["github_username"] == "learner1"
        assert body["submissions"][0]["submitted_at"] == "2024-01-15T10:30:00Z"

    @patch("backend.handlers.admin_submissions.get_capstone_submissions")
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_empty_submissions_display_correctly(self, mock_get_submissions):
        """
        Test that empty submissions list displays correctly in dashboard.

        Validates Requirement 4.7: Display message when no submissions exist
        """
        from backend.auth.jwt_utils import generate_jwt

        # Setup: Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock empty submissions
        mock_get_submissions.return_value = ([], 0)

        # Execute: Call backend endpoint
        response = handle_get_submissions(
            headers={"Cookie": f"dsb_token={token}"}, query_params={}
        )

        # Verify: Response is successful
        assert response["statusCode"] == 200

        # Verify: Parse response body
        body = json.loads(response["body"])

        # Verify: Empty submissions list
        assert body["submissions"] == []
        assert body["total_count"] == 0

        # Frontend should display "No capstone submissions yet" message
        # This is verified in frontend component tests


class TestRegistryStatusDataFlow:
    """Test data flow from backend to frontend for registry status."""

    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch("backend.handlers.admin_registry.time")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_registry_status_shows_accurate_cache_information(
        self, mock_time, mock_get_registry
    ):
        """
        Test that registry status displays accurate cache information.

        Validates Requirement 5.2: Dashboard fetches and displays registry status
        Validates Requirement 2.6: Include cache TTL and expiry time
        """
        from backend.auth.jwt_utils import generate_jwt

        # Setup: Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock current time
        current_time = 1000.0
        mock_time.time.return_value = current_time

        # Setup: Mock registry service with cache information
        mock_service = Mock()
        mock_service._registry = {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "entries": {
                "module1": {"content_type": "module", "title": "Test Module 1"},
                "module2": {"content_type": "quiz", "title": "Test Quiz 1"},
                "module3": {"content_type": "capstone", "title": "Test Capstone"},
            },
        }
        mock_service.cache_ttl_seconds = 300  # 5 minutes
        mock_service._last_loaded_at = current_time - 120  # Loaded 2 minutes ago
        mock_service.s3_bucket = "test-bucket"
        mock_service.s3_key = "content-registry/latest.json"
        mock_get_registry.return_value = mock_service

        # Execute: Call backend endpoint
        response = handle_get_registry_status(headers={"Cookie": f"dsb_token={token}"})

        # Verify: Response is successful
        assert response["statusCode"] == 200

        # Verify: Parse response body (simulating frontend parsing)
        body = json.loads(response["body"])

        # Verify: All required fields for frontend display are present
        # Requirement 5.3: Display schema_version, last_updated, total_entries
        assert "schema_version" in body
        assert "last_updated" in body
        assert "total_entries" in body
        assert "cache_status" in body
        assert "cache_ttl_seconds" in body
        assert "cache_expires_in_seconds" in body
        assert "s3_bucket" in body
        assert "s3_key" in body
        assert "status" in body

        # Verify: Cache information is accurate
        assert body["schema_version"] == "1.0.0"
        assert body["last_updated"] == "2024-01-15T08:00:00Z"
        assert body["total_entries"] == 3
        assert body["cache_status"] == "loaded"
        assert body["cache_ttl_seconds"] == 300
        assert (
            body["cache_expires_in_seconds"] == 180
        )  # 300 - 120 = 180 seconds remaining
        assert body["s3_bucket"] == "test-bucket"
        assert body["s3_key"] == "content-registry/latest.json"

        # Requirement 5.4: Display cache status indicating registry is loaded and accessible
        assert body["status"] == "healthy"

        # Verify: Frontend can use this data for display
        # - Schema version: "1.0.0"
        # - Last updated: Can be formatted as relative time
        # - Total entries: 3
        # - Cache status: "loaded" (green indicator)
        # - Cache expires in: 180 seconds (3 minutes) - can show countdown

    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_registry_unavailable_displays_error_state(self, mock_get_registry):
        """
        Test that registry unavailable state displays correctly in dashboard.

        Validates Requirement 5.5: Display error indicator when registry unavailable
        """
        from backend.auth.jwt_utils import generate_jwt

        # Setup: Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock registry service that fails to load
        mock_get_registry.side_effect = ValueError(
            "Failed to load registry from S3: NoSuchKey"
        )

        # Execute: Call backend endpoint
        response = handle_get_registry_status(headers={"Cookie": f"dsb_token={token}"})

        # Verify: Response indicates service unavailable
        assert response["statusCode"] == 503

        # Verify: Parse response body
        body = json.loads(response["body"])

        # Verify: Error message is present for frontend display
        assert "error" in body
        assert "Service unavailable" in body["error"]

        # Frontend should display red error indicator with error message
        # Requirement 5.6: Use color coding (red for unavailable)


class TestModuleHealthDataFlow:
    """Test data flow from backend to frontend for module health."""

    @patch("backend.handlers.admin_health.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_module_health_displays_validation_metrics(self, mock_get_registry):
        """
        Test that module health displays validation metrics correctly.

        Validates Requirement 6.2: Dashboard fetches and displays module health data
        Validates Requirement 6.3: Display total modules and validation pass percentage
        Validates Requirement 6.4: Display breakdown by content type
        """
        from backend.auth.jwt_utils import generate_jwt

        # Setup: Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock registry service with various content types
        mock_service = Mock()
        mock_service._registry = {
            "entries": {
                # Quizzes (2 total, 1 with error)
                "quiz1": {
                    "content_type": "quiz",
                    "title": "Test Quiz 1",
                    "description": "Test description",
                    "quiz": {
                        "passing_score": 80,
                        "questions": [{"question": "Test?", "answers": []}],
                    },
                },
                "quiz2": {
                    "content_type": "quiz",
                    "title": "Test Quiz 2",
                    "description": "Test description",
                    "quiz": {
                        "questions": [{"question": "Test?", "answers": []}]
                        # Missing passing_score - validation error
                    },
                },
                # Modules (3 total, all valid)
                "module1": {
                    "content_type": "module",
                    "title": "Test Module 1",
                    "description": "Test description",
                },
                "module2": {
                    "content_type": "module",
                    "title": "Test Module 2",
                    "description": "Test description",
                },
                "module3": {
                    "content_type": "module",
                    "title": "Test Module 3",
                    "description": "Test description",
                },
                # Capstones (1 total, valid)
                "capstone1": {
                    "content_type": "capstone",
                    "title": "Test Capstone",
                    "description": "Test description",
                    "capstone": {"requirements": ["Requirement 1"]},
                },
                # Walkthroughs (1 total, valid)
                "walkthrough1": {
                    "content_type": "walkthrough",
                    "title": "Test Walkthrough",
                    "description": "Test description",
                    "walkthrough": {"steps": ["Step 1"]},
                },
            }
        }
        mock_get_registry.return_value = mock_service

        # Execute: Call backend endpoint
        response = handle_get_module_health(headers={"Cookie": f"dsb_token={token}"})

        # Verify: Response is successful
        assert response["statusCode"] == 200

        # Verify: Parse response body (simulating frontend parsing)
        body = json.loads(response["body"])

        # Verify: All required fields for frontend display are present
        assert "total_modules" in body
        assert "validation_pass_percentage" in body
        assert "content_by_type" in body
        assert "validation_errors" in body
        assert "status" in body

        # Verify: Total modules count
        # Requirement 6.3: Display total module count
        assert body["total_modules"] == 7

        # Verify: Content type breakdown
        # Requirement 6.4: Display breakdown by type
        assert body["content_by_type"]["quiz"] == 2
        assert body["content_by_type"]["module"] == 3
        assert body["content_by_type"]["capstone"] == 1
        assert body["content_by_type"]["walkthrough"] == 1

        # Verify: Validation errors
        # Requirement 6.5: Display validation errors with module_id and error_message
        assert len(body["validation_errors"]) == 1
        error = body["validation_errors"][0]
        assert "module_id" in error
        assert "error_type" in error
        assert "error_message" in error
        assert error["module_id"] == "quiz2"

        # Verify: Validation pass percentage
        # Requirement 3.6: Calculate percentage of modules with passing validation
        # 6 passing out of 7 total = 85.71% (rounded to 85.7 by backend)
        expected_percentage = 85.7
        assert body["validation_pass_percentage"] == expected_percentage

        # Verify: Status for frontend color coding
        # Requirement 6.6: Color coding based on percentage
        # 85.71% is < 90%, so should be "error" (red)
        assert body["status"] == "error"

        # Frontend should display:
        # - Total modules: 7
        # - Validation pass percentage: 85.7% (red color)
        # - Content breakdown: Quiz: 2, Module: 3, Capstone: 1, Walkthrough: 1
        # - Validation errors: 1 error for quiz2

    @patch("backend.handlers.admin_health.get_registry_service")
    @patch.dict(
        "os.environ",
        {"CONTENT_BUCKET": "test-bucket", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_module_health_with_all_passing_validation(self, mock_get_registry):
        """
        Test that module health displays correctly when all modules pass validation.

        Validates Requirement 6.6: Green color coding for 100% passing
        """
        from backend.auth.jwt_utils import generate_jwt

        # Setup: Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock registry service with all valid modules
        mock_service = Mock()
        mock_service._registry = {
            "entries": {
                "module1": {
                    "content_type": "module",
                    "title": "Test Module 1",
                    "description": "Test description",
                },
                "module2": {
                    "content_type": "module",
                    "title": "Test Module 2",
                    "description": "Test description",
                },
            }
        }
        mock_get_registry.return_value = mock_service

        # Execute: Call backend endpoint
        response = handle_get_module_health(headers={"Cookie": f"dsb_token={token}"})

        # Verify: Response is successful
        assert response["statusCode"] == 200

        # Verify: Parse response body
        body = json.loads(response["body"])

        # Verify: 100% validation pass rate
        assert body["validation_pass_percentage"] == 100.0
        assert len(body["validation_errors"]) == 0
        assert body["status"] == "healthy"

        # Frontend should display green color for 100% passing


class TestDataFlowErrorHandling:
    """Test error handling in data flow from backend to frontend."""

    @patch("backend.handlers.admin_submissions.get_capstone_submissions")
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_submissions_error_displays_correctly(self, mock_get_submissions):
        """
        Test that submission fetch errors display correctly in dashboard.

        Validates Requirement 10.4: Display error message on failure
        """
        from backend.auth.jwt_utils import generate_jwt

        # Setup: Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock DynamoDB failure
        mock_get_submissions.side_effect = Exception("DynamoDB connection failed")

        # Execute: Call backend endpoint
        response = handle_get_submissions(
            headers={"Cookie": f"dsb_token={token}"}, query_params={}
        )

        # Verify: Response indicates error
        assert response["statusCode"] == 500

        # Verify: Parse response body
        body = json.loads(response["body"])

        # Verify: Error message is present for frontend display
        assert "error" in body

        # Frontend should display error message with retry button
        # Requirement 10.6: Provide retry button for transient errors


class TestCompleteDataFlowIntegration:
    """Test complete data flow for all three sections together."""

    @patch("backend.handlers.admin_submissions.get_capstone_submissions")
    @patch("backend.handlers.admin_registry.get_registry_service")
    @patch("backend.handlers.admin_health.get_registry_service")
    @patch("backend.handlers.admin_registry.time")
    @patch.dict(
        "os.environ",
        {
            "PROGRESS_TABLE": "test-progress-table",
            "CONTENT_BUCKET": "test-bucket",
            "JWT_SECRET_NAME": "test-jwt-secret",
        },
    )
    def test_all_three_sections_display_data_correctly(
        self,
        mock_time,
        mock_health_registry,
        mock_status_registry,
        mock_get_submissions,
    ):
        """
        Test that all three dashboard sections display data correctly together.

        Simulates the complete dashboard load with parallel data fetching.
        Validates Requirements 4.2, 5.2, 6.2, 11.4
        """
        from backend.auth.jwt_utils import generate_jwt

        # Setup: Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )
        headers = {"Cookie": f"dsb_token={token}"}

        # Setup: Mock submissions data
        mock_get_submissions.return_value = (
            [
                {
                    "user_id": "github|11111",
                    "github_username": "learner1",
                    "repo_url": "https://github.com/learner1/capstone",
                    "submitted_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                }
            ],
            1,
        )

        # Setup: Mock registry status
        mock_time.time.return_value = 1000.0
        mock_status_service = Mock()
        mock_status_service._registry = {
            "schema_version": "1.0.0",
            "last_updated": "2024-01-15T08:00:00Z",
            "entries": {"module1": {"content_type": "module"}},
        }
        mock_status_service.cache_ttl_seconds = 300
        mock_status_service._last_loaded_at = 900.0
        mock_status_service.s3_bucket = "test-bucket"
        mock_status_service.s3_key = "content-registry/latest.json"
        mock_status_registry.return_value = mock_status_service

        # Setup: Mock module health
        mock_health_service = Mock()
        mock_health_service._registry = {
            "entries": {
                "module1": {
                    "content_type": "module",
                    "title": "Test Module",
                    "description": "Test description",
                }
            }
        }
        mock_health_registry.return_value = mock_health_service

        # Execute: Call all three endpoints (simulating parallel fetch)
        submissions_response = handle_get_submissions(headers=headers, query_params={})
        registry_response = handle_get_registry_status(headers=headers)
        health_response = handle_get_module_health(headers=headers)

        # Verify: All responses are successful
        assert submissions_response["statusCode"] == 200
        assert registry_response["statusCode"] == 200
        assert health_response["statusCode"] == 200

        # Verify: Parse all response bodies
        submissions_body = json.loads(submissions_response["body"])
        registry_body = json.loads(registry_response["body"])
        health_body = json.loads(health_response["body"])

        # Verify: Submissions data is complete
        assert len(submissions_body["submissions"]) == 1
        assert submissions_body["total_count"] == 1

        # Verify: Registry status data is complete
        assert registry_body["schema_version"] == "1.0.0"
        assert registry_body["status"] == "healthy"
        assert registry_body["cache_status"] == "loaded"

        # Verify: Module health data is complete
        assert health_body["total_modules"] == 1
        assert health_body["validation_pass_percentage"] == 100.0
        assert len(health_body["validation_errors"]) == 0

        # This simulates the frontend receiving all three responses
        # and displaying them in their respective dashboard sections
        # Requirement 11.4: Parallel data fetching
