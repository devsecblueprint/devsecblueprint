"""
Property-based tests for cookie handling.

Feature: backend-phase1
"""

from hypothesis import given, strategies as st, settings
from backend.utils.responses import create_cookie

# Strategy for JWT tokens (simplified - just alphanumeric with dots)
jwt_token_strategy = st.from_regex(
    r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", fullmatch=True
)


class TestCookieProperties:
    """Property-based tests for cookie formatting."""

    @settings(max_examples=100)
    @given(jwt_token=jwt_token_strategy)
    def test_property_5_cookie_formatting(self, jwt_token):
        """
        Property 5: Cookie Formatting

        For any valid JWT token, when creating the authentication cookie,
        the Set-Cookie header should:
        - Have name "dsb_token"
        - Include the JWT as the value
        - Include "HttpOnly" attribute
        - Include "Secure" attribute
        - Include "SameSite=Lax" attribute
        - Include "Max-Age=3600" attribute
        - Be properly formatted according to RFC 6265

        **Validates: Requirements 2.5, 12.6**
        """
        # Create cookie with standard authentication parameters
        cookie_header = create_cookie(
            name="dsb_token",
            value=jwt_token,
            max_age=3600,
            secure=True,
            http_only=True,
            same_site="Lax",
        )

        # Verify it's a string
        assert isinstance(cookie_header, str), "Cookie header should be a string"
        assert len(cookie_header) > 0, "Cookie header should not be empty"

        # Property: Has name "dsb_token"
        assert cookie_header.startswith(
            "dsb_token="
        ), f"Cookie should start with 'dsb_token=', got: {cookie_header[:20]}"

        # Property: Includes the JWT as the value
        assert (
            jwt_token in cookie_header
        ), f"Cookie should contain JWT token {jwt_token}"

        # Property: Includes "HttpOnly" attribute
        assert "HttpOnly" in cookie_header, "Cookie should include HttpOnly attribute"

        # Property: Includes "Secure" attribute
        assert "Secure" in cookie_header, "Cookie should include Secure attribute"

        # Property: Includes "SameSite=Lax" attribute
        assert (
            "SameSite=Lax" in cookie_header
        ), "Cookie should include SameSite=Lax attribute"

        # Property: Includes "Max-Age=3600" attribute
        assert (
            "Max-Age=3600" in cookie_header
        ), "Cookie should include Max-Age=3600 attribute"

        # Property: Properly formatted according to RFC 6265
        # Basic format: name=value; attribute1; attribute2; ...
        parts = cookie_header.split(";")
        assert (
            len(parts) >= 5
        ), f"Cookie should have at least 5 parts (name=value + 4 attributes), got {len(parts)}"

        # First part should be name=value
        name_value = parts[0].strip()
        assert "=" in name_value, "First part should be name=value format"
        name, value = name_value.split("=", 1)
        assert name == "dsb_token", f"Cookie name should be 'dsb_token', got {name}"
        assert value == jwt_token, f"Cookie value should be {jwt_token}, got {value}"
