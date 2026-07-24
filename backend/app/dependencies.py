"""Shared FastAPI dependencies.

Provides dependency injection for boto3 clients, settings, and other
shared resources used across routers and services.
"""

from functools import lru_cache
from typing import Any

import boto3

from app.config import Settings


@lru_cache
def get_settings() -> Settings:
    """Cached application settings singleton."""
    return Settings()


def get_dynamodb_resource() -> Any:
    """Create a DynamoDB resource."""
    return boto3.resource("dynamodb")


def get_secrets_client() -> Any:
    """Create a Secrets Manager client."""
    return boto3.client("secretsmanager")


def get_s3_client() -> Any:
    """Create an S3 client."""
    return boto3.client("s3")


def get_ssm_client() -> Any:
    """Create an SSM Parameter Store client."""
    return boto3.client("ssm")
