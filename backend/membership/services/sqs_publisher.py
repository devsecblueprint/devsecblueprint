import json
import logging
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def publish_sync_event(
    user_id: str, event_type: str, new_tier: str | None = None
) -> bool:
    """
    Publish a sync event to the SQS FIFO queue.

    Args:
        user_id: DSB user ID (used as MessageGroupId for per-user ordering)
        event_type: Type of event (e.g., "tier_change", "discord_connected", "admin_sync")
        new_tier: New membership tier (optional, for informational purposes)

    Returns:
        bool: True if published successfully, False on failure
    """
    queue_url = os.environ.get("DISCORD_SYNC_QUEUE_URL")
    if not queue_url:
        logger.error("DISCORD_SYNC_QUEUE_URL environment variable not set")
        return False

    message_body = json.dumps(
        {
            "user_id": user_id,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "new_membership_tier": new_tier,
        }
    )

    try:
        sqs = boto3.client("sqs")
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body,
            MessageGroupId=user_id,
        )
        logger.info(f"Published sync event for user {user_id}: {event_type}")
        return True
    except ClientError as e:
        logger.error(f"Failed to publish sync event for user {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error publishing sync event: {e}")
        return False
