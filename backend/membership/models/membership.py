"""Membership record data model for DynamoDB serialization."""

from dataclasses import dataclass, field


@dataclass
class MembershipRecord:
    """Represents a user's membership/subscription state in the dsb_membership table.

    Stored at PK=USER#{user_id} SK=MEMBERSHIP.
    """

    user_id: str
    membership_tier: str = "FREE"  # FREE, EXPLORER, BUILDER, BUILDER_ACADEMY
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    subscription_status: str | None = None  # active, past_due, canceled, incomplete
    current_period_end: str | None = None  # ISO 8601
    updated_at: str | None = None  # ISO 8601

    def to_dynamo_item(self) -> dict:
        """Serialize to a DynamoDB item dict."""
        item: dict = {
            "PK": {"S": f"USER#{self.user_id}"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": self.user_id},
            "membership_tier": {"S": self.membership_tier},
        }
        if self.stripe_customer_id is not None:
            item["stripe_customer_id"] = {"S": self.stripe_customer_id}
        if self.stripe_subscription_id is not None:
            item["stripe_subscription_id"] = {"S": self.stripe_subscription_id}
        if self.subscription_status is not None:
            item["subscription_status"] = {"S": self.subscription_status}
        if self.current_period_end is not None:
            item["current_period_end"] = {"S": self.current_period_end}
        if self.updated_at is not None:
            item["updated_at"] = {"S": self.updated_at}
        return item

    @classmethod
    def from_dynamo_item(cls, item: dict) -> "MembershipRecord":
        """Deserialize from a DynamoDB item dict."""
        return cls(
            user_id=item["user_id"]["S"],
            membership_tier=item.get("membership_tier", {}).get("S", "FREE"),
            stripe_customer_id=item.get("stripe_customer_id", {}).get("S"),
            stripe_subscription_id=item.get("stripe_subscription_id", {}).get("S"),
            subscription_status=item.get("subscription_status", {}).get("S"),
            current_period_end=item.get("current_period_end", {}).get("S"),
            updated_at=item.get("updated_at", {}).get("S"),
        )
