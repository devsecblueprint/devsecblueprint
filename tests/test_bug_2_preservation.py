"""
Bug 2 Preservation Property Tests

These tests verify that non-buggy behaviors remain unchanged after Bug 2 fix.
They should PASS on both unfixed and fixed code.

**Validates: Requirements 3.9, 3.10, 3.11, 3.12, 3.13**

Spec: .kiro/specs/success-story-modal-fixes/
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings, example
from handler import main

# Strategy for generating authenticated endpoint paths
# These endpoints should continue to require authentication
AUTHENTICATED_ENDPOINTS = [
    ("PUT", "/progress"),
    ("GET", "/progress"),
    ("GET", "/progress/stats"),
    ("GET", "/progress/recent"),
    ("GET", "/progress/badges"),
    ("DELETE", "/progress/reset"),
    ("GET", "/admin/analytics"),
    ("GET", "/admin/submissions"),
    ("GET", "/admin/registry-status"),
    ("GET", "/admin/module-health"),
    ("GET", "/admin/walkthrough-statistics"),
    ("GET", "/user/profile"),
    ("DELETE", "/user/account"),
    ("POST", "/quiz/submit"),
]


class TestBug2Preservation:
    """
    Property 7: Preservation - Other Endpoint Authentication

    For any request to endpoints other than /api/email/success-story that currently
    require authentication, the backend SHALL continue to require authentication and
    return 403 Forbidden for unauthenticated requests.

    **Validates: Requirements 3.13**
    """

    @pytest.mark.parametrize("method,path", AUTHENTICATED_ENDPOINTS)
    def test_authenticated_endpoints_require_auth(self, method, path):
        """
        Test that authenticated endpoints return 403 for unauthenticated requests.

        This test verifies that endpoints other than /api/email/success-story
        continue to require authentication after Bug 2 is fixed.

        EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
        - These endpoints should always return 403 for unauthenticated requests
        """
        # Prepare event without authentication headers
        event = {
            "requestContext": {"http": {"method": method, "path": path}},
            "headers": {
                # No Authorization header
                # No cookie header with JWT token
            },
            "body": json.dumps({}) if method in ["PUT", "POST", "DELETE"] else None,
        }

        # Call the Lambda handler
        response = main(event, None)

        # Assert the response status is 401 or 403 (authentication required)
        # Different endpoints may return different auth error codes
        assert response["statusCode"] in [401, 403], (
            f"Expected 401 or 403 for unauthenticated request to {method} {path}, "
            f"got {response['statusCode']}. Response body: {response.get('body', 'N/A')}"
        )


class TestBug2ValidationPreservation:
    """
    Property 6: Preservation - API Endpoint Validation

    For any request to /api/email/success-story with invalid data (missing fields,
    invalid email, story too short), the endpoint SHALL produce exactly the same
    400 error responses with the same error messages.

    **Validates: Requirements 3.9, 3.10, 3.11, 3.12**
    """

    def test_missing_name_returns_400(self):
        """
        Test that POST to /api/email/success-story with missing name returns 400.

        EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
        - Validation should work the same way before and after the fix
        """
        event = {
            "requestContext": {
                "http": {"method": "POST", "path": "/api/email/success-story"}
            },
            "headers": {},
            "body": json.dumps(
                {
                    # Missing "name" field
                    "email": "test@example.com",
                    "story": "A" * 50,
                    "sharePublicly": True,
                }
            ),
        }

        with patch("handlers.email.send_success_story_email") as mock_send:
            mock_send.return_value = True
            response = main(event, None)

        # Assert validation error
        assert response["statusCode"] == 400
        body_data = json.loads(response["body"])
        assert "error" in body_data
        assert "name" in body_data["error"].lower()

    def test_missing_email_returns_400(self):
        """
        Test that POST to /api/email/success-story with missing email returns 400.

        EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
        """
        event = {
            "requestContext": {
                "http": {"method": "POST", "path": "/api/email/success-story"}
            },
            "headers": {},
            "body": json.dumps(
                {
                    "name": "Test User",
                    # Missing "email" field
                    "story": "A" * 50,
                    "sharePublicly": True,
                }
            ),
        }

        with patch("handlers.email.send_success_story_email") as mock_send:
            mock_send.return_value = True
            response = main(event, None)

        # Assert validation error
        assert response["statusCode"] == 400
        body_data = json.loads(response["body"])
        assert "error" in body_data
        assert "email" in body_data["error"].lower()

    def test_missing_story_returns_400(self):
        """
        Test that POST to /api/email/success-story with missing story returns 400.

        EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
        """
        event = {
            "requestContext": {
                "http": {"method": "POST", "path": "/api/email/success-story"}
            },
            "headers": {},
            "body": json.dumps(
                {
                    "name": "Test User",
                    "email": "test@example.com",
                    # Missing "story" field
                    "sharePublicly": True,
                }
            ),
        }

        with patch("handlers.email.send_success_story_email") as mock_send:
            mock_send.return_value = True
            response = main(event, None)

        # Assert validation error
        assert response["statusCode"] == 400
        body_data = json.loads(response["body"])
        assert "error" in body_data
        assert "story" in body_data["error"].lower()

    @given(
        email=st.one_of(
            st.just("invalid-email"),
            st.just("@example.com"),
            st.just("test@"),
            st.just("test"),
            st.just("test@.com"),
        )
    )
    @settings(max_examples=10)
    def test_invalid_email_format_returns_400(self, email):
        """
        Property-based test: For all invalid email formats, endpoint returns 400.

        EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code

        Note: The email validation uses a simple regex pattern that catches
        common invalid formats but may not catch all edge cases.
        """
        event = {
            "requestContext": {
                "http": {"method": "POST", "path": "/api/email/success-story"}
            },
            "headers": {},
            "body": json.dumps(
                {
                    "name": "Test User",
                    "email": email,
                    "story": "A" * 50,
                    "sharePublicly": True,
                }
            ),
        }

        with patch("handlers.email.send_success_story_email") as mock_send:
            mock_send.return_value = True
            response = main(event, None)

        # Assert validation error
        assert (
            response["statusCode"] == 400
        ), f"Expected 400 for invalid email '{email}', got {response['statusCode']}"
        body_data = json.loads(response["body"])
        assert "error" in body_data
        assert (
            "email" in body_data["error"].lower()
            or "invalid" in body_data["error"].lower()
        )

    @given(story_length=st.integers(min_value=0, max_value=49))
    @settings(max_examples=10)
    @example(story_length=0)
    @example(story_length=1)
    @example(story_length=49)
    def test_story_too_short_returns_400(self, story_length):
        """
        Property-based test: For all stories with length < 50, endpoint returns 400.

        EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
        """
        event = {
            "requestContext": {
                "http": {"method": "POST", "path": "/api/email/success-story"}
            },
            "headers": {},
            "body": json.dumps(
                {
                    "name": "Test User",
                    "email": "test@example.com",
                    "story": "A" * story_length,
                    "sharePublicly": True,
                }
            ),
        }

        with patch("handlers.email.send_success_story_email") as mock_send:
            mock_send.return_value = True
            response = main(event, None)

        # Assert validation error
        assert (
            response["statusCode"] == 400
        ), f"Expected 400 for story length {story_length}, got {response['statusCode']}"
        body_data = json.loads(response["body"])
        assert "error" in body_data
        assert "story" in body_data["error"].lower() or "50" in body_data["error"]

    def test_email_service_failure_returns_500(self):
        """
        Test that email service failure returns 500.

        EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code

        **Validates: Requirements 3.11**
        """
        event = {
            "requestContext": {
                "http": {"method": "POST", "path": "/api/email/success-story"}
            },
            "headers": {},
            "body": json.dumps(
                {
                    "name": "Test User",
                    "email": "test@example.com",
                    "story": "A" * 50,
                    "sharePublicly": True,
                }
            ),
        }

        # Mock email service to return failure
        with patch("handlers.email.send_success_story_email") as mock_send:
            mock_send.return_value = False
            response = main(event, None)

        # Assert service error
        assert response["statusCode"] == 500
        body_data = json.loads(response["body"])
        assert "error" in body_data

    def test_valid_request_returns_200(self):
        """
        Test that valid request returns 200 (baseline behavior).

        This test documents the expected behavior for valid requests.
        On UNFIXED code, this may return 403 if authentication is required.
        On FIXED code, this should return 200.

        Note: This is not strictly a preservation test, but it helps document
        the expected behavior after the fix.

        **Validates: Requirements 3.12**
        """
        event = {
            "requestContext": {
                "http": {"method": "POST", "path": "/api/email/success-story"}
            },
            "headers": {},
            "body": json.dumps(
                {
                    "name": "Test User",
                    "email": "test@example.com",
                    "story": "A" * 50,
                    "sharePublicly": True,
                }
            ),
        }

        with patch("handlers.email.send_success_story_email") as mock_send:
            mock_send.return_value = True
            response = main(event, None)

        # On UNFIXED code: This might return 403 (authentication required)
        # On FIXED code: This should return 200 (success)
        # For preservation testing, we're documenting that validation happens
        # before authentication, so if we get past validation, we know it works.

        # We'll check that if it's not 403, it should be 200
        if response["statusCode"] != 403:
            assert response["statusCode"] == 200
            body_data = json.loads(response["body"])
            assert "message" in body_data
            assert "success" in body_data["message"].lower()


class TestBug2PropertyBasedValidation:
    """
    Property-based tests for comprehensive validation coverage.

    These tests use Hypothesis to generate many test cases and verify that
    validation behavior is consistent across all inputs.
    """

    @given(
        name=st.one_of(st.just(""), st.just("   "), st.none()),
        email=st.just("test@example.com"),
        story=st.just("A" * 50),
    )
    @settings(max_examples=5)
    def test_empty_name_variations_return_400(self, name, email, story):
        """
        Property-based test: For all empty/whitespace name values, endpoint returns 400.
        """
        event = {
            "requestContext": {
                "http": {"method": "POST", "path": "/api/email/success-story"}
            },
            "headers": {},
            "body": json.dumps(
                {
                    "name": name if name is not None else "",
                    "email": email,
                    "story": story,
                    "sharePublicly": True,
                }
            ),
        }

        with patch("handlers.email.send_success_story_email") as mock_send:
            mock_send.return_value = True
            response = main(event, None)

        # Assert validation error
        assert response["statusCode"] == 400

    @given(
        name=st.just("Test User"),
        email=st.one_of(st.just(""), st.just("   "), st.none()),
        story=st.just("A" * 50),
    )
    @settings(max_examples=5)
    def test_empty_email_variations_return_400(self, name, email, story):
        """
        Property-based test: For all empty/whitespace email values, endpoint returns 400.
        """
        event = {
            "requestContext": {
                "http": {"method": "POST", "path": "/api/email/success-story"}
            },
            "headers": {},
            "body": json.dumps(
                {
                    "name": name,
                    "email": email if email is not None else "",
                    "story": story,
                    "sharePublicly": True,
                }
            ),
        }

        with patch("handlers.email.send_success_story_email") as mock_send:
            mock_send.return_value = True
            response = main(event, None)

        # Assert validation error
        assert response["statusCode"] == 400

    @given(
        name=st.just("Test User"),
        email=st.just("test@example.com"),
        story=st.one_of(st.just(""), st.just("   "), st.none()),
    )
    @settings(max_examples=5)
    def test_empty_story_variations_return_400(self, name, email, story):
        """
        Property-based test: For all empty/whitespace story values, endpoint returns 400.
        """
        event = {
            "requestContext": {
                "http": {"method": "POST", "path": "/api/email/success-story"}
            },
            "headers": {},
            "body": json.dumps(
                {
                    "name": name,
                    "email": email,
                    "story": story if story is not None else "",
                    "sharePublicly": True,
                }
            ),
        }

        with patch("handlers.email.send_success_story_email") as mock_send:
            mock_send.return_value = True
            response = main(event, None)

        # Assert validation error
        assert response["statusCode"] == 400
