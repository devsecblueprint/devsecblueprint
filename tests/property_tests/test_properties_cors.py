"""
Property-based tests for CORS headers.

Feature: backend-phase1
"""

from hypothesis import given, strategies as st, settings
from backend.utils.responses import json_response, redirect_response, error_response

# Strategy for response bodies
response_body_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20),
    values=st.one_of(st.text(max_size=100), st.integers(), st.booleans()),
    min_size=0,
    max_size=5,
)

# Strategy for status codes
success_status_strategy = st.sampled_from([200, 201, 204])
error_status_strategy = st.sampled_from([400, 401, 403, 404, 500, 502, 503])
redirect_status_strategy = st.just(302)

# Strategy for URLs
url_strategy = st.from_regex(
    r"https://[a-z0-9\-\.]+\.[a-z]{2,}/[a-z0-9\-/]*", fullmatch=True
)


class TestCORSProperties:
    """Property-based tests for CORS headers presence."""

    @settings(max_examples=100)
    @given(status_code=success_status_strategy, body=response_body_strategy)
    def test_property_17_cors_headers_in_json_responses(self, status_code, body):
        """
        Property 17: CORS Headers Presence (JSON Responses)

        For any JSON response from any endpoint, the response headers should include:
        - Access-Control-Allow-Origin: https://devsecblueprint.com
        - Access-Control-Allow-Credentials: true
        - Access-Control-Allow-Methods: GET, PUT, OPTIONS (or appropriate subset)
        - Access-Control-Allow-Headers: Content-Type, Cookie (or appropriate subset)

        **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
        """
        # Create JSON response
        response = json_response(status_code, body)

        # Verify response structure
        assert "headers" in response, "Response should have headers"
        headers = response["headers"]

        # Property: Access-Control-Allow-Origin is set correctly
        assert (
            "Access-Control-Allow-Origin" in headers
        ), "Response should include Access-Control-Allow-Origin header"
        assert (
            headers["Access-Control-Allow-Origin"] == "https://devsecblueprint.com"
        ), f"Access-Control-Allow-Origin should be https://devsecblueprint.com, got {headers['Access-Control-Allow-Origin']}"

        # Property: Access-Control-Allow-Credentials is set to true
        assert (
            "Access-Control-Allow-Credentials" in headers
        ), "Response should include Access-Control-Allow-Credentials header"
        assert (
            headers["Access-Control-Allow-Credentials"] == "true"
        ), f"Access-Control-Allow-Credentials should be 'true', got {headers['Access-Control-Allow-Credentials']}"

        # Property: Access-Control-Allow-Methods is present
        assert (
            "Access-Control-Allow-Methods" in headers
        ), "Response should include Access-Control-Allow-Methods header"

        # Property: Access-Control-Allow-Headers is present
        assert (
            "Access-Control-Allow-Headers" in headers
        ), "Response should include Access-Control-Allow-Headers header"

    @settings(max_examples=100)
    @given(location=url_strategy)
    def test_property_17_cors_headers_in_redirect_responses(self, location):
        """
        Property 17: CORS Headers Presence (Redirect Responses)

        For any redirect response, the response headers should include CORS headers.

        **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
        """
        # Create redirect response
        response = redirect_response(location)

        # Verify response structure
        assert "headers" in response, "Response should have headers"
        headers = response["headers"]

        # Property: CORS headers are present
        assert (
            "Access-Control-Allow-Origin" in headers
        ), "Redirect response should include Access-Control-Allow-Origin header"
        assert headers["Access-Control-Allow-Origin"] == "https://devsecblueprint.com"

        assert (
            "Access-Control-Allow-Credentials" in headers
        ), "Redirect response should include Access-Control-Allow-Credentials header"
        assert headers["Access-Control-Allow-Credentials"] == "true"

    @settings(max_examples=100)
    @given(status_code=error_status_strategy, message=st.text(min_size=1, max_size=100))
    def test_property_17_cors_headers_in_error_responses(self, status_code, message):
        """
        Property 17: CORS Headers Presence (Error Responses)

        For any error response, the response headers should include CORS headers.

        **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
        """
        # Create error response
        response = error_response(status_code, message)

        # Verify response structure
        assert "headers" in response, "Response should have headers"
        headers = response["headers"]

        # Property: CORS headers are present
        assert (
            "Access-Control-Allow-Origin" in headers
        ), "Error response should include Access-Control-Allow-Origin header"
        assert headers["Access-Control-Allow-Origin"] == "https://devsecblueprint.com"

        assert (
            "Access-Control-Allow-Credentials" in headers
        ), "Error response should include Access-Control-Allow-Credentials header"
        assert headers["Access-Control-Allow-Credentials"] == "true"
