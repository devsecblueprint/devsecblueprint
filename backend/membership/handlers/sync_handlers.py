"""Handler functions for SQS-triggered Discord sync and scheduled reconciliation.

These handlers are invoked by the Lambda entry point (handler.py) based on
event source detection:
- SQS event source → handle_sqs_event
- EventBridge Scheduler → handle_reconciliation

Validates: Requirements 12.5–12.7, 13.1–13.10
"""

import json
import logging
import time
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from config.settings import MEMBERSHIP_TABLE
from models.audit_event import AuditEvent, AuditEventType
from services.audit import write_audit_log

logger = logging.getLogger(__name__)

# Reconciliation constants
RECONCILIATION_TIMEOUT_SECONDS = 14400  # 4 hours
RECONCILIATION_LOCK_TTL_SECONDS = 14400  # 4 hours
RATE_LIMIT_DELAY_SECONDS = 1  # Minimum delay between Discord API calls


def handle_sqs_event(event: dict) -> dict:
    """Process SQS FIFO messages triggering Discord role sync.

    Each SQS record contains a JSON body with user_id identifying which
    user's Discord roles need synchronization. On success, Lambda's SQS
    integration auto-deletes the message. On failure, raising an exception
    causes the message to return to the queue for retry (up to maxReceiveCount=3,
    then routed to DLQ).

    Args:
        event: Lambda event dict containing SQS Records.

    Returns:
        dict with statusCode and processing summary.

    Raises:
        Exception: On sync failure, so the message returns to queue for retry.
    """
    records = event.get("Records", [])

    if not records:
        logger.warning("SQS event received with no records")
        return {"statusCode": 200, "body": "No records to process"}

    for record in records:
        message_id = record.get("messageId", "unknown")
        body_str = record.get("body", "{}")

        try:
            body = json.loads(body_str)
        except (json.JSONDecodeError, TypeError):
            logger.error("Failed to parse SQS message body: message_id=%s", message_id)
            # Raise to trigger retry — malformed messages will eventually go to DLQ
            raise ValueError(f"Invalid JSON in SQS message {message_id}")

        user_id = body.get("user_id")
        event_type = body.get("event_type", "unknown")

        if not user_id:
            logger.error(
                "SQS message missing user_id: message_id=%s, body=%s",
                message_id,
                body_str,
            )
            # Skip messages without user_id — they can't be processed
            continue

        logger.info(
            "Processing sync event: user=%s, type=%s, message_id=%s",
            user_id,
            event_type,
            message_id,
        )

        # Import here to avoid circular imports and allow mocking in tests
        from services.discord_sync import sync_discord_roles

        # Call sync — on failure, raise to trigger SQS retry
        sync_discord_roles(user_id)

        logger.info(
            "Sync completed successfully: user=%s, type=%s, message_id=%s",
            user_id,
            event_type,
            message_id,
        )

    return {"statusCode": 200, "body": f"Processed {len(records)} record(s)"}


