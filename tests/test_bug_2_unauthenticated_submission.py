"""
Bug Condition Exploration Test for Bug 2: Unauthenticated Success Story Submission

This test verifies Bug 2 exists by attempting to submit a success story without
authentication headers. On UNFIXED code, this test is EXPECTED TO FAIL with a
403 Forbidden response, confirming the bug exists.

**Validates: Requirements 2.4, 2.5**
"""

import json
import pytest
from unittest.mock import patch
from handler import main


def test_unauthenticated_success_story_submission():
    """
    Test that POST to /api/email/success-story without authentication processes the request.

    This is a bug condition exploration test. On UNFIXED code, this test should FAIL
    because the endpoint incorrectly returns 403 Forbidden for unauthenticated requests.

    When the bug is fixed, this test will PASS, confirming that the endpoint accepts
    unauthenticated requests as intended.

    **EXPECTED OUTCOME ON UNFIXED CODE**: Test FAILS (returns 403 Forbidden)
    **EXPECTED OUTCOME ON FIXED CODE**: Test PASSES (returns 200 OK)

    Counterexample: Unauthenticated request with valid data returns 403 instead of 200

    **Validates: Requirements 2.4, 2.5**
    """
    # Prepare event with valid success story data but NO authentication headers
    event = {
        "requestContext": {
            "http": {"method": "POST", "path": "/api/email/success-story"}
        },
        "headers": {
            # No Authorization header
            # No cookie header with JWT token
        },
        "body": json.dumps(
            {
                "name": "Test User",
                "email": "test@example.com",
                "story": "A" * 50,  # Minimum 50 characters
                "sharePublicly": True,
            }
        ),
    }

    # Mock the email sending service to avoid actual email sending
    with patch("handlers.email.send_success_story_email") as mock_send:
        mock_send.return_value = True

        # Call the Lambda handler
        response = main(event, None)

    # Assert the response status is 200 (expected behavior after fix)
    # On UNFIXED code, this will be 403, causing the test to FAIL
    assert response["statusCode"] == 200, (
        f"Expected 200 OK for unauthenticated request, got {response['statusCode']}. "
        f"Response body: {response.get('body', 'N/A')}"
    )

    # Assert the response indicates success
    body_data = json.loads(response["body"])
    assert "message" in body_data
    assert "success" in body_data["message"].lower()

    # Assert the email service was called (request was processed)
    mock_send.assert_called_once()
