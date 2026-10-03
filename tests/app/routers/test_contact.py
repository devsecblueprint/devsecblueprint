"""Tests for the contact router — POST /api/contact.

Public endpoint (no auth). Validates the ContactRequest schema and sends a
notification email via send_contact_notification, which we patch at the
router import site.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app

TEST_SETTINGS = Settings(
    membership_table="test-membership",
    progress_table="test-progress",
    user_state_table="test-user-state",
    testimonials_table="test-testimonials",
    notifications_table="test-notifications",
    discord_secret_name="test-discord",
    discord_bot_secret_name="test-discord-bot",
    stripe_secret_name="test-stripe",
    stripe_webhook_secret_name="test-stripe-webhook",
    jwt_secret_name="test-jwt-secret",
    github_secret_name="test-github",
    gitlab_secret_name="test-gitlab",
    bitbucket_secret_name="test-bitbucket",
    discord_guild_id="123456",
    discord_role_free_id="111",
    discord_role_explorer_id="222",
    discord_role_builder_id="333",
    discord_role_builder_academy_id="444",
    discord_callback_url="https://example.com/callback",
    frontend_url="https://example.com",
    frontend_origin="https://example.com",
    github_callback_url="https://example.com/auth/github/callback",
    gitlab_callback_url="https://example.com/auth/gitlab/callback",
    bitbucket_callback_url="https://example.com/auth/bitbucket/callback",
    session_token_lifetime_hours=8,
)


@pytest.fixture
def client():
    from app.dependencies import get_settings as dep_get_settings

    app.dependency_overrides[dep_get_settings] = lambda: TEST_SETTINGS
    yield TestClient(app)
    app.dependency_overrides.clear()


def _valid_body():
    return {
        "full_name": "Jane Doe",
        "email": "jane@example.com",
        "organization": "Acme",
        "inquiry_type": "general-inquiry",
        "subject": "Hello there",
        "message": "This is a sufficiently long message.",
    }


class TestSubmitContactForm:
    def test_success(self, client):
        with patch("app.routers.contact.send_contact_notification") as mock_send:
            mock_send.return_value = True
            response = client.post("/api/contact", json=_valid_body())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "sent" in data["message"].lower()
        mock_send.assert_called_once_with(
            full_name="Jane Doe",
            email="jane@example.com",
            organization="Acme",
            inquiry_type="general-inquiry",
            subject="Hello there",
            message="This is a sufficiently long message.",
        )

    def test_email_strip_and_default_organization(self, client):
        """Email is stripped; organization defaults to empty string."""
        body = _valid_body()
        body["email"] = "  jane@example.com  "
        del body["organization"]
        with patch("app.routers.contact.send_contact_notification") as mock_send:
            mock_send.return_value = True
            response = client.post("/api/contact", json=body)

        assert response.status_code == 200
        _, kwargs = mock_send.call_args
        assert kwargs["email"] == "jane@example.com"
        assert kwargs["organization"] == ""

    def test_send_failure_returns_500(self, client):
        with patch("app.routers.contact.send_contact_notification") as mock_send:
            mock_send.return_value = False
            response = client.post("/api/contact", json=_valid_body())

        assert response.status_code == 500
        assert "Failed to send" in response.json()["detail"]

    def test_invalid_email_422(self, client):
        body = _valid_body()
        body["email"] = "not-an-email"
        response = client.post("/api/contact", json=body)
        assert response.status_code == 422

    def test_invalid_inquiry_type_422(self, client):
        body = _valid_body()
        body["inquiry_type"] = "not-a-type"
        response = client.post("/api/contact", json=body)
        assert response.status_code == 422

    def test_message_too_short_422(self, client):
        body = _valid_body()
        body["message"] = "short"  # < 10 chars
        response = client.post("/api/contact", json=body)
        assert response.status_code == 422

    def test_missing_required_field_422(self, client):
        body = _valid_body()
        del body["subject"]
        response = client.post("/api/contact", json=body)
        assert response.status_code == 422

    def test_full_name_too_long_422(self, client):
        body = _valid_body()
        body["full_name"] = "x" * 101
        response = client.post("/api/contact", json=body)
        assert response.status_code == 422
