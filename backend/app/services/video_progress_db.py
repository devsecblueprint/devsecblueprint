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

        Uses updates (never a whole-record replace) so fields written for
        analytics survive later saves, and never reads:

        * ``maxPercentComplete`` is a high-water mark. DynamoDB has no ``max()``,
          so the first update only raises it when the new percent is higher
          (a single write, the common case while watching forward). If the
          viewer is behind their best, the condition fails and a second update
          saves the progress fields without touching the high-water mark.
        * ``everCompleted`` is sticky. It is set on any save at or above the
          completion threshold and is never cleared by a lower save.
        * Records written before these fields existed are upgraded in place:
          their old percent and completed values seed the new fields.

        Args:
            user_id: The user identifier.
            video_id: The video identifier.
            data: Dict with position_seconds, duration_seconds,
                percent_complete, completed, last_watched_at, updated_at.
        """
        key = {
            "PK": {"S": f"USER#{user_id}"},
            "SK": {"S": f"VIDEO#{video_id}"},
        }
        values: dict[str, Any] = {
            ":pos": {"N": str(data["position_seconds"])},
            ":dur": {"N": str(data["duration_seconds"])},
            ":pct": {"N": str(data["percent_complete"])},
            ":done": {"BOOL": data["completed"]},
            ":lw": {"S": data["last_watched_at"]},
            ":upd": {"S": data["updated_at"]},
        }
        base_sets = [
            "positionSeconds = :pos",
            "durationSeconds = :dur",
            "percentComplete = :pct",
            "completed = :done",
            "lastWatchedAt = :lw",
            "updatedAt = :upd",
        ]

        completed = bool(data["completed"])
        if completed:
            values[":true"] = {"BOOL": True}
        table = self._table_name

        try:
            # Common case: new high-water mark (or first save). One write.
            # A save that is not a completion can't be a legacy completed
            # record being lowered here (that would need a higher percent), so
            # everCompleted is only written when this save is a completion.
            fast_sets = base_sets + ["maxPercentComplete = :pct"]
            if completed:
                fast_sets.append("everCompleted = :true")
            self._client.update_item(
                TableName=table,
                Key=key,
                UpdateExpression="SET " + ", ".join(fast_sets),
                ConditionExpression=(
                    "(attribute_not_exists(maxPercentComplete) AND "
                    "(attribute_not_exists(percentComplete) OR percentComplete <= :pct))"
                    " OR maxPercentComplete < :pct"
                ),
                ExpressionAttributeValues=values,
            )
            return
        except ClientError as e:
            code = e.response["Error"]["Code"]
            behind_best = code == "ConditionalCheckFailedException"
            if not behind_best:
                # Unexpected failure of the analytics write. Still try to save
                # the member's progress below.
                logger.warning(
                    "Best-progress write failed for user %s video %s: %s",
                    user_id,
                    video_id,
                    code,
                )

        # Fallback: save the progress fields only.
        slow_sets = list(base_sets)
        if completed:
            slow_sets.append("everCompleted = :true")
        if behind_best:
            # The record exists, so these may read its old values: keep (or,
            # for legacy records, seed) the high-water mark and the sticky flag.
            slow_sets.append(
                "maxPercentComplete = if_not_exists(maxPercentComplete, percentComplete)"
            )
            if not completed:
                slow_sets.append(
                    "everCompleted = if_not_exists(everCompleted, completed)"
                )
        try:
            self._client.update_item(
                TableName=table,
                Key=key,
                UpdateExpression="SET " + ", ".join(slow_sets),
                ExpressionAttributeValues=values,
            )
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
