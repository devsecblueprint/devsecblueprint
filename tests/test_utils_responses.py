"""
Unit tests for utils/responses.py response formatting functions.
"""

import json
import pytest
from backend.utils.responses import (
    add_cors_headers,
    json_response,
    redirect_response,
    error_response,
    create_cookie,
)


class TestAddCorsHeaders:
    """Test CORS header addition."""

    def test_adds_cors_headers_to_empty_dict(self):
        """Should add all CORS headers to empty dictionary."""
        headers = add_cors_headers()

        assert headers["Access-Control-Allow-Origin"] == "https://devsecblueprint.com"
        assert headers["Access-Control-Allow-Credentials"] == "true"
        assert headers["Access-Control-Allow-Methods"] == "GET, PUT, OPTIONS"
        assert headers["Access-Control-Allow-Headers"] == "Content-Type, Cookie"

    def test_adds_cors_headers_to_existing_headers(self):
        """Should preserve existing headers and add CORS headers."""
        existing = {"Content-Type": "application/json", "X-Custom": "value"}
        headers = add_cors_headers(existing)

        assert headers["Content-Type"] == "application/json"
        assert headers["X-Custom"] == "value"
        assert headers["Access-Control-Allow-Origin"] == "https://devsecblueprint.com"
        assert headers["Access-Control-Allow-Credentials"] == "true"

    def test_handles_none_input(self):
        """Should handle None input gracefully."""
        headers = add_cors_headers(None)

        assert "Access-Control-Allow-Origin" in headers
        assert len(headers) == 4


class TestJsonResponse:
    """Test JSON response formatting."""

    def test_creates_valid_json_response(self):
        """Should create properly formatted JSON response."""
        response = json_response(200, {"message": "success"})

        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "application/json"
        assert "Access-Control-Allow-Origin" in response["headers"]

        body = json.loads(response["body"])
        assert body["message"] == "success"

    def test_includes_cors_headers(self):
        """Should include CORS headers in response."""
        response = json_response(200, {"data": "test"})

        assert (
            response["headers"]["Access-Control-Allow-Origin"]
            == "https://devsecblueprint.com"
        )
        assert response["headers"]["Access-Control-Allow-Credentials"] == "true"

    def test_preserves_additional_headers(self):
        """Should preserve additional headers passed in."""
        response = json_response(200, {"data": "test"}, {"X-Custom": "header"})

        assert response["headers"]["X-Custom"] == "header"
        assert response["headers"]["Content-Type"] == "application/json"

    def test_serializes_complex_body(self):
        """Should serialize complex nested structures."""
        body = {
            "user_id": "12345",
            "authenticated": True,
            "metadata": {"role": "user", "count": 42},
        }
        response = json_response(200, body)

        parsed = json.loads(response["body"])
        assert parsed["user_id"] == "12345"
        assert parsed["authenticated"] is True
        assert parsed["metadata"]["count"] == 42


class TestRedirectResponse:
    """Test redirect response formatting."""

    def test_creates_redirect_without_cookies(self):
        """Should create 302 redirect response."""
        response = redirect_response("https://example.com/callback")

        assert response["statusCode"] == 302
        assert response["headers"]["Location"] == "https://example.com/callback"
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["body"] == ""

    def test_creates_redirect_with_single_cookie(self):
        """Should include Set-Cookie header with single cookie."""
        cookie = "dsb_token=abc123; Max-Age=3600; Secure; HttpOnly"
        response = redirect_response("https://example.com", [cookie])

        assert response["statusCode"] == 302
        assert response["headers"]["Set-Cookie"] == cookie

    def test_creates_redirect_with_multiple_cookies(self):
        """Should handle multiple cookies as array."""
        cookies = ["cookie1=value1; Max-Age=3600", "cookie2=value2; Max-Age=7200"]
        response = redirect_response("https://example.com", cookies)

        assert response["statusCode"] == 302
        assert response["headers"]["Set-Cookie"] == cookies

    def test_includes_cors_headers(self):
        """Should include CORS headers in redirect."""
        response = redirect_response("https://example.com")

        assert (
            response["headers"]["Access-Control-Allow-Origin"]
            == "https://devsecblueprint.com"
        )
        assert response["headers"]["Access-Control-Allow-Credentials"] == "true"


class TestErrorResponse:
    """Test error response formatting."""

    def test_creates_400_error(self):
        """Should create 400 Bad Request error."""
        response = error_response(400, "Invalid request")

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "Invalid request"

    def test_creates_401_error(self):
        """Should create 401 Unauthorized error."""
        response = error_response(401, "Authentication failed")

        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert body["error"] == "Authentication failed"

    def test_creates_404_error(self):
        """Should create 404 Not Found error."""
        response = error_response(404, "Not found")

        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"] == "Not found"

    def test_creates_500_error(self):
        """Should create 500 Internal Server Error."""
        response = error_response(500, "Internal server error")

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["error"] == "Internal server error"

    def test_includes_cors_headers(self):
        """Should include CORS headers in error response."""
        response = error_response(500, "Error")

        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["headers"]["Content-Type"] == "application/json"

    def test_does_not_expose_sensitive_info(self):
        """Should only include generic error message."""
        response = error_response(500, "Service temporarily unavailable")

        body = json.loads(response["body"])
        assert "error" in body
        assert "stack" not in body
        assert "trace" not in body


class TestCreateCookie:
    """Test cookie creation."""

    def test_creates_basic_cookie(self):
        """Should create cookie with all default attributes."""
        cookie = create_cookie("dsb_token", "jwt_value", 3600)

        assert "dsb_token=jwt_value" in cookie
        assert "Max-Age=3600" in cookie
        assert "Secure" in cookie
        assert "HttpOnly" in cookie
        assert "SameSite=Lax" in cookie

    def test_creates_cookie_without_secure(self):
        """Should create cookie without Secure flag when disabled."""
        cookie = create_cookie("test", "value", 3600, secure=False)

        assert "test=value" in cookie
        assert "Secure" not in cookie
        assert "HttpOnly" in cookie

    def test_creates_cookie_without_httponly(self):
        """Should create cookie without HttpOnly flag when disabled."""
        cookie = create_cookie("test", "value", 3600, http_only=False)

        assert "test=value" in cookie
        assert "HttpOnly" not in cookie
        assert "Secure" in cookie

    def test_creates_cookie_with_different_samesite(self):
        """Should support different SameSite values."""
        cookie = create_cookie("test", "value", 3600, same_site="Strict")

        assert "SameSite=Strict" in cookie

    def test_creates_cookie_without_samesite(self):
        """Should create cookie without SameSite when empty string."""
        cookie = create_cookie("test", "value", 3600, same_site="")

        assert "SameSite" not in cookie

    def test_cookie_format_matches_rfc6265(self):
        """Should format cookie according to RFC 6265."""
        cookie = create_cookie("dsb_token", "abc123", 3600)

        # Should be semicolon-separated
        parts = cookie.split("; ")
        # Should have: name=value, Max-Age, Path, Secure, HttpOnly, SameSite
        assert len(parts) == 6
        assert parts[0] == "dsb_token=abc123"
        assert parts[1] == "Max-Age=3600"
        assert parts[2] == "Path=/"

    def test_creates_cookie_with_special_characters_in_value(self):
        """Should handle JWT tokens with special characters."""
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        cookie = create_cookie("dsb_token", jwt_token, 3600)

        assert f"dsb_token={jwt_token}" in cookie
        assert "Max-Age=3600" in cookie
