"""
Tests for Content Registry Service dataclasses and basic functionality.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, BotoCoreError
from backend.services.content_registry import (
    ContentRegistryEntry,
    QuizValidationResult,
    ContentRegistryService,
    SchemaVersionError,
    get_registry_service,
)


class TestContentRegistryDataclasses:
    """Test the dataclasses used by Content Registry Service."""

    def test_content_registry_entry_creation(self):
        """Test creating a ContentRegistryEntry with all required fields."""
        entry = ContentRegistryEntry(
            content_type="quiz",
            topic_slug="what_is_the_secure_sdlc",
            module_id="devsecops/what_is_the_secure_sdlc",
            data={"passing_score": 80, "question_count": 10, "questions": []},
        )

        assert entry.content_type == "quiz"
        assert entry.topic_slug == "what_is_the_secure_sdlc"
        assert entry.module_id == "devsecops/what_is_the_secure_sdlc"
        assert entry.data["passing_score"] == 80
        assert entry.data["question_count"] == 10

    def test_quiz_validation_result_creation(self):
        """Test creating a QuizValidationResult with all required fields."""
        result = QuizValidationResult(
            score=85.0,
            passed=True,
            correct_count=17,
            total_count=20,
            per_question={"q1": True, "q2": True, "q3": False, "q4": True},
        )

        assert result.score == 85.0
        assert result.passed is True
        assert result.correct_count == 17
        assert result.total_count == 20
        assert len(result.per_question) == 4
        assert result.per_question["q1"] is True
        assert result.per_question["q3"] is False

    def test_quiz_validation_result_failed(self):
        """Test creating a QuizValidationResult for a failed quiz."""
        result = QuizValidationResult(
            score=65.0,
            passed=False,
            correct_count=13,
            total_count=20,
            per_question={"q1": True, "q2": False},
        )

        assert result.score == 65.0
        assert result.passed is False
        assert result.correct_count == 13
        assert result.total_count == 20


class TestContentRegistryService:
    """Test the ContentRegistryService initialization and S3 loading."""

    @patch("backend.services.content_registry.boto3.client")
    def test_service_initialization_loads_registry(self, mock_boto_client):
        """Test that ContentRegistryService loads registry from S3 on initialization."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 80,
                    "question_count": 5,
                    "questions": [],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        # Initialize service
        service = ContentRegistryService(
            s3_bucket="test-bucket", s3_key="content-registry/latest.json"
        )

        # Verify S3 was called
        mock_s3.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="content-registry/latest.json"
        )

        # Verify registry was loaded
        assert service._registry is not None
        assert service._registry["schema_version"] == "1.0.0"
        assert "test_quiz" in service._registry["entries"]

    @patch("backend.services.content_registry.boto3.client")
    def test_service_initialization_with_defaults(self, mock_boto_client):
        """Test that ContentRegistryService uses default s3_key."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {},
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")

        assert service.s3_bucket == "test-bucket"
        assert service.s3_key == "content-registry/latest.json"

        # Verify default key was used
        mock_s3.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="content-registry/latest.json"
        )

    @patch("backend.services.content_registry.boto3.client")
    def test_service_handles_s3_not_found_error(self, mock_boto_client):
        """Test that service raises exception when registry not found in S3."""
        # Mock S3 client error
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        error_response = {
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist.",
            }
        }
        mock_s3.get_object.side_effect = ClientError(error_response, "GetObject")

        # Should raise exception
        with pytest.raises(ClientError) as exc_info:
            ContentRegistryService(s3_bucket="test-bucket")

        assert exc_info.value.response["Error"]["Code"] == "NoSuchKey"

    @patch("backend.services.content_registry.boto3.client")
    def test_service_handles_s3_access_denied_error(self, mock_boto_client):
        """Test that service raises exception when S3 access is denied."""
        # Mock S3 client error
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}
        mock_s3.get_object.side_effect = ClientError(error_response, "GetObject")

        # Should raise exception
        with pytest.raises(ClientError) as exc_info:
            ContentRegistryService(s3_bucket="test-bucket")

        assert exc_info.value.response["Error"]["Code"] == "AccessDenied"

    @patch("backend.services.content_registry.boto3.client")
    def test_service_handles_malformed_json(self, mock_boto_client):
        """Test that service raises exception when registry JSON is malformed."""
        # Mock S3 response with invalid JSON
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        mock_response = {"Body": Mock(read=Mock(return_value=b"{ invalid json }"))}
        mock_s3.get_object.return_value = mock_response

        # Should raise JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            ContentRegistryService(s3_bucket="test-bucket")

    @patch("backend.services.content_registry.boto3.client")
    def test_service_handles_botocore_error(self, mock_boto_client):
        """Test that service raises exception on BotoCore errors."""
        # Mock BotoCore error
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        mock_s3.get_object.side_effect = BotoCoreError()

        # Should raise BotoCoreError
        with pytest.raises(BotoCoreError):
            ContentRegistryService(s3_bucket="test-bucket")

    @patch("backend.services.content_registry.boto3.client")
    def test_registry_cached_in_memory(self, mock_boto_client):
        """Test that registry is cached in memory after loading."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {},
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")

        # Verify registry is cached
        assert service._registry is not None
        assert service._registry == registry_data

        # Verify S3 was only called once (during initialization)
        assert mock_s3.get_object.call_count == 1

    @patch("backend.services.content_registry.boto3.client")
    def test_service_validates_schema_version(self, mock_boto_client):
        """Test that service validates schema version on load."""
        # Mock S3 response with valid schema version
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {},
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        # Should not raise exception
        service = ContentRegistryService(s3_bucket="test-bucket")
        assert service._registry["schema_version"] == "1.0.0"

    @patch("backend.services.content_registry.boto3.client")
    def test_service_rejects_missing_schema_version(self, mock_boto_client):
        """Test that service raises error when schema_version is missing."""
        # Mock S3 response without schema_version
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {},
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        # Should raise SchemaVersionError
        with pytest.raises(SchemaVersionError) as exc_info:
            ContentRegistryService(s3_bucket="test-bucket")

        assert "missing schema_version field" in str(exc_info.value)

    @patch("backend.services.content_registry.boto3.client")
    def test_service_rejects_incompatible_major_version(self, mock_boto_client):
        """Test that service raises error when major version is incompatible."""
        # Mock S3 response with incompatible major version
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "2.0.0",  # Incompatible major version
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {},
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        # Should raise SchemaVersionError
        with pytest.raises(SchemaVersionError) as exc_info:
            ContentRegistryService(s3_bucket="test-bucket")

        assert "Incompatible registry schema version" in str(exc_info.value)
        assert "Expected: 1.0.0" in str(exc_info.value)
        assert "Actual: 2.0.0" in str(exc_info.value)

    @patch("backend.services.content_registry.boto3.client")
    def test_service_accepts_compatible_minor_version(self, mock_boto_client):
        """Test that service accepts different minor/patch versions with same major version."""
        # Mock S3 response with different minor version
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.2.3",  # Different minor/patch but same major
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {},
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        # Should not raise exception (compatible)
        service = ContentRegistryService(s3_bucket="test-bucket")
        assert service._registry["schema_version"] == "1.2.3"


