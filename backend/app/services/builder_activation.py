"""Builder Activation lifecycle event service.

Records exactly-once BUILDER_ACTIVATED events in DynamoDB when a user
transitions from a non-Builder tier (FREE or EXPLORER) to BUILDER.

Uses conditional writes (attribute_not_exists) for deduplication — a second
call for the same user returns False without raising.

Requirements: 2.3, 2.4, 2.5
"""

import logging
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from app.config import Settings

logger = logging.getLogger(__name__)

# Valid activation sources
VALID_ACTIVATION_SOURCES = (
    "STRIPE_SUBSCRIPTION",
    "ADMIN_GRANT",
    "CONTRIBUTOR_GRANT",
    "SCHOLAR_GRANT",
    "CAMPAIGN",
    "PROMOTION",
    "SYSTEM",
)


def record_builder_activation(
    user_id: str,
    activation_source: str,
    previous_tier: str,
    settings: Settings,
) -> bool:
    """Record a BUILDER_ACTIVATED lifecycle event in DynamoDB.

    Uses a conditional put_item with attribute_not_exists(SK) to ensure
    exactly-once semantics. If the item already exists (duplicate call),
    the function returns False without raising.

    Args:
        user_id: DSB user identifier.
        activation_source: What triggered the activation (e.g. STRIPE_SUBSCRIPTION).
        previous_tier: The tier the user was on before becoming BUILDER.
        settings: Application settings instance.

    Returns:
        True if the activation event was newly recorded.
        False if deduplicated (item already existed).
    """
    dynamodb = boto3.client("dynamodb")
    table_name = settings.membership_table
    now = datetime.now(timezone.utc).isoformat()

    item = {
        "PK": {"S": f"USER#{user_id}"},
        "SK": {"S": "BUILDER_ACTIVATED"},
        "activated_at": {"S": now},
        "activation_source": {"S": activation_source},
        "previous_tier": {"S": previous_tier},
    }

    try:
        dynamodb.put_item(
            TableName=table_name,
            Item=item,
            ConditionExpression="attribute_not_exists(SK)",
        )
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ConditionalCheckFailedException":
            # Deduplication: item already exists — not an error
            logger.info(
                "Builder activation already recorded for user %s (deduplicated)",
                user_id,
            )
            return False
        logger.error("Failed to record builder activation for user %s: %s", user_id, e)
        raise

    # On success: update MEMBERSHIP record with builderActivatedAt timestamp
    try:
        dynamodb.update_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "MEMBERSHIP"},
            },
            UpdateExpression="SET builderActivatedAt = :ts",
            ExpressionAttributeValues={":ts": {"S": now}},
        )
    except ClientError as e:
        # Non-critical — the activation event is already recorded
        logger.error("Failed to update builderActivatedAt for user %s: %s", user_id, e)

    logger.info(
        "Builder activation recorded: user=%s, source=%s, previous_tier=%s",
        user_id,
        activation_source,
        previous_tier,
    )
    return True
