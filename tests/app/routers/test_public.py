"""Tests for the public credential verification router — GET /public/credentials/{id}."""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app

# Minimal settings for testing
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
    """Create a test client with overridden settings."""
    from app.dependencies import get_settings as dep_get_settings

    app.dependency_overrides[dep_get_settings] = lambda: TEST_SETTINGS
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestVerifyCredential:
    """Tests for GET /public/credentials/{credential_id}."""

    @patch("app.routers.public.CertificationDB")
    def test_returns_credential_when_found(self, mock_db_class, client):
        """Returns 200 with public credential data when credential exists."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_credential_by_id.return_value = {
            "credential_id": "DSB-DSEP-8F4C92A1",
            "pathway_id": "devsecops-engineering",
            "credential_status": "ACTIVE",
            "issued_at": "2025-01-15T10:00:00Z",
            "expires_at": "2026-01-15T10:00:00Z",
            "full_name_at_issuance": "Jane Doe",
        }
        mock_db.get_active_pathway.return_value = {
            "pathway_id": "devsecops-engineering",
            "display_name": "DevSecOps Engineering",
            "version": "2027.1",
        }

        response = client.get("/public/credentials/DSB-DSEP-8F4C92A1")

        assert response.status_code == 200
        data = response.json()
        assert data["credential_id"] == "DSB-DSEP-8F4C92A1"
        assert data["holder_name"] == "Jane Doe"
        assert data["pathway_name"] == "DevSecOps Engineering"
        assert data["issued_at"] == "2025-01-15T10:00:00Z"
        assert data["expires_at"] == "2026-01-15T10:00:00Z"
        assert data["credential_status"] == "ACTIVE"

    @patch("app.routers.public.CertificationDB")
    def test_returns_404_when_credential_not_found(self, mock_db_class, client):
        """Returns 404 when credential_id does not exist."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_credential_by_id.return_value = None

        response = client.get("/public/credentials/DSB-DSEP-NONEXIST")

        assert response.status_code == 404
        assert response.json()["detail"] == "Credential not found"

    @patch("app.routers.public.CertificationDB")
    def test_does_not_expose_user_id_or_email(self, mock_db_class, client):
        """Response does not contain user_id, email, or internal identifiers."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_credential_by_id.return_value = {
            "credential_id": "DSB-CSEP-12345678",
            "pathway_id": "cloud-security-engineering",
            "credential_status": "ACTIVE",
            "issued_at": "2025-03-01T12:00:00Z",
            "expires_at": "2026-03-01T12:00:00Z",
            "full_name_at_issuance": "John Smith",
            "user_id": "user-secret-123",
            "email": "john@secret.com",
        }
        mock_db.get_active_pathway.return_value = {
            "pathway_id": "cloud-security-engineering",
            "display_name": "Cloud Security Engineering",
            "version": "2027.1",
        }

        response = client.get("/public/credentials/DSB-CSEP-12345678")

        assert response.status_code == 200
        data = response.json()
        assert "user_id" not in data
        assert "email" not in data

    @patch("app.routers.public.CertificationDB")
    def test_no_authentication_required(self, mock_db_class, client):
        """Endpoint is accessible without any authentication headers or cookies."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_credential_by_id.return_value = {
            "credential_id": "DSB-DSEP-AABBCCDD",
            "pathway_id": "devsecops-engineering",
            "credential_status": "EXPIRED",
            "issued_at": "2024-01-01T00:00:00Z",
            "expires_at": "2025-01-01T00:00:00Z",
            "full_name_at_issuance": "Alice Johnson",
        }
        mock_db.get_active_pathway.return_value = {
            "pathway_id": "devsecops-engineering",
            "display_name": "DevSecOps Engineering",
            "version": "2027.1",
        }

        # No auth headers, no cookies
        response = client.get("/public/credentials/DSB-DSEP-AABBCCDD")

        assert response.status_code == 200

    @patch("app.routers.public.CertificationDB")
    def test_fallback_pathway_name_when_no_active_pathway(self, mock_db_class, client):
        """Uses formatted pathway_id as fallback when no active pathway found."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_credential_by_id.return_value = {
            "credential_id": "DSB-DSEP-FALLBACK1",
            "pathway_id": "devsecops-engineering",
            "credential_status": "ACTIVE",
            "issued_at": "2025-06-01T00:00:00Z",
            "expires_at": "2026-06-01T00:00:00Z",
            "full_name_at_issuance": "Bob Builder",
        }
        mock_db.get_active_pathway.return_value = None

        response = client.get("/public/credentials/DSB-DSEP-FALLBACK1")

        assert response.status_code == 200
        data = response.json()
        assert data["pathway_name"] == "Devsecops Engineering"
