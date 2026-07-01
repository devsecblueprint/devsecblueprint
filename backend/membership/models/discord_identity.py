"""Discord identity record data model for DynamoDB serialization."""

from dataclasses import dataclass, field


@dataclass
class DiscordIdentityRecord:
    """Represents a user's Discord identity connection in the dsb_membership table.

    Stored at PK=USER#{user_id} SK=DISCORD#{discord_user_id}.
    """

    user_id: str
    discord_user_id: str
    username: str
    display_name: str | None = None
    avatar_url: str | None = None
    connected_at: str | None = None  # ISO 8601
    verified_at: str | None = None  # ISO 8601
    disconnected_at: str | None = None  # ISO 8601
    disconnect_reason: str | None = None
    active: bool = False
    platform_state: str = (
        "Discord_Connected"  # Discord_Connected, Discord_Verified, Not_in_Server, Server_Joined, Roles_Synced
    )
    last_synced_at: str | None = None  # ISO 8601
    last_sync_status: str | None = None  # SUCCESS, FAILED, SKIPPED

    def to_dynamo_item(self) -> dict:
        """Serialize to a DynamoDB item dict."""
        item: dict = {
            "PK": {"S": f"USER#{self.user_id}"},
            "SK": {"S": f"DISCORD#{self.discord_user_id}"},
            "user_id": {"S": self.user_id},
            "discord_user_id": {"S": self.discord_user_id},
            "username": {"S": self.username},
            "active": {"BOOL": self.active},
            "platform_state": {"S": self.platform_state},
        }
        if self.display_name is not None:
            item["display_name"] = {"S": self.display_name}
        if self.avatar_url is not None:
            item["avatar_url"] = {"S": self.avatar_url}
        if self.connected_at is not None:
            item["connected_at"] = {"S": self.connected_at}
        if self.verified_at is not None:
            item["verified_at"] = {"S": self.verified_at}
        if self.disconnected_at is not None:
            item["disconnected_at"] = {"S": self.disconnected_at}
        if self.disconnect_reason is not None:
            item["disconnect_reason"] = {"S": self.disconnect_reason}
        if self.last_synced_at is not None:
            item["last_synced_at"] = {"S": self.last_synced_at}
        if self.last_sync_status is not None:
            item["last_sync_status"] = {"S": self.last_sync_status}
        return item

    @classmethod
    def from_dynamo_item(cls, item: dict) -> "DiscordIdentityRecord":
        """Deserialize from a DynamoDB item dict."""
        return cls(
            user_id=item["user_id"]["S"],
            discord_user_id=item["discord_user_id"]["S"],
            username=item["username"]["S"],
            display_name=item.get("display_name", {}).get("S"),
            avatar_url=item.get("avatar_url", {}).get("S"),
            connected_at=item.get("connected_at", {}).get("S"),
            verified_at=item.get("verified_at", {}).get("S"),
            disconnected_at=item.get("disconnected_at", {}).get("S"),
            disconnect_reason=item.get("disconnect_reason", {}).get("S"),
            active=item.get("active", {}).get("BOOL", False),
            platform_state=item.get("platform_state", {}).get("S", "Discord_Connected"),
            last_synced_at=item.get("last_synced_at", {}).get("S"),
            last_sync_status=item.get("last_sync_status", {}).get("S"),
        )
