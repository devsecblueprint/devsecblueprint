"""
Secrets Manager service with caching.

This module provides functions to retrieve secrets from AWS Secrets Manager
with module-level caching to optimize Lambda warm start performance.
"""

import json
import boto3
from botocore.exceptions import ClientError

# Module-level cache for secrets
_secrets_cache = {}


def get_secret(secret_name: str) -> dict:
    """
    Retrieve secret from AWS Secrets Manager with caching.

    Args:
        secret_name: Name of the secret in Secrets Manager

    Returns:
        dict: Parsed secret value (JSON)

    Caching:
        - Secrets are cached in module-level dictionary
        - Cache persists across warm Lambda invocations
        - No TTL - relies on Lambda lifecycle

    Raises:
        Exception: If secret retrieval fails
    """
    # Check cache first
    if secret_name in _secrets_cache:
        return _secrets_cache[secret_name]

    # Retrieve from AWS Secrets Manager
    try:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_name)

        # Parse the secret string as JSON
        secret_string = response["SecretString"]
        secret_value = json.loads(secret_string)

        # Cache the secret
        _secrets_cache[secret_name] = secret_value

        return secret_value

    except ClientError as e:
        raise Exception(f"Failed to retrieve secret {secret_name}: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse secret {secret_name} as JSON: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error retrieving secret {secret_name}: {str(e)}")
