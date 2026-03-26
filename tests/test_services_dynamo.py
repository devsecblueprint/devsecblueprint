"""
Unit tests for DynamoDB service.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from botocore.exceptions import ClientError

from backend.services.dynamo import save_progress


class TestSaveProgress:
    """Tests for save_progress function."""

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_progress_success(self, mock_boto_client):
        """Test successful progress save."""
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        user_id = "12345678"
        content_id = "secure-sdlc/intro"

        save_progress(user_id, content_id)

        # Verify put_item was called
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args

        # Verify table name
        assert call_args.kwargs["TableName"] == "test-progress-table"

        # Verify item structure
        item = call_args.kwargs["Item"]
        assert item["PK"]["S"] == f"USER#{user_id}"
        assert item["SK"]["S"] == f"CONTENT#{content_id}"
        assert item["status"]["S"] == "complete"
        assert "completed_at" in item
        assert item["completed_at"]["S"]  # Should have ISO 8601 timestamp

        # Verify timestamp is valid ISO 8601
        timestamp = item["completed_at"]["S"]
        datetime.fromisoformat(timestamp)  # Should not raise

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_progress_formats_pk_sk_correctly(self, mock_boto_client):
        """Test that PK and SK are formatted with correct prefixes."""
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        user_id = "87654321"
        content_id = "api-security/basics"

        save_progress(user_id, content_id)

        call_args = mock_dynamodb.put_item.call_args
        item = call_args.kwargs["Item"]

        assert item["PK"]["S"] == "USER#87654321"
        assert item["SK"]["S"] == "CONTENT#api-security/basics"

    @patch.dict(os.environ, {}, clear=True)
    def test_save_progress_missing_table_name(self):
        """Test error when PROGRESS_TABLE environment variable is missing."""
        with pytest.raises(Exception) as exc_info:
            save_progress("12345", "content/test")

        assert "PROGRESS_TABLE environment variable not set" in str(exc_info.value)

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_progress_dynamodb_error(self, mock_boto_client):
        """Test error handling when DynamoDB operation fails."""
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Simulate DynamoDB error
        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_dynamodb.put_item.side_effect = ClientError(error_response, "PutItem")

        with pytest.raises(Exception) as exc_info:
            save_progress("12345", "content/test")

        assert "Failed to save progress to DynamoDB" in str(exc_info.value)
        assert "ResourceNotFoundException" in str(exc_info.value)

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_progress_timestamp_is_recent(self, mock_boto_client):
        """Test that completed_at timestamp is current."""
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        before = datetime.now(timezone.utc)
        save_progress("12345", "content/test")
        after = datetime.now(timezone.utc)

        call_args = mock_dynamodb.put_item.call_args
        item = call_args.kwargs["Item"]
        timestamp_str = item["completed_at"]["S"]
        timestamp = datetime.fromisoformat(timestamp_str)

        # Timestamp should be between before and after
        assert before <= timestamp <= after


class TestGetStreakData:
    """Tests for get_streak_data function."""

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_get_streak_data_success(self, mock_boto_client):
        """Test successful streak data retrieval."""
        from backend.services.dynamo import get_streak_data

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Mock DynamoDB response
        mock_dynamodb.get_item.return_value = {
            "Item": {
                "PK": {"S": "USER#12345"},
                "SK": {"S": "STREAK"},
                "current_streak": {"N": "5"},
                "longest_streak": {"N": "10"},
                "last_activity_date": {"S": "2024-01-15"},
            }
        }

        result = get_streak_data("12345")

        # Verify get_item was called correctly
        mock_dynamodb.get_item.assert_called_once()
        call_args = mock_dynamodb.get_item.call_args
        assert call_args.kwargs["TableName"] == "test-progress-table"
        assert call_args.kwargs["Key"]["PK"]["S"] == "USER#12345"
        assert call_args.kwargs["Key"]["SK"]["S"] == "STREAK"

        # Verify returned data
        assert result["current_streak"] == 5
        assert result["longest_streak"] == 10
        assert result["last_activity_date"] == "2024-01-15"

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_get_streak_data_no_record(self, mock_boto_client):
        """Test default values returned when no streak record exists."""
        from backend.services.dynamo import get_streak_data

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Mock DynamoDB response with no item
        mock_dynamodb.get_item.return_value = {}

        result = get_streak_data("12345")

        # Verify default values
        assert result["current_streak"] == 0
        assert result["longest_streak"] == 0
        assert result["last_activity_date"] is None

    @patch.dict(os.environ, {}, clear=True)
    def test_get_streak_data_missing_table_name(self):
        """Test error when PROGRESS_TABLE environment variable is missing."""
        from backend.services.dynamo import get_streak_data

        with pytest.raises(Exception) as exc_info:
            get_streak_data("12345")

        assert "PROGRESS_TABLE environment variable not set" in str(exc_info.value)

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_get_streak_data_dynamodb_error(self, mock_boto_client):
        """Test error handling when DynamoDB operation fails."""
        from backend.services.dynamo import get_streak_data

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Simulate DynamoDB error
        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_dynamodb.get_item.side_effect = ClientError(error_response, "GetItem")

        with pytest.raises(Exception) as exc_info:
            get_streak_data("12345")

        assert "Failed to get streak data from DynamoDB" in str(exc_info.value)
        assert "ResourceNotFoundException" in str(exc_info.value)


class TestUpdateStreakData:
    """Tests for update_streak_data function."""

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_update_streak_data_success(self, mock_boto_client):
        """Test successful streak data update."""
        from backend.services.dynamo import update_streak_data

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        user_id = "12345"
        current_streak = 7
        longest_streak = 15
        last_activity_date = "2024-01-20"

        update_streak_data(user_id, current_streak, longest_streak, last_activity_date)

        # Verify put_item was called
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args

        # Verify table name
        assert call_args.kwargs["TableName"] == "test-progress-table"

        # Verify item structure
        item = call_args.kwargs["Item"]
        assert item["PK"]["S"] == "USER#12345"
        assert item["SK"]["S"] == "STREAK"
        assert item["current_streak"]["N"] == "7"
        assert item["longest_streak"]["N"] == "15"
        assert item["last_activity_date"]["S"] == "2024-01-20"

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_update_streak_data_formats_keys_correctly(self, mock_boto_client):
        """Test that PK and SK are formatted correctly."""
        from backend.services.dynamo import update_streak_data

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        update_streak_data("87654321", 3, 8, "2024-02-01")

        call_args = mock_dynamodb.put_item.call_args
        item = call_args.kwargs["Item"]

        assert item["PK"]["S"] == "USER#87654321"
        assert item["SK"]["S"] == "STREAK"

    @patch.dict(os.environ, {}, clear=True)
    def test_update_streak_data_missing_table_name(self):
        """Test error when PROGRESS_TABLE environment variable is missing."""
        from backend.services.dynamo import update_streak_data

        with pytest.raises(Exception) as exc_info:
            update_streak_data("12345", 1, 1, "2024-01-01")

        assert "PROGRESS_TABLE environment variable not set" in str(exc_info.value)

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_update_streak_data_dynamodb_error(self, mock_boto_client):
        """Test error handling when DynamoDB operation fails."""
        from backend.services.dynamo import update_streak_data

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Simulate DynamoDB error
        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_dynamodb.put_item.side_effect = ClientError(error_response, "PutItem")

        with pytest.raises(Exception) as exc_info:
            update_streak_data("12345", 1, 1, "2024-01-01")

        assert "Failed to update streak data in DynamoDB" in str(exc_info.value)
        assert "ResourceNotFoundException" in str(exc_info.value)

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_update_streak_data_date_format(self, mock_boto_client):
        """Test that date is stored in YYYY-MM-DD format."""
        from backend.services.dynamo import update_streak_data

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        update_streak_data("12345", 1, 1, "2024-12-31")

        call_args = mock_dynamodb.put_item.call_args
        item = call_args.kwargs["Item"]

        # Verify date format
        date_str = item["last_activity_date"]["S"]
        assert date_str == "2024-12-31"
        # Verify it's a valid date format
        from datetime import datetime

        datetime.strptime(date_str, "%Y-%m-%d")  # Should not raise


class TestGetModuleCompletion:
    """Tests for get_module_completion function."""

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_get_module_completion_success(self, mock_boto_client):
        """Test successful module completion retrieval."""
        from backend.services.dynamo import get_module_completion

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Mock DynamoDB response
        mock_dynamodb.get_item.return_value = {
            "Item": {
                "PK": {"S": "USER#12345"},
                "SK": {"S": "MODULE#secure-sdlc"},
                "score": {"N": "85"},
                "first_completed_at": {"S": "2024-01-15T10:00:00+00:00"},
                "completed_at": {"S": "2024-01-20T15:30:00+00:00"},
            }
        }

        result = get_module_completion("12345", "secure-sdlc")

        # Verify get_item was called correctly
        mock_dynamodb.get_item.assert_called_once()
        call_args = mock_dynamodb.get_item.call_args
        assert call_args.kwargs["TableName"] == "test-progress-table"
        assert call_args.kwargs["Key"]["PK"]["S"] == "USER#12345"
        assert call_args.kwargs["Key"]["SK"]["S"] == "MODULE#secure-sdlc"

        # Verify returned data
        assert result["score"] == 85
        assert result["first_completed_at"] == "2024-01-15T10:00:00+00:00"
        assert result["completed_at"] == "2024-01-20T15:30:00+00:00"

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_get_module_completion_not_found(self, mock_boto_client):
        """Test None returned when module completion record doesn't exist."""
        from backend.services.dynamo import get_module_completion

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Mock DynamoDB response with no item
        mock_dynamodb.get_item.return_value = {}

        result = get_module_completion("12345", "nonexistent-module")

        # Verify None is returned
        assert result is None

    @patch.dict(os.environ, {}, clear=True)
    def test_get_module_completion_missing_table_name(self):
        """Test error when PROGRESS_TABLE environment variable is missing."""
        from backend.services.dynamo import get_module_completion

        with pytest.raises(Exception) as exc_info:
            get_module_completion("12345", "module-id")

        assert "PROGRESS_TABLE environment variable not set" in str(exc_info.value)

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_get_module_completion_dynamodb_error(self, mock_boto_client):
        """Test error handling when DynamoDB operation fails."""
        from backend.services.dynamo import get_module_completion

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Simulate DynamoDB error
        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_dynamodb.get_item.side_effect = ClientError(error_response, "GetItem")

        with pytest.raises(Exception) as exc_info:
            get_module_completion("12345", "module-id")

        assert "Failed to get module completion from DynamoDB" in str(exc_info.value)
        assert "ResourceNotFoundException" in str(exc_info.value)


