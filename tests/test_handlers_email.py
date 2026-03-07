"""
Unit tests for handlers/email.py
"""

import json
import pytest
from unittest.mock import patch

from handlers import email


@pytest.fixture
def mock_send_success_story_email():
    """Mock send_success_story_email function."""
    with patch("handlers.email.send_success_story_email") as mock:
        mock.return_value = True
        yield mock


def test_handle_send_success_story_valid_request(mock_send_success_story_email):
    """Test successful email sending with valid request."""
    headers = {}
    body = json.dumps(
        {
            "name": "John Doe",
            "email": "john@example.com",
            "story": "A" * 50,  # Minimum 50 characters
            "sharePublicly": True,
        }
    )

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 200
    body_data = json.loads(response["body"])
    assert body_data["message"] == "Success story sent successfully"
    mock_send_success_story_email.assert_called_once_with(
        "John Doe", "john@example.com", "A" * 50, True
    )


def test_handle_send_success_story_share_publicly_false(mock_send_success_story_email):
    """Test email sending with sharePublicly set to False."""
    headers = {}
    body = json.dumps(
        {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "story": "B" * 50,
            "sharePublicly": False,
        }
    )

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 200
    mock_send_success_story_email.assert_called_once_with(
        "Jane Smith", "jane@example.com", "B" * 50, False
    )


def test_handle_send_success_story_missing_name(mock_send_success_story_email):
    """Test request with missing name field."""
    headers = {}
    body = json.dumps(
        {"email": "john@example.com", "story": "A" * 50, "sharePublicly": True}
    )

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 400
    body_data = json.loads(response["body"])
    assert "name" in body_data["error"]
    mock_send_success_story_email.assert_not_called()


def test_handle_send_success_story_empty_name(mock_send_success_story_email):
    """Test request with empty name field."""
    headers = {}
    body = json.dumps(
        {
            "name": "   ",  # Whitespace only
            "email": "john@example.com",
            "story": "A" * 50,
            "sharePublicly": True,
        }
    )

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 400
    body_data = json.loads(response["body"])
    assert "name" in body_data["error"]
    mock_send_success_story_email.assert_not_called()


def test_handle_send_success_story_missing_email(mock_send_success_story_email):
    """Test request with missing email field."""
    headers = {}
    body = json.dumps({"name": "John Doe", "story": "A" * 50, "sharePublicly": True})

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 400
    body_data = json.loads(response["body"])
    assert "email" in body_data["error"]
    mock_send_success_story_email.assert_not_called()


def test_handle_send_success_story_invalid_email_format(mock_send_success_story_email):
    """Test request with invalid email format."""
    headers = {}

    # Test various invalid email formats
    invalid_emails = [
        "invalid-email",
        "missing-at-sign.com",
        "@no-local-part.com",
        "no-domain@",
        "spaces in@email.com",
        "double@@domain.com",
    ]

    for invalid_email in invalid_emails:
        body = json.dumps(
            {
                "name": "John Doe",
                "email": invalid_email,
                "story": "A" * 50,
                "sharePublicly": True,
            }
        )

        response = email.handle_send_success_story(headers, body)

        assert response["statusCode"] == 400
        body_data = json.loads(response["body"])
        assert "email" in body_data["error"].lower()

    mock_send_success_story_email.assert_not_called()


def test_handle_send_success_story_missing_story(mock_send_success_story_email):
    """Test request with missing story field."""
    headers = {}
    body = json.dumps(
        {"name": "John Doe", "email": "john@example.com", "sharePublicly": True}
    )

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 400
    body_data = json.loads(response["body"])
    assert "story" in body_data["error"]
    mock_send_success_story_email.assert_not_called()


def test_handle_send_success_story_story_too_short(mock_send_success_story_email):
    """Test request with story less than 50 characters."""
    headers = {}
    body = json.dumps(
        {
            "name": "John Doe",
            "email": "john@example.com",
            "story": "Too short",  # Less than 50 characters
            "sharePublicly": True,
        }
    )

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 400
    body_data = json.loads(response["body"])
    assert "50 characters" in body_data["error"]
    mock_send_success_story_email.assert_not_called()


def test_handle_send_success_story_story_exactly_50_chars(
    mock_send_success_story_email,
):
    """Test request with story exactly 50 characters."""
    headers = {}
    story_50_chars = "A" * 50
    body = json.dumps(
        {
            "name": "John Doe",
            "email": "john@example.com",
            "story": story_50_chars,
            "sharePublicly": True,
        }
    )

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 200
    mock_send_success_story_email.assert_called_once()


