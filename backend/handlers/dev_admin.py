"""
Dev-only admin session handler.

Provides a synthetic admin session for local UI development without requiring
real OAuth authentication. This endpoint is gated by the DEV_ADMIN_ENABLED
environment variable, which must only be set in development environments.

If DEV_ADMIN_ENABLED is not set or is not "true", the endpoint returns 404,
making it invisible in production.
"""

import os
import logging
from utils.responses import json_response, error_response

logger = logging.getLogger()


def handle_dev_admin_session() -> dict:
    """
    Return a synthetic admin session for local development.

    This endpoint requires no authentication. It returns the same response
    shape as GET /me so the frontend auth provider can consume it directly.

    The endpoint is only active when the DEV_ADMIN_ENABLED environment
    variable is set to "true". In all other cases it returns 404.

    Returns:
        dict: API Gateway response with synthetic admin user data,
              or 404 if dev admin mode is not enabled.
    """
    if os.environ.get("DEV_ADMIN_ENABLED") != "true":
        return error_response(404, "Not found")

    logger.warning(
        "DEV ADMIN SESSION: Returning synthetic admin — do NOT use in production"
    )

    return json_response(
        200,
        {
            "user_id": "dev-admin-local",
            "authenticated": True,
            "is_admin": True,
            "provider": "github",
            "username": "Dev Admin",
            "github_username": "dev-admin",
        },
    )
