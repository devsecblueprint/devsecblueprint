"""
Content Registry Service

This service loads and manages the content registry from S3.
It provides methods to retrieve content definitions and validate submissions.
"""

import json
import logging
import boto3
import time
from botocore.exceptions import ClientError, BotoCoreError
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Type aliases for registry structure
RegistryData = Dict[str, Any]
QuizAnswers = Dict[str, str]
PerQuestionResults = Dict[str, bool]


@dataclass
class ContentRegistryEntry:
    """Represents a single entry in the content registry."""

    content_type: str
    topic_slug: str
    module_id: str
    data: RegistryData


@dataclass
class QuizValidationResult:
    """Result of quiz submission validation."""

    score: float
    passed: bool
    correct_count: int
    total_count: int
    per_question: PerQuestionResults


class SchemaVersionError(Exception):
    """Raised when registry schema version is incompatible."""

    pass


class ContentRegistryService:
    """Service for loading and accessing the content registry."""

    # Expected schema version (major.minor.patch)
    EXPECTED_SCHEMA_VERSION = "1.0.0"

    def __init__(
        self,
        s3_bucket: str,
        s3_key: str = "content-registry/latest.json",
        cache_ttl_seconds: Optional[int] = None,
    ):
        """
        Initialize the content registry service.

        Args:
            s3_bucket: S3 bucket name containing the registry
            s3_key: S3 key for the registry file
            cache_ttl_seconds: Optional TTL in seconds for cache expiration (None = no expiration)
        """
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.cache_ttl_seconds = cache_ttl_seconds
        self._registry: Optional[RegistryData] = None
        self._last_loaded_at: Optional[float] = None
        # Load registry on initialization
        self._load_registry()

    def _load_registry(self) -> None:
        """
        Load registry from S3 and cache in memory.

        Raises:
            Exception: If registry cannot be fetched from S3 (will be caught by caller)
        """
        try:
            logger.info(
                "Loading content registry from S3",
                extra={"bucket": self.s3_bucket, "key": self.s3_key},
            )

            # Create S3 client
            s3_client = boto3.client("s3")

            # Fetch registry from S3
            response = s3_client.get_object(Bucket=self.s3_bucket, Key=self.s3_key)

            # Read and decode content
            content = response["Body"].read().decode("utf-8")

            # Parse JSON
            self._registry = json.loads(content)

            # Update last loaded timestamp
            self._last_loaded_at = time.time()

            # Validate schema version
            self._validate_schema_version()

            # Log success with metadata
            entry_count = (
                len(self._registry.get("entries", {})) if self._registry else 0
            )
            schema_version = (
                self._registry.get("schema_version", "unknown")
                if self._registry
                else "unknown"
            )

            logger.info(
                "Content registry loaded successfully",
                extra={
                    "schema_version": schema_version,
                    "entry_count": entry_count,
                    "bucket": self.s3_bucket,
                    "key": self.s3_key,
                    "loaded_at": self._last_loaded_at,
                },
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(
                f"Failed to load registry from S3: {error_code}",
                extra={
                    "bucket": self.s3_bucket,
                    "key": self.s3_key,
                    "error_code": error_code,
                    "error_message": str(e),
                },
            )
            raise

        except BotoCoreError as e:
            logger.error(
                f"BotoCore error loading registry: {str(e)}",
                extra={"bucket": self.s3_bucket, "key": self.s3_key, "error": str(e)},
            )
            raise

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse registry JSON: {str(e)}",
                extra={"bucket": self.s3_bucket, "key": self.s3_key, "error": str(e)},
            )
            raise

        except Exception as e:
            logger.error(
                f"Unexpected error loading registry: {str(e)}",
                extra={"bucket": self.s3_bucket, "key": self.s3_key, "error": str(e)},
            )
            raise

    def _validate_schema_version(self) -> None:
        """
        Validate that the registry schema version is compatible.

        Raises:
            SchemaVersionError: If schema version is missing or incompatible
        """
        if not self._registry:
            raise SchemaVersionError("Registry is empty or not loaded")

        schema_version = self._registry.get("schema_version")

        if not schema_version:
            logger.error(
                "Registry missing schema_version field",
                extra={"bucket": self.s3_bucket, "key": self.s3_key},
            )
            raise SchemaVersionError("Registry missing schema_version field")

        # Check compatibility (major version must match)
        expected_major = self.EXPECTED_SCHEMA_VERSION.split(".")[0]
        actual_major = schema_version.split(".")[0]

        if expected_major != actual_major:
            logger.error(
                "Incompatible registry schema version",
                extra={
                    "expected_version": self.EXPECTED_SCHEMA_VERSION,
                    "actual_version": schema_version,
                    "bucket": self.s3_bucket,
                    "key": self.s3_key,
                },
            )
            raise SchemaVersionError(
                f"Incompatible registry schema version. "
                f"Expected: {self.EXPECTED_SCHEMA_VERSION}, "
                f"Actual: {schema_version}"
            )

        logger.info(
            "Schema version validated successfully",
            extra={
                "expected_version": self.EXPECTED_SCHEMA_VERSION,
                "actual_version": schema_version,
            },
        )

    def _is_cache_expired(self) -> bool:
        """
        Check if the cache has expired based on TTL.

        Returns:
            True if cache is expired or TTL is configured and time has elapsed, False otherwise
        """
        # If no TTL configured, cache never expires
        if self.cache_ttl_seconds is None:
            return False

        # If registry was never loaded, it's expired
        if self._last_loaded_at is None:
            return True

        # Check if TTL has elapsed
        elapsed_seconds = time.time() - self._last_loaded_at
        return elapsed_seconds >= self.cache_ttl_seconds

    def _refresh_if_needed(self) -> None:
        """
        Refresh the registry from S3 if the cache has expired.

        Logs cache refresh events. If refresh fails, continues using stale cache.
        """
        if not self._is_cache_expired():
            return

        logger.info(
            "Cache TTL expired, refreshing registry from S3",
            extra={
                "bucket": self.s3_bucket,
                "key": self.s3_key,
                "ttl_seconds": self.cache_ttl_seconds,
                "last_loaded_at": self._last_loaded_at,
            },
        )

        try:
            self._load_registry()
            logger.info(
                "Cache refreshed successfully",
                extra={
                    "bucket": self.s3_bucket,
                    "key": self.s3_key,
                    "new_loaded_at": self._last_loaded_at,
                },
            )
        except Exception as e:
            logger.error(
                f"Failed to refresh cache, continuing with stale cache: {str(e)}",
                extra={"bucket": self.s3_bucket, "key": self.s3_key, "error": str(e)},
            )

    def get_entry(self, topic_slug: str) -> Optional[ContentRegistryEntry]:
        """
        Retrieve content entry by topic_slug.

        Args:
            topic_slug: The topic identifier

        Returns:
            ContentRegistryEntry if found, None otherwise
        """
        # Refresh cache if TTL expired
        self._refresh_if_needed()

        if not self._registry:
            logger.warning("Registry not loaded, cannot retrieve entry")
            return None

        entries = self._registry.get("entries", {})
        entry_data = entries.get(topic_slug)

        if not entry_data:
            logger.debug(
                f"Entry not found for topic_slug: {topic_slug}",
                extra={"topic_slug": topic_slug},
            )
            return None

        # Create ContentRegistryEntry from the data
        return ContentRegistryEntry(
            content_type=entry_data.get("content_type", "unknown"),
            topic_slug=entry_data.get("topic_slug", topic_slug),
            module_id=entry_data.get("module_id", ""),
            data=entry_data,
        )

    def get_quiz(self, topic_slug: str) -> Optional[RegistryData]:
        """
        Get quiz definition for validation.

        Args:
            topic_slug: The quiz identifier

        Returns:
            Quiz definition dict if found, None otherwise
        """
        entry = self.get_entry(topic_slug)

        if not entry:
            return None

        # Verify this is a quiz entry
        if entry.content_type != "quiz":
            logger.warning(
                f"Entry found but not a quiz: {topic_slug}",
                extra={"topic_slug": topic_slug, "content_type": entry.content_type},
            )
            return None

        return entry.data

    def get_walkthrough(self, walkthrough_id: str) -> Optional[RegistryData]:
        """
        Get walkthrough metadata.

        Args:
            walkthrough_id: The walkthrough identifier

        Returns:
            Walkthrough definition dict if found, None otherwise
        """
        entry = self.get_entry(walkthrough_id)

        if not entry:
            return None

        # Verify this is a walkthrough entry
        if entry.content_type != "walkthrough":
            logger.warning(
                f"Entry found but not a walkthrough: {walkthrough_id}",
                extra={
                    "walkthrough_id": walkthrough_id,
                    "content_type": entry.content_type,
                },
            )
            return None

        return entry.data

    def validate_quiz_submission(
        self, topic_slug: str, submitted_answers: QuizAnswers
    ) -> Optional[QuizValidationResult]:
        """
        Validate quiz submission and return results.

        This method:
        1. Looks up the quiz definition by topic_slug
        2. Compares submitted answers against correct answers
        3. Calculates score as percentage of correct answers
        4. Determines pass/fail based on passing_score
        5. Returns complete validation result with per-question correctness

        Args:
            topic_slug: The quiz identifier
            submitted_answers: Dict mapping question IDs to submitted answer letters
                              (e.g., {"q1": "A", "q2": "B"})

        Returns:
            QuizValidationResult with score, passed, correct_count, total_count, per_question
            None if quiz not found
        """
        # Look up quiz definition
        quiz = self.get_quiz(topic_slug)

        if not quiz:
            logger.warning(
                f"Quiz not found for validation: {topic_slug}",
                extra={"topic_slug": topic_slug},
            )
            return None

        # Get questions from quiz definition
        questions = quiz.get("questions", [])

        if not questions:
            logger.warning(
                f"Quiz has no questions: {topic_slug}", extra={"topic_slug": topic_slug}
            )
            return None

        # Compare submitted answers against correct answers
        correct_count = 0
        per_question: PerQuestionResults = {}

        for question in questions:
            question_id = question.get("id", "")
            correct_answer = question.get("correct_answer", "")
            submitted_answer = submitted_answers.get(question_id, "")

            # Check if answer is correct
            is_correct = submitted_answer == correct_answer
            per_question[question_id] = is_correct

            if is_correct:
                correct_count += 1

        # Calculate score as percentage
        total_count = len(questions)
        score = (correct_count / total_count * 100) if total_count > 0 else 0.0

        # Determine pass/fail based on passing_score
        passing_score = quiz.get("passing_score", 70)
        passed = score >= passing_score

        logger.info(
            f"Quiz validation completed: {topic_slug}",
            extra={
                "topic_slug": topic_slug,
                "score": score,
                "passed": passed,
                "correct_count": correct_count,
                "total_count": total_count,
            },
        )

        # Return complete validation result
        return QuizValidationResult(
            score=score,
            passed=passed,
            correct_count=correct_count,
            total_count=total_count,
            per_question=per_question,
        )

    def refresh_cache(self) -> Dict[str, Any]:
        """
        Manually refresh the registry cache from S3.

        This method forces a reload of the registry from S3 regardless of TTL,
        allowing operators to immediately update the cache without waiting for
        TTL expiration or Lambda cold starts.

        Returns:
            Dict with status information:
            - success: bool indicating if refresh succeeded
            - message: str describing the result
            - schema_version: str of the loaded registry (if successful)
            - entry_count: int number of entries in registry (if successful)
            - error: str error message (if failed)

        Example:
            >>> service = ContentRegistryService(s3_bucket="my-bucket")
            >>> result = service.refresh_cache()
            >>> print(result)
            {'success': True, 'message': 'Cache refreshed successfully',
             'schema_version': '1.0.0', 'entry_count': 12}
        """
        try:
            logger.info(
                "Manual cache refresh requested",
                extra={"bucket": self.s3_bucket, "key": self.s3_key},
            )

            # Force reload from S3
            self._load_registry()

            # Extract metadata for response
            schema_version = (
                self._registry.get("schema_version", "unknown")
                if self._registry
                else "unknown"
            )
            entry_count = (
                len(self._registry.get("entries", {})) if self._registry else 0
            )

            logger.info(
                "Manual cache refresh completed successfully",
                extra={
                    "bucket": self.s3_bucket,
                    "key": self.s3_key,
                    "schema_version": schema_version,
                    "entry_count": entry_count,
                },
            )

            return {
                "success": True,
                "message": "Cache refreshed successfully",
                "schema_version": schema_version,
                "entry_count": entry_count,
            }

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = f"S3 error during cache refresh: {error_code}"

            logger.error(
                error_message,
                extra={
                    "bucket": self.s3_bucket,
                    "key": self.s3_key,
                    "error_code": error_code,
                    "error_message": str(e),
                },
            )

            return {
                "success": False,
                "message": "Failed to refresh cache",
                "error": error_message,
            }

        except SchemaVersionError as e:
            error_message = f"Schema version error: {str(e)}"

            logger.error(
                error_message,
                extra={"bucket": self.s3_bucket, "key": self.s3_key, "error": str(e)},
            )

            return {
                "success": False,
                "message": "Failed to refresh cache",
                "error": error_message,
            }

        except Exception as e:
            error_message = f"Unexpected error during cache refresh: {str(e)}"

            logger.error(
                error_message,
                extra={"bucket": self.s3_bucket, "key": self.s3_key, "error": str(e)},
            )

            return {
                "success": False,
                "message": "Failed to refresh cache",
                "error": error_message,
            }


# Module-level cache for the registry service
_registry_service: Optional[ContentRegistryService] = None


def get_registry_service(s3_bucket: Optional[str] = None) -> ContentRegistryService:
    """
    Get or create the global registry service instance.

    This function implements a singleton pattern to ensure the registry
    is loaded only once per Lambda execution context.

    Args:
        s3_bucket: S3 bucket name (required on first call, optional afterwards)

    Returns:
        ContentRegistryService instance

    Raises:
        ValueError: If s3_bucket is not provided on first call
    """
    global _registry_service

    if _registry_service is None:
        if s3_bucket is None:
            raise ValueError(
                "s3_bucket must be provided on first call to get_registry_service"
            )
        _registry_service = ContentRegistryService(s3_bucket)

    return _registry_service
