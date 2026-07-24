"""Unit tests for middleware components: CORS, structured logging, and error handler."""

import json
import logging
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.middleware.cors import setup_cors
from app.middleware.logging import LoggingMiddleware
from app.middleware.error_handler import setup_exception_handlers

# ---------------------------------------------------------------------------
# Test app fixture
# ---------------------------------------------------------------------------


def _create_test_app() -> FastAPI:
    """Create a minimal FastAPI app with all middleware for testing."""
    app = FastAPI()

    # Register middleware
    with patch("app.middleware.cors.get_settings") as mock_settings:
        mock_settings.return_value.frontend_origin = "https://devsecblueprint.com"
        mock_settings.return_value.frontend_url = "https://www.devsecblueprint.com"
        setup_cors(app)

    app.add_middleware(LoggingMiddleware)
    setup_exception_handlers(app)

    @app.get("/test-ok")
    async def test_ok():
        return {"message": "ok"}

    @app.get("/test-error")
    async def test_error():
        raise ValueError("secret_db_password in /home/user/.env leaked")

    @app.post("/test-post")
    async def test_post():
        return {"created": True}

    return app


@pytest.fixture
def app():
    return _create_test_app()


@pytest.fixture
def client(app):
    return TestClient(app)


# ---------------------------------------------------------------------------
# CORS Tests
# ---------------------------------------------------------------------------


class TestCORSMiddleware:
    """Tests for CORS middleware configuration."""

    def test_allowed_origin_gets_cors_headers(self, client):
        """An allowed origin should receive Access-Control-Allow-Origin."""
        response = client.get(
            "/test-ok",
            headers={"Origin": "https://devsecblueprint.com"},
        )
        assert response.status_code == 200
        assert (
            response.headers.get("access-control-allow-origin")
            == "https://devsecblueprint.com"
        )

    def test_disallowed_origin_no_cors_header(self, client):
        """A disallowed origin should NOT receive Access-Control-Allow-Origin."""
        response = client.get(
            "/test-ok",
            headers={"Origin": "https://evil.example.com"},
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" not in response.headers

    def test_preflight_allowed_origin(self, client):
        """OPTIONS preflight from allowed origin returns CORS headers."""
        response = client.options(
            "/test-ok",
            headers={
                "Origin": "https://devsecblueprint.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        assert response.status_code == 200
        assert (
            response.headers.get("access-control-allow-origin")
            == "https://devsecblueprint.com"
        )
        assert "access-control-allow-methods" in response.headers

    def test_preflight_disallowed_origin(self, client):
        """OPTIONS preflight from disallowed origin does not return CORS headers."""
        response = client.options(
            "/test-ok",
            headers={
                "Origin": "https://attacker.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "access-control-allow-origin" not in response.headers

    def test_credentials_allowed(self, client):
        """CORS allows credentials (cookies/auth headers)."""
        response = client.get(
            "/test-ok",
            headers={"Origin": "https://devsecblueprint.com"},
        )
        assert response.headers.get("access-control-allow-credentials") == "true"


# ---------------------------------------------------------------------------
# Structured Logging Tests
# ---------------------------------------------------------------------------


class TestLoggingMiddleware:
    """Tests for structured request/response logging."""

    def test_logs_json_with_required_fields(self, client, caplog):
        """Each request should produce a JSON log with method, path, status_code, duration_ms."""
        with caplog.at_level(logging.INFO, logger="app.access"):
            client.get("/test-ok")

        # Find the log entry from our middleware
        log_messages = [r.message for r in caplog.records if r.name == "app.access"]
        assert len(log_messages) >= 1

        entry = json.loads(log_messages[-1])
        assert entry["method"] == "GET"
        assert entry["path"] == "/test-ok"
        assert entry["status_code"] == 200
        assert "duration_ms" in entry
        assert isinstance(entry["duration_ms"], (int, float))

    def test_logs_post_request(self, client, caplog):
        """POST requests are logged with correct method."""
        with caplog.at_level(logging.INFO, logger="app.access"):
            client.post("/test-post")

        log_messages = [r.message for r in caplog.records if r.name == "app.access"]
        assert len(log_messages) >= 1

        entry = json.loads(log_messages[-1])
        assert entry["method"] == "POST"
        assert entry["path"] == "/test-post"
        assert entry["status_code"] == 200

    def test_logs_404_status_code(self, client, caplog):
        """Unknown routes log a 404 status code."""
        with caplog.at_level(logging.INFO, logger="app.access"):
            client.get("/nonexistent-path")

        log_messages = [r.message for r in caplog.records if r.name == "app.access"]
        assert len(log_messages) >= 1

        entry = json.loads(log_messages[-1])
        assert entry["status_code"] == 404
        assert entry["path"] == "/nonexistent-path"

    def test_duration_is_positive(self, client, caplog):
        """Duration should be a positive number."""
        with caplog.at_level(logging.INFO, logger="app.access"):
            client.get("/test-ok")

        log_messages = [r.message for r in caplog.records if r.name == "app.access"]
        entry = json.loads(log_messages[-1])
        assert entry["duration_ms"] > 0


# ---------------------------------------------------------------------------
# Error Handler Tests
# ---------------------------------------------------------------------------


class TestGlobalExceptionHandler:
    """Tests for the global exception handler."""

    def test_returns_500_on_unhandled_exception(self, client):
        """Unhandled exceptions return HTTP 500."""
        response = client.get("/test-error")
        assert response.status_code == 500

    def test_returns_generic_error_body(self, client):
        """Response body contains only a generic error message."""
        response = client.get("/test-error")
        body = response.json()
        assert body == {"detail": "Internal server error"}

    def test_does_not_leak_exception_message(self, client):
        """Response body must not contain the internal exception message."""
        response = client.get("/test-error")
        text = response.text
        assert "secret_db_password" not in text
        assert "/home/user/.env" not in text
        assert "ValueError" not in text

    def test_does_not_leak_stack_trace(self, client):
        """Response must not contain stack trace information."""
        response = client.get("/test-error")
        text = response.text
        assert "Traceback" not in text
        assert "File " not in text

    def test_logs_error_details_internally(self, client, caplog):
        """The error handler should log the exception details for debugging."""
        with caplog.at_level(logging.ERROR, logger="app.error"):
            client.get("/test-error")

        error_records = [r for r in caplog.records if r.name == "app.error"]
        assert len(error_records) >= 1

        record = error_records[-1]
        assert record.levelname == "ERROR"
        # The extra fields should contain error information for internal debugging
        assert hasattr(record, "error_type")
        assert record.error_type == "ValueError"
