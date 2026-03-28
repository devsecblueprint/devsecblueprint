"""
Admin handler for active sessions retrieval.

Provides endpoint to retrieve all active session records from DynamoDB.
"""

import logging
import os
import time
from typing import Dict, Any
from botocore.exceptions import ClientError
import boto3
from auth.admin import require_admin
from utils.responses import json_response, error_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@require_admin
def handle_get_active_sessions(
    headers: Dict[str, str],
    username: str,
    user_id: str,
    query_params: Dict[str, str] = None,
) -> Dict[str, Any]:
    """
    Handle GET /admin/sessions endpoint.

    Scans for all SESSION# records that have not yet expired and returns
    only the latest session per user (with resolved username), sorted newest first.
    """
    try:
        table_name = os.environ.get("PROGRESS_TABLE")
        if not table_name:
            logger.error("PROGRESS_TABLE environment variable not set")
            return error_response(503, "Service unavailable")

        dynamodb = boto3.client("dynamodb")
        now = int(time.time())

        # Collect all active sessions
        all_sessions: list[dict] = []
        scan_kwargs = {
            "TableName": table_name,
            "FilterExpression": "begins_with(SK, :sk_prefix) AND expires_at > :now",
            "ExpressionAttributeValues": {
                ":sk_prefix": {"S": "SESSION#"},
                ":now": {"N": str(now)},
            },
        }

        while True:
            try:
                response = dynamodb.scan(**scan_kwargs)
            except ClientError as e:
                logger.error(f"DynamoDB scan failed: {e.response['Error']['Code']}")
                return error_response(500, "Failed to retrieve sessions")

            for item in response.get("Items", []):
                all_sessions.append(
                    {
                        "user_id": item.get("user_id", {}).get("S", "unknown"),
                        "created_at": int(item.get("created_at", {}).get("N", "0")),
                        "expires_at": int(item.get("expires_at", {}).get("N", "0")),
                    }
                )

            if "LastEvaluatedKey" in response:
                scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            else:
                break

        # Keep only the latest session per user
        latest_by_user: Dict[str, dict] = {}
        for session in all_sessions:
            uid = session["user_id"]
            if (
                uid not in latest_by_user
                or session["created_at"] > latest_by_user[uid]["created_at"]
            ):
                latest_by_user[uid] = session

        # Resolve user_ids to usernames via PROFILE records
        user_ids = list(latest_by_user.keys())
        username_map: Dict[str, str] = {}
        # BatchGetItem supports up to 100 keys per call
        for i in range(0, len(user_ids), 100):
            batch = user_ids[i : i + 100]
            keys = [
                {"PK": {"S": f"USER#{uid}"}, "SK": {"S": "PROFILE"}} for uid in batch
            ]
            try:
                batch_response = dynamodb.batch_get_item(
                    RequestItems={table_name: {"Keys": keys}}
                )
                for profile in batch_response.get("Responses", {}).get(table_name, []):
                    pk = profile.get("PK", {}).get("S", "")
                    uid = pk.removeprefix("USER#")
                    display_name = (
                        profile.get("github_username", {}).get("S", "")
                        or profile.get("gitlab_username", {}).get("S", "")
                        or profile.get("bitbucket_username", {}).get("S", "")
                        or profile.get("username", {}).get("S", "")
                    )
                    if display_name:
                        username_map[uid] = display_name
            except ClientError as e:
                logger.warning(
                    f"Failed to batch-get profiles: {e.response['Error']['Code']}"
                )

        # Attach usernames to sessions
        for session in latest_by_user.values():
            uid = session["user_id"]
            session["username"] = username_map.get(uid, uid)

        sessions = sorted(
            latest_by_user.values(), key=lambda s: s["created_at"], reverse=True
        )

        return json_response(
            200,
            {
                "sessions": sessions,
                "total_active": len(sessions),
            },
        )

    except Exception as e:
        logger.error(f"Unexpected error in handle_get_active_sessions: {e}")
        return error_response(500, "Internal server error")
