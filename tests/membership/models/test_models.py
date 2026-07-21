"""Unit tests for membership data models."""

import json
from datetime import datetime, timezone

from models.audit_event import AuditEvent, AuditEventType
from models.discord_identity import DiscordIdentityRecord
from models.membership import MembershipRecord
from models.sync_message import SyncMessage

# --- MembershipRecord tests ---


class TestMembershipRecord:
    def test_defaults(self):
        record = MembershipRecord(user_id="user1")
        assert record.membership_tier == "FREE"
        assert record.stripe_customer_id is None
        assert record.stripe_subscription_id is None
        assert record.subscription_status is None
        assert record.current_period_end is None
        assert record.updated_at is None

    def test_to_dynamo_item_minimal(self):
        record = MembershipRecord(user_id="user1")
        item = record.to_dynamo_item()
        assert item["PK"] == {"S": "USER#user1"}
        assert item["SK"] == {"S": "MEMBERSHIP"}
        assert item["user_id"] == {"S": "user1"}
        assert item["membership_tier"] == {"S": "FREE"}
        # Optional fields should not be present
        assert "stripe_customer_id" not in item
        assert "stripe_subscription_id" not in item

    def test_to_dynamo_item_full(self):
        record = MembershipRecord(
            user_id="user1",
            membership_tier="BUILDER",
            stripe_customer_id="cus_abc",
            stripe_subscription_id="sub_xyz",
            subscription_status="active",
            current_period_end="2024-12-31T23:59:59Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        item = record.to_dynamo_item()
        assert item["stripe_customer_id"] == {"S": "cus_abc"}
        assert item["stripe_subscription_id"] == {"S": "sub_xyz"}
        assert item["subscription_status"] == {"S": "active"}
        assert item["current_period_end"] == {"S": "2024-12-31T23:59:59Z"}
        assert item["updated_at"] == {"S": "2024-01-01T00:00:00Z"}

    def test_roundtrip(self):
        original = MembershipRecord(
            user_id="user42",
            membership_tier="EXPLORER",
            stripe_customer_id="cus_123",
            subscription_status="past_due",
        )
        item = original.to_dynamo_item()
        restored = MembershipRecord.from_dynamo_item(item)
        assert restored.user_id == original.user_id
        assert restored.membership_tier == original.membership_tier
        assert restored.stripe_customer_id == original.stripe_customer_id
        assert restored.subscription_status == original.subscription_status
        assert restored.stripe_subscription_id is None

    def test_from_dynamo_item_missing_optional_fields(self):
        item = {
            "PK": {"S": "USER#user1"},
            "SK": {"S": "MEMBERSHIP"},
            "user_id": {"S": "user1"},
        }
        record = MembershipRecord.from_dynamo_item(item)
        assert record.user_id == "user1"
        assert record.membership_tier == "FREE"
        assert record.stripe_customer_id is None


# --- DiscordIdentityRecord tests ---


class TestDiscordIdentityRecord:
    def test_defaults(self):
        record = DiscordIdentityRecord(
            user_id="user1",
            discord_user_id="123456789012345678",
            username="testuser",
        )
        assert record.active is False
        assert record.platform_state == "Discord_Connected"
        assert record.display_name is None
        assert record.last_sync_status is None

    def test_to_dynamo_item_minimal(self):
        record = DiscordIdentityRecord(
            user_id="user1",
            discord_user_id="123456789012345678",
            username="testuser",
        )
        item = record.to_dynamo_item()
        assert item["PK"] == {"S": "USER#user1"}
        assert item["SK"] == {"S": "DISCORD#123456789012345678"}
        assert item["username"] == {"S": "testuser"}
        assert item["active"] == {"BOOL": False}
        assert "display_name" not in item

    def test_to_dynamo_item_full(self):
        record = DiscordIdentityRecord(
            user_id="user1",
            discord_user_id="123456789012345678",
            username="testuser",
            display_name="Test User",
            avatar_url="https://cdn.discordapp.com/avatars/123/abc.png",
            connected_at="2024-01-01T00:00:00Z",
            verified_at="2024-01-01T00:01:00Z",
            active=True,
            platform_state="Roles_Synced",
            last_synced_at="2024-01-02T00:00:00Z",
            last_sync_status="SUCCESS",
        )
        item = record.to_dynamo_item()
        assert item["display_name"] == {"S": "Test User"}
        assert item["avatar_url"] == {
            "S": "https://cdn.discordapp.com/avatars/123/abc.png"
        }
        assert item["active"] == {"BOOL": True}
        assert item["platform_state"] == {"S": "Roles_Synced"}
        assert item["last_sync_status"] == {"S": "SUCCESS"}

    def test_roundtrip(self):
        original = DiscordIdentityRecord(
            user_id="user1",
            discord_user_id="123456789012345678",
            username="someone",
            display_name="Someone Cool",
            active=True,
            platform_state="Server_Joined",
            last_sync_status="FAILED",
        )
        item = original.to_dynamo_item()
        restored = DiscordIdentityRecord.from_dynamo_item(item)
        assert restored.user_id == original.user_id
        assert restored.discord_user_id == original.discord_user_id
        assert restored.username == original.username
        assert restored.display_name == original.display_name
        assert restored.active is True
        assert restored.platform_state == "Server_Joined"
        assert restored.last_sync_status == "FAILED"

    def test_disconnect_fields_roundtrip(self):
        record = DiscordIdentityRecord(
            user_id="user1",
            discord_user_id="123456789012345678",
            username="testuser",
            disconnected_at="2024-06-01T12:00:00Z",
            disconnect_reason="User requested",
            active=False,
        )
        item = record.to_dynamo_item()
        restored = DiscordIdentityRecord.from_dynamo_item(item)
        assert restored.disconnected_at == "2024-06-01T12:00:00Z"
        assert restored.disconnect_reason == "User requested"
        assert restored.active is False


# --- AuditEvent tests ---


class TestAuditEvent:
    def test_build_with_auto_timestamp(self):
        event = AuditEvent.build(
            AuditEventType.CONNECTED,
            dsb_user_id="user1",
            actor="user:user1",
        )
        assert event.event_type == AuditEventType.CONNECTED
        assert event.dsb_user_id == "user1"
        assert event.actor == "user:user1"
        # Timestamp should be set and in ISO format with Z suffix
        assert event.timestamp.endswith("Z")
        assert "T" in event.timestamp

    def test_build_with_explicit_timestamp(self):
        ts = "2024-01-15T10:30:00.123Z"
        event = AuditEvent.build(
            AuditEventType.SYNC_SUCCESSFUL,
            dsb_user_id="user1",
            actor="system",
            timestamp=ts,
        )
        assert event.timestamp == ts

    def test_builder_chaining(self):
        event = (
            AuditEvent.build(AuditEventType.ROLES_ADDED, "user1", "system")
            .with_discord("123456789012345678")
            .with_state_change("Server_Joined", "Roles_Synced")
            .with_roles(added=["role1", "role2"])
            .with_stripe(subscription_id="sub_abc")
            .with_reason("Tier upgraded to BUILDER")
        )
        assert event.discord_user_id == "123456789012345678"
        assert event.previous_state == "Server_Joined"
        assert event.new_state == "Roles_Synced"
        assert event.roles_added == ["role1", "role2"]
        assert event.roles_removed is None
        assert event.stripe_subscription_id == "sub_abc"
        assert event.reason == "Tier upgraded to BUILDER"

    def test_reason_truncation(self):
        long_reason = "x" * 600
        event = AuditEvent.build(AuditEventType.ADMIN_OVERRIDE, "user1", "admin:admin1")
        event.with_reason(long_reason)
        assert len(event.reason) == 500

    def test_error_message_truncation(self):
        long_error = "e" * 1200
        event = AuditEvent.build(AuditEventType.SYNC_FAILED, "user1", "system")
        event.with_error(long_error)
        assert len(event.error_message) == 1000

    def test_to_dynamo_item(self):
        event = (
            AuditEvent.build(
                AuditEventType.DISCONNECTED,
                "user1",
                "user:user1",
                timestamp="2024-01-15T10:30:00.123Z",
            )
            .with_discord("123456789012345678")
            .with_reason("User choice")
        )
        item = event.to_dynamo_item("01HXYZ123ABC")
        assert item["PK"] == {"S": "USER#user1"}
        assert item["SK"] == {"S": "AUDIT#2024-01-15T10:30:00.123Z#01HXYZ123ABC"}
        assert item["event_type"] == {"S": "Disconnected"}
        assert item["discord_user_id"] == {"S": "123456789012345678"}
        assert item["reason"] == {"S": "User choice"}
        # Optional fields not set should be absent
        assert "roles_added" not in item
        assert "error_message" not in item

    def test_roundtrip(self):
        original = (
            AuditEvent.build(
                AuditEventType.ROLES_REMOVED,
                "user1",
                "system",
                timestamp="2024-03-01T08:00:00.000Z",
            )
            .with_roles(removed=["role_old"])
            .with_error("Discord API returned 429")
        )
        item = original.to_dynamo_item("ULID001")
        restored = AuditEvent.from_dynamo_item(item)
        assert restored.event_type == AuditEventType.ROLES_REMOVED
        assert restored.dsb_user_id == "user1"
        assert restored.roles_removed == ["role_old"]
        assert restored.roles_added is None
        assert restored.error_message == "Discord API returned 429"

    def test_all_event_types_are_strings(self):
        for event_type in AuditEventType:
            assert isinstance(event_type.value, str)


# --- SyncMessage tests ---


class TestSyncMessage:
    def test_to_json_full(self):
        msg = SyncMessage(
            user_id="user1",
            event_type="tier_change",
            timestamp="2024-01-01T00:00:00Z",
            new_membership_tier="BUILDER",
        )
        data = json.loads(msg.to_json())
        assert data["user_id"] == "user1"
        assert data["event_type"] == "tier_change"
        assert data["timestamp"] == "2024-01-01T00:00:00Z"
        assert data["new_membership_tier"] == "BUILDER"

    def test_to_json_without_tier(self):
        msg = SyncMessage(
            user_id="user1",
            event_type="discord_connected",
            timestamp="2024-01-01T00:00:00Z",
        )
        data = json.loads(msg.to_json())
        assert "new_membership_tier" not in data

    def test_from_json_string(self):
        json_str = json.dumps(
            {
                "user_id": "user1",
                "event_type": "admin_sync",
                "timestamp": "2024-06-01T12:00:00Z",
                "new_membership_tier": "EXPLORER",
            }
        )
        msg = SyncMessage.from_json(json_str)
        assert msg.user_id == "user1"
        assert msg.event_type == "admin_sync"
        assert msg.new_membership_tier == "EXPLORER"

    def test_from_json_dict(self):
        data = {
            "user_id": "user2",
            "event_type": "tier_change",
            "timestamp": "2024-01-01T00:00:00Z",
        }
        msg = SyncMessage.from_json(data)
        assert msg.user_id == "user2"
        assert msg.new_membership_tier is None

    def test_roundtrip(self):
        original = SyncMessage(
            user_id="user99",
            event_type="tier_change",
            timestamp="2024-12-25T00:00:00Z",
            new_membership_tier="BUILDER_ACADEMY",
        )
        restored = SyncMessage.from_json(original.to_json())
        assert restored.user_id == original.user_id
        assert restored.event_type == original.event_type
        assert restored.timestamp == original.timestamp
        assert restored.new_membership_tier == original.new_membership_tier
