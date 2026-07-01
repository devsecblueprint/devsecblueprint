"""
Response formatting utilities for API Gateway HTTP API compatibility.

This module provides helper functions to format responses with proper CORS headers,
JSON serialization, and redirects. Matches the pattern from the existing DSB backend.
"""

import json
import os
from typing import Any, Dict, List, Optional


def add_cors_headers(headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Add CORS headers to response.

    Args:
        headers: Existing headers dictionary (optional)

    Returns:
        dict: Headers with CORS added

    CORS Configuration:
        - Access-Control-Allow-Origin: From FRONTEND_URL env var
        - Access-Control-Allow-Credentials: true
        - Access-Control-Allow-Methods: GET, PUT, POST, DELETE, OPTIONS
        - Access-Control-Allow-Headers: Content-Type, Cookie, Authorization

    Validates: Requirements 19.1
    """
    if headers is None:
        headers = {}

    frontend_origin = os.environ.get(
        "FRONTEND_URL", "https://staging.devsecblueprint.com"
    )

    cors_headers = {
        "Access-Control-Allow-Origin": frontend_origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, PUT, POST, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Cookie, Authorization",
    }

    return {**headers, **cors_headers}


def json_response(
    status_code: int,
    body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Create JSON response with CORS headers.

    Args:
        status_code: HTTP status code
        body: Response body (will be JSON serialized)
        headers: Additional headers (optional)

    Returns:
        dict: API Gateway response format with:
            - statusCode: HTTP status code
            - headers: Response headers including CORS and Content-Type
            - body: JSON serialized response body

    Validates: Requirements 19.1, 19.6
    """
    if headers is None:
        headers = {}

    headers["Content-Type"] = "application/json"
    headers = add_cors_headers(headers)

    return {"statusCode": status_code, "headers": headers, "body": json.dumps(body)}


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Create error response with CORS headers.

    Args:
        status_code: HTTP error status code (400, 401, 403, 404, 500)
        message: Generic error message (no sensitive information)

    Returns:
        dict: API Gateway response format with error structure

    Validates: Requirements 19.6, 19.11
    """
    return json_response(status_code, {"error": message})


def redirect_response(
    location: str, cookies: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create 302 redirect response with CORS headers.

    Args:
        location: Redirect URL
        cookies: List of Set-Cookie header values (optional)

    Returns:
        dict: API Gateway response with:
            - statusCode: 302
            - headers: Location header, CORS headers, and optional Set-Cookie

    Validates: Requirements 19.1
    """
    headers = {"Location": location}
    headers = add_cors_headers(headers)

    if cookies:
        headers["Set-Cookie"] = cookies[0] if len(cookies) == 1 else cookies

    return {"statusCode": 302, "headers": headers, "body": ""}
