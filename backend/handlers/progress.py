"""
Progress tracking endpoint handler.

This module provides the handler for the PUT /progress endpoint, which allows
authenticated users to mark content as complete. It validates JWT tokens,
extracts content_id from the request body, and saves progress to DynamoDB.
"""

import json
import re
from typing import Dict, Any
from jose import JWTError
from auth.jwt_utils import extract_token_from_cookie, validate_jwt
from services.dynamo import save_progress, save_capstone_submission
from utils.responses import json_response, error_response


def validate_github_url(url: str, expected_username: str) -> Dict[str, Any]:
    """
    Validate GitHub repository URL and extract metadata.

    Validates that the URL matches the GitHub URL format and that the username
    in the URL matches the expected username (case-insensitive).

    Args:
        url: GitHub repository URL to validate
        expected_username: Expected GitHub username (from authenticated user)

    Returns:
        dict: Validation result with one of the following structures:
            Success: {
                "valid": True,
                "username": str,  # Extracted GitHub username
                "repo_name": str  # Extracted repository name
            }
            Failure: {
                "valid": False,
                "error": str  # Error message describing the validation failure
            }

    Examples:
        >>> validate_github_url("https://github.com/user/repo", "user")
        {"valid": True, "username": "user", "repo_name": "repo"}

        >>> validate_github_url("https://github.com/User/repo", "user")
        {"valid": True, "username": "User", "repo_name": "repo"}

        >>> validate_github_url("https://github.com/other/repo", "user")
        {"valid": False, "error": "Repository must be under your GitHub account"}

        >>> validate_github_url("invalid-url", "user")
        {"valid": False, "error": "Invalid GitHub URL format"}

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
    """
    # GitHub URL pattern: supports http/https, with/without www
    # Captures username (group 2) and repo name (group 3)
    pattern = r"^https?://(www\.)?github\.com/([^/]+)/([^/]+)/?$"

    match = re.match(pattern, url)

    # Check if URL matches GitHub format (Requirement 2.5)
    if not match:
        return {"valid": False, "error": "Invalid GitHub URL format"}

    # Extract username and repo name from URL (Requirement 2.1)
    username = match.group(2)
    repo_name = match.group(3)

    # Compare username with expected username (case-insensitive) (Requirement 2.2, 2.3)
    if username.lower() != expected_username.lower():
        return {
            "valid": False,
            "error": f"Repository must be under your GitHub account ({expected_username})",  # Requirement 2.4
        }

    # Return success with extracted metadata
    return {"valid": True, "username": username, "repo_name": repo_name}


def handle_progress(headers: Dict[str, str], body: str) -> Dict[str, Any]:
    """
    Handle PUT /progress endpoint to save user progress.

    This endpoint allows authenticated users to mark content as complete.
    It validates the JWT from cookies, extracts content_id from the request body,
    and writes the progress record to DynamoDB. Optionally accepts repo_url for
    capstone submissions.

    Args:
        headers: Request headers (lowercase keys) from API Gateway event
        body: Request body (JSON string) containing content_id and optional repo_url

    Returns:
        dict: API Gateway response

    Response Format (Success):
        {
            "statusCode": 200,
            "headers": {...CORS headers...},
            "body": '{"message": "Progress saved successfully"}'
        }

    Response Format (Success with repo_url):
        {
            "statusCode": 200,
            "headers": {...CORS headers...},
            "body": '{
                "message": "Progress saved successfully",
                "submission": {
                    "repo_url": "...",
                    "github_username": "...",
                    "repo_name": "...",
                    "submitted_at": "..."
                }
            }'
        }

    Response Format (Error - 401):
        {
            "statusCode": 401,
            "headers": {...CORS headers...},
            "body": '{"error": "Authentication failed"}'
        }

    Response Format (Error - 400):
        {
            "statusCode": 400,
            "headers": {...CORS headers...},
            "body": '{"error": "Invalid request"}'
        }

    Response Format (Error - 500):
        {
            "statusCode": 500,
            "headers": {...CORS headers...},
            "body": '{"error": "Service temporarily unavailable"}'
        }

    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
    """
    try:
        # Extract and validate JWT from cookie (Requirement 4.1)
        token = extract_token_from_cookie(headers)

        # Handle missing JWT (Requirement 4.4)
        if not token:
            return error_response(401, "Authentication failed")

        # Validate JWT
        try:
            payload = validate_jwt(token)
        except JWTError:
            # Invalid or expired JWT (Requirement 4.4)
            return error_response(401, "Authentication failed")

        # Extract user_id and github_username from JWT payload
        user_id = payload.get("sub")
        github_username = payload.get("github_login")
        if not user_id:
            return error_response(401, "Authentication failed")

        # Parse JSON body to extract content_id and optional repo_url (Requirement 4.1)
        try:
            if not body:
                return error_response(400, "Invalid request")

            body_data = json.loads(body)
            content_id = body_data.get("content_id")
            repo_url = body_data.get("repo_url")

            # Handle missing content_id (Requirement 4.5)
            if not content_id:
                return error_response(400, "Invalid request")

        except (json.JSONDecodeError, ValueError):
            # Invalid JSON body
            return error_response(400, "Invalid request")

        # Handle capstone submission if repo_url is provided
        submission_metadata = None
        if repo_url:
            # Validate GitHub URL and username match
            validation_result = validate_github_url(repo_url, github_username)

            if not validation_result["valid"]:
                # Return validation error
                return error_response(400, validation_result["error"])

            # Save capstone submission
            try:
                from datetime import datetime, timezone

                save_capstone_submission(
                    user_id=user_id,
                    content_id=content_id,
                    repo_url=repo_url,
                    github_username=validation_result["username"],
                    repo_name=validation_result["repo_name"],
                )

                # Prepare submission metadata for response
                submission_metadata = {
                    "repo_url": repo_url,
                    "github_username": validation_result["username"],
                    "repo_name": validation_result["repo_name"],
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                }
            except Exception:
                # Handle DynamoDB errors for submission
                return error_response(500, "Service temporarily unavailable")

        # Save progress to DynamoDB (Requirement 4.2)
        try:
            save_progress(user_id, content_id)
        except Exception:
            # Handle DynamoDB errors (Requirement 4.6)
            return error_response(500, "Service temporarily unavailable")

        # Return success response (Requirement 4.3)
        response_data = {"message": "Progress saved successfully"}
        if submission_metadata:
            response_data["submission"] = submission_metadata

        return json_response(200, response_data)

    except Exception:
        # Catch any unexpected errors and return generic error
        # Don't expose internal details or stack traces (Requirement 8.2, 8.3)
        return error_response(500, "Service temporarily unavailable")