def handle_reconciliation(event: dict) -> dict:
    """Run scheduled reconciliation for all active Discord users.

    Scans DynamoDB for all DISCORD_ACTIVE items and synchronizes each user's
    Discord roles with their current membership tier. Implements:
    - Concurrency guard via conditional lock in DynamoDB
    - 1-second delay between Discord API calls (rate limit respect)
    - 4-hour timeout enforcement
    - Per-user error isolation (failures don't stop processing)
    - Metrics tracking and audit logging

    Args:
        event: Lambda event dict from EventBridge Scheduler.

    Returns:
        dict with summary metrics of the reconciliation run.
    """
    start_time = time.time()
    dynamodb = boto3.client("dynamodb")

    # Metrics tracking
    metrics = {
        "total_processed": 0,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "timed_out": False,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    # Acquire concurrency lock
    if not _acquire_reconciliation_lock(dynamodb):
        logger.warning("Reconciliation already in progress — skipping this run")
        return {
            "statusCode": 200,
            "body": "Reconciliation skipped — another instance is running",
        }

    try:
        # Write Reconciliation_Started audit entry
        _write_reconciliation_audit(
            AuditEventType.RECONCILIATION_STARTED,
            "Reconciliation started",
        )

        # Scan for all active Discord users
        active_users = _scan_active_discord_users(dynamodb)
        logger.info("Reconciliation found %d active Discord users", len(active_users))

        # Process each user
        for item in active_users:
            # Check 4-hour timeout before processing next user
            elapsed = time.time() - start_time
            if elapsed >= RECONCILIATION_TIMEOUT_SECONDS:
                logger.warning(
                    "Reconciliation timeout reached after %d seconds, "
                    "processed %d/%d users",
                    int(elapsed),
                    metrics["total_processed"],
                    len(active_users),
                )
                metrics["timed_out"] = True
                break

            # Extract user_id from PK (format: USER#{user_id})
            pk = item.get("PK", {}).get("S", "")
            if not pk.startswith("USER#"):
                continue
            user_id = pk[5:]  # Strip "USER#" prefix

            metrics["total_processed"] += 1

            try:
                from services.discord_sync import sync_discord_roles

                sync_discord_roles(user_id)
                metrics["successful"] += 1
                logger.info("Reconciliation sync successful: user=%s", user_id)
            except Exception as e:
                metrics["failed"] += 1
                logger.error(
                    "Reconciliation sync failed: user=%s, error=%s",
                    user_id,
                    str(e),
                )

            # Rate limit: wait at least 1 second between Discord API calls
            time.sleep(RATE_LIMIT_DELAY_SECONDS)

        # Calculate final metrics
        metrics["completed_at"] = datetime.now(timezone.utc).isoformat()
        metrics["elapsed_seconds"] = int(time.time() - start_time)

        # Write Reconciliation_Completed audit entry with summary
        summary = (
            f"total={metrics['total_processed']}, "
            f"successful={metrics['successful']}, "
            f"failed={metrics['failed']}, "
            f"timed_out={metrics['timed_out']}, "
            f"elapsed={metrics['elapsed_seconds']}s"
        )
        _write_reconciliation_audit(
            AuditEventType.RECONCILIATION_COMPLETED,
            summary,
        )

        # Log summary to CloudWatch
        logger.info("Reconciliation completed: %s", summary)

        return {"statusCode": 200, "body": metrics}

    finally:
        # Always release the concurrency lock
        _release_reconciliation_lock(dynamodb)


def _acquire_reconciliation_lock(dynamodb) -> bool:
    """Acquire a concurrency lock for reconciliation using conditional write.

    Uses DynamoDB conditional PutItem with attribute_not_exists to ensure
    only one reconciliation runs at a time. Lock has a TTL matching the
    4-hour timeout as a safety net.

    Args:
        dynamodb: boto3 DynamoDB client.

    Returns:
        True if lock acquired, False if another reconciliation is running.
    """
    table_name = MEMBERSHIP_TABLE
    expires_at = int(time.time()) + RECONCILIATION_LOCK_TTL_SECONDS

    try:
        dynamodb.put_item(
            TableName=table_name,
            Item={
                "PK": {"S": "RECONCILIATION_LOCK"},
                "SK": {"S": "ACTIVE"},
                "acquired_at": {"S": datetime.now(timezone.utc).isoformat()},
                "expires_at": {"N": str(expires_at)},
            },
            ConditionExpression="attribute_not_exists(PK)",
        )
        logger.info("Reconciliation lock acquired")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        logger.error("Error acquiring reconciliation lock: %s", e)
        raise


def _release_reconciliation_lock(dynamodb) -> None:
    """Release the reconciliation concurrency lock.

    Args:
        dynamodb: boto3 DynamoDB client.
    """
    table_name = MEMBERSHIP_TABLE

    try:
        dynamodb.delete_item(
            TableName=table_name,
            Key={
                "PK": {"S": "RECONCILIATION_LOCK"},
                "SK": {"S": "ACTIVE"},
            },
        )
        logger.info("Reconciliation lock released")
    except ClientError as e:
        logger.error("Error releasing reconciliation lock: %s", e)


def _scan_active_discord_users(dynamodb) -> list[dict]:
    """Scan DynamoDB for all items where SK=DISCORD_ACTIVE.

    Handles pagination for large result sets.

    Args:
        dynamodb: boto3 DynamoDB client.

    Returns:
        List of DynamoDB items representing active Discord connections.
    """
    table_name = MEMBERSHIP_TABLE
    items = []
    last_evaluated_key = None

    while True:
        scan_kwargs = {
            "TableName": table_name,
            "FilterExpression": "SK = :sk",
            "ExpressionAttributeValues": {":sk": {"S": "DISCORD_ACTIVE"}},
        }
        if last_evaluated_key:
            scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

        response = dynamodb.scan(**scan_kwargs)
        items.extend(response.get("Items", []))

        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break

    return items


def _write_reconciliation_audit(event_type: AuditEventType, reason: str) -> None:
    """Write a reconciliation audit entry.

    Uses "SYSTEM" as the user_id and "scheduler" as the actor since
    reconciliation is a system-initiated process.

    Args:
        event_type: The audit event type (Started or Completed).
        reason: Description/summary for the audit entry.
    """
    audit_event = AuditEvent.build(
        event_type=event_type,
        dsb_user_id="SYSTEM",
        actor="scheduler",
    ).with_reason(reason)
    write_audit_log(audit_event)
