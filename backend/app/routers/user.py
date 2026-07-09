"""User router — /user/* and /me routes.

Ports the following Lambda handler routes:
- GET /me            → verify_user() from auth/jwt_utils.py
- GET /user/profile  → handle_get_user_profile() from handlers/user.py
- DELETE /user/account → handle_delete_account() from handlers/user_delete.py

All routes require JWT authentication via the get_current_user dependency.

Requirements: 4.2
"""

import logging
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, Response

from app.auth.jwt import get_current_user
from app.config import Settings
from app.dependencies import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["user"])


# ---------------------------------------------------------------------------
# GET /me — Returns authenticated user info extracted from the JWT payload.
# ---------------------------------------------------------------------------


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)) -> dict:
    """Return authenticated user information from the JWT payload.

    This is the FastAPI equivalent of the Lambda verify_user() handler.
    Since get_current_user already validates the token and extracts the
    payload, this endpoint simply formats and returns the relevant fields.

    Returns:
        User info including user_id, authenticated status, admin flag, and
        provider-specific fields (avatar, username, provider login).
    """
    response_data: dict[str, Any] = {
        "user_id": user.get("sub"),
        "authenticated": True,
        "is_admin": user.get("is_admin", False),
        "provider": user.get("provider", "github"),
    }

    # Optional fields from the JWT payload
    avatar_url = user.get("avatar")
    if avatar_url:
        response_data["avatar_url"] = avatar_url

    username = user.get("name")
    if username:
        response_data["username"] = username

    provider = user.get("provider", "github")
    if provider == "gitlab" and user.get("gitlab_login"):
        response_data["gitlab_username"] = user["gitlab_login"]
    elif provider == "bitbucket" and user.get("bitbucket_login"):
        response_data["bitbucket_username"] = user["bitbucket_login"]
    elif user.get("github_login"):
        response_data["github_username"] = user["github_login"]

    return response_data


# ---------------------------------------------------------------------------
# GET /user/profile — Returns full user profile from DynamoDB.
# ---------------------------------------------------------------------------


def _get_user_profile_from_db(user_id: str, table_name: str) -> dict | None:
    """Query DynamoDB for the user profile record.

    Args:
        user_id: The authenticated user's ID.
        table_name: DynamoDB table name (PROGRESS_TABLE).

    Returns:
        Profile dict or None if not found.
    """
    dynamodb = boto3.client("dynamodb")
    response = dynamodb.get_item(
        TableName=table_name,
        Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "PROFILE"}},
    )
    item = response.get("Item")
    if not item:
        return None

    return {
        "user_id": user_id,
        "username": item.get("username", {}).get("S", ""),
        "avatar_url": item.get("avatar_url", {}).get("S", ""),
        "registered_at": item.get("registered_at", {}).get("S", ""),
        "last_login": item.get("last_login", {}).get("S", ""),
        "github_username": item.get("github_username", {}).get("S", ""),
        "gitlab_username": item.get("gitlab_username", {}).get("S", ""),
        "bitbucket_username": item.get("bitbucket_username", {}).get("S", ""),
        "provider": item.get("provider", {}).get("S", "github"),
        "email": item.get("email", {}).get("S", ""),
    }


def _get_user_progress_count(user_id: str, table_name: str) -> int:
    """Count the user's completed content items in DynamoDB.

    Args:
        user_id: The authenticated user's ID.
        table_name: DynamoDB table name (PROGRESS_TABLE).

    Returns:
        Number of completed content items.
    """
    dynamodb = boto3.client("dynamodb")
    response = dynamodb.query(
        TableName=table_name,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": {"S": f"USER#{user_id}"},
            ":sk_prefix": {"S": "CONTENT#"},
        },
        Select="COUNT",
    )
    return response.get("Count", 0)


def _get_contributor_role_from_db(user_id: str, table_name: str) -> dict | None:
    """Query DynamoDB for the user's contributor role record.

    Args:
        user_id: The authenticated user's ID.
        table_name: DynamoDB table name (PROGRESS_TABLE).

    Returns:
        Dict with role, assigned_by, assigned_at, note or None if not set.
    """
    dynamodb = boto3.client("dynamodb")
    response = dynamodb.get_item(
        TableName=table_name,
        Key={"PK": {"S": f"USER#{user_id}"}, "SK": {"S": "CONTRIBUTOR_ROLE"}},
    )
    item = response.get("Item")
    if not item:
        return None
    return {
        "role": item.get("role", {}).get("S", ""),
        "assigned_by": item.get("assigned_by", {}).get("S", ""),
        "assigned_at": item.get("assigned_at", {}).get("S", ""),
        "note": item.get("note", {}).get("S", ""),
    }


