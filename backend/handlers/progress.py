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


def validate_repo_url(
    url: str, expected_username: str, provider: str = "github"
) -> Dict[str, Any]:
    """
    Validate a repository URL for the given provider and extract metadata.

    Args:
        url: Repository URL to validate
        expected_username: Expected username (from authenticated user)
        provider: Authentication provider ("github" or "gitlab")

    Returns:
        dict: Validation result with valid/error keys

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
    """
    patterns = {
        "github": {
            "regex": r"^https?://(www\.)?github\.com/([^/]+)/([^/]+)/?$",
            "domain": "GitHub",
        },
        "gitlab": {
            "regex": r"^https?://(www\.)?gitlab\.com/([^/]+)/([^/]+)/?$",
            "domain": "GitLab",
        },
        "bitbucket": {
            "regex": r"^https?://(www\.)?bitbucket\.org/([^/]+)/([^/]+)/?$",
            "domain": "Bitbucket Cloud",
        },
    }

    config = patterns.get(provider, patterns["github"])
    match = re.match(config["regex"], url)

    if not match:
        return {"valid": False, "error": f"Invalid {config['domain']} URL format"}

    username = match.group(2)
    repo_name = match.group(3)

    # Bitbucket repos live under workspaces, not usernames — skip ownership check
    if provider == "bitbucket":
        return {"valid": True, "username": username, "repo_name": repo_name}

    if username.lower() != expected_username.lower():
        return {
            "valid": False,
            "error": f"Repository must be under your {config['domain']} account ({expected_username})",
        }

    return {"valid": True, "username": username, "repo_name": repo_name}


def validate_github_url(url: str, expected_username: str) -> Dict[str, Any]:
    """
    Validate GitHub repository URL and extract metadata.
    Retained for backward compatibility — delegates to validate_repo_url.

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
    """
    return validate_repo_url(url, expected_username, "github")


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

        # Extract user_id and provider info from JWT payload
        user_id = payload.get("sub")
        provider = payload.get("provider", "github")
        github_username = payload.get("github_login")
        gitlab_username = payload.get("gitlab_login")
        bitbucket_username = payload.get("bitbucket_login")
        if provider == "bitbucket":
            provider_username = bitbucket_username
        elif provider == "gitlab":
            provider_username = gitlab_username
        else:
            provider_username = github_username
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
            # Validate repo URL for the user's provider
            validation_result = validate_repo_url(repo_url, provider_username, provider)

            if not validation_result["valid"]:
                return error_response(400, validation_result["error"])

            try:
                from datetime import datetime, timezone

                save_capstone_submission(
                    user_id=user_id,
                    content_id=content_id,
                    repo_url=repo_url,
                    github_username=(
                        validation_result["username"] if provider != "bitbucket" else ""
                    ),
                    repo_name=validation_result["repo_name"],
                    provider=provider,
                    bitbucket_username=bitbucket_username or "",
                )

                submission_metadata = {
                    "repo_url": repo_url,
                    "github_username": (
                        validation_result["username"] if provider != "bitbucket" else ""
                    ),
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