class TestSaveModuleCompletion:
    """Tests for save_module_completion function."""

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_module_completion_first_completion(self, mock_boto_client):
        """Test saving first completion sets all fields."""
        from backend.services.dynamo import save_module_completion

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        user_id = "12345"
        module_id = "secure-sdlc"
        score = 85

        save_module_completion(user_id, module_id, score, is_first_completion=True)

        # Verify put_item was called
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args

        # Verify table name
        assert call_args.kwargs["TableName"] == "test-progress-table"

        # Verify item structure
        item = call_args.kwargs["Item"]
        assert item["PK"]["S"] == "USER#12345"
        assert item["SK"]["S"] == "MODULE#secure-sdlc"
        assert item["score"]["N"] == "85"
        assert "first_completed_at" in item
        assert "completed_at" in item
        # Both timestamps should be the same for first completion
        assert item["first_completed_at"]["S"] == item["completed_at"]["S"]

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    @patch("backend.services.dynamo.get_module_completion")
    def test_save_module_completion_recompletion_higher_score(
        self, mock_get_completion, mock_boto_client
    ):
        """Test re-completion with higher score updates score and completed_at."""
        from backend.services.dynamo import save_module_completion

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Mock existing completion with lower score
        mock_get_completion.return_value = {
            "score": 70,
            "first_completed_at": "2024-01-15T10:00:00+00:00",
            "completed_at": "2024-01-15T10:00:00+00:00",
        }

        user_id = "12345"
        module_id = "secure-sdlc"
        new_score = 90

        save_module_completion(user_id, module_id, new_score, is_first_completion=False)

        # Verify update_item was called (not put_item)
        mock_dynamodb.update_item.assert_called_once()
        call_args = mock_dynamodb.update_item.call_args

        # Verify table name and key
        assert call_args.kwargs["TableName"] == "test-progress-table"
        assert call_args.kwargs["Key"]["PK"]["S"] == "USER#12345"
        assert call_args.kwargs["Key"]["SK"]["S"] == "MODULE#secure-sdlc"

        # Verify update expression includes both score and completed_at
        assert "score" in call_args.kwargs["UpdateExpression"]
        assert "completed_at" in call_args.kwargs["UpdateExpression"]
        assert call_args.kwargs["ExpressionAttributeValues"][":score"]["N"] == "90"

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    @patch("backend.services.dynamo.get_module_completion")
    def test_save_module_completion_recompletion_lower_score(
        self, mock_get_completion, mock_boto_client
    ):
        """Test re-completion with lower score only updates completed_at."""
        from backend.services.dynamo import save_module_completion

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Mock existing completion with higher score
        mock_get_completion.return_value = {
            "score": 95,
            "first_completed_at": "2024-01-15T10:00:00+00:00",
            "completed_at": "2024-01-15T10:00:00+00:00",
        }

        user_id = "12345"
        module_id = "secure-sdlc"
        new_score = 80

        save_module_completion(user_id, module_id, new_score, is_first_completion=False)

        # Verify update_item was called
        mock_dynamodb.update_item.assert_called_once()
        call_args = mock_dynamodb.update_item.call_args

        # Verify update expression only includes completed_at (not score)
        update_expr = call_args.kwargs["UpdateExpression"]
        assert "completed_at" in update_expr
        assert "score" not in update_expr
        # Verify only completed_at in attribute values
        assert ":completed_at" in call_args.kwargs["ExpressionAttributeValues"]
        assert ":score" not in call_args.kwargs["ExpressionAttributeValues"]

    @patch.dict(os.environ, {}, clear=True)
    def test_save_module_completion_missing_table_name(self):
        """Test error when PROGRESS_TABLE environment variable is missing."""
        from backend.services.dynamo import save_module_completion

        with pytest.raises(Exception) as exc_info:
            save_module_completion("12345", "module-id", 85, True)

        assert "PROGRESS_TABLE environment variable not set" in str(exc_info.value)

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_module_completion_dynamodb_error(self, mock_boto_client):
        """Test error handling when DynamoDB operation fails."""
        from backend.services.dynamo import save_module_completion

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Simulate DynamoDB error
        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_dynamodb.put_item.side_effect = ClientError(error_response, "PutItem")

        with pytest.raises(Exception) as exc_info:
            save_module_completion("12345", "module-id", 85, True)

        assert "Failed to save module completion to DynamoDB" in str(exc_info.value)
        assert "ResourceNotFoundException" in str(exc_info.value)