@router.get("/user/profile")
async def get_user_profile(
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Return the full user profile from DynamoDB.

    Includes profile data and whether the user is new (has no progress).

    Returns:
        User profile dict with fields: user_id, username, avatar_url,
        github_username, registered_at, last_login, is_new_user,
        total_completions.

    Raises:
        HTTPException(404): If no profile record exists for the user.
        HTTPException(500): On DynamoDB errors.
    """
    user_id = user.get("sub")
    table_name = settings.progress_table

    try:
        profile = _get_user_profile_from_db(user_id, table_name)
    except ClientError as exc:
        logger.error("DynamoDB error fetching profile for user %s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Failed to fetch user profile")

    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    try:
        progress_count = _get_user_progress_count(user_id, table_name)
    except ClientError as exc:
        logger.error("DynamoDB error fetching progress for user %s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Failed to fetch user profile")

    # Fetch contributor role (if assigned by admin)
    contributor_role = None
    try:
        contributor_role = _get_contributor_role_from_db(user_id, table_name)
    except Exception as exc:
        logger.warning("Failed to fetch contributor role for user %s: %s", user_id, exc)

    return {
        "user_id": profile["user_id"],
        "username": profile["username"],
        "avatar_url": profile.get("avatar_url", ""),
        "github_username": profile.get("github_username", ""),
        "registered_at": profile["registered_at"],
        "last_login": profile["last_login"],
        "is_new_user": progress_count == 0,
        "total_completions": progress_count,
        "contributor_role": contributor_role,
    }


# ---------------------------------------------------------------------------
# DELETE /user/account — Permanently delete the user account.
# ---------------------------------------------------------------------------


def _delete_all_user_items(user_id: str, table_name: str) -> bool:
    """Delete all DynamoDB items for a user (profile, progress, etc.).

    Args:
        user_id: The authenticated user's ID.
        table_name: DynamoDB table name (PROGRESS_TABLE).

    Returns:
        True if successful, False otherwise.
    """
    dynamodb = boto3.client("dynamodb")
    last_evaluated_key = None

    while True:
        query_params: dict[str, Any] = {
            "TableName": table_name,
            "KeyConditionExpression": "PK = :pk",
            "ExpressionAttributeValues": {":pk": {"S": f"USER#{user_id}"}},
        }
        if last_evaluated_key:
            query_params["ExclusiveStartKey"] = last_evaluated_key

        response = dynamodb.query(**query_params)

        for item in response.get("Items", []):
            dynamodb.delete_item(
                TableName=table_name,
                Key={"PK": item["PK"], "SK": item["SK"]},
            )

        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break

    return True


def _revoke_user_sessions(user_id: str, table_name: str) -> None:
    """Revoke all refresh token sessions for a user.

    Uses the user-state table to delete session records.

    Args:
        user_id: The authenticated user's ID.
        table_name: DynamoDB table name (USER_STATE_TABLE).
    """
    dynamodb = boto3.client("dynamodb")

    # Query all session records for this user
    try:
        response = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"USER#{user_id}"},
                ":sk_prefix": {"S": "SESSION#"},
            },
        )
        for item in response.get("Items", []):
            dynamodb.delete_item(
                TableName=table_name,
                Key={"PK": item["PK"], "SK": item["SK"]},
            )
    except ClientError as exc:
        logger.warning("Failed to revoke sessions for user %s: %s", user_id, exc)


@router.delete("/user/account")
async def delete_account(
    response: Response,
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Permanently delete the authenticated user's account and all data.

    Deletes the user's profile, progress records, capstone submissions, and
    revokes all active sessions. Clears session cookies on the response.

    Returns:
        Success message.

    Raises:
        HTTPException(500): On deletion failure.
    """
    user_id = user.get("sub")
    table_name = settings.progress_table

    logger.info("Deleting account for user: %s", user_id)

    try:
        success = _delete_all_user_items(user_id, table_name)
    except ClientError as exc:
        logger.error("Failed to delete account for user %s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Failed to delete account")

    if not success:
        logger.error("Failed to delete account for user %s", user_id)
        raise HTTPException(status_code=500, detail="Failed to delete account")

    logger.info("Successfully deleted account for user: %s", user_id)

    # Revoke sessions so the user is logged out immediately
    try:
        _revoke_user_sessions(user_id, settings.user_state_table)
    except Exception as exc:
        logger.warning(
            "Failed to revoke sessions after account deletion for %s: %s",
            user_id,
            exc,
        )

    # Clear session cookies
    cookie_domain = os.environ.get("COOKIE_DOMAIN", "")
    response.delete_cookie("dsb_session", domain=cookie_domain or None, path="/")
    response.delete_cookie("dsb_refresh", domain=cookie_domain or None, path="/refresh")
    response.delete_cookie("dsb_token", domain=cookie_domain or None, path="/")

    return {"message": "Account successfully deleted"}
