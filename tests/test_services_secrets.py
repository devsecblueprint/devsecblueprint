"""
Unit tests for services/secrets.py
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

from backend.services import secrets


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the secrets cache before each test."""
    secrets._secrets_cache.clear()
    yield
    secrets._secrets_cache.clear()


def test_get_secret_success():
    """Test successful secret retrieval."""
    secret_name = "test-secret"
    secret_value = {"key": "value", "client_id": "test123"}

    with patch("boto3.client") as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(secret_value)
        }

        result = secrets.get_secret(secret_name)

        assert result == secret_value
        mock_client.get_secret_value.assert_called_once_with(SecretId=secret_name)


def test_get_secret_caching():
    """Test that secrets are cached and AWS API is only called once."""
    secret_name = "test-secret"
    secret_value = {"key": "cached_value"}

    with patch("boto3.client") as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(secret_value)
        }

        # First call - should hit AWS
        result1 = secrets.get_secret(secret_name)
        assert result1 == secret_value
        assert mock_client.get_secret_value.call_count == 1

        # Second call - should use cache
        result2 = secrets.get_secret(secret_name)
        assert result2 == secret_value
        assert mock_client.get_secret_value.call_count == 1  # Still 1, not 2

        # Third call - should still use cache
        result3 = secrets.get_secret(secret_name)
        assert result3 == secret_value
        assert mock_client.get_secret_value.call_count == 1


def test_get_secret_different_secrets():
    """Test that different secrets are cached separately."""
    secret1_name = "secret-one"
    secret1_value = {"key": "value1"}
    secret2_name = "secret-two"
    secret2_value = {"key": "value2"}

    with patch("boto3.client") as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        def get_secret_side_effect(SecretId):
            if SecretId == secret1_name:
                return {"SecretString": json.dumps(secret1_value)}
            elif SecretId == secret2_name:
                return {"SecretString": json.dumps(secret2_value)}

        mock_client.get_secret_value.side_effect = get_secret_side_effect

        # Get first secret
        result1 = secrets.get_secret(secret1_name)
        assert result1 == secret1_value

        # Get second secret
        result2 = secrets.get_secret(secret2_name)
        assert result2 == secret2_value

        # Get first secret again (should be cached)
        result1_again = secrets.get_secret(secret1_name)
        assert result1_again == secret1_value

        # Should have called AWS twice (once for each secret)
        assert mock_client.get_secret_value.call_count == 2


def test_get_secret_not_found():
    """Test behavior when secret doesn't exist."""
    secret_name = "nonexistent-secret"

    with patch("boto3.client") as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "Secret not found",
                }
            },
            "GetSecretValue",
        )

        with pytest.raises(Exception) as exc_info:
            secrets.get_secret(secret_name)

        assert "Failed to retrieve secret" in str(exc_info.value)


def test_get_secret_aws_api_failure():
    """Test behavior when AWS API fails."""
    secret_name = "test-secret"

    with patch("boto3.client") as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "InternalServiceError", "Message": "Service error"}},
            "GetSecretValue",
        )

        with pytest.raises(Exception) as exc_info:
            secrets.get_secret(secret_name)

        assert "Failed to retrieve secret" in str(exc_info.value)


def test_get_secret_invalid_json():
    """Test behavior when secret value is not valid JSON."""
    secret_name = "invalid-json-secret"

    with patch("boto3.client") as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.get_secret_value.return_value = {"SecretString": "not valid json {"}

        with pytest.raises(Exception) as exc_info:
            secrets.get_secret(secret_name)

        assert "Failed to parse secret" in str(exc_info.value)
        assert "as JSON" in str(exc_info.value)


def test_get_secret_empty_string():
    """Test behavior with empty secret string."""
    secret_name = "empty-secret"

    with patch("boto3.client") as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.get_secret_value.return_value = {"SecretString": ""}

        with pytest.raises(Exception) as exc_info:
            secrets.get_secret(secret_name)

        assert "Failed to parse secret" in str(exc_info.value)


def test_get_secret_complex_json():
    """Test with complex nested JSON structure."""
    secret_name = "complex-secret"
    secret_value = {
        "client_id": "abc123",
        "client_secret": "xyz789",
        "nested": {"key1": "value1", "key2": ["item1", "item2"]},
    }

    with patch("boto3.client") as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(secret_value)
        }

        result = secrets.get_secret(secret_name)

        assert result == secret_value
        assert result["nested"]["key2"] == ["item1", "item2"]
