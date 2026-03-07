"""
Parameter Store service with caching.

This module provides functions to retrieve parameters from AWS Systems Manager
Parameter Store with module-level caching to optimize Lambda warm start performance.
"""

import boto3
from botocore.exceptions import ClientError

# Module-level cache for parameters
_parameter_cache = {}


def get_parameter(parameter_name: str, with_decryption: bool = True) -> str:
    """
    Retrieve parameter from AWS Systems Manager Parameter Store with caching.

    Args:
        parameter_name: Name of the parameter in Parameter Store
        with_decryption: Whether to decrypt SecureString parameters (default: True)

    Returns:
        str: Parameter value

    Caching:
        - Parameters are cached in module-level dictionary
        - Cache persists across warm Lambda invocations
        - No TTL - relies on Lambda lifecycle

    Raises:
        Exception: If parameter retrieval fails
    """
    # Check cache first
    if parameter_name in _parameter_cache:
        return _parameter_cache[parameter_name]

    # Retrieve from AWS Parameter Store
    try:
        client = boto3.client("ssm")
        response = client.get_parameter(
            Name=parameter_name, WithDecryption=with_decryption
        )

        # Extract parameter value
        parameter_value = response["Parameter"]["Value"]

        # Cache the parameter
        _parameter_cache[parameter_name] = parameter_value

        return parameter_value

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        raise Exception(
            f"Failed to retrieve parameter {parameter_name}: {error_code} - {str(e)}"
        )
    except KeyError as e:
        raise Exception(
            f"Unexpected response format from Parameter Store for {parameter_name}: {str(e)}"
        )
    except Exception as e:
        raise Exception(
            f"Unexpected error retrieving parameter {parameter_name}: {str(e)}"
        )
