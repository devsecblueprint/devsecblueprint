"""
Unit tests for admin walkthrough statistics functionality.

Tests the get_all_walkthrough_progress, get_walkthrough_statistics,
and handle_get_walkthrough_statistics functions.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from backend.handlers.admin_walkthrough_stats import (
    handle_get_walkthrough_statistics,
    log_error,
)
from backend.services.progress_service import get_walkthrough_statistics
from backend.services.dynamo import get_all_walkthrough_progress


class TestGetAllWalkthroughProgress:
    """Test the get_all_walkthrough_progress function."""

    @patch("backend.services.dynamo.boto3.client")
    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    def test_scans_for_walkthrough_records(self, mock_boto3_client):
        """Test that function scans DynamoDB for WALKTHROUGH# records."""
        mock_dynamodb = Mock()
        mock_boto3_client.return_value = mock_dynamodb

        # Mock scan response
        mock_dynamodb.scan.return_value = {
            "Items": [
                {
                    "PK": {"S": "USER#github|12345"},
                    "SK": {"S": "WALKTHROUGH#stripe-integration"},
                    "status": {"S": "completed"},
                    "started_at": {"S": "2024-01-15T10:30:00Z"},
                    "completed_at": {"S": "2024-01-16T14:20:00Z"},
                }
            ]
        }

        result = get_all_walkthrough_progress()

        # Verify scan was called with correct parameters
        mock_dynamodb.scan.assert_called_once()
        call_args = mock_dynamodb.scan.call_args[1]
        assert call_args["TableName"] == "test-progress-table"
        assert "FilterExpression" in call_args
        assert (
            call_args["ExpressionAttributeValues"][":sk_prefix"]["S"] == "WALKTHROUGH#"
        )

        # Verify result
        assert len(result) == 1
        assert result[0]["user_id"] == "github|12345"
        assert result[0]["walkthrough_id"] == "stripe-integration"
        assert result[0]["status"] == "completed"

    @patch("backend.services.dynamo.boto3.client")
    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    def test_handles_pagination(self, mock_boto3_client):
        """Test that function handles pagination with LastEvaluatedKey."""
        mock_dynamodb = Mock()
        mock_boto3_client.return_value = mock_dynamodb

        # Mock paginated responses
        mock_dynamodb.scan.side_effect = [
            {
                "Items": [
                    {
                        "PK": {"S": "USER#user1"},
                        "SK": {"S": "WALKTHROUGH#wt1"},
                        "status": {"S": "completed"},
                        "started_at": {"S": "2024-01-15T10:30:00Z"},
                    }
                ],
                "LastEvaluatedKey": {
                    "PK": {"S": "USER#user1"},
                    "SK": {"S": "WALKTHROUGH#wt1"},
                },
            },
            {
                "Items": [
                    {
                        "PK": {"S": "USER#user2"},
                        "SK": {"S": "WALKTHROUGH#wt2"},
                        "status": {"S": "in_progress"},
                        "started_at": {"S": "2024-01-16T10:30:00Z"},
                    }
                ]
            },
        ]

        result = get_all_walkthrough_progress()

        # Verify scan was called twice (pagination)
        assert mock_dynamodb.scan.call_count == 2
        assert len(result) == 2

    @patch.dict(os.environ, {}, clear=True)
    def test_raises_error_when_table_name_missing(self):
        """Test that function raises error when PROGRESS_TABLE env var is missing."""
        with pytest.raises(
            Exception, match="PROGRESS_TABLE environment variable not set"
        ):
            get_all_walkthrough_progress()