class TestGetWalkthroughProgress:
    """Tests for get_walkthrough_progress function."""

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_get_walkthrough_progress_success(self, mock_boto_client):
        """Test successful walkthrough progress retrieval."""
        from backend.services.dynamo import get_walkthrough_progress

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Mock DynamoDB response
        mock_dynamodb.get_item.return_value = {
            "Item": {
                "PK": {"S": "USER#12345"},
                "SK": {"S": "WALKTHROUGH#secure-cicd-pipeline"},
                "status": {"S": "in_progress"},
                "started_at": {"S": "2024-01-15T10:00:00+00:00"},
            }
        }

        result = get_walkthrough_progress("12345", "secure-cicd-pipeline")

        # Verify get_item was called correctly
        mock_dynamodb.get_item.assert_called_once()
        call_args = mock_dynamodb.get_item.call_args
        assert call_args.kwargs["TableName"] == "test-progress-table"
        assert call_args.kwargs["Key"]["PK"]["S"] == "USER#12345"
        assert call_args.kwargs["Key"]["SK"]["S"] == "WALKTHROUGH#secure-cicd-pipeline"

        # Verify returned data
        assert result["status"] == "in_progress"
        assert result["started_at"] == "2024-01-15T10:00:00+00:00"
        assert result["completed_at"] is None

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_get_walkthrough_progress_completed(self, mock_boto_client):
        """Test retrieving completed walkthrough progress."""
        from backend.services.dynamo import get_walkthrough_progress

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Mock DynamoDB response with completed status
        mock_dynamodb.get_item.return_value = {
            "Item": {
                "PK": {"S": "USER#12345"},
                "SK": {"S": "WALKTHROUGH#secure-cicd-pipeline"},
                "status": {"S": "completed"},
                "started_at": {"S": "2024-01-15T10:00:00+00:00"},
                "completed_at": {"S": "2024-01-20T15:30:00+00:00"},
            }
        }

        result = get_walkthrough_progress("12345", "secure-cicd-pipeline")

        # Verify returned data includes completed_at
        assert result["status"] == "completed"
        assert result["started_at"] == "2024-01-15T10:00:00+00:00"
        assert result["completed_at"] == "2024-01-20T15:30:00+00:00"

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_get_walkthrough_progress_not_found(self, mock_boto_client):
        """Test None returned when walkthrough progress record doesn't exist."""
        from backend.services.dynamo import get_walkthrough_progress

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Mock DynamoDB response with no item
        mock_dynamodb.get_item.return_value = {}

        result = get_walkthrough_progress("12345", "nonexistent-walkthrough")

        # Verify None is returned
        assert result is None

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_get_walkthrough_progress_formats_keys_correctly(self, mock_boto_client):
        """Test that PK and SK are formatted with correct prefixes."""
        from backend.services.dynamo import get_walkthrough_progress

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        mock_dynamodb.get_item.return_value = {
            "Item": {
                "PK": {"S": "USER#87654321"},
                "SK": {"S": "WALKTHROUGH#container-security"},
                "status": {"S": "in_progress"},
                "started_at": {"S": "2024-01-15T10:00:00+00:00"},
            }
        }

        get_walkthrough_progress("87654321", "container-security")

        call_args = mock_dynamodb.get_item.call_args
        assert call_args.kwargs["Key"]["PK"]["S"] == "USER#87654321"
        assert call_args.kwargs["Key"]["SK"]["S"] == "WALKTHROUGH#container-security"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_walkthrough_progress_missing_table_name(self):
        """Test error when PROGRESS_TABLE environment variable is missing."""
        from backend.services.dynamo import get_walkthrough_progress

        with pytest.raises(Exception) as exc_info:
            get_walkthrough_progress("12345", "walkthrough-id")

        assert "PROGRESS_TABLE environment variable not set" in str(exc_info.value)

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_get_walkthrough_progress_dynamodb_error(self, mock_boto_client):
        """Test error handling when DynamoDB operation fails."""
        from backend.services.dynamo import get_walkthrough_progress

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Simulate DynamoDB error
        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_dynamodb.get_item.side_effect = ClientError(error_response, "GetItem")

        with pytest.raises(Exception) as exc_info:
            get_walkthrough_progress("12345", "walkthrough-id")

        assert "Failed to get walkthrough progress from DynamoDB" in str(exc_info.value)
        assert "ResourceNotFoundException" in str(exc_info.value)


