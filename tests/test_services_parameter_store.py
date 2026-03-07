"""
Unit tests for services/parameter_store.py
"""

import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

from services import parameter_store


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the parameter cache before each test."""
    parameter_store._parameter_cache.clear()
    yield
    parameter_store._parameter_cache.clear()


@pytest.fixture
def mock_ssm_client():
    """Mock SSM client for parameter store tests."""
    with patch("boto3.client") as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        yield mock_client


def test_get_parameter_success(mock_ssm_client):
    """Test successful parameter retrieval."""
    parameter_name = "/app/test/parameter"
    parameter_value = "test-value-123"

    mock_ssm_client.get_parameter.return_value = {
        "Parameter": {"Value": parameter_value}
    }

    result = parameter_store.get_parameter(parameter_name)

    assert result == parameter_value
    mock_ssm_client.get_parameter.assert_called_once_with(
        Name=parameter_name, WithDecryption=True
    )


def test_get_parameter_with_decryption_false(mock_ssm_client):
    """Test parameter retrieval without decryption."""
    parameter_name = "/app/test/parameter"
    parameter_value = "plain-text-value"

    mock_ssm_client.get_parameter.return_value = {
        "Parameter": {"Value": parameter_value}
    }

    result = parameter_store.get_parameter(parameter_name, with_decryption=False)

    assert result == parameter_value
    mock_ssm_client.get_parameter.assert_called_once_with(
        Name=parameter_name, WithDecryption=False
    )


def test_get_parameter_caching(mock_ssm_client):
    """Test that parameters are cached and AWS API is only called once."""
    parameter_name = "/app/test/cached"
    parameter_value = "cached-value"

    mock_ssm_client.get_parameter.return_value = {
        "Parameter": {"Value": parameter_value}
    }

    # First call - should hit AWS
    result1 = parameter_store.get_parameter(parameter_name)
    assert result1 == parameter_value
    assert mock_ssm_client.get_parameter.call_count == 1

    # Second call - should use cache
    result2 = parameter_store.get_parameter(parameter_name)
    assert result2 == parameter_value
    assert mock_ssm_client.get_parameter.call_count == 1  # Still 1, not 2

    # Third call - should still use cache
    result3 = parameter_store.get_parameter(parameter_name)
    assert result3 == parameter_value
    assert mock_ssm_client.get_parameter.call_count == 1


def test_get_parameter_different_parameters(mock_ssm_client):
    """Test that different parameters are cached separately."""
    param1_name = "/app/param1"
    param1_value = "value1"
    param2_name = "/app/param2"
    param2_value = "value2"

    def get_parameter_side_effect(Name, WithDecryption):
        if Name == param1_name:
            return {"Parameter": {"Value": param1_value}}
        elif Name == param2_name:
            return {"Parameter": {"Value": param2_value}}

    mock_ssm_client.get_parameter.side_effect = get_parameter_side_effect

    # Get first parameter
    result1 = parameter_store.get_parameter(param1_name)
    assert result1 == param1_value

    # Get second parameter
    result2 = parameter_store.get_parameter(param2_name)
    assert result2 == param2_value

    # Get first parameter again (should be cached)
    result1_again = parameter_store.get_parameter(param1_name)
    assert result1_again == param1_value

    # Should have called AWS twice (once for each parameter)
    assert mock_ssm_client.get_parameter.call_count == 2


def test_get_parameter_not_found(mock_ssm_client):
    """Test behavior when parameter doesn't exist."""
    parameter_name = "/app/nonexistent"

    mock_ssm_client.get_parameter.side_effect = ClientError(
        {
            "Error": {
                "Code": "ParameterNotFound",
                "Message": "Parameter not found",
            }
        },
        "GetParameter",
    )

    with pytest.raises(Exception) as exc_info:
        parameter_store.get_parameter(parameter_name)

    assert "Failed to retrieve parameter" in str(exc_info.value)
    assert "ParameterNotFound" in str(exc_info.value)


def test_get_parameter_access_denied(mock_ssm_client):
    """Test behavior when access is denied."""
    parameter_name = "/app/restricted"

    mock_ssm_client.get_parameter.side_effect = ClientError(
        {
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "Access denied",
            }
        },
        "GetParameter",
    )

    with pytest.raises(Exception) as exc_info:
        parameter_store.get_parameter(parameter_name)

    assert "Failed to retrieve parameter" in str(exc_info.value)
    assert "AccessDeniedException" in str(exc_info.value)


def test_get_parameter_aws_api_failure(mock_ssm_client):
    """Test behavior when AWS API fails."""
    parameter_name = "/app/test/parameter"

    mock_ssm_client.get_parameter.side_effect = ClientError(
        {"Error": {"Code": "InternalServiceError", "Message": "Service error"}},
        "GetParameter",
    )

    with pytest.raises(Exception) as exc_info:
        parameter_store.get_parameter(parameter_name)

    assert "Failed to retrieve parameter" in str(exc_info.value)


def test_get_parameter_unexpected_response_format(mock_ssm_client):
    """Test behavior when response format is unexpected."""
    parameter_name = "/app/test/parameter"

    # Missing "Parameter" key in response
    mock_ssm_client.get_parameter.return_value = {"Value": "test"}

    with pytest.raises(Exception) as exc_info:
        parameter_store.get_parameter(parameter_name)

    assert "Unexpected response format" in str(exc_info.value)


def test_get_parameter_secure_string(mock_ssm_client):
    """Test retrieval of SecureString parameter with decryption."""
    parameter_name = "/app/mailgun/api-key"
    parameter_value = "key-abc123xyz789"

    mock_ssm_client.get_parameter.return_value = {
        "Parameter": {
            "Value": parameter_value,
            "Type": "SecureString",
        }
    }

    result = parameter_store.get_parameter(parameter_name, with_decryption=True)

    assert result == parameter_value
    mock_ssm_client.get_parameter.assert_called_once_with(
        Name=parameter_name, WithDecryption=True
    )


def test_get_parameter_empty_value(mock_ssm_client):
    """Test behavior with empty parameter value."""
    parameter_name = "/app/empty"

    mock_ssm_client.get_parameter.return_value = {"Parameter": {"Value": ""}}

    result = parameter_store.get_parameter(parameter_name)

    # Empty string is a valid parameter value
    assert result == ""


def test_get_parameter_special_characters(mock_ssm_client):
    """Test parameter value with special characters."""
    parameter_name = "/app/test/special"
    parameter_value = "value-with-special!@#$%^&*()_+={}[]|:;<>,.?/~`"

    mock_ssm_client.get_parameter.return_value = {
        "Parameter": {"Value": parameter_value}
    }

    result = parameter_store.get_parameter(parameter_name)

    assert result == parameter_value
