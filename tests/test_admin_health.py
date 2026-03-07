"""
Unit tests for admin module health handler.

Tests the handle_get_module_health endpoint.
"""

import pytest
from unittest.mock import Mock, patch
from backend.handlers.admin_health import build_module_health, validate_entry, log_error


class TestBuildModuleHealth:
    """Test the build_module_health function."""

    def test_builds_health_with_all_fields(self):
        """Test that build_module_health includes all required fields."""
        mock_service = Mock()
        mock_service._registry = {
            "entries": {
                "quiz1": {
                    "content_type": "quiz",
                    "title": "Test Quiz",
                    "description": "A test quiz",
                    "quiz": {"passing_score": 80, "questions": [{"id": "q1"}]},
                },
                "module1": {
                    "content_type": "module",
                    "title": "Test Module",
                    "description": "A test module",
                },
                "capstone1": {
                    "content_type": "capstone",
                    "title": "Test Capstone",
                    "description": "A test capstone",
                    "capstone": {"repo": "test"},
                },
                "walkthrough1": {
                    "content_type": "walkthrough",
                    "title": "Test Walkthrough",
                    "description": "A test walkthrough",
                    "walkthrough": {"steps": []},
                },
            }
        }

        health = build_module_health(mock_service)

        assert health["total_modules"] == 4
        assert health["validation_pass_percentage"] == 100.0
        assert health["content_by_type"]["quiz"] == 1
        assert health["content_by_type"]["module"] == 1
        assert health["content_by_type"]["capstone"] == 1
        assert health["content_by_type"]["walkthrough"] == 1
        assert health["validation_errors"] == []
        assert health["status"] == "healthy"

    def test_counts_entries_by_type(self):
        """Test that entries are correctly counted by content_type."""
        mock_service = Mock()
        mock_service._registry = {
            "entries": {
                "quiz1": {
                    "content_type": "quiz",
                    "title": "Q1",
                    "description": "D1",
                    "quiz": {"passing_score": 80, "questions": []},
                },
                "quiz2": {
                    "content_type": "quiz",
                    "title": "Q2",
                    "description": "D2",
                    "quiz": {"passing_score": 80, "questions": []},
                },
                "module1": {
                    "content_type": "module",
                    "title": "M1",
                    "description": "D1",
                },
                "module2": {
                    "content_type": "module",
                    "title": "M2",
                    "description": "D2",
                },
                "module3": {
                    "content_type": "module",
                    "title": "M3",
                    "description": "D3",
                },
                "capstone1": {
                    "content_type": "capstone",
                    "title": "C1",
                    "description": "D1",
                    "capstone": {},
                },
                "walkthrough1": {
                    "content_type": "walkthrough",
                    "title": "W1",
                    "description": "D1",
                    "walkthrough": {},
                },
            }
        }

        health = build_module_health(mock_service)

        assert health["content_by_type"]["quiz"] == 2
        assert health["content_by_type"]["module"] == 3
        assert health["content_by_type"]["capstone"] == 1
        assert health["content_by_type"]["walkthrough"] == 1

    def test_detects_validation_errors(self):
        """Test that validation errors are detected and included."""
        mock_service = Mock()
        mock_service._registry = {
            "entries": {
                "valid_module": {
                    "content_type": "module",
                    "title": "Valid Module",
                    "description": "A valid module",
                },
                "invalid_entry": "not a dictionary",  # Invalid structure
            }
        }

        health = build_module_health(mock_service)

        assert health["total_modules"] == 2
        assert len(health["validation_errors"]) == 1
        assert health["validation_errors"][0]["module_id"] == "invalid_entry"
        assert health["validation_errors"][0]["error_type"] == "invalid_structure"
        assert "dictionary" in health["validation_errors"][0]["error_message"]

    def test_calculates_validation_percentage(self):
        """Test that validation pass percentage is calculated correctly."""
        mock_service = Mock()
        mock_service._registry = {
            "entries": {
                "valid1": {
                    "content_type": "module",
                    "title": "V1",
                    "description": "D1",
                },
                "valid2": {
                    "content_type": "module",
                    "title": "V2",
                    "description": "D2",
                },
                "valid3": {
                    "content_type": "module",
                    "title": "V3",
                    "description": "D3",
                },
                "invalid1": "not a dict",  # Invalid structure
                "invalid2": ["also", "invalid"],  # Invalid structure
            }
        }

        health = build_module_health(mock_service)

        # 3 valid out of 5 total = 60%
        assert health["total_modules"] == 5
        # 2 invalid entries
        assert len(health["validation_errors"]) == 2
        assert health["validation_pass_percentage"] == 60.0

    def test_status_healthy_when_100_percent(self):
        """Test that status is 'healthy' when validation is 100%."""
        mock_service = Mock()
        mock_service._registry = {
            "entries": {
                "module1": {
                    "content_type": "module",
                    "title": "M1",
                    "description": "D1",
                }
            }
        }

        health = build_module_health(mock_service)

        assert health["validation_pass_percentage"] == 100.0
        assert health["status"] == "healthy"

    def test_status_warning_when_90_to_99_percent(self):
        """Test that status is 'warning' when validation is 90-99%."""
        mock_service = Mock()
        # Create 95 valid entries and 5 invalid entries
        valid_entries = {
            f"valid{i}": {
                "content_type": "module",
                "title": f"M{i}",
                "description": f"D{i}",
            }
            for i in range(95)
        }
        invalid_entries = {f"invalid{i}": f"not_a_dict_{i}" for i in range(5)}

        mock_service._registry = {"entries": {**valid_entries, **invalid_entries}}

        health = build_module_health(mock_service)

        # 95 valid out of 100 = 95%
        assert health["validation_pass_percentage"] == 95.0
        assert health["status"] == "warning"

    def test_status_error_when_below_90_percent(self):
        """Test that status is 'error' when validation is below 90%."""
        mock_service = Mock()
        mock_service._registry = {
            "entries": {
                "valid1": {
                    "content_type": "module",
                    "title": "M1",
                    "description": "D1",
                },
                "invalid1": "not a dict",
                "invalid2": ["also", "invalid"],
            }
        }

        health = build_module_health(mock_service)

        # 1 valid out of 3 = 33.3%
        assert health["validation_pass_percentage"] == 33.3
        assert health["status"] == "error"

    def test_handles_empty_registry(self):
        """Test that empty registry returns 100% validation."""
        mock_service = Mock()
        mock_service._registry = {"entries": {}}

        health = build_module_health(mock_service)

        assert health["total_modules"] == 0
        assert health["validation_pass_percentage"] == 100.0
        assert health["validation_errors"] == []
        assert health["status"] == "healthy"

    def test_handles_unknown_content_type(self):
        """Test that unknown content types are counted as modules."""
        mock_service = Mock()
        mock_service._registry = {
            "entries": {
                "unknown1": {
                    "content_type": "unknown_type",
                    "title": "Unknown",
                    "description": "Unknown type",
                }
            }
        }

        health = build_module_health(mock_service)

        assert health["content_by_type"]["module"] == 1
        assert health["total_modules"] == 1


