"""
Unit tests for services/mailgun.py
"""

import pytest
from unittest.mock import patch, MagicMock

from services import mailgun


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up environment variables for tests."""
    monkeypatch.setenv("MAILGUN_DOMAIN", "test.mailgun.org")
    monkeypatch.setenv("MAILGUN_PARAM_NAME", "/app/mailgun/api-key")
    monkeypatch.setenv("SUCCESS_STORY_TO_EMAIL", "test@example.com")


@pytest.fixture
def mock_get_parameter():
    """Mock parameter store get_parameter function."""
    with patch("services.mailgun.get_parameter") as mock:
        mock.return_value = "test-api-key-123"
        yield mock


@pytest.fixture
def mock_requests_post():
    """Mock requests.post function."""
    with patch("services.mailgun.requests.post") as mock:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock.return_value = mock_response
        yield mock


def test_send_success_story_email_success(
    mock_env_vars, mock_get_parameter, mock_requests_post
):
    """Test successful email sending."""
    result = mailgun.send_success_story_email(
        name="John Doe",
        email="john@example.com",
        story="This is my success story about implementing DevSecOps practices.",
        share_publicly=True,
    )

    assert result is True
    mock_get_parameter.assert_called_once_with("/app/mailgun/api-key")
    mock_requests_post.assert_called_once()

    # Verify the API call parameters
    call_args = mock_requests_post.call_args
    assert call_args[0][0] == "https://api.mailgun.net/v3/test.mailgun.org/messages"
    assert call_args[1]["auth"] == ("api", "test-api-key-123")
    assert call_args[1]["data"]["to"] == "test@example.com"
    assert call_args[1]["data"]["subject"] == "New Success Story Submission"
    assert "John Doe" in call_args[1]["data"]["text"]
    assert "john@example.com" in call_args[1]["data"]["text"]
    assert "This is my success story" in call_args[1]["data"]["text"]
    assert "Public Sharing Permission: Yes" in call_args[1]["data"]["text"]


def test_send_success_story_email_no_public_sharing(
    mock_env_vars, mock_get_parameter, mock_requests_post
):
    """Test email with public sharing set to False."""
    result = mailgun.send_success_story_email(
        name="Jane Smith",
        email="jane@example.com",
        story="My private success story.",
        share_publicly=False,
    )

    assert result is True

    # Verify permission text is "No"
    call_args = mock_requests_post.call_args
    assert "Public Sharing Permission: No" in call_args[1]["data"]["text"]


def test_send_success_story_email_mailgun_api_error(
    mock_env_vars, mock_get_parameter, mock_requests_post
):
    """Test handling of Mailgun API error."""
    mock_requests_post.return_value.status_code = 400
    mock_requests_post.return_value.text = "Bad Request"

    result = mailgun.send_success_story_email(
        name="Test User",
        email="test@example.com",
        story="Test story",
        share_publicly=True,
    )

    assert result is False


def test_send_success_story_email_mailgun_unauthorized(
    mock_env_vars, mock_get_parameter, mock_requests_post
):
    """Test handling of unauthorized Mailgun API response."""
    mock_requests_post.return_value.status_code = 401
    mock_requests_post.return_value.text = "Unauthorized"

    result = mailgun.send_success_story_email(
        name="Test User",
        email="test@example.com",
        story="Test story",
        share_publicly=True,
    )

    assert result is False


def test_send_success_story_email_parameter_store_failure(
    mock_env_vars, mock_get_parameter, mock_requests_post
):
    """Test that Parameter Store failure raises exception."""
    mock_get_parameter.side_effect = Exception(
        "Failed to retrieve parameter /app/mailgun/api-key: ParameterNotFound"
    )

    with pytest.raises(Exception) as exc_info:
        mailgun.send_success_story_email(
            name="Test User",
            email="test@example.com",
            story="Test story",
            share_publicly=True,
        )

    assert "Failed to retrieve parameter" in str(exc_info.value)
    # Verify Mailgun API was never called
    mock_requests_post.assert_not_called()


def test_send_success_story_email_missing_mailgun_domain(
    monkeypatch, mock_get_parameter, mock_requests_post
):
    """Test handling when MAILGUN_DOMAIN is not set."""
    monkeypatch.setenv("MAILGUN_PARAM_NAME", "/app/mailgun/api-key")
    monkeypatch.setenv("SUCCESS_STORY_TO_EMAIL", "test@example.com")
    # Don't set MAILGUN_DOMAIN

    result = mailgun.send_success_story_email(
        name="Test User",
        email="test@example.com",
        story="Test story",
        share_publicly=True,
    )

    assert result is False
    mock_requests_post.assert_not_called()


def test_send_success_story_email_missing_to_email(
    monkeypatch, mock_get_parameter, mock_requests_post
):
    """Test handling when SUCCESS_STORY_TO_EMAIL is not set."""
    monkeypatch.setenv("MAILGUN_DOMAIN", "test.mailgun.org")
    monkeypatch.setenv("MAILGUN_PARAM_NAME", "/app/mailgun/api-key")
    # Don't set SUCCESS_STORY_TO_EMAIL

    result = mailgun.send_success_story_email(
        name="Test User",
        email="test@example.com",
        story="Test story",
        share_publicly=True,
    )

    assert result is False
    mock_requests_post.assert_not_called()


def test_send_success_story_email_network_timeout(
    mock_env_vars, mock_get_parameter, mock_requests_post
):
    """Test handling of network timeout."""
    import requests

    mock_requests_post.side_effect = requests.exceptions.Timeout("Request timed out")

    result = mailgun.send_success_story_email(
        name="Test User",
        email="test@example.com",
        story="Test story",
        share_publicly=True,
    )

    assert result is False


def test_send_success_story_email_network_error(
    mock_env_vars, mock_get_parameter, mock_requests_post
):
    """Test handling of network error."""
    import requests

    mock_requests_post.side_effect = requests.exceptions.ConnectionError(
        "Connection failed"
    )

    result = mailgun.send_success_story_email(
        name="Test User",
        email="test@example.com",
        story="Test story",
        share_publicly=True,
    )

    assert result is False


def test_send_success_story_email_special_characters(
    mock_env_vars, mock_get_parameter, mock_requests_post
):
    """Test email with special characters in content."""
    result = mailgun.send_success_story_email(
        name="José García",
        email="jose@example.com",
        story="My story includes special chars: <>&\"'@#$%",
        share_publicly=True,
    )

    assert result is True

    # Verify special characters are included in email body
    call_args = mock_requests_post.call_args
    assert "José García" in call_args[1]["data"]["text"]
    assert "<>&\"'@#$%" in call_args[1]["data"]["text"]


def test_send_success_story_email_long_story(
    mock_env_vars, mock_get_parameter, mock_requests_post
):
    """Test email with very long story text."""
    long_story = "A" * 5000  # 5000 character story

    result = mailgun.send_success_story_email(
        name="Test User",
        email="test@example.com",
        story=long_story,
        share_publicly=True,
    )

    assert result is True

    # Verify long story is included
    call_args = mock_requests_post.call_args
    assert long_story in call_args[1]["data"]["text"]


def test_send_success_story_email_multiline_story(
    mock_env_vars, mock_get_parameter, mock_requests_post
):
    """Test email with multiline story text."""
    multiline_story = """This is line 1.
This is line 2.
This is line 3."""

    result = mailgun.send_success_story_email(
        name="Test User",
        email="test@example.com",
        story=multiline_story,
        share_publicly=True,
    )

    assert result is True

    # Verify multiline story is preserved
    call_args = mock_requests_post.call_args
    assert multiline_story in call_args[1]["data"]["text"]
