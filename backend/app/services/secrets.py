"""Secrets Manager service with TTL-based caching.

Retrieves secrets from AWS Secrets Manager with an in-memory TTL cache.
Unlike the Lambda version (infinite cache relying on container lifecycle),
this uses a 15-minute TTL suitable for long-lived ECS tasks.
"""

import json
import time

import boto3
from botocore.exceptions import ClientError

_cache: dict = {}
_CACHE_TTL = 900  # 15 minutes


def get_secret(secret_name: str) -> dict:
    """Retrieve a secret from AWS Secrets Manager with TTL caching.

    Args:
        secret_name: Name or ARN of the secret in Secrets Manager.

    Returns:
        Parsed JSON secret value as a dictionary.

    Raises:
        Exception: If secret retrieval or parsing fails.
    """
    now = time.time()
    cached = _cache.get(secret_name)
    if cached and (now - cached["ts"]) < _CACHE_TTL:
        return cached["data"]

    try:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_name)
        data = json.loads(response["SecretString"])
    except ClientError as e:
        raise Exception(f"Failed to retrieve secret {secret_name}: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse secret {secret_name} as JSON: {str(e)}")

    _cache[secret_name] = {"data": data, "ts": now}
    return data