class TestValidateEntry:
    """Test the validate_entry function."""

    def test_valid_dict_entry_has_no_errors(self):
        """Test that a valid dictionary entry has no validation errors."""
        entry = {
            "content_type": "module",
            "title": "Test Module",
            "description": "A test module",
        }

        errors = validate_entry(entry, "test-module")

        assert errors == []

    def test_valid_quiz_has_no_errors(self):
        """Test that a valid quiz entry has no validation errors."""
        entry = {
            "content_type": "quiz",
            "title": "Test Quiz",
            "description": "A test quiz",
        }

        errors = validate_entry(entry, "test-quiz")

        assert errors == []

    def test_valid_walkthrough_has_no_errors(self):
        """Test that a valid walkthrough entry has no validation errors."""
        entry = {
            "content_type": "walkthrough",
            "title": "Test Walkthrough",
            "description": "A test walkthrough",
        }

        errors = validate_entry(entry, "test-walkthrough")

        assert errors == []

    def test_valid_capstone_has_no_errors(self):
        """Test that a valid capstone entry has no validation errors."""
        entry = {
            "content_type": "capstone",
            "title": "Test Capstone",
            "description": "A test capstone",
        }

        errors = validate_entry(entry, "test-capstone")

        assert errors == []

    def test_minimal_entry_has_no_errors(self):
        """Test that minimal entry (just content_type) has no validation errors."""
        entry = {"content_type": "module"}

        errors = validate_entry(entry, "test-module")

        assert errors == []

    def test_empty_dict_has_no_errors(self):
        """Test that empty dictionary has no validation errors."""
        entry = {}

        errors = validate_entry(entry, "test-entry")

        assert errors == []

    def test_non_dict_entry_creates_error(self):
        """Test that non-dictionary entry creates validation error."""
        entry = "not a dictionary"

        errors = validate_entry(entry, "test-entry")

        assert len(errors) == 1
        assert errors[0]["module_id"] == "test-entry"
        assert errors[0]["error_type"] == "invalid_structure"
        assert "dictionary" in errors[0]["error_message"]

    def test_list_entry_creates_error(self):
        """Test that list entry creates validation error."""
        entry = ["not", "a", "dict"]

        errors = validate_entry(entry, "test-entry")

        assert len(errors) == 1
        assert errors[0]["module_id"] == "test-entry"
        assert errors[0]["error_type"] == "invalid_structure"

    def test_none_entry_creates_error(self):
        """Test that None entry creates validation error."""
        entry = None

        errors = validate_entry(entry, "test-entry")

        assert len(errors) == 1
        assert errors[0]["module_id"] == "test-entry"
        assert errors[0]["error_type"] == "invalid_structure"


class TestLogError:
    """Test the log_error function."""

    @patch("backend.handlers.admin_health.logger")
    def test_logs_error_with_all_fields(self, mock_logger):
        """Test that log_error creates structured log entry."""
        log_error(
            endpoint="test_endpoint",
            error_type="TestError",
            error_message="Test error message",
            username="test_admin",
            user_id="github|12345",
            context={"bucket": "test-bucket"},
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
        assert extra["context"]["bucket"] == "test-bucket"
        assert "timestamp" in extra
        assert "stack_trace" in extra

    @patch("backend.handlers.admin_health.logger")
    def test_handles_missing_optional_fields(self, mock_logger):
        """Test that log_error handles missing optional fields."""
        log_error(
            endpoint="test_endpoint",
            error_type="TestError",
            error_message="Test error message",
        )

        # Verify logger.error was called
        assert mock_logger.error.called

        # Get the extra dict
        extra = mock_logger.error.call_args[1]["extra"]
        assert extra["username"] == "unknown"
        assert extra["user_id"] == "unknown"
        assert "context" not in extra
