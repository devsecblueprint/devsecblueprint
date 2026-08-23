"""DynamoDB operations for video playback progress.

Stores per-user, per-video progress in the existing progress_table
using PK=USER#{user_id}, SK=VIDEO#{video_id}.

Requirements: 5.1, 5.2, 6.1, 6.2, 6.3
"""

import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings

logger = logging.getLogger(__name__)


class VideoProgressDB:
    """DynamoDB operations for playback progress.

    Stores per-user, per-video progress in the existing progress_table.
    PK: USER#{user_id}
    SK: VIDEO#{video_id}
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = boto3.client("dynamodb")

    @property
    def _table_name(self) -> str:
        return self._settings.progress_table

    def get_progress(
        self,
        user_id: str,
        video_id: str,
    ) -> dict[str, Any] | None:
        """Retrieve playback progress for a user and video.

        Args:
            user_id: The user identifier.
            video_id: The video identifier.

        Returns:
            The progress item as a dict, or None if not found.
        """
        try:
            response = self._client.get_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": f"VIDEO#{video_id}"},
                },
            )
            return response.get("Item")
        except ClientError as e:
            logger.error(
                "Failed to get progress for user %s video %s: %s",
                user_id,
                video_id,
                e.response["Error"]["Code"],
            )
            raise

    def save_progress(
        self,
        user_id: str,
        video_id: str,
        data: dict[str, Any],
    ) -> None:
        """Create or update playback progress for a user and video.

        Args:
            user_id: The user identifier.
            video_id: The video identifier.
            data: Dict with positionSeconds, durationSeconds,
                percentComplete, completed, lastWatchedAt, updatedAt.
        """
        item: dict[str, Any] = {
            "PK": {"S": f"USER#{user_id}"},
            "SK": {"S": f"VIDEO#{video_id}"},
            "positionSeconds": {"N": str(data["position_seconds"])},
            "durationSeconds": {"N": str(data["duration_seconds"])},
            "percentComplete": {"N": str(data["percent_complete"])},
            "completed": {"BOOL": data["completed"]},
            "lastWatchedAt": {"S": data["last_watched_at"]},
            "updatedAt": {"S": data["updated_at"]},
        }

        try:
            self._client.put_item(TableName=self._table_name, Item=item)
        except ClientError as e:
            logger.error(
                "Failed to save progress for user %s video %s: %s",
                user_id,
                video_id,
                e.response["Error"]["Code"],
            )
            raise

    def get_user_video_progress(
        self,
        user_id: str,
    ) -> list[dict[str, Any]]:
        """Retrieve all video progress items for a user.

        Queries items with SK beginning with 'VIDEO#'.
        Used to build the Continue Watching list.

        Args:
            user_id: The user identifier.

        Returns:
            List of progress items for the user.
        """
        try:
            response = self._client.query(
                TableName=self._table_name,
                KeyConditionExpression=("PK = :pk AND begins_with(SK, :sk_prefix)"),
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk_prefix": {"S": "VIDEO#"},
                },
            )
            return response.get("Items", [])
        except ClientError as e:
            logger.error(
                "Failed to get video progress for user %s: %s",
                user_id,
                e.response["Error"]["Code"],
            )
            raise