class TestSaveWalkthroughProgress:
    """Tests for save_walkthrough_progress function."""

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_walkthrough_progress_in_progress(self, mock_boto_client):
        """Test saving walkthrough progress with in_progress status."""
        from backend.services.dynamo import save_walkthrough_progress

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        user_id = "12345"
        walkthrough_id = "secure-cicd-pipeline"
        status = "in_progress"
        started_at = "2024-01-15T10:00:00+00:00"

        save_walkthrough_progress(
            user_id, walkthrough_id, status, started_at=started_at
        )

        # Verify put_item was called
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args

        # Verify table name
        assert call_args.kwargs["TableName"] == "test-progress-table"

        # Verify item structure
        item = call_args.kwargs["Item"]
        assert item["PK"]["S"] == "USER#12345"
        assert item["SK"]["S"] == "WALKTHROUGH#secure-cicd-pipeline"
        assert item["status"]["S"] == "in_progress"
        assert item["started_at"]["S"] == "2024-01-15T10:00:00+00:00"
        assert "completed_at" not in item

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_walkthrough_progress_completed(self, mock_boto_client):
        """Test saving walkthrough progress with completed status."""
        from backend.services.dynamo import save_walkthrough_progress

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        user_id = "12345"
        walkthrough_id = "secure-cicd-pipeline"
        status = "completed"
        started_at = "2024-01-15T10:00:00+00:00"
        completed_at = "2024-01-20T15:30:00+00:00"

        save_walkthrough_progress(
            user_id,
            walkthrough_id,
            status,
            started_at=started_at,
            completed_at=completed_at,
        )

        # Verify put_item was called
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args

        # Verify item structure includes completed_at
        item = call_args.kwargs["Item"]
        assert item["PK"]["S"] == "USER#12345"
        assert item["SK"]["S"] == "WALKTHROUGH#secure-cicd-pipeline"
        assert item["status"]["S"] == "completed"
        assert item["started_at"]["S"] == "2024-01-15T10:00:00+00:00"
        assert item["completed_at"]["S"] == "2024-01-20T15:30:00+00:00"

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_walkthrough_progress_formats_keys_correctly(self, mock_boto_client):
        """Test that PK and SK are formatted with correct prefixes."""
        from backend.services.dynamo import save_walkthrough_progress

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        save_walkthrough_progress(
            "87654321",
            "container-security",
            "in_progress",
            started_at="2024-01-15T10:00:00+00:00",
        )

        call_args = mock_dynamodb.put_item.call_args
        item = call_args.kwargs["Item"]

        assert item["PK"]["S"] == "USER#87654321"
        assert item["SK"]["S"] == "WALKTHROUGH#container-security"

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_walkthrough_progress_without_timestamps(self, mock_boto_client):
        """Test saving walkthrough progress without optional timestamps."""
        from backend.services.dynamo import save_walkthrough_progress

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        save_walkthrough_progress("12345", "walkthrough-id", "not_started")

        call_args = mock_dynamodb.put_item.call_args
        item = call_args.kwargs["Item"]

        # Verify only required fields are present
        assert item["PK"]["S"] == "USER#12345"
        assert item["SK"]["S"] == "WALKTHROUGH#walkthrough-id"
        assert item["status"]["S"] == "not_started"
        assert "started_at" not in item
        assert "completed_at" not in item

    @patch.dict(os.environ, {}, clear=True)
    def test_save_walkthrough_progress_missing_table_name(self):
        """Test error when PROGRESS_TABLE environment variable is missing."""
        from backend.services.dynamo import save_walkthrough_progress

        with pytest.raises(Exception) as exc_info:
            save_walkthrough_progress("12345", "walkthrough-id", "in_progress")

        assert "PROGRESS_TABLE environment variable not set" in str(exc_info.value)

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_walkthrough_progress_dynamodb_error(self, mock_boto_client):
        """Test error handling when DynamoDB operation fails."""
        from backend.services.dynamo import save_walkthrough_progress

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Simulate DynamoDB error
        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_dynamodb.put_item.side_effect = ClientError(error_response, "PutItem")

        with pytest.raises(Exception) as exc_info:
            save_walkthrough_progress("12345", "walkthrough-id", "in_progress")

        assert "Failed to save walkthrough progress to DynamoDB" in str(exc_info.value)
        assert "ResourceNotFoundException" in str(exc_info.value)

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_walkthrough_progress_status_transitions(self, mock_boto_client):
        """Test different status transitions."""
        from backend.services.dynamo import save_walkthrough_progress

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Test not_started -> in_progress
        save_walkthrough_progress(
            "12345",
            "walkthrough-id",
            "in_progress",
            started_at="2024-01-15T10:00:00+00:00",
        )
        item = mock_dynamodb.put_item.call_args.kwargs["Item"]
        assert item["status"]["S"] == "in_progress"
        assert "started_at" in item
        assert "completed_at" not in item

        # Test in_progress -> completed
        save_walkthrough_progress(
            "12345",
            "walkthrough-id",
            "completed",
            started_at="2024-01-15T10:00:00+00:00",
            completed_at="2024-01-20T15:30:00+00:00",
        )
        item = mock_dynamodb.put_item.call_args.kwargs["Item"]
        assert item["status"]["S"] == "completed"
        assert "started_at" in item
        assert "completed_at" in item