class TestGetRegistryService:
    """Test the module-level get_registry_service function."""

    def setup_method(self):
        """Reset the global registry service before each test."""
        import backend.services.content_registry as registry_module

        registry_module._registry_service = None

    @patch("backend.services.content_registry.boto3.client")
    def test_get_registry_service_creates_singleton(self, mock_boto_client):
        """Test that get_registry_service creates a singleton instance."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {},
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        # First call creates instance
        service1 = get_registry_service(s3_bucket="test-bucket")

        # Second call returns same instance
        service2 = get_registry_service()

        assert service1 is service2

        # S3 should only be called once
        assert mock_s3.get_object.call_count == 1

    def test_get_registry_service_requires_bucket_on_first_call(self):
        """Test that get_registry_service requires s3_bucket on first call."""
        with pytest.raises(ValueError) as exc_info:
            get_registry_service()

        assert "s3_bucket must be provided" in str(exc_info.value)


class TestRegistryLookupMethods:
    """Test the registry lookup methods (get_entry, get_quiz, get_walkthrough)."""

    @patch("backend.services.content_registry.boto3.client")
    def test_get_entry_returns_quiz_entry(self, mock_boto_client):
        """Test get_entry returns a quiz entry when found."""
        # Mock S3 response with quiz entry
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "what_is_the_secure_sdlc": {
                    "content_type": "quiz",
                    "topic_slug": "what_is_the_secure_sdlc",
                    "module_id": "devsecops/what_is_the_secure_sdlc",
                    "passing_score": 80,
                    "question_count": 10,
                    "questions": [
                        {
                            "id": "q1",
                            "question_text": "What is SDLC?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "A",
                            "explanation": "Explanation here",
                        }
                    ],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")
        entry = service.get_entry("what_is_the_secure_sdlc")

        assert entry is not None
        assert entry.content_type == "quiz"
        assert entry.topic_slug == "what_is_the_secure_sdlc"
        assert entry.module_id == "devsecops/what_is_the_secure_sdlc"
        assert entry.data["passing_score"] == 80
        assert entry.data["question_count"] == 10
        assert len(entry.data["questions"]) == 1

    @patch("backend.services.content_registry.boto3.client")
    def test_get_entry_returns_walkthrough_entry(self, mock_boto_client):
        """Test get_entry returns a walkthrough entry when found."""
        # Mock S3 response with walkthrough entry
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "kubernetes-security-policies": {
                    "content_type": "walkthrough",
                    "id": "kubernetes-security-policies",
                    "topic_slug": "kubernetes-security-policies",
                    "module_id": "walkthroughs/kubernetes-security-policies",
                    "title": "Kubernetes Security Policies",
                    "description": "Learn about K8s security",
                    "difficulty": "Intermediate",
                    "estimated_time": 120,
                    "topics": ["kubernetes", "security"],
                    "prerequisites": [],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")
        entry = service.get_entry("kubernetes-security-policies")

        assert entry is not None
        assert entry.content_type == "walkthrough"
        assert entry.topic_slug == "kubernetes-security-policies"
        assert entry.data["title"] == "Kubernetes Security Policies"
        assert entry.data["difficulty"] == "Intermediate"

    @patch("backend.services.content_registry.boto3.client")
    def test_get_entry_returns_none_when_not_found(self, mock_boto_client):
        """Test get_entry returns None when topic_slug not found."""
        # Mock S3 response with empty entries
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {},
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")
        entry = service.get_entry("nonexistent-topic")

        assert entry is None

    @patch("backend.services.content_registry.boto3.client")
    def test_get_quiz_returns_quiz_data(self, mock_boto_client):
        """Test get_quiz returns quiz data dict when found."""
        # Mock S3 response with quiz entry
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "prerequisites": {
                    "content_type": "quiz",
                    "topic_slug": "prerequisites",
                    "module_id": "know_before_you_go/prerequisites",
                    "passing_score": 70,
                    "question_count": 5,
                    "questions": [],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")
        quiz_data = service.get_quiz("prerequisites")

        assert quiz_data is not None
        assert quiz_data["content_type"] == "quiz"
        assert quiz_data["passing_score"] == 70
        assert quiz_data["question_count"] == 5

    @patch("backend.services.content_registry.boto3.client")
    def test_get_quiz_returns_none_when_not_found(self, mock_boto_client):
        """Test get_quiz returns None when topic_slug not found."""
        # Mock S3 response with empty entries
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {},
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")
        quiz_data = service.get_quiz("nonexistent-quiz")

        assert quiz_data is None

    @patch("backend.services.content_registry.boto3.client")
    def test_get_quiz_returns_none_for_non_quiz_entry(self, mock_boto_client):
        """Test get_quiz returns None when entry exists but is not a quiz."""
        # Mock S3 response with walkthrough entry
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "kubernetes-security-policies": {
                    "content_type": "walkthrough",
                    "id": "kubernetes-security-policies",
                    "topic_slug": "kubernetes-security-policies",
                    "module_id": "walkthroughs/kubernetes-security-policies",
                    "title": "Kubernetes Security Policies",
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")
        quiz_data = service.get_quiz("kubernetes-security-policies")

        assert quiz_data is None

    @patch("backend.services.content_registry.boto3.client")
    def test_get_walkthrough_returns_walkthrough_data(self, mock_boto_client):
        """Test get_walkthrough returns walkthrough data dict when found."""
        # Mock S3 response with walkthrough entry
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "aws-iam-security": {
                    "content_type": "walkthrough",
                    "id": "aws-iam-security",
                    "topic_slug": "aws-iam-security",
                    "module_id": "walkthroughs/aws-iam-security",
                    "title": "AWS IAM Security",
                    "description": "Learn IAM best practices",
                    "difficulty": "Advanced",
                    "estimated_time": 90,
                    "topics": ["aws", "iam", "security"],
                    "prerequisites": ["kubernetes-security-policies"],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")
        walkthrough_data = service.get_walkthrough("aws-iam-security")

        assert walkthrough_data is not None
        assert walkthrough_data["content_type"] == "walkthrough"
        assert walkthrough_data["title"] == "AWS IAM Security"
        assert walkthrough_data["difficulty"] == "Advanced"
        assert walkthrough_data["estimated_time"] == 90

    @patch("backend.services.content_registry.boto3.client")
    def test_get_walkthrough_returns_none_when_not_found(self, mock_boto_client):
        """Test get_walkthrough returns None when walkthrough_id not found."""
        # Mock S3 response with empty entries
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {},
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")
        walkthrough_data = service.get_walkthrough("nonexistent-walkthrough")

        assert walkthrough_data is None

    @patch("backend.services.content_registry.boto3.client")
    def test_get_walkthrough_returns_none_for_non_walkthrough_entry(
        self, mock_boto_client
    ):
        """Test get_walkthrough returns None when entry exists but is not a walkthrough."""
        # Mock S3 response with quiz entry
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "prerequisites": {
                    "content_type": "quiz",
                    "topic_slug": "prerequisites",
                    "module_id": "know_before_you_go/prerequisites",
                    "passing_score": 70,
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")
        walkthrough_data = service.get_walkthrough("prerequisites")

        assert walkthrough_data is None


class TestQuizSubmissionValidation:
    """Test the validate_quiz_submission method."""

    @patch("backend.services.content_registry.boto3.client")
    def test_validate_quiz_submission_all_correct(self, mock_boto_client):
        """Test validation with all correct answers."""
        # Mock S3 response with quiz entry
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 80,
                    "question_count": 3,
                    "questions": [
                        {
                            "id": "q1",
                            "question_text": "Question 1?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "A",
                            "explanation": "Explanation 1",
                        },
                        {
                            "id": "q2",
                            "question_text": "Question 2?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "B",
                            "explanation": "Explanation 2",
                        },
                        {
                            "id": "q3",
                            "question_text": "Question 3?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "A",
                            "explanation": "Explanation 3",
                        },
                    ],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")

        # Submit all correct answers
        submitted_answers = {"q1": "A", "q2": "B", "q3": "A"}

        result = service.validate_quiz_submission("test_quiz", submitted_answers)

        assert result is not None
        assert result.score == 100.0
        assert result.passed is True
        assert result.correct_count == 3
        assert result.total_count == 3
        assert result.per_question["q1"] is True
        assert result.per_question["q2"] is True
        assert result.per_question["q3"] is True

    @patch("backend.services.content_registry.boto3.client")
    def test_validate_quiz_submission_all_wrong(self, mock_boto_client):
        """Test validation with all wrong answers."""
        # Mock S3 response with quiz entry
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 70,
                    "question_count": 3,
                    "questions": [
                        {
                            "id": "q1",
                            "question_text": "Question 1?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "A",
                            "explanation": "Explanation 1",
                        },
                        {
                            "id": "q2",
                            "question_text": "Question 2?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "B",
                            "explanation": "Explanation 2",
                        },
                        {
                            "id": "q3",
                            "question_text": "Question 3?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "A",
                            "explanation": "Explanation 3",
                        },
                    ],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")

        # Submit all wrong answers
        submitted_answers = {"q1": "B", "q2": "A", "q3": "B"}

        result = service.validate_quiz_submission("test_quiz", submitted_answers)

        assert result is not None
        assert result.score == 0.0
        assert result.passed is False
        assert result.correct_count == 0
        assert result.total_count == 3
        assert result.per_question["q1"] is False
        assert result.per_question["q2"] is False
        assert result.per_question["q3"] is False

    @patch("backend.services.content_registry.boto3.client")
    def test_validate_quiz_submission_mixed_answers(self, mock_boto_client):
        """Test validation with mixed correct and wrong answers."""
        # Mock S3 response with quiz entry
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 60,
                    "question_count": 5,
                    "questions": [
                        {
                            "id": "q1",
                            "question_text": "Question 1?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "A",
                            "explanation": "Explanation 1",
                        },
                        {
                            "id": "q2",
                            "question_text": "Question 2?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "B",
                            "explanation": "Explanation 2",
                        },
                        {
                            "id": "q3",
                            "question_text": "Question 3?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "A",
                            "explanation": "Explanation 3",
                        },
                        {
                            "id": "q4",
                            "question_text": "Question 4?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "B",
                            "explanation": "Explanation 4",
                        },
                        {
                            "id": "q5",
                            "question_text": "Question 5?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "A",
                            "explanation": "Explanation 5",
                        },
                    ],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")

        # Submit mixed answers (3 correct, 2 wrong)
        submitted_answers = {
            "q1": "A",  # Correct
            "q2": "A",  # Wrong
            "q3": "A",  # Correct
            "q4": "B",  # Correct
            "q5": "B",  # Wrong
        }

        result = service.validate_quiz_submission("test_quiz", submitted_answers)

        assert result is not None
        assert result.score == 60.0  # 3/5 = 60%
        assert result.passed is True  # 60% >= 60% passing score
        assert result.correct_count == 3
        assert result.total_count == 5
        assert result.per_question["q1"] is True
        assert result.per_question["q2"] is False
        assert result.per_question["q3"] is True
        assert result.per_question["q4"] is True
        assert result.per_question["q5"] is False

    @patch("backend.services.content_registry.boto3.client")
    def test_validate_quiz_submission_score_calculation(self, mock_boto_client):
        """Test that score is calculated correctly as percentage."""
        # Mock S3 response with quiz entry
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 75,
                    "question_count": 10,
                    "questions": [
                        {
                            "id": f"q{i}",
                            "question_text": f"Question {i}?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "A",
                            "explanation": f"Explanation {i}",
                        }
                        for i in range(1, 11)
                    ],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")

        # Submit 7 correct answers out of 10
        submitted_answers = {
            "q1": "A",
            "q2": "A",
            "q3": "A",
            "q4": "A",
            "q5": "A",
            "q6": "A",
            "q7": "A",
            "q8": "B",
            "q9": "B",
            "q10": "B",
        }

        result = service.validate_quiz_submission("test_quiz", submitted_answers)

        assert result is not None
        assert result.score == 70.0  # 7/10 = 70%
        assert result.passed is False  # 70% < 75% passing score
        assert result.correct_count == 7
        assert result.total_count == 10

    @patch("backend.services.content_registry.boto3.client")
    def test_validate_quiz_submission_pass_fail_threshold(self, mock_boto_client):
        """Test pass/fail determination based on passing_score threshold."""
        # Mock S3 response with quiz entry
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 80,
                    "question_count": 5,
                    "questions": [
                        {
                            "id": f"q{i}",
                            "question_text": f"Question {i}?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "A",
                            "explanation": f"Explanation {i}",
                        }
                        for i in range(1, 6)
                    ],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")

        # Test exactly at threshold (80%)
        submitted_answers_pass = {"q1": "A", "q2": "A", "q3": "A", "q4": "A", "q5": "B"}
        result_pass = service.validate_quiz_submission(
            "test_quiz", submitted_answers_pass
        )
        assert result_pass.score == 80.0
        assert result_pass.passed is True

        # Test just below threshold (60%)
        submitted_answers_fail = {"q1": "A", "q2": "A", "q3": "A", "q4": "B", "q5": "B"}
        result_fail = service.validate_quiz_submission(
            "test_quiz", submitted_answers_fail
        )
        assert result_fail.score == 60.0
        assert result_fail.passed is False

    @patch("backend.services.content_registry.boto3.client")
    def test_validate_quiz_submission_missing_answers(self, mock_boto_client):
        """Test validation when some answers are missing (treated as wrong)."""
        # Mock S3 response with quiz entry
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 70,
                    "question_count": 3,
                    "questions": [
                        {
                            "id": "q1",
                            "question_text": "Question 1?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "A",
                            "explanation": "Explanation 1",
                        },
                        {
                            "id": "q2",
                            "question_text": "Question 2?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "B",
                            "explanation": "Explanation 2",
                        },
                        {
                            "id": "q3",
                            "question_text": "Question 3?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "A",
                            "explanation": "Explanation 3",
                        },
                    ],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")

        # Submit only 2 answers (q3 is missing)
        submitted_answers = {
            "q1": "A",
            "q2": "B",
            # q3 is missing
        }

        result = service.validate_quiz_submission("test_quiz", submitted_answers)

        assert result is not None
        assert abs(result.score - 66.67) < 0.01  # 2/3 = 66.67% (approximately)
        assert result.passed is False  # 66.67% < 70% passing score
        assert result.correct_count == 2
        assert result.total_count == 3
        assert result.per_question["q1"] is True
        assert result.per_question["q2"] is True
        assert result.per_question["q3"] is False  # Missing answer treated as wrong

    @patch("backend.services.content_registry.boto3.client")
    def test_validate_quiz_submission_quiz_not_found(self, mock_boto_client):
        """Test validation returns None when quiz not found."""
        # Mock S3 response with empty entries
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {},
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")

        submitted_answers = {"q1": "A"}
        result = service.validate_quiz_submission("nonexistent_quiz", submitted_answers)

        assert result is None

    @patch("backend.services.content_registry.boto3.client")
    def test_validate_quiz_submission_empty_questions(self, mock_boto_client):
        """Test validation returns None when quiz has no questions."""
        # Mock S3 response with quiz entry but no questions
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 70,
                    "question_count": 0,
                    "questions": [],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")

        submitted_answers = {"q1": "A"}
        result = service.validate_quiz_submission("test_quiz", submitted_answers)

        assert result is None

    @patch("backend.services.content_registry.boto3.client")
    def test_validate_quiz_submission_default_passing_score(self, mock_boto_client):
        """Test validation uses default passing_score of 70 when not specified."""
        # Mock S3 response with quiz entry without passing_score
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    # passing_score not specified
                    "question_count": 2,
                    "questions": [
                        {
                            "id": "q1",
                            "question_text": "Question 1?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "A",
                            "explanation": "Explanation 1",
                        },
                        {
                            "id": "q2",
                            "question_text": "Question 2?",
                            "options": ["A. Option 1", "B. Option 2"],
                            "correct_answer": "B",
                            "explanation": "Explanation 2",
                        },
                    ],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")

        # Submit 1 correct answer (50%)
        submitted_answers = {"q1": "A", "q2": "A"}
        result = service.validate_quiz_submission("test_quiz", submitted_answers)

        assert result is not None
        assert result.score == 50.0
        assert result.passed is False  # 50% < 70% (default)

    @patch("backend.services.content_registry.boto3.client")
    def test_validate_quiz_submission_per_question_completeness(self, mock_boto_client):
        """Test that per_question dict includes all questions."""
        # Mock S3 response with quiz entry
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 70,
                    "question_count": 4,
                    "questions": [
                        {
                            "id": "q1",
                            "question_text": "Q1?",
                            "options": ["A. 1", "B. 2"],
                            "correct_answer": "A",
                            "explanation": "E1",
                        },
                        {
                            "id": "q2",
                            "question_text": "Q2?",
                            "options": ["A. 1", "B. 2"],
                            "correct_answer": "B",
                            "explanation": "E2",
                        },
                        {
                            "id": "q3",
                            "question_text": "Q3?",
                            "options": ["A. 1", "B. 2"],
                            "correct_answer": "A",
                            "explanation": "E3",
                        },
                        {
                            "id": "q4",
                            "question_text": "Q4?",
                            "options": ["A. 1", "B. 2"],
                            "correct_answer": "B",
                            "explanation": "E4",
                        },
                    ],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        service = ContentRegistryService(s3_bucket="test-bucket")

        submitted_answers = {"q1": "A", "q2": "B", "q3": "B", "q4": "A"}
        result = service.validate_quiz_submission("test_quiz", submitted_answers)

        assert result is not None
        # Verify all questions are in per_question dict
        assert len(result.per_question) == 4
        assert "q1" in result.per_question
        assert "q2" in result.per_question
        assert "q3" in result.per_question
        assert "q4" in result.per_question
        # Verify correctness
        assert result.per_question["q1"] is True
        assert result.per_question["q2"] is True
        assert result.per_question["q3"] is False
        assert result.per_question["q4"] is False


class TestCacheTTLMechanism:
    """Test the cache TTL mechanism."""

    @patch("backend.services.content_registry.boto3.client")
    @patch("backend.services.content_registry.time.time")
    def test_cache_ttl_not_configured_never_expires(self, mock_time, mock_boto_client):
        """Test that cache never expires when TTL is not configured."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 80,
                    "question_count": 5,
                    "questions": [],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        # Set initial time
        mock_time.return_value = 1000.0

        # Initialize service without TTL
        service = ContentRegistryService(s3_bucket="test-bucket")

        # Verify initial load
        assert mock_s3.get_object.call_count == 1

        # Simulate time passing (1 hour)
        mock_time.return_value = 4600.0

        # Access entry - should not trigger refresh
        entry = service.get_entry("test_quiz")

        assert entry is not None
        assert entry.topic_slug == "test_quiz"
        # S3 should still only be called once (no refresh)
        assert mock_s3.get_object.call_count == 1

    @patch("backend.services.content_registry.boto3.client")
    @patch("backend.services.content_registry.time.time")
    def test_cache_ttl_expires_and_refreshes(self, mock_time, mock_boto_client):
        """Test that cache refreshes from S3 when TTL expires."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data_v1 = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 80,
                    "question_count": 5,
                    "questions": [],
                }
            },
        }

        registry_data_v2 = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T11:00:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 90,  # Changed
                    "question_count": 5,
                    "questions": [],
                }
            },
        }

        # First call returns v1, second call returns v2
        mock_response_v1 = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data_v1).encode("utf-8"))
            )
        }
        mock_response_v2 = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data_v2).encode("utf-8"))
            )
        }
        mock_s3.get_object.side_effect = [mock_response_v1, mock_response_v2]

        # Set initial time
        mock_time.return_value = 1000.0

        # Initialize service with 300 second TTL (5 minutes)
        service = ContentRegistryService(s3_bucket="test-bucket", cache_ttl_seconds=300)

        # Verify initial load
        assert mock_s3.get_object.call_count == 1

        # Access entry before TTL expires
        mock_time.return_value = 1200.0  # 200 seconds later
        entry = service.get_entry("test_quiz")
        assert entry is not None
        assert entry.data["passing_score"] == 80  # Still v1
        # S3 should still only be called once (no refresh yet)
        assert mock_s3.get_object.call_count == 1

        # Simulate time passing beyond TTL
        mock_time.return_value = 1400.0  # 400 seconds later (beyond 300s TTL)

        # Access entry - should trigger refresh
        entry = service.get_entry("test_quiz")

        assert entry is not None
        assert entry.data["passing_score"] == 90  # Now v2
        # S3 should be called twice (initial + refresh)
        assert mock_s3.get_object.call_count == 2

    @patch("backend.services.content_registry.boto3.client")
    @patch("backend.services.content_registry.time.time")
    def test_cache_ttl_refresh_failure_uses_stale_cache(
        self, mock_time, mock_boto_client
    ):
        """Test that service continues with stale cache if refresh fails."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 80,
                    "question_count": 5,
                    "questions": [],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }

        # First call succeeds, second call fails
        error_response = {
            "Error": {"Code": "ServiceUnavailable", "Message": "Service unavailable"}
        }
        mock_s3.get_object.side_effect = [
            mock_response,
            ClientError(error_response, "GetObject"),
        ]

        # Set initial time
        mock_time.return_value = 1000.0

        # Initialize service with 300 second TTL
        service = ContentRegistryService(s3_bucket="test-bucket", cache_ttl_seconds=300)

        # Verify initial load
        assert mock_s3.get_object.call_count == 1

        # Simulate time passing beyond TTL
        mock_time.return_value = 1400.0  # 400 seconds later

        # Access entry - should attempt refresh but fail and use stale cache
        entry = service.get_entry("test_quiz")

        assert entry is not None
        assert entry.data["passing_score"] == 80  # Still using stale cache
        # S3 should be called twice (initial + failed refresh attempt)
        assert mock_s3.get_object.call_count == 2

    @patch("backend.services.content_registry.boto3.client")
    @patch("backend.services.content_registry.time.time")
    def test_cache_ttl_exact_boundary(self, mock_time, mock_boto_client):
        """Test cache behavior at exact TTL boundary."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 80,
                    "question_count": 5,
                    "questions": [],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        # Set initial time
        mock_time.return_value = 1000.0

        # Initialize service with 300 second TTL
        service = ContentRegistryService(s3_bucket="test-bucket", cache_ttl_seconds=300)

        # Verify initial load
        assert mock_s3.get_object.call_count == 1

        # Access at exactly TTL boundary (should trigger refresh)
        mock_time.return_value = 1300.0  # Exactly 300 seconds later

        entry = service.get_entry("test_quiz")

        assert entry is not None
        # S3 should be called twice (initial + refresh at boundary)
        assert mock_s3.get_object.call_count == 2

    @patch("backend.services.content_registry.boto3.client")
    @patch("backend.services.content_registry.time.time")
    def test_cache_ttl_multiple_accesses_within_ttl(self, mock_time, mock_boto_client):
        """Test that multiple accesses within TTL don't trigger refresh."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 80,
                    "question_count": 5,
                    "questions": [],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        # Set initial time
        mock_time.return_value = 1000.0

        # Initialize service with 300 second TTL
        service = ContentRegistryService(s3_bucket="test-bucket", cache_ttl_seconds=300)

        # Verify initial load
        assert mock_s3.get_object.call_count == 1

        # Multiple accesses within TTL
        for i in range(5):
            mock_time.return_value = 1000.0 + (i * 50)  # 0, 50, 100, 150, 200 seconds
            entry = service.get_entry("test_quiz")
            assert entry is not None

        # S3 should still only be called once (no refreshes)
        assert mock_s3.get_object.call_count == 1

    @patch("backend.services.content_registry.boto3.client")
    @patch("backend.services.content_registry.time.time")
    def test_cache_ttl_zero_seconds(self, mock_time, mock_boto_client):
        """Test that TTL of 0 seconds causes immediate expiration."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 80,
                    "question_count": 5,
                    "questions": [],
                }
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        # Set initial time
        mock_time.return_value = 1000.0

        # Initialize service with 0 second TTL
        service = ContentRegistryService(s3_bucket="test-bucket", cache_ttl_seconds=0)

        # Verify initial load
        assert mock_s3.get_object.call_count == 1

        # Any time advancement should trigger refresh
        mock_time.return_value = 1000.1  # Even 0.1 seconds later

        entry = service.get_entry("test_quiz")

        assert entry is not None
        # S3 should be called twice (initial + immediate refresh)
        assert mock_s3.get_object.call_count == 2

    @patch("backend.services.content_registry.boto3.client")
    @patch("backend.services.content_registry.time.time")
    def test_is_cache_expired_method(self, mock_time, mock_boto_client):
        """Test the _is_cache_expired method directly."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {},
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        # Set initial time
        mock_time.return_value = 1000.0

        # Test with no TTL configured
        service_no_ttl = ContentRegistryService(s3_bucket="test-bucket")
        assert service_no_ttl._is_cache_expired() is False

        # Test with TTL configured
        service_with_ttl = ContentRegistryService(
            s3_bucket="test-bucket", cache_ttl_seconds=300
        )

        # Initially not expired
        assert service_with_ttl._is_cache_expired() is False

        # After TTL expires
        mock_time.return_value = 1400.0  # 400 seconds later
        assert service_with_ttl._is_cache_expired() is True


