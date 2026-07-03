"""Audit logging service for the membership system.

Writes audit log entries to DynamoDB. On failure, logs to CloudWatch
but never blocks the triggering operation.

Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.5
"""

import base64
import logging
import os

import boto3

from models.audit_event import AuditEvent
from config.settings import MEMBERSHIP_TABLE

logger = logging.getLogger(__name__)

_dynamodb_client = boto3.client("dynamodb")


def generate_ulid_suffix() -> str:
    """Generate a short random suffix for collision avoidance on same-millisecond events.

    Uses 6 random bytes encoded as base32 for a compact unique identifier.
    """
    return base64.b32encode(os.urandom(6)).decode("ascii").rstrip("=").lower()


def write_audit_log(event: AuditEvent) -> None:
    """Write an audit log entry to DynamoDB.

    Generates a ULID suffix to avoid collisions for events occurring within the
    same millisecond. Delegates item construction to the AuditEvent model, then
    performs a PutItem.

    On ANY failure (network, validation, DynamoDB error), logs the error to
    CloudWatch but never raises — the caller must never be blocked.

    Args:
        event: The AuditEvent dataclass instance containing all event data.
    """
    try:
        ulid_suffix = generate_ulid_suffix()

        # Build the DynamoDB item using the model's serialization
        item = event.to_dynamo_item(ulid_suffix)

        # Store NULL for conditional fields that are applicable but unavailable.
        # IMPORTANT: Do NOT add NULL for GSI key attributes (discord_user_id,
        # stripe_customer_id, user_id) — DynamoDB rejects NULL values for
        # index key attributes. Items without these fields simply won't
        # appear in the respective GSI, which is correct behavior.
        conditional_fields = [
            "previous_state",
            "new_state",
            "roles_added",
            "roles_removed",
            "stripe_subscription_id",
            "stripe_event_id",
            "reason",
            "error_message",
        ]
        for field_name in conditional_fields:
            if field_name not in item:
                item[field_name] = {"NULL": True}

        # Write to DynamoDB
        _dynamodb_client.put_item(
            TableName=MEMBERSHIP_TABLE,
            Item=item,
        )

        logger.info(
            "Audit log written: event_type=%s, user=%s, sk=%s",
            event.event_type.value,
            event.dsb_user_id,
            item["SK"]["S"],
        )

    except Exception:
        # Never block the triggering operation — log and swallow
        logger.error(
            "Failed to write audit log: event_type=%s, dsb_user_id=%s",
            event.event_type.value if event else "unknown",
            event.dsb_user_id if event else "unknown",
            exc_info=True,
        )
