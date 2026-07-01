"""SQS sync message data model for the dsb-discord-sync.fifo queue."""

import json
from dataclasses import dataclass


@dataclass
class SyncMessage:
    """Represents an SQS FIFO message for triggering Discord role sync.

    Published when a tier change occurs (Stripe webhook) or a Discord
    connection is confirmed. The sync consumer reads the latest state
    from DynamoDB, so this message primarily signals *which* user to sync.
    """

    user_id: str
    event_type: str  # e.g., "tier_change", "discord_connected", "admin_sync"
    timestamp: str  # ISO 8601
    new_membership_tier: str | None = None

    def to_json(self) -> str:
        """Serialize to a JSON string for SQS message body."""
        payload: dict = {
            "user_id": self.user_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
        }
        if self.new_membership_tier is not None:
            payload["new_membership_tier"] = self.new_membership_tier
        return json.dumps(payload)

    @classmethod
    def from_json(cls, data: str | dict) -> "SyncMessage":
        """Deserialize from a JSON string or already-parsed dict."""
        if isinstance(data, str):
            data = json.loads(data)
        return cls(
            user_id=data["user_id"],
            event_type=data["event_type"],
            timestamp=data["timestamp"],
            new_membership_tier=data.get("new_membership_tier"),
        )