def test_handle_send_success_story_invalid_json(mock_send_success_story_email):
    """Test request with invalid JSON body."""
    headers = {}
    body = "not valid json {"

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 400
    body_data = json.loads(response["body"])
    assert "JSON" in body_data["error"]
    mock_send_success_story_email.assert_not_called()


def test_handle_send_success_story_empty_body(mock_send_success_story_email):
    """Test request with empty body."""
    headers = {}
    body = ""

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 400
    body_data = json.loads(response["body"])
    assert "name" in body_data["error"]
    mock_send_success_story_email.assert_not_called()


def test_handle_send_success_story_mailgun_failure(mock_send_success_story_email):
    """Test handling of Mailgun service failure."""
    mock_send_success_story_email.return_value = False

    headers = {}
    body = json.dumps(
        {
            "name": "John Doe",
            "email": "john@example.com",
            "story": "A" * 50,
            "sharePublicly": True,
        }
    )

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 500
    body_data = json.loads(response["body"])
    assert "Failed to send email" in body_data["error"]


def test_handle_send_success_story_parameter_store_failure(
    mock_send_success_story_email,
):
    """Test handling of Parameter Store credential retrieval failure."""
    mock_send_success_story_email.side_effect = Exception(
        "Failed to retrieve parameter /app/mailgun/api-key: ParameterNotFound"
    )

    headers = {}
    body = json.dumps(
        {
            "name": "John Doe",
            "email": "john@example.com",
            "story": "A" * 50,
            "sharePublicly": True,
        }
    )

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 500
    body_data = json.loads(response["body"])
    assert "Email service temporarily unavailable" in body_data["error"]


def test_handle_send_success_story_unexpected_exception(mock_send_success_story_email):
    """Test handling of unexpected exception."""
    mock_send_success_story_email.side_effect = Exception("Unexpected error")

    headers = {}
    body = json.dumps(
        {
            "name": "John Doe",
            "email": "john@example.com",
            "story": "A" * 50,
            "sharePublicly": True,
        }
    )

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 500
    body_data = json.loads(response["body"])
    assert "Failed to send email" in body_data["error"]


def test_handle_send_success_story_cors_headers(mock_send_success_story_email):
    """Test that CORS headers are present in response."""
    headers = {}
    body = json.dumps(
        {
            "name": "John Doe",
            "email": "john@example.com",
            "story": "A" * 50,
            "sharePublicly": True,
        }
    )

    response = email.handle_send_success_story(headers, body)

    assert "Access-Control-Allow-Origin" in response["headers"]
    assert "Access-Control-Allow-Credentials" in response["headers"]


def test_handle_send_success_story_whitespace_trimming(mock_send_success_story_email):
    """Test that whitespace is trimmed from input fields."""
    headers = {}
    body = json.dumps(
        {
            "name": "  John Doe  ",
            "email": "  john@example.com  ",
            "story": "  " + ("A" * 50) + "  ",
            "sharePublicly": True,
        }
    )

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 200
    mock_send_success_story_email.assert_called_once_with(
        "John Doe", "john@example.com", "A" * 50, True
    )


def test_handle_send_success_story_default_share_publicly(
    mock_send_success_story_email,
):
    """Test that sharePublicly defaults to False if not provided."""
    headers = {}
    body = json.dumps(
        {
            "name": "John Doe",
            "email": "john@example.com",
            "story": "A" * 50,
            # sharePublicly not provided
        }
    )

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 200
    mock_send_success_story_email.assert_called_once_with(
        "John Doe", "john@example.com", "A" * 50, False
    )


def test_handle_send_success_story_special_characters(mock_send_success_story_email):
    """Test handling of special characters in input."""
    headers = {}
    body = json.dumps(
        {
            "name": "José García",
            "email": "jose@example.com",
            "story": "My story includes special chars: <>&\"'@#$% " + ("A" * 50),
            "sharePublicly": True,
        }
    )

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 200
    call_args = mock_send_success_story_email.call_args[0]
    assert call_args[0] == "José García"
    assert "<>&\"'@#$%" in call_args[2]


def test_handle_send_success_story_multiline_story(mock_send_success_story_email):
    """Test handling of multiline story text."""
    headers = {}
    multiline_story = """Line 1 of my story.
Line 2 of my story.
Line 3 of my story with enough characters to meet minimum."""

    body = json.dumps(
        {
            "name": "John Doe",
            "email": "john@example.com",
            "story": multiline_story,
            "sharePublicly": True,
        }
    )

    response = email.handle_send_success_story(headers, body)

    assert response["statusCode"] == 200
    call_args = mock_send_success_story_email.call_args[0]
    assert call_args[2] == multiline_story
