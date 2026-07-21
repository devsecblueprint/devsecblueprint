"""Content registry service — loads content-registry/latest.json from S3.

Provides a cached interface to the content registry stored in S3. The registry
contains quiz definitions, walkthrough metadata, and other content entries.

Uses a module-level singleton with TTL-based cache refresh.
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

RegistryData = dict[str, Any]
QuizAnswers = dict[str, str]
PerQuestionResults = dict[str, bool]


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
    """Loads and caches the content registry from S3.

    Args:
        s3_bucket: Bucket name containing the registry JSON.
        s3_key: Object key for the registry file.
        cache_ttl_seconds: Time before cache is considered stale. None = no expiry.
    """

    EXPECTED_SCHEMA_VERSION = "1.0.0"

    def __init__(
        self,
        s3_bucket: str,
        s3_key: str = "content-registry/latest.json",
        cache_ttl_seconds: int | None = 300,
    ) -> None:
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.cache_ttl_seconds = cache_ttl_seconds
        self._registry: RegistryData | None = None
        self._last_loaded_at: float | None = None
        self._load_registry()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_registry(self) -> None:
        """Fetch and parse the registry JSON from S3."""
        try:
            s3 = boto3.client("s3")
            response = s3.get_object(Bucket=self.s3_bucket, Key=self.s3_key)
            content = response["Body"].read().decode("utf-8")
            self._registry = json.loads(content)
            self._last_loaded_at = time.time()
            self._validate_schema_version()

            entry_count = (
                len(self._registry.get("entries", {})) if self._registry else 0
            )
            logger.info(
                "Content registry loaded: %d entries from s3://%s/%s",
                entry_count,
                self.s3_bucket,
                self.s3_key,
            )
        except ClientError as e:
            logger.error("S3 error loading registry: %s", e)
            raise
        except json.JSONDecodeError as e:
            logger.error("JSON parse error loading registry: %s", e)
            raise
        except Exception as e:
            logger.error("Unexpected error loading registry: %s", e)
            raise

    def _validate_schema_version(self) -> None:
        """Ensure the major version matches expectations."""
        if not self._registry:
            raise SchemaVersionError("Registry is empty or not loaded")

        version = self._registry.get("schema_version")
        if not version:
            raise SchemaVersionError("Registry missing schema_version field")

        expected_major = self.EXPECTED_SCHEMA_VERSION.split(".")[0]
        actual_major = version.split(".")[0]
        if expected_major != actual_major:
            raise SchemaVersionError(
                f"Incompatible schema: expected {self.EXPECTED_SCHEMA_VERSION}, got {version}"
            )

    def _refresh_if_needed(self) -> None:
        """Refresh from S3 if the TTL has elapsed."""
        if self.cache_ttl_seconds is None:
            return
        if self._last_loaded_at is None:
            self._load_registry()
            return
        if (time.time() - self._last_loaded_at) >= self.cache_ttl_seconds:
            try:
                self._load_registry()
            except Exception as e:
                logger.error("Cache refresh failed, using stale data: %s", e)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_quiz(self, topic_slug: str) -> RegistryData | None:
        """Get quiz definition by topic slug.

        Returns:
            Quiz dict with keys: passing_score, questions, etc. or None.
        """
        self._refresh_if_needed()
        if not self._registry:
            return None
        entries = self._registry.get("entries", {})
        entry = entries.get(topic_slug)
        if not entry or entry.get("content_type") != "quiz":
            return None
        return entry

    def get_walkthrough(self, walkthrough_id: str) -> RegistryData | None:
        """Get walkthrough metadata by ID."""
        self._refresh_if_needed()
        if not self._registry:
            return None
        entries = self._registry.get("entries", {})
        entry = entries.get(walkthrough_id)
        if not entry or entry.get("content_type") != "walkthrough":
            return None
        return entry

    def get_all_walkthroughs(self) -> list[dict[str, Any]]:
        """Return all walkthrough entries with their ID and difficulty."""
        self._refresh_if_needed()
        if not self._registry:
            return []
        results = []
        for entry_id, entry_data in self._registry.get("entries", {}).items():
            if entry_data.get("content_type") == "walkthrough":
                results.append(
                    {
                        "id": entry_id,
                        "difficulty": entry_data.get("difficulty", ""),
                    }
                )
        return results

    def validate_quiz_submission(
        self, topic_slug: str, submitted_answers: QuizAnswers
    ) -> QuizValidationResult | None:
        """Validate quiz answers against the registry answer key.

        Returns:
            QuizValidationResult or None if quiz not found.
        """
        quiz = self.get_quiz(topic_slug)
        if not quiz:
            return None

        questions = quiz.get("questions", [])
        if not questions:
            return None

        correct_count = 0
        per_question: PerQuestionResults = {}

        for question in questions:
            qid = question.get("id", "")
            correct_answer = question.get("correct_answer", "")
            submitted = submitted_answers.get(qid, "")
            is_correct = submitted == correct_answer
            per_question[qid] = is_correct
            if is_correct:
                correct_count += 1

        total_count = len(questions)
        score = (correct_count / total_count * 100) if total_count > 0 else 0.0
        passing_score = quiz.get("passing_score", 70)
        passed = score >= passing_score

        return QuizValidationResult(
            score=score,
            passed=passed,
            correct_count=correct_count,
            total_count=total_count,
            per_question=per_question,
        )

    def refresh_cache(self) -> dict[str, Any]:
        """Force a cache refresh. Returns status info."""
        try:
            self._load_registry()
            schema_version = (
                self._registry.get("schema_version", "unknown")
                if self._registry
                else "unknown"
            )
            entry_count = (
                len(self._registry.get("entries", {})) if self._registry else 0
            )
            return {
                "success": True,
                "message": "Cache refreshed successfully",
                "schema_version": schema_version,
                "entry_count": entry_count,
            }
        except Exception as e:
            return {
                "success": False,
                "message": "Failed to refresh cache",
                "error": str(e),
            }


# Module-level singleton
_registry_service: ContentRegistryService | None = None


def get_registry_service(s3_bucket: str | None = None) -> ContentRegistryService:
    """Get or create the global registry service singleton.

    Args:
        s3_bucket: Required on first call.

    Returns:
        ContentRegistryService instance.

    Raises:
        ValueError: If s3_bucket is None on first call.
    """
    global _registry_service

    if _registry_service is None:
        if s3_bucket is None:
            raise ValueError("s3_bucket must be provided on first call")
        _registry_service = ContentRegistryService(s3_bucket)

    return _registry_service