class TestSaveCapstoneSubmission:
    """Tests for save_capstone_submission function."""

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_capstone_submission_success(self, mock_boto_client):
        """Test successful capstone submission save."""
        from backend.services.dynamo import save_capstone_submission

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        user_id = "github|12345678"
        content_id = "devsecops-capstone"
        repo_url = "https://github.com/testuser/my-project"
        github_username = "testuser"
        repo_name = "my-project"

        save_capstone_submission(
            user_id, content_id, repo_url, github_username, repo_name
        )

        # Verify put_item was called
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args

        # Verify table name
        assert call_args.kwargs["TableName"] == "test-progress-table"

        # Verify item structure
        item = call_args.kwargs["Item"]
        assert item["PK"]["S"] == f"USER#{user_id}"
        assert item["SK"]["S"] == f"CAPSTONE_SUBMISSION#{content_id}"
        assert item["repo_url"]["S"] == repo_url
        assert item["github_username"]["S"] == github_username
        assert item["repo_name"]["S"] == repo_name
        assert "submitted_at" in item
        assert "updated_at" in item
        assert item["submitted_at"]["S"]  # Should have ISO 8601 timestamp
        assert item["updated_at"]["S"]  # Should have ISO 8601 timestamp

        # Verify timestamps are valid ISO 8601
        datetime.fromisoformat(item["submitted_at"]["S"])
        datetime.fromisoformat(item["updated_at"]["S"])

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_capstone_submission_formats_pk_sk_correctly(self, mock_boto_client):
        """Test that PK and SK are formatted with correct prefixes."""
        from backend.services.dynamo import save_capstone_submission

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        user_id = "github|87654321"
        content_id = "python-capstone"

        save_capstone_submission(
            user_id,
            content_id,
            "https://github.com/user/repo",
            "user",
            "repo",
        )

        call_args = mock_dynamodb.put_item.call_args
        item = call_args.kwargs["Item"]

        assert item["PK"]["S"] == "USER#github|87654321"
        assert item["SK"]["S"] == "CAPSTONE_SUBMISSION#python-capstone"

    @patch.dict(os.environ, {}, clear=True)
    def test_save_capstone_submission_missing_table_name(self):
        """Test error when PROGRESS_TABLE environment variable is missing."""
        from backend.services.dynamo import save_capstone_submission

        with pytest.raises(Exception) as exc_info:
            save_capstone_submission(
                "user123", "capstone", "https://github.com/user/repo", "user", "repo"
            )

        assert "PROGRESS_TABLE environment variable not set" in str(exc_info.value)

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_capstone_submission_dynamodb_error(self, mock_boto_client):
        """Test error handling when DynamoDB operation fails."""
        from backend.services.dynamo import save_capstone_submission

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Simulate DynamoDB error
        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_dynamodb.put_item.side_effect = ClientError(error_response, "PutItem")

        with pytest.raises(Exception) as exc_info:
            save_capstone_submission(
                "user123", "capstone", "https://github.com/user/repo", "user", "repo"
            )

        assert "Failed to save capstone submission to DynamoDB" in str(exc_info.value)
        assert "ResourceNotFoundException" in str(exc_info.value)

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_capstone_submission_timestamp_is_recent(self, mock_boto_client):
        """Test that submitted_at and updated_at timestamps are current."""
        from backend.services.dynamo import save_capstone_submission

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        before = datetime.now(timezone.utc)
        save_capstone_submission(
            "user123", "capstone", "https://github.com/user/repo", "user", "repo"
        )
        after = datetime.now(timezone.utc)

        call_args = mock_dynamodb.put_item.call_args
        item = call_args.kwargs["Item"]

        submitted_at = datetime.fromisoformat(item["submitted_at"]["S"])
        updated_at = datetime.fromisoformat(item["updated_at"]["S"])

        # Timestamps should be between before and after
        assert before <= submitted_at <= after
        assert before <= updated_at <= after

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_save_capstone_submission_all_fields_present(self, mock_boto_client):
        """Test that all required fields are included in the DynamoDB item."""
        from backend.services.dynamo import save_capstone_submission

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        save_capstone_submission(
            "user123",
            "capstone",
            "https://github.com/testuser/test-repo",
            "testuser",
            "test-repo",
        )

        call_args = mock_dynamodb.put_item.call_args
        item = call_args.kwargs["Item"]

        # Verify all required fields are present
        required_fields = [
            "PK",
            "SK",
            "repo_url",
            "github_username",
            "repo_name",
            "submitted_at",
            "updated_at",
        ]
        for field in required_fields:
            assert field in item, f"Missing required field: {field}"