class TestGetWalkthroughStatistics:
    """Test the get_walkthrough_statistics function."""

    @patch("services.dynamo.get_all_walkthrough_progress")
    def test_calculates_completed_count(self, mock_get_all):
        """Test that function correctly counts completed walkthroughs."""
        mock_get_all.return_value = [
            {"user_id": "user1", "walkthrough_id": "wt1", "status": "completed"},
            {"user_id": "user2", "walkthrough_id": "wt2", "status": "completed"},
            {"user_id": "user3", "walkthrough_id": "wt3", "status": "in_progress"},
        ]

        result = get_walkthrough_statistics()

        assert result["completed_count"] == 2

    @patch("services.dynamo.get_all_walkthrough_progress")
    def test_calculates_in_progress_count(self, mock_get_all):
        """Test that function correctly counts in-progress walkthroughs."""
        mock_get_all.return_value = [
            {"user_id": "user1", "walkthrough_id": "wt1", "status": "completed"},
            {"user_id": "user2", "walkthrough_id": "wt2", "status": "in_progress"},
            {"user_id": "user3", "walkthrough_id": "wt3", "status": "in_progress"},
        ]

        result = get_walkthrough_statistics()

        assert result["in_progress_count"] == 2

    @patch("services.dynamo.get_all_walkthrough_progress")
    def test_identifies_most_popular_walkthrough(self, mock_get_all):
        """Test that function identifies walkthrough with highest combined count."""
        mock_get_all.return_value = [
            {"user_id": "user1", "walkthrough_id": "wt1", "status": "completed"},
            {"user_id": "user2", "walkthrough_id": "wt1", "status": "in_progress"},
            {"user_id": "user3", "walkthrough_id": "wt2", "status": "completed"},
        ]

        result = get_walkthrough_statistics()

        # wt1 has 2 records (1 completed + 1 in_progress)
        # wt2 has 1 record (1 completed)
        assert result["most_popular_walkthrough"] == "wt1"

    @patch("services.dynamo.get_all_walkthrough_progress")
    def test_applies_alphabetical_tie_breaking(self, mock_get_all):
        """Test that function applies alphabetical tie-breaking for equal popularity."""
        mock_get_all.return_value = [
            {"user_id": "user1", "walkthrough_id": "zebra", "status": "completed"},
            {"user_id": "user2", "walkthrough_id": "apple", "status": "completed"},
        ]

        result = get_walkthrough_statistics()

        # Both have 1 record, should return alphabetically first
        assert result["most_popular_walkthrough"] == "apple"

    @patch("services.dynamo.get_all_walkthrough_progress")
    def test_returns_none_for_empty_data(self, mock_get_all):
        """Test that function returns None for most_popular when no data exists."""
        mock_get_all.return_value = []

        result = get_walkthrough_statistics()

        assert result["completed_count"] == 0
        assert result["in_progress_count"] == 0
        assert result["most_popular_walkthrough"] is None


class TestHandleGetWalkthroughStatistics:
    """Test the handle_get_walkthrough_statistics handler."""

    @patch(
        "backend.handlers.admin_walkthrough_stats.progress_service.get_walkthrough_statistics"
    )
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_returns_200_with_statistics(self, mock_get_stats):
        """Test that handler returns 200 with statistics data."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(user_id="github|12345", username="damienjburks")

        mock_get_stats.return_value = {
            "completed_count": 5,
            "in_progress_count": 3,
            "most_popular_walkthrough": "stripe-integration",
        }

        response = handle_get_walkthrough_statistics(
            headers={"Cookie": f"dsb_token={token}"}
        )

        assert response["statusCode"] == 200
        assert "application/json" in response["headers"]["Content-Type"]

        import json

        body = json.loads(response["body"])
        assert body["completed_count"] == 5
        assert body["in_progress_count"] == 3
        assert body["most_popular_walkthrough"] == "stripe-integration"

    @patch(
        "backend.handlers.admin_walkthrough_stats.progress_service.get_walkthrough_statistics"
    )
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_returns_503_for_table_not_found(self, mock_get_stats):
        """Test that handler returns 503 when DynamoDB table not found."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(user_id="github|12345", username="damienjburks")

        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_get_stats.side_effect = ClientError(error_response, "Scan")

        response = handle_get_walkthrough_statistics(
            headers={"Cookie": f"dsb_token={token}"}
        )

        assert response["statusCode"] == 503

    @patch(
        "backend.handlers.admin_walkthrough_stats.progress_service.get_walkthrough_statistics"
    )
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_returns_500_for_unexpected_error(self, mock_get_stats):
        """Test that handler returns 500 for unexpected errors."""
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(user_id="github|12345", username="damienjburks")

        mock_get_stats.side_effect = Exception("Unexpected error")

        response = handle_get_walkthrough_statistics(
            headers={"Cookie": f"dsb_token={token}"}
        )

        assert response["statusCode"] == 500


class TestLogError:
    """Test the log_error function."""

    @patch("backend.handlers.admin_walkthrough_stats.logger")
    def test_logs_error_with_all_fields(self, mock_logger):
        """Test that log_error creates structured log entry."""
        log_error(
            endpoint="test_endpoint",
            error_type="TestError",
            error_message="Test error message",
            username="test_admin",
            user_id="github|12345",
            error_code="ResourceNotFoundException",
            context={"table": "test-table"},
        )

        # Verify logger.error was called
        assert mock_logger.error.called

        # Get the call arguments
        call_args = mock_logger.error.call_args

        # Check the message
        assert "test_endpoint" in call_args[0][0]
        assert "TestError" in call_args[0][0]

        # Check the extra dict
        extra = call_args[1]["extra"]
        assert extra["event"] == "admin_endpoint_error"
        assert extra["endpoint"] == "test_endpoint"
        assert extra["error_type"] == "TestError"
        assert extra["error_message"] == "Test error message"
        assert extra["username"] == "test_admin"
        assert extra["user_id"] == "github|12345"
        assert extra["error_code"] == "ResourceNotFoundException"
        assert extra["context"]["table"] == "test-table"
        assert "timestamp" in extra
        assert "stack_trace" in extra
