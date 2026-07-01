"""Audit event data model for DynamoDB serialization.

Validates: Requirements 15.1, 15.2, 15.5
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class AuditEventType(str, Enum):
    """All auditable event types in the membership system."""

    CONNECTED = "Connected"
    VERIFIED = "Verified"
    DISCONNECTED = "Disconnected"
    DUPLICATE_LINK_REJECTED = "Duplicate_Link_Rejected"
    GUILD_JOINED = "Guild_Joined"
    ROLES_ADDED = "Roles_Added"
    ROLES_REMOVED = "Roles_Removed"
    SYNC_SUCCESSFUL = "Sync_Successful"
    SYNC_FAILED = "Sync_Failed"
    RECONCILIATION_STARTED = "Reconciliation_Started"
    RECONCILIATION_COMPLETED = "Reconciliation_Completed"
    ADMIN_OVERRIDE = "Admin_Override"
    SUBSCRIPTION_CREATED = "Subscription_Created"
    SUBSCRIPTION_UPDATED = "Subscription_Updated"
    SUBSCRIPTION_ENDED = "Subscription_Ended"
    PAYMENT_FAILED = "Payment_Failed"


@dataclass
class AuditEvent:
    """Represents an audit log entry for identity, subscription, or sync events.

    Required fields: event_type, dsb_user_id, actor, timestamp.
    Conditional fields: stored as None (NULL in DynamoDB) when applicable but unavailable.

    Use the builder pattern via AuditEvent.build() for convenient construction.
    """

    # Required fields
    event_type: AuditEventType
    dsb_user_id: str
    actor: str  # "system", "user:{user_id}", "admin:{admin_id}", "stripe", "scheduler"
    timestamp: str  # ISO 8601 with millisecond precision

    # Conditional fields — None means not-applicable for this event
    discord_user_id: str | None = None
    previous_state: str | None = None
    new_state: str | None = None
    roles_added: list[str] | None = None
    roles_removed: list[str] | None = None
    stripe_subscription_id: str | None = None
    stripe_event_id: str | None = None
    reason: str | None = None  # max 500 chars
    error_message: str | None = None  # max 1000 chars

    @classmethod
    def build(
        cls,
        event_type: AuditEventType,
        dsb_user_id: str,
        actor: str,
        timestamp: str | None = None,
    ) -> "AuditEvent":
        """Create an AuditEvent with auto-generated timestamp if not provided.

        Args:
            event_type: The type of audit event.
            dsb_user_id: The DSB user ID associated with this event.
            actor: Who/what triggered the event.
            timestamp: Optional ISO 8601 timestamp. Auto-generated if omitted.

        Returns:
            A new AuditEvent instance ready for chaining builder methods.
        """
        if timestamp is None:
            timestamp = (
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            )
        return cls(
            event_type=event_type,
            dsb_user_id=dsb_user_id,
            actor=actor,
            timestamp=timestamp,
        )

    def with_discord(self, discord_user_id: str) -> "AuditEvent":
        """Set the Discord user ID for this event."""
        self.discord_user_id = discord_user_id
        return self

    def with_state_change(self, previous_state: str, new_state: str) -> "AuditEvent":
        """Set previous and new state for state transition events."""
        self.previous_state = previous_state
        self.new_state = new_state
        return self

    def with_roles(
        self,
        added: list[str] | None = None,
        removed: list[str] | None = None,
    ) -> "AuditEvent":
        """Set roles added and/or removed."""
        self.roles_added = added
        self.roles_removed = removed
        return self

    def with_stripe(
        self,
        subscription_id: str | None = None,
        event_id: str | None = None,
    ) -> "AuditEvent":
        """Set Stripe-related fields."""
        self.stripe_subscription_id = subscription_id
        self.stripe_event_id = event_id
        return self

    def with_reason(self, reason: str) -> "AuditEvent":
        """Set the reason field (truncated to 500 chars)."""
        self.reason = reason[:500]
        return self

    def with_error(self, error_message: str) -> "AuditEvent":
        """Set the error message field (truncated to 1000 chars)."""
        self.error_message = error_message[:1000]
        return self

    def to_dynamo_item(self, ulid_suffix: str) -> dict:
        """Serialize to a DynamoDB item dict.

        Args:
            ulid_suffix: The ULID suffix for the sort key to avoid collisions.

        Returns:
            A dict representing the DynamoDB item with low-level attribute types.
        """
        item: dict = {
            "PK": {"S": f"USER#{self.dsb_user_id}"},
            "SK": {"S": f"AUDIT#{self.timestamp}#{ulid_suffix}"},
            "event_type": {"S": self.event_type.value},
            "dsb_user_id": {"S": self.dsb_user_id},
            "actor": {"S": self.actor},
            "timestamp": {"S": self.timestamp},
        }

        # Conditional fields — only include if set (not None)
        if self.discord_user_id is not None:
            item["discord_user_id"] = {"S": self.discord_user_id}
        if self.previous_state is not None:
            item["previous_state"] = {"S": self.previous_state}
        if self.new_state is not None:
            item["new_state"] = {"S": self.new_state}
        if self.roles_added is not None and len(self.roles_added) > 0:
            item["roles_added"] = {"L": [{"S": role} for role in self.roles_added]}
        if self.roles_removed is not None and len(self.roles_removed) > 0:
            item["roles_removed"] = {"L": [{"S": role} for role in self.roles_removed]}
        if self.stripe_subscription_id is not None:
            item["stripe_subscription_id"] = {"S": self.stripe_subscription_id}
        if self.stripe_event_id is not None:
            item["stripe_event_id"] = {"S": self.stripe_event_id}
        if self.reason is not None:
            item["reason"] = {"S": self.reason}
        if self.error_message is not None:
            item["error_message"] = {"S": self.error_message}

        return item

    @classmethod
    def from_dynamo_item(cls, item: dict) -> "AuditEvent":
        """Deserialize from a DynamoDB item dict.

        Args:
            item: The raw DynamoDB item with low-level attribute types.

        Returns:
            An AuditEvent instance populated from the item.
        """
        # Parse roles_added list
        roles_added = None
        if "roles_added" in item and "L" in item["roles_added"]:
            roles_added = [r["S"] for r in item["roles_added"]["L"]]

        # Parse roles_removed list
        roles_removed = None
        if "roles_removed" in item and "L" in item["roles_removed"]:
            roles_removed = [r["S"] for r in item["roles_removed"]["L"]]

        return cls(
            event_type=AuditEventType(item["event_type"]["S"]),
            dsb_user_id=item["dsb_user_id"]["S"],
            actor=item["actor"]["S"],
            timestamp=item["timestamp"]["S"],
            discord_user_id=item.get("discord_user_id", {}).get("S"),
            previous_state=item.get("previous_state", {}).get("S"),
            new_state=item.get("new_state", {}).get("S"),
            roles_added=roles_added,
            roles_removed=roles_removed,
            stripe_subscription_id=item.get("stripe_subscription_id", {}).get("S"),
            stripe_event_id=item.get("stripe_event_id", {}).get("S"),
            reason=item.get("reason", {}).get("S"),
            error_message=item.get("error_message", {}).get("S"),
        )