class TestGetCapstoneSubmission:
    """Tests for get_capstone_submission function."""

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_get_capstone_submission_success(self, mock_boto_client):
        """Test successful capstone submission retrieval."""
        from backend.services.dynamo import get_capstone_submission

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Mock DynamoDB response
        mock_dynamodb.get_item.return_value = {
            "Item": {
                "PK": {"S": "USER#user123"},
                "SK": {"S": "CAPSTONE_SUBMISSION#capstone"},
                "repo_url": {"S": "https://github.com/testuser/test-repo"},
                "github_username": {"S": "testuser"},
                "repo_name": {"S": "test-repo"},
                "submitted_at": {"S": "2024-01-15T10:30:00Z"},
                "updated_at": {"S": "2024-01-15T10:30:00Z"},
            }
        }

        result = get_capstone_submission("user123", "capstone")

        # Verify get_item was called with correct parameters
        mock_dynamodb.get_item.assert_called_once()
        call_args = mock_dynamodb.get_item.call_args
        assert call_args.kwargs["Key"]["PK"]["S"] == "USER#user123"
        assert call_args.kwargs["Key"]["SK"]["S"] == "CAPSTONE_SUBMISSION#capstone"

        # Verify returned data
        assert result is not None
        assert result["repo_url"] == "https://github.com/testuser/test-repo"
        assert result["github_username"] == "testuser"
        assert result["repo_name"] == "test-repo"
        assert result["submitted_at"] == "2024-01-15T10:30:00Z"
        assert result["updated_at"] == "2024-01-15T10:30:00Z"

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_get_capstone_submission_not_found(self, mock_boto_client):
        """Test None returned when capstone submission doesn't exist."""
        from backend.services.dynamo import get_capstone_submission

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Mock DynamoDB response with no item
        mock_dynamodb.get_item.return_value = {}

        result = get_capstone_submission("user123", "capstone")

        assert result is None

    @patch.dict(os.environ, {}, clear=True)
    def test_get_capstone_submission_missing_table_name(self):
        """Test error when PROGRESS_TABLE environment variable is missing."""
        from backend.services.dynamo import get_capstone_submission

        with pytest.raises(Exception) as exc_info:
            get_capstone_submission("user123", "capstone")

        assert "PROGRESS_TABLE environment variable not set" in str(exc_info.value)

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_get_capstone_submission_dynamodb_error(self, mock_boto_client):
        """Test error handling when DynamoDB operation fails."""
        from backend.services.dynamo import get_capstone_submission
        from botocore.exceptions import ClientError

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Mock DynamoDB error
        mock_dynamodb.get_item.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable"}}, "GetItem"
        )

        with pytest.raises(Exception) as exc_info:
            get_capstone_submission("user123", "capstone")

        assert "Failed to get capstone submission from DynamoDB" in str(exc_info.value)


