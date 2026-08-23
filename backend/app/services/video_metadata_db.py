"""DynamoDB operations for video metadata.

Encapsulates all DynamoDB interactions for the videos_table,
including CRUD operations and index queries.

Requirements: 2.1, 3.1, 3.2
"""

import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings

logger = logging.getLogger(__name__)


class VideoMetadataDB:
    """DynamoDB operations for the videos metadata table.

    Table: videos_table
    PK: VIDEO#{video_id}
    SK: METADATA
    GSI1 (status-publishedAt-index):
      GSI1PK: STATUS#{status}
      GSI1SK: {publishedAt} (ISO 8601, only for PUBLISHED)
    GSI2 (slug-index):
      GSI2PK: {slug}
      GSI2SK: METADATA
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = boto3.client("dynamodb")

    @property
    def _table_name(self) -> str:
        return self._settings.videos_table

    def put_video(self, video: dict[str, Any]) -> None:
        """Write a video item to DynamoDB.

        Args:
            video: A dict representing the video attributes.
                Must include id, title, slug, status, etc.
        """
        item: dict[str, Any] = {
            "PK": {"S": f"VIDEO#{video['id']}"},
            "SK": {"S": "METADATA"},
            "id": {"S": video["id"]},
            "title": {"S": video["title"]},
            "slug": {"S": video["slug"]},
            "description": {"S": video.get("description", "")},
            "cloudflareStreamId": {"S": video["cloudflare_stream_id"]},
            "thumbnailUrl": {"S": video.get("thumbnail_url", "")},
            "durationSeconds": {"N": str(video.get("duration_seconds", 0))},
            "instructor": {"S": video["instructor"]},
            "recordedAt": {"S": video["recorded_at"]},
            "status": {"S": video["status"]},
            "requiredEntitlement": {"S": "VIDEO_RECORDINGS"},
            "tags": {"L": [{"S": t} for t in video.get("tags", [])]},
            "resources": {
                "L": [
                    {
                        "M": {
                            "title": {"S": r["title"]},
                            "url": {"S": r["url"]},
                        }
                    }
                    for r in video.get("resources", [])
                ]
            },
            "createdAt": {"S": video["created_at"]},
            "updatedAt": {"S": video["updated_at"]},
            "instructors": {
                "L": [
                    {
                        "M": {
                            "name": {"S": i.get("name", "")},
                            "linkedin_url": {"S": i.get("linkedin_url") or ""},
                        }
                    }
                    for i in video.get("instructors", [])
                ]
            },
            "GSI1PK": {"S": f"STATUS#{video['status']}"},
            "GSI1SK": {"S": video.get("published_at") or video["created_at"]},
            "GSI2PK": {"S": video["slug"]},
            "GSI2SK": {"S": "METADATA"},
        }

        if video.get("published_at"):
            item["publishedAt"] = {"S": video["published_at"]}

        try:
            self._client.put_item(TableName=self._table_name, Item=item)
        except ClientError as e:
            logger.error(
                "Failed to put video %s: %s",
                video["id"],
                e.response["Error"]["Code"],
            )
            raise

    def get_video(self, video_id: str) -> dict[str, Any] | None:
        """Retrieve a video by its ID.

        Args:
            video_id: The video identifier.

        Returns:
            The DynamoDB item as a dict, or None if not found.
        """
        try:
            response = self._client.get_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"VIDEO#{video_id}"},
                    "SK": {"S": "METADATA"},
                },
            )
            return response.get("Item")
        except ClientError as e:
            logger.error(
                "Failed to get video %s: %s",
                video_id,
                e.response["Error"]["Code"],
            )
            raise

    def get_video_by_slug(self, slug: str) -> dict[str, Any] | None:
        """Retrieve a video by its slug via GSI2.

        Args:
            slug: The video slug.

        Returns:
            The DynamoDB item as a dict, or None if not found.
        """
        try:
            response = self._client.query(
                TableName=self._table_name,
                IndexName="slug-index",
                KeyConditionExpression=("GSI2PK = :slug AND GSI2SK = :sk"),
                ExpressionAttributeValues={
                    ":slug": {"S": slug},
                    ":sk": {"S": "METADATA"},
                },
                Limit=1,
            )
            items = response.get("Items", [])
            return items[0] if items else None
        except ClientError as e:
            logger.error(
                "Failed to get video by slug %s: %s",
                slug,
                e.response["Error"]["Code"],
            )
            raise

    def query_published(
        self,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Query PUBLISHED videos via GSI1, ordered by publishedAt.

        Args:
            page: 1-based page number.
            page_size: Number of items per page.

        Returns:
            Tuple of (items list, total count).
        """
        return self.query_by_status("PUBLISHED", page, page_size)

    def query_by_status(
        self,
        status: str,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Query videos filtered by status via GSI1.

        Args:
            status: The video status to filter by.
            page: 1-based page number.
            page_size: Number of items per page.

        Returns:
            Tuple of (items list, total count).
        """
        try:
            # First get the total count
            count_response = self._client.query(
                TableName=self._table_name,
                IndexName="status-publishedAt-index",
                KeyConditionExpression="GSI1PK = :status",
                ExpressionAttributeValues={
                    ":status": {"S": f"STATUS#{status}"},
                },
                Select="COUNT",
            )
            total_count = count_response.get("Count", 0)

            # Fetch the page of items
            response = self._client.query(
                TableName=self._table_name,
                IndexName="status-publishedAt-index",
                KeyConditionExpression="GSI1PK = :status",
                ExpressionAttributeValues={
                    ":status": {"S": f"STATUS#{status}"},
                },
                ScanIndexForward=False,  # Most recent first
                Limit=page_size * page,
            )
            items = response.get("Items", [])

            # Manual pagination offset
            start = (page - 1) * page_size
            end = start + page_size
            paged_items = items[start:end]

            return paged_items, total_count
        except ClientError as e:
            logger.error(
                "Failed to query videos by status %s: %s",
                status,
                e.response["Error"]["Code"],
            )
            raise

    def query_all(
        self,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Query all videos with pagination.

        Args:
            page: 1-based page number.
            page_size: Number of items per page.

        Returns:
            Tuple of (items list, total count).
        """
        try:
            # Scan for all metadata items
            count_response = self._client.scan(
                TableName=self._table_name,
                FilterExpression="SK = :sk",
                ExpressionAttributeValues={":sk": {"S": "METADATA"}},
                Select="COUNT",
            )
            total_count = count_response.get("Count", 0)

            response = self._client.scan(
                TableName=self._table_name,
                FilterExpression="SK = :sk",
                ExpressionAttributeValues={":sk": {"S": "METADATA"}},
            )
            items = response.get("Items", [])

            # Sort by createdAt descending
            items.sort(
                key=lambda x: x.get("createdAt", {}).get("S", ""),
                reverse=True,
            )

            # Manual pagination
            start = (page - 1) * page_size
            end = start + page_size
            paged_items = items[start:end]

            return paged_items, total_count
        except ClientError as e:
            logger.error(
                "Failed to query all videos: %s",
                e.response["Error"]["Code"],
            )
            raise

    def slug_exists(self, slug: str) -> bool:
        """Check if a slug already exists in the table.

        Args:
            slug: The slug to check.

        Returns:
            True if the slug exists, False otherwise.
        """
        result = self.get_video_by_slug(slug)
        return result is not None
