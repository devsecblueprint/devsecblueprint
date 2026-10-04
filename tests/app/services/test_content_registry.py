"""Unit tests for app.services.content_registry.

Covers S3 load, schema validation, TTL cache refresh, quiz/walkthrough getters,
quiz submission validation, forced refresh, and the singleton accessor.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import content_registry as mod
from app.services.content_registry import (
    ContentRegistryService,
    SchemaVersionError,
    get_registry_service,
)

REGISTRY = {
    "schema_version": "1.0.0",
    "entries": {
        "python-quiz": {
            "content_type": "quiz",
            "passing_score": 70,
            "questions": [
                {"id": "q1", "correct_answer": "a"},
                {"id": "q2", "correct_answer": "b"},
            ],
        },
        "k8s-walkthrough": {
            "content_type": "walkthrough",
            "difficulty": "Intermediate",
        },
    },
}


def _s3_client_returning(registry: dict) -> MagicMock:
    client = MagicMock()
    body = MagicMock()
    body.read.return_value = json.dumps(registry).encode("utf-8")
    client.get_object.return_value = {"Body": body}
    return client


def _build(registry: dict = REGISTRY, **kwargs) -> ContentRegistryService:
    client = _s3_client_returning(registry)
    with patch.object(mod.boto3, "client", return_value=client):
        return ContentRegistryService("test-bucket", **kwargs)


@pytest.fixture(autouse=True)
def _reset_singleton():
    mod._registry_service = None
    yield
    mod._registry_service = None


class TestLoad:
    def test_loads_and_parses_registry(self):
        svc = _build()
        assert svc._registry == REGISTRY
        assert svc._last_loaded_at is not None

    def test_s3_client_error_propagates(self):
        client = MagicMock()
        client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "x"}}, "GetObject"
        )
        with patch.object(mod.boto3, "client", return_value=client):
            with pytest.raises(ClientError):
                ContentRegistryService("test-bucket")

    def test_invalid_json_raises(self):
        client = MagicMock()
        body = MagicMock()
        body.read.return_value = b"not json{"
        client.get_object.return_value = {"Body": body}
        with patch.object(mod.boto3, "client", return_value=client):
            with pytest.raises(json.JSONDecodeError):
                ContentRegistryService("test-bucket")


class TestSchemaValidation:
    def test_missing_schema_version_raises(self):
        with pytest.raises(SchemaVersionError, match="missing schema_version"):
            _build({"entries": {}})

    def test_incompatible_major_version_raises(self):
        with pytest.raises(SchemaVersionError, match="Incompatible schema"):
            _build({"schema_version": "2.0.0", "entries": {}})

    def test_compatible_minor_version_ok(self):
        svc = _build({"schema_version": "1.5.9", "entries": {}})
        assert svc._registry is not None


class TestGetters:
    def test_get_quiz_returns_quiz_entry(self):
        svc = _build()
        quiz = svc.get_quiz("python-quiz")
        assert quiz is not None
        assert quiz["passing_score"] == 70

    def test_get_quiz_wrong_type_returns_none(self):
        svc = _build()
        assert svc.get_quiz("k8s-walkthrough") is None

    def test_get_quiz_missing_returns_none(self):
        svc = _build()
        assert svc.get_quiz("nope") is None

    def test_get_walkthrough_returns_entry(self):
        svc = _build()
        wt = svc.get_walkthrough("k8s-walkthrough")
        assert wt is not None
        assert wt["difficulty"] == "Intermediate"

    def test_get_walkthrough_wrong_type_returns_none(self):
        svc = _build()
        assert svc.get_walkthrough("python-quiz") is None

    def test_get_all_walkthroughs(self):
        svc = _build()
        result = svc.get_all_walkthroughs()
        assert result == [{"id": "k8s-walkthrough", "difficulty": "Intermediate"}]


class TestQuizValidation:
    def test_all_correct_passes(self):
        svc = _build()
        result = svc.validate_quiz_submission("python-quiz", {"q1": "a", "q2": "b"})
        assert result is not None
        assert result.score == 100.0
        assert result.passed is True
        assert result.correct_count == 2
        assert result.per_question == {"q1": True, "q2": True}

    def test_partial_fails(self):
        svc = _build()
        result = svc.validate_quiz_submission("python-quiz", {"q1": "a", "q2": "x"})
        assert result.score == 50.0
        assert result.passed is False
        assert result.per_question == {"q1": True, "q2": False}

    def test_unknown_quiz_returns_none(self):
        svc = _build()
        assert svc.validate_quiz_submission("nope", {}) is None

    def test_quiz_with_no_questions_returns_none(self):
        reg = {
            "schema_version": "1.0.0",
            "entries": {"empty": {"content_type": "quiz", "questions": []}},
        }
        svc = _build(reg)
        assert svc.validate_quiz_submission("empty", {}) is None


class TestCacheRefresh:
    def test_no_refresh_when_ttl_none(self):
        svc = _build(cache_ttl_seconds=None)
        with patch.object(svc, "_load_registry") as load:
            svc._refresh_if_needed()
            load.assert_not_called()

    def test_refresh_when_ttl_elapsed(self):
        svc = _build(cache_ttl_seconds=1)
        svc._last_loaded_at = 0.0  # far in the past
        with patch.object(svc, "_load_registry") as load:
            svc._refresh_if_needed()
            load.assert_called_once()

    def test_refresh_failure_keeps_stale_data(self):
        svc = _build(cache_ttl_seconds=1)
        svc._last_loaded_at = 0.0
        with patch.object(svc, "_load_registry", side_effect=RuntimeError("s3 down")):
            # Should not raise; logs and keeps stale registry.
            svc._refresh_if_needed()
        assert svc._registry == REGISTRY

    def test_refresh_cache_success(self):
        svc = _build()
        # refresh_cache re-fetches from S3, so keep boto3 patched for the call.
        client = _s3_client_returning(REGISTRY)
        with patch.object(mod.boto3, "client", return_value=client):
            result = svc.refresh_cache()
        assert result["success"] is True
        assert result["entry_count"] == 2
        assert result["schema_version"] == "1.0.0"

    def test_refresh_cache_failure_returns_error(self):
        svc = _build()
        with patch.object(svc, "_load_registry", side_effect=RuntimeError("boom")):
            result = svc.refresh_cache()
        assert result["success"] is False
        assert "boom" in result["error"]


class TestSingleton:
    def test_first_call_requires_bucket(self):
        with pytest.raises(ValueError, match="s3_bucket must be provided"):
            get_registry_service(None)

    def test_singleton_reused(self):
        client = _s3_client_returning(REGISTRY)
        with patch.object(mod.boto3, "client", return_value=client):
            first = get_registry_service("test-bucket")
            second = get_registry_service()  # no bucket needed after first
        assert first is second
