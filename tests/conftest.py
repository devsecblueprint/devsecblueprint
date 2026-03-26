"""
Pytest configuration and shared fixtures for all tests.
"""

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

# Set ADMIN_USERS before any backend modules are imported, since
# backend/handlers/progress_reset.py and backend/auth/admin.py read
# this env var at module level during collection.
os.environ.setdefault("ADMIN_USERS", "testadmin,damienjburks,Damien Burks")

# Add backend directory to Python path for imports
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(backend_dir))


@pytest.fixture(autouse=True)
def mock_frontend_origin():
    """
    Mock FRONTEND_ORIGIN environment variable for all tests.

    This fixture automatically applies to all tests and sets the
    FRONTEND_ORIGIN to the production URL that tests expect.
    """
    with patch.dict(os.environ, {"FRONTEND_ORIGIN": "https://devsecblueprint.com"}):
        yield


@pytest.fixture(autouse=True)
def mock_progress_table():
    """
    Mock PROGRESS_TABLE environment variable for all tests.

    This fixture automatically applies to all tests to prevent
    errors when code tries to access DynamoDB table name.
    """
    with patch.dict(os.environ, {"PROGRESS_TABLE": "test-progress-table"}):
        yield


@pytest.fixture(autouse=True)
def mock_jwt_secret():
    """
    Mock JWT secret retrieval for all tests.

    This fixture automatically applies to all tests to prevent
    actual AWS Secrets Manager calls during JWT validation.
    Mocks at the boto3 client level to catch all secret retrievals.
    """
    with patch("boto3.client") as mock_boto_client:
        mock_secrets_client = MagicMock()
        mock_boto_client.return_value = mock_secrets_client

        # Mock get_secret_value to return JWT secret
        mock_secrets_client.get_secret_value.return_value = {
            "SecretString": json.dumps(
                {"secret_key": "test-secret-key-min-32-characters-long-for-testing"}
            )
        }

        yield mock_secrets_client
