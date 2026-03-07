"""
Property-based tests for DynamoDB quiz-related functions.

Feature: module-quiz-system
"""

import os
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings
from backend.services.dynamo import (
    get_module_completion,
    save_module_completion,
    get_streak_data,
    update_streak_data,
)

# Strategies for generating test data
user_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip() != "")

module_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_",
    min_size=1,
    max_size=100,
).filter(lambda x: x.strip() != "" and not x.startswith("-") and not x.endswith("-"))

score_strategy = st.integers(min_value=0, max_value=100)

date_strategy = st.dates().map(lambda d: d.isoformat())


class TestModuleCompletionProperties:
    """Property-based tests for module completion functions."""

    @settings(max_examples=100)
    @given(user_id=user_id_strategy, module_id=module_id_strategy)
    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_property_28_completion_record_key_format(
        self, mock_boto_client, user_id, module_id
    ):
        """
        Property 28: Completion Record Key Format

        For any module completion record in DynamoDB, the PK should match the format
        "USER#<user_id>" and the SK should match the format "MODULE#<module_id>".

        **Validates: Requirements 10.2, 10.3**
        """
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Mock DynamoDB response
        mock_dynamodb.get_item.return_value = {
            "Item": {
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": f"MODULE#{module_id}"},
                "score": {"N": "85"},
                "first_completed_at": {"S": "2024-01-15T10:00:00+00:00"},
                "completed_at": {"S": "2024-01-20T15:30:00+00:00"},
            }
        }

        # Call get_module_completion
        get_module_completion(user_id, module_id)

        # Verify the key format used in the query
        call_args = mock_dynamodb.get_item.call_args
        key = call_args.kwargs["Key"]

        # Verify PK format: "USER#<user_id>"
        assert key["PK"]["S"] == f"USER#{user_id}"
        assert key["PK"]["S"].startswith("USER#")

        # Verify SK format: "MODULE#<module_id>"
        assert key["SK"]["S"] == f"MODULE#{module_id}"
        assert key["SK"]["S"].startswith("MODULE#")

    @settings(max_examples=100)
    @given(user_id=user_id_strategy, module_id=module_id_strategy, score=score_strategy)
    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_property_28_save_completion_key_format(
        self, mock_boto_client, user_id, module_id, score
    ):
        """
        Property 28: Completion Record Key Format (Save Operation)

        For any module completion save operation, the stored record should use
        PK format "USER#<user_id>" and SK format "MODULE#<module_id>".

        **Validates: Requirements 10.2, 10.3**
        """
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Save first completion
        save_module_completion(user_id, module_id, score, is_first_completion=True)

        # Verify the key format used in put_item
        call_args = mock_dynamodb.put_item.call_args
        item = call_args.kwargs["Item"]

        # Verify PK format: "USER#<user_id>"
        assert item["PK"]["S"] == f"USER#{user_id}"
        assert item["PK"]["S"].startswith("USER#")

        # Verify SK format: "MODULE#<module_id>"
        assert item["SK"]["S"] == f"MODULE#{module_id}"
        assert item["SK"]["S"].startswith("MODULE#")


class TestStreakDataProperties:
    """Property-based tests for streak tracking functions."""

    @settings(max_examples=100)
    @given(user_id=user_id_strategy)
    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_property_29_streak_record_key_format(self, mock_boto_client, user_id):
        """
        Property 29: Streak Record Key Format

        For any streak record in DynamoDB, the PK should match the format
        "USER#<user_id>" and the SK should equal "STREAK".

        **Validates: Requirements 10.4**
        """
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Mock DynamoDB response
        mock_dynamodb.get_item.return_value = {
            "Item": {
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "STREAK"},
                "current_streak": {"N": "5"},
                "longest_streak": {"N": "10"},
                "last_activity_date": {"S": "2024-01-15"},
            }
        }

        # Call get_streak_data
        get_streak_data(user_id)

        # Verify the key format used in the query
        call_args = mock_dynamodb.get_item.call_args
        key = call_args.kwargs["Key"]

        # Verify PK format: "USER#<user_id>"
        assert key["PK"]["S"] == f"USER#{user_id}"
        assert key["PK"]["S"].startswith("USER#")

        # Verify SK is exactly "STREAK"
        assert key["SK"]["S"] == "STREAK"

    @settings(max_examples=100)
    @given(
        user_id=user_id_strategy,
        current_streak=st.integers(min_value=0, max_value=1000),
        longest_streak=st.integers(min_value=0, max_value=1000),
        last_activity_date=date_strategy,
    )
    @patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"})
    @patch("backend.services.dynamo.boto3.client")
    def test_property_29_update_streak_key_format(
        self,
        mock_boto_client,
        user_id,
        current_streak,
        longest_streak,
        last_activity_date,
    ):
        """
        Property 29: Streak Record Key Format (Update Operation)

        For any streak update operation, the stored record should use
        PK format "USER#<user_id>" and SK "STREAK".

        **Validates: Requirements 10.4**
        """
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Update streak data
        update_streak_data(user_id, current_streak, longest_streak, last_activity_date)

        # Verify the key format used in put_item
        call_args = mock_dynamodb.put_item.call_args
        item = call_args.kwargs["Item"]

        # Verify PK format: "USER#<user_id>"
        assert item["PK"]["S"] == f"USER#{user_id}"
        assert item["PK"]["S"].startswith("USER#")

        # Verify SK is exactly "STREAK"
        assert item["SK"]["S"] == "STREAK"