class TestGetAllRegisteredUsers:
    """Tests for get_all_registered_users function."""

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_returns_gitlab_username_and_provider(self, mock_boto_client):
        """Test that returned user dicts include gitlab_username and provider fields."""
        from backend.services.dynamo import get_all_registered_users

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        mock_dynamodb.scan.return_value = {
            "Items": [
                {
                    "PK": {"S": "USER#123"},
                    "SK": {"S": "PROFILE"},
                    "username": {"S": "testuser"},
                    "github_username": {"S": "ghuser"},
                    "gitlab_username": {"S": "gluser"},
                    "provider": {"S": "gitlab"},
                    "avatar_url": {"S": "https://example.com/avatar.png"},
                    "registered_at": {"S": "2024-01-15T10:30:00Z"},
                    "last_login": {"S": "2024-03-25T08:00:00Z"},
                }
            ]
        }

        users = get_all_registered_users()

        assert len(users) == 1
        user = users[0]
        assert user["gitlab_username"] == "gluser"
        assert user["provider"] == "gitlab"
        assert user["github_username"] == "ghuser"
        assert user["user_id"] == "123"

    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_provider_defaults_to_github_when_missing(self, mock_boto_client):
        """Test that provider defaults to 'github' when not present in DynamoDB item."""
        from backend.services.dynamo import get_all_registered_users

        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Item without provider or gitlab_username attributes
        mock_dynamodb.scan.return_value = {
            "Items": [
                {
                    "PK": {"S": "USER#456"},
                    "SK": {"S": "PROFILE"},
                    "username": {"S": "olduser"},
                    "github_username": {"S": "oldghuser"},
                    "avatar_url": {"S": "https://example.com/old.png"},
                    "registered_at": {"S": "2023-06-01T00:00:00Z"},
                    "last_login": {"S": "2023-12-01T00:00:00Z"},
                }
            ]
        }

        users = get_all_registered_users()

        assert len(users) == 1
        user = users[0]
        assert user["provider"] == "github"
        assert user["gitlab_username"] == ""