class TestManualCacheRefresh:
    """Test the manual cache refresh functionality."""

    @patch("backend.services.content_registry.boto3.client")
    def test_refresh_cache_success(self, mock_boto_client):
        """Test successful manual cache refresh."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        initial_registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 80,
                    "question_count": 5,
                    "questions": [],
                }
            },
        }

        updated_registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T11:00:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 80,
                    "question_count": 5,
                    "questions": [],
                },
                "new_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "new_quiz",
                    "module_id": "test/new_quiz",
                    "passing_score": 70,
                    "question_count": 3,
                    "questions": [],
                },
            },
        }

        # First call returns initial data, second call returns updated data
        mock_s3.get_object.side_effect = [
            {
                "Body": Mock(
                    read=Mock(
                        return_value=json.dumps(initial_registry_data).encode("utf-8")
                    )
                )
            },
            {
                "Body": Mock(
                    read=Mock(
                        return_value=json.dumps(updated_registry_data).encode("utf-8")
                    )
                )
            },
        ]

        # Initialize service
        service = ContentRegistryService(s3_bucket="test-bucket")

        # Verify initial state
        assert service.get_entry("test_quiz") is not None
        assert service.get_entry("new_quiz") is None
        assert mock_s3.get_object.call_count == 1

        # Manually refresh cache
        result = service.refresh_cache()

        # Verify refresh result
        assert result["success"] is True
        assert result["message"] == "Cache refreshed successfully"
        assert result["schema_version"] == "1.0.0"
        assert result["entry_count"] == 2
        assert "error" not in result

        # Verify S3 was called again
        assert mock_s3.get_object.call_count == 2

        # Verify new entry is now available
        assert service.get_entry("test_quiz") is not None
        assert service.get_entry("new_quiz") is not None

    @patch("backend.services.content_registry.boto3.client")
    def test_refresh_cache_s3_error(self, mock_boto_client):
        """Test manual cache refresh handles S3 errors gracefully."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        initial_registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 80,
                    "question_count": 5,
                    "questions": [],
                }
            },
        }

        # First call succeeds, second call fails
        error_response = {
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist.",
            }
        }
        mock_s3.get_object.side_effect = [
            {
                "Body": Mock(
                    read=Mock(
                        return_value=json.dumps(initial_registry_data).encode("utf-8")
                    )
                )
            },
            ClientError(error_response, "GetObject"),
        ]

        # Initialize service
        service = ContentRegistryService(s3_bucket="test-bucket")

        # Verify initial state
        assert service.get_entry("test_quiz") is not None
        assert mock_s3.get_object.call_count == 1

        # Manually refresh cache (should fail)
        result = service.refresh_cache()

        # Verify refresh result indicates failure
        assert result["success"] is False
        assert result["message"] == "Failed to refresh cache"
        assert "error" in result
        assert "S3 error" in result["error"]
        assert "NoSuchKey" in result["error"]

        # Verify S3 was called again
        assert mock_s3.get_object.call_count == 2

        # Verify old cache is still available (not cleared on error)
        assert service.get_entry("test_quiz") is not None

    @patch("backend.services.content_registry.boto3.client")
    def test_refresh_cache_schema_version_error(self, mock_boto_client):
        """Test manual cache refresh handles schema version errors."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        initial_registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {},
        }

        incompatible_registry_data = {
            "schema_version": "2.0.0",  # Incompatible major version
            "generated_at": "2024-01-15T11:00:00Z",
            "generator_version": "2.0.0",
            "entries": {},
        }

        # First call succeeds, second call returns incompatible version
        mock_s3.get_object.side_effect = [
            {
                "Body": Mock(
                    read=Mock(
                        return_value=json.dumps(initial_registry_data).encode("utf-8")
                    )
                )
            },
            {
                "Body": Mock(
                    read=Mock(
                        return_value=json.dumps(incompatible_registry_data).encode(
                            "utf-8"
                        )
                    )
                )
            },
        ]

        # Initialize service
        service = ContentRegistryService(s3_bucket="test-bucket")

        # Verify initial state
        assert mock_s3.get_object.call_count == 1

        # Manually refresh cache (should fail due to schema version)
        result = service.refresh_cache()

        # Verify refresh result indicates failure
        assert result["success"] is False
        assert result["message"] == "Failed to refresh cache"
        assert "error" in result
        assert "Schema version error" in result["error"]

        # Verify S3 was called again
        assert mock_s3.get_object.call_count == 2

    @patch("backend.services.content_registry.boto3.client")
    def test_refresh_cache_json_decode_error(self, mock_boto_client):
        """Test manual cache refresh handles malformed JSON."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        initial_registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {},
        }

        # First call succeeds, second call returns invalid JSON
        mock_s3.get_object.side_effect = [
            {
                "Body": Mock(
                    read=Mock(
                        return_value=json.dumps(initial_registry_data).encode("utf-8")
                    )
                )
            },
            {"Body": Mock(read=Mock(return_value=b"{ invalid json }"))},
        ]

        # Initialize service
        service = ContentRegistryService(s3_bucket="test-bucket")

        # Verify initial state
        assert mock_s3.get_object.call_count == 1

        # Manually refresh cache (should fail due to JSON error)
        result = service.refresh_cache()

        # Verify refresh result indicates failure
        assert result["success"] is False
        assert result["message"] == "Failed to refresh cache"
        assert "error" in result
        assert "Unexpected error" in result["error"]

        # Verify S3 was called again
        assert mock_s3.get_object.call_count == 2

    @patch("backend.services.content_registry.boto3.client")
    def test_refresh_cache_returns_metadata(self, mock_boto_client):
        """Test that refresh_cache returns correct metadata."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.2.3",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "quiz1": {
                    "content_type": "quiz",
                    "topic_slug": "quiz1",
                    "module_id": "test/quiz1",
                },
                "quiz2": {
                    "content_type": "quiz",
                    "topic_slug": "quiz2",
                    "module_id": "test/quiz2",
                },
                "quiz3": {
                    "content_type": "quiz",
                    "topic_slug": "quiz3",
                    "module_id": "test/quiz3",
                },
            },
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        # Initialize service
        service = ContentRegistryService(s3_bucket="test-bucket")

        # Manually refresh cache
        result = service.refresh_cache()

        # Verify metadata in result
        assert result["success"] is True
        assert result["schema_version"] == "1.2.3"
        assert result["entry_count"] == 3
        assert result["message"] == "Cache refreshed successfully"

    @patch("backend.services.content_registry.boto3.client")
    def test_refresh_cache_logs_events(self, mock_boto_client):
        """Test that refresh_cache logs appropriate events."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {},
        }

        mock_response = {
            "Body": Mock(
                read=Mock(return_value=json.dumps(registry_data).encode("utf-8"))
            )
        }
        mock_s3.get_object.return_value = mock_response

        # Initialize service
        service = ContentRegistryService(s3_bucket="test-bucket")

        # Manually refresh cache
        with patch("backend.services.content_registry.logger") as mock_logger:
            result = service.refresh_cache()

            # Verify logging calls
            assert mock_logger.info.called

            # Check for manual refresh log messages
            log_messages = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("Manual cache refresh requested" in msg for msg in log_messages)
            assert any(
                "Manual cache refresh completed successfully" in msg
                for msg in log_messages
            )

    @patch("backend.services.content_registry.boto3.client")
    @patch("backend.services.content_registry.time.time")
    def test_refresh_cache_bypasses_ttl(self, mock_time, mock_boto_client):
        """Test that refresh_cache forces reload regardless of TTL."""
        # Mock S3 response
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        initial_registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 80,
                    "question_count": 5,
                    "questions": [],
                }
            },
        }

        updated_registry_data = {
            "schema_version": "1.0.0",
            "generated_at": "2024-01-15T10:35:00Z",
            "generator_version": "1.0.0",
            "entries": {
                "test_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "test_quiz",
                    "module_id": "test/test_quiz",
                    "passing_score": 80,
                    "question_count": 5,
                    "questions": [],
                },
                "new_quiz": {
                    "content_type": "quiz",
                    "topic_slug": "new_quiz",
                    "module_id": "test/new_quiz",
                    "passing_score": 70,
                    "question_count": 3,
                    "questions": [],
                },
            },
        }

        # First call returns initial data, second call returns updated data
        mock_s3.get_object.side_effect = [
            {
                "Body": Mock(
                    read=Mock(
                        return_value=json.dumps(initial_registry_data).encode("utf-8")
                    )
                )
            },
            {
                "Body": Mock(
                    read=Mock(
                        return_value=json.dumps(updated_registry_data).encode("utf-8")
                    )
                )
            },
        ]

        # Set initial time
        mock_time.return_value = 1000.0

        # Initialize service with long TTL (3600 seconds)
        service = ContentRegistryService(
            s3_bucket="test-bucket", cache_ttl_seconds=3600
        )

        # Verify initial state
        assert service.get_entry("test_quiz") is not None
        assert service.get_entry("new_quiz") is None
        assert mock_s3.get_object.call_count == 1

        # Advance time by only 60 seconds (well within TTL)
        mock_time.return_value = 1060.0

        # Normal access should NOT trigger refresh (within TTL)
        entry = service.get_entry("test_quiz")
        assert entry is not None
        assert mock_s3.get_object.call_count == 1  # Still only 1 call

        # Manual refresh should force reload despite TTL
        result = service.refresh_cache()

        # Verify refresh succeeded
        assert result["success"] is True
        assert mock_s3.get_object.call_count == 2  # Now 2 calls

        # Verify new entry is now available
        assert service.get_entry("new_quiz") is not None
