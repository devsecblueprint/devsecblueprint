"""
Response formatting utilities for API Gateway HTTP API compatibility.

This module provides helper functions to format responses with proper CORS headers,
JSON serialization, redirects, and cookie handling.
"""

import json
import os
import hashlib
from typing import Any, Dict, List, Optional


def add_cors_headers(headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Add CORS headers to response.

    Args:
        headers: Existing headers dictionary (optional)

    Returns:
        dict: Headers with CORS added

    CORS Configuration:
        - Access-Control-Allow-Origin: From FRONTEND_ORIGIN env var
        - Access-Control-Allow-Credentials: true
        - Access-Control-Allow-Methods: GET, PUT, OPTIONS
        - Access-Control-Allow-Headers: Content-Type, Cookie

    Environment Variables:
        - FRONTEND_ORIGIN: Frontend URL for CORS (e.g., https://staging.devsecblueprint.com)

    Validates: Requirements 7.1, 7.2, 7.3, 7.4
    """
    if headers is None:
        headers = {}

    # Get frontend origin from environment variable
    frontend_origin = os.environ.get(
        "FRONTEND_ORIGIN", "https://staging.devsecblueprint.com"
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
    cache_control: Optional[str] = None,
    etag: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create JSON response with CORS headers and optional caching headers.

    Args:
        status_code: HTTP status code
        body: Response body (will be JSON serialized)
        headers: Additional headers (optional)
        cache_control: Cache-Control header value (optional)
        etag: ETag header value (optional)

    Returns:
        dict: API Gateway response format with:
            - statusCode: HTTP status code
            - headers: Response headers including CORS, Content-Type, and caching headers
            - body: JSON serialized response body

    Validates: Requirements 12.1, 12.3, 7.1, 7.2, 7.3, 7.4, 18.5
    """
    if headers is None:
        headers = {}

    headers["Content-Type"] = "application/json"

    # Add caching headers if provided (Requirement 18.5)
    if cache_control:
        headers["Cache-Control"] = cache_control

    if etag:
        headers["ETag"] = etag

    headers = add_cors_headers(headers)

    return {"statusCode": status_code, "headers": headers, "body": json.dumps(body)}


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

    Validates: Requirements 12.4, 12.6, 7.1, 7.2, 7.3, 7.4
    """
    headers = {"Location": location}
    headers = add_cors_headers(headers)

    if cookies:
        # API Gateway HTTP API supports multiple Set-Cookie headers via array
        headers["Set-Cookie"] = cookies[0] if len(cookies) == 1 else cookies

    return {"statusCode": 302, "headers": headers, "body": ""}


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Create error response with CORS headers.

    Args:
        status_code: HTTP error status code (400, 401, 404, 500)
        message: Generic error message (no sensitive information)

    Returns:
        dict: API Gateway response format with error structure

    Validates: Requirements 12.2, 8.2, 8.3, 7.1, 7.2, 7.3, 7.4
    """
    return json_response(status_code, {"error": message})


def create_cookie(
    name: str,
    value: str,
    max_age: int,
    secure: bool = True,
    http_only: bool = True,
    same_site: str = "Lax",
    domain: Optional[str] = None,
    path: str = "/",
) -> str:
    """
    Create Set-Cookie header value.

    Args:
        name: Cookie name
        value: Cookie value
        max_age: Max age in seconds
        secure: Secure flag (default: True)
        http_only: HttpOnly flag (default: True)
        same_site: SameSite attribute (default: "Lax")
        domain: Domain attribute for cross-subdomain cookies (optional)
        path: Path attribute (default: "/")

    Returns:
        str: Set-Cookie header value formatted according to RFC 6265

    Example:
        >>> create_cookie("dsb_token", "jwt_value", 3600)
        'dsb_token=jwt_value; Max-Age=3600; Path=/; Secure; HttpOnly; SameSite=Lax'

    Validates: Requirements 12.6, 2.5
    """
    cookie_parts = [f"{name}={value}", f"Max-Age={max_age}", f"Path={path}"]

    if domain:
        cookie_parts.append(f"Domain={domain}")

    if secure:
        cookie_parts.append("Secure")

    if http_only:
        cookie_parts.append("HttpOnly")

    if same_site:
        cookie_parts.append(f"SameSite={same_site}")

    return "; ".join(cookie_parts)


def delete_cookie(
    name: str,
    domain: Optional[str] = None,
    path: str = "/",
) -> str:
    """
    Create Set-Cookie header value to delete a cookie.

    Args:
        name: Cookie name
        domain: Domain attribute (optional). If not provided, uses
            the cookie domain derived from FRONTEND_ORIGIN.
        path: Path attribute (default: "/")

    Returns:
        str: Set-Cookie header value that expires the cookie immediately

    Example:
        >>> delete_cookie("dsb_token", domain=".example.com")
        'dsb_token=; Max-Age=0; Path=/; Domain=.example.com'
    """
    cookie_parts = [f"{name}=", "Max-Age=0", f"Path={path}"]

    if domain:
        cookie_parts.append(f"Domain={domain}")

    return "; ".join(cookie_parts)


def get_cookie_domain() -> str:
    """Derive the root cookie domain from the FRONTEND_ORIGIN env var.

    For example, ``https://app.example.com`` yields ``.example.com``.
    Returns an empty string if the domain cannot be determined, which
    means the cookie will be scoped to the responding host only.

    Returns:
        str: Root domain prefixed with a dot for cross-subdomain cookies,
        or empty string if not determinable.
    """
    origin = os.environ.get("FRONTEND_ORIGIN", "")
    try:
        # Strip protocol
        host = origin.split("://", 1)[-1].split("/")[0].split(":")[0]
        parts = host.split(".")
        if len(parts) >= 2:
            return "." + ".".join(parts[-2:])
    except Exception:
        pass
    return ""


def generate_etag(content: str) -> str:
    """
    Generate ETag from content using MD5 hash.

    Args:
        content: Content to hash (typically JSON string)

    Returns:
        str: ETag value in format "hash"

    Example:
        >>> generate_etag('{"data": "value"}')
        '"5d41402abc4b2a76b9719d911017c592"'

    Validates: Requirements 18.5
    """
    hash_value = hashlib.md5(content.encode("utf-8")).hexdigest()
    return f'"{hash_value}"'
