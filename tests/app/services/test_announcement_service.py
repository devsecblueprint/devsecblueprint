"""Tests for app.services.announcement_service.

The ledger is exercised against moto's DynamoDB so conditional writes, GSI
queries and update expressions behave like the real service. Broadcast
creation, email delivery, the registry, and the videos table are mocked.
"""

import itertools
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import boto3
import pytest
from hypothesis import HealthCheck, given, settings as hyp_settings, strategies as st
from moto import mock_aws

from app.services import announcement_service as mod
from app.services.announcement_service import (
    AUTO_ANNOUNCE_USER,
    AnnouncementConflict,
    AnnouncementNotFound,
    AnnouncementService,
    build_video_message,
    build_walkthrough_message,
    video_item_to_fields,
)

_table_counter = itertools.count()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_settings(table: str, **overrides) -> SimpleNamespace:
    values = dict(
        announcements_table=table,
        announcements_enabled=True,
        announcement_settle_minutes=15,
        announcement_max_attempts=3,
        announcement_stale_claim_minutes=30,
        frontend_origin="https://dsb.example",
        content_registry_bucket="registry-bucket",
        broadcasts_table="test-broadcasts",
        videos_table="test-videos",
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def create_table(name: str) -> None:
    client = boto3.client("dynamodb", region_name="us-east-2")
    client.create_table(
        TableName=name,
        BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
            {"AttributeName": "GSI1PK", "AttributeType": "S"},
            {"AttributeName": "GSI1SK", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "GSI1",
                "KeySchema": [
                    {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    )


@contextmanager
def ledger(**overrides):
    """Yield (service, mocks) backed by a fresh moto table."""
    import os

    env = {
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_DEFAULT_REGION": "us-east-2",
    }
    with patch.dict(os.environ, env):
        with mock_aws():
            table = f"announcements-{next(_table_counter)}"
            create_table(table)
            settings = make_settings(table, **overrides)

            broadcast_svc = MagicMock()
            broadcast_svc.create_broadcast.side_effect = lambda **kw: {
                "broadcast_id": f"b-{next(_table_counter)}",
                **kw,
            }
            emails = MagicMock(return_value={"sent": 5, "failed": 0, "total": 5})
            with (
                patch.object(mod, "BroadcastService", return_value=broadcast_svc),
                patch.object(mod, "send_broadcast_emails", emails),
            ):
                service = AnnouncementService(settings)
                yield service, SimpleNamespace(
                    broadcasts=broadcast_svc, emails=emails, settings=settings
                )


def video(**overrides) -> dict:
    data = {
        "id": "vid-1",
        "title": "Intro to DevSecOps",
        "slug": "intro-to-devsecops",
        "description": "A great talk about shifting left.",
        "instructor": "Jane Doe",
        "duration_seconds": 3000,
        "tags": ["security", "instructor:Jane Doe", "devops"],
        "access_tier": "BUILDER",
        "status": "PUBLISHED",
    }
    data.update(overrides)
    return data


def wt(wid: str, **overrides) -> dict:
    data = {
        "id": wid,
        "content_type": "walkthrough",
        "title": f"Walkthrough {wid}",
        "description": "Build a pipeline.",
        "difficulty": "Beginner",
        "topics": ["ci", "security"],
        "estimated_time": 90,
    }
    data.update(overrides)
    return data


def patch_registry(entries):
    """Patch the registry to return the given walkthrough entries."""
    registry = MagicMock()
    if isinstance(entries, Exception):
        registry.get_all_walkthrough_entries.side_effect = entries
    else:
        registry.get_all_walkthrough_entries.return_value = entries
    return patch.object(mod, "get_registry_service", return_value=registry), registry


def record(service, key):
    return service._get(key)


def age(service, key, **delta):
    """Move first_seen_at / claimed_at into the past for time-based tests."""
    past = (datetime.now(timezone.utc) - timedelta(**delta)).isoformat()
    service._client.update_item(
        TableName=service._table,
        Key=service._key(key),
        UpdateExpression="SET first_seen_at = :t, GSI1SK = :t, claimed_at = :t",
        ExpressionAttributeValues={":t": {"S": past}},
    )


# ---------------------------------------------------------------------------
# Message builders
# ---------------------------------------------------------------------------


class TestBuildVideoMessage:
    def test_basic_fields(self):
        title, message, link = build_video_message(video(), "https://dsb.example")
        assert title == "New video: Intro to DevSecOps"
        assert "A great talk about shifting left." in message
        assert "**Instructor:** Jane Doe" in message
        assert "**Length:** 50 min" in message
        assert "**Topics:** security, devops" in message
        assert link == "https://dsb.example/videos/preview/intro-to-devsecops"

    def test_instructor_tags_are_not_listed_as_topics(self):
        _, message, _ = build_video_message(video(tags=["instructor:Bob", "aws"]))
        assert "instructor:" not in message.lower().replace("**instructor:**", "")
        assert "**Topics:** aws" in message

    def test_builder_tier_wording(self):
        _, message, _ = build_video_message(video(access_tier="BUILDER"))
        assert "Available to Builder members." in message

    def test_free_tier_wording(self):
        _, message, _ = build_video_message(video(access_tier="FREE"))
        assert "Free for all members." in message
        assert "Builder" not in message

    def test_long_title_is_not_truncated(self):
        long_title = (
            "From Authentik to Okta: Enterprise SSO with AWS IAM Identity "
            "Center (Paid \u2014 Builder Session)"
        )
        assert len(f"New video: {long_title}") > 100
        title, _, _ = build_video_message(video(title=long_title))
        assert title == f"New video: {long_title}"

    def test_full_description_is_copied_without_a_cap(self):
        description = "\n\n".join(f"Paragraph {i} " + "word " * 80 for i in range(30))
        assert len(description) > 5000
        _, message, _ = build_video_message(video(description=description))
        assert description.strip() in message
        assert "\u2026" not in message  # no ellipsis from truncation
        assert "Available to Builder members." in message

    def test_follows_the_announcement_template_in_order(self):
        _, message, _ = build_video_message(video())
        positions = [
            message.index(text)
            for text in (
                "**A new session is here.**",
                "**Intro to DevSecOps**",
                "A great talk about shifting left.",
                "**Instructor:** Jane Doe",
                "Available to Builder members.",
                "Ready to watch?",
            )
        ]
        assert positions == sorted(positions)
        assert message.endswith("Ready to watch?")

    def test_detail_lines_use_hard_breaks_so_they_stay_on_separate_lines(self):
        _, message, _ = build_video_message(video())
        assert (
            "**Instructor:** Jane Doe  \n**Length:** 50 min  \n**Topics:** security, devops"
            in message
        )

    def test_missing_description_skips_that_block_without_blank_gaps(self):
        _, message, _ = build_video_message(video(description=""))
        assert "\n\n\n" not in message
        assert message.startswith(
            "**A new session is here.**\n\n**Intro to DevSecOps**\n\n**Instructor:**"
        )

    def test_title_formatting_characters_are_escaped(self):
        _, message, _ = build_video_message(video(title="Terraform_Cloud *and* [more]"))
        assert "**Terraform\\_Cloud \\*and\\* \\[more\\]**" in message

    def test_html_in_description_is_neutralized(self):
        _, message, _ = build_video_message(
            video(description="<script>alert(1)</script> hello")
        )
        assert "<script>" not in message
        assert "&lt;script&gt;" in message

    def test_short_video_rounds_up_to_one_minute(self):
        _, message, _ = build_video_message(video(duration_seconds=20))
        assert "**Length:** 1 min" in message

    def test_zero_duration_omits_length(self):
        _, message, _ = build_video_message(video(duration_seconds=0))
        assert "**Length:**" not in message

    def test_relative_link_without_base_url(self):
        _, _, link = build_video_message(video())
        assert link == "/videos/preview/intro-to-devsecops"

    def test_unknown_tier_fails_closed_to_builder(self):
        _, message, _ = build_video_message(video(access_tier="WHATEVER"))
        assert "Builder members" in message


class TestBuildWalkthroughMessage:
    def test_basic_fields(self):
        title, message, link = build_walkthrough_message(
            wt("k8s"), "https://dsb.example"
        )
        assert title == "New walkthrough: Walkthrough k8s"
        assert "**Your next hands-on walkthrough is here.**" in message
        assert "**Walkthrough k8s**" in message
        assert "Build a pipeline." in message
        assert "**Level:** Beginner  \n**Estimated time:** 1 hr 30 min" in message
        assert message.endswith("Ready to put it into practice?")
        assert link == "https://dsb.example/walkthroughs/preview/k8s"

    def test_follows_the_announcement_template_in_order(self):
        _, message, _ = build_walkthrough_message(wt("k8s"))
        positions = [
            message.index(text)
            for text in (
                "**Your next hands-on walkthrough is here.**",
                "**Walkthrough k8s**",
                "Build a pipeline.",
                "**Level:** Beginner",
                "**Estimated time:**",
                "Ready to put it into practice?",
            )
        ]
        assert positions == sorted(positions)

    @pytest.mark.parametrize(
        "minutes,expected",
        [(45, "45 min"), (60, "1 hr"), (125, "2 hr 5 min")],
    )
    def test_time_formats(self, minutes, expected):
        _, message, _ = build_walkthrough_message(wt("a", estimated_time=minutes))
        assert f"**Estimated time:** {expected}" in message

    def test_extra_registry_fields_do_not_change_the_message(self):
        base = build_walkthrough_message(wt("a"))
        with_extra = build_walkthrough_message(
            wt("a", outcomes=["x"], prerequisites=["y"])
        )
        assert base == with_extra

    def test_topics_are_not_part_of_the_template(self):
        _, message, _ = build_walkthrough_message(wt("a", topics=["ci", "security"]))
        assert "Topics" not in message

    def test_missing_optional_fields_still_make_a_valid_message(self):
        _, message, _ = build_walkthrough_message(
            {"id": "x", "title": "T", "description": ""}
        )
        assert message == (
            "**Your next hands-on walkthrough is here.**\n\n"
            "**T**\n\n"
            "Ready to put it into practice?"
        )

    def test_only_level_or_only_time(self):
        _, message, _ = build_walkthrough_message(
            {"id": "x", "title": "T", "difficulty": "Advanced"}
        )
        assert "**Level:** Advanced" in message
        assert "Estimated time" not in message
        _, message, _ = build_walkthrough_message(
            {"id": "x", "title": "T", "estimated_time": 30}
        )
        assert "**Estimated time:** 30 min" in message
        assert "Level" not in message

    def test_title_and_description_are_not_truncated(self):
        description = "Intro paragraph. " * 400
        title, message, _ = build_walkthrough_message(
            wt("a", title="t" * 300, description=description)
        )
        assert title == "New walkthrough: " + "t" * 300
        assert description.strip() in message
        assert "\u2026" not in message

    def test_no_blank_gaps_when_blocks_are_missing(self):
        _, message, _ = build_walkthrough_message(wt("a", description=""))
        assert "\n\n\n" not in message


class TestEmailRendering:
    """The message, markdown renderer and real email template together."""

    def render(
        self, content_type, message, link="https://dsb.example/x", name="Damien Burks"
    ):
        from app.services import broadcast_email as be

        extras = AnnouncementService._email_extras(content_type)
        html = be._jinja_env.get_template("broadcast_notification.html").render(
            title="T",
            message_html=be._render_markdown_to_html(message),
            link=link,
            username=be._first_name(name),
            cta_label=extras.get("cta_label", ""),
            signoff_lines=extras.get("signoff_lines", []),
        )
        return html

    def test_walkthrough_email_matches_the_template(self):
        _, message, link = build_walkthrough_message(
            wt("k8s", title="Connect Authentik to Google Cloud"),
            "https://dsb.example",
        )
        html = self.render("WALKTHROUGH#k8s", message, link)

        # greeting uses the first name
        assert "Hi <strong>Damien</strong>," in html
        assert "Damien Burks" not in html
        # structure, in order
        order = [
            "Hi <strong>Damien</strong>,",
            "<strong>Your next hands-on walkthrough is here.</strong>",
            "<strong>Connect Authentik to Google Cloud</strong>",
            "Build a pipeline.",
            "<strong>Level:</strong> Beginner<br />",
            "<strong>Estimated time:</strong> 1 hr 30 min",
            "Ready to put it into practice?",
            "Start the walkthrough",
            "Happy building,<br>The DevSec Blueprint",
        ]
        positions = [html.index(text) for text in order]
        assert positions == sorted(positions)
        assert 'href="https://dsb.example/walkthroughs/preview/k8s"' in html
        assert "View on Platform" not in html
        assert "**" not in html  # no raw markdown leaks into the email

    def test_video_email_uses_video_wording(self):
        _, message, link = build_video_message(video(), "https://dsb.example")
        html = self.render("VIDEO#vid-1", message, link)
        assert "<strong>A new session is here.</strong>" in html
        assert "Ready to watch?" in html
        assert "Watch the session" in html
        assert "Happy building,<br>The DevSec Blueprint" in html
        assert "Start the walkthrough" not in html

    def test_sign_off_comes_after_the_button(self):
        _, message, link = build_video_message(video(), "https://dsb.example")
        html = self.render("VIDEO#vid-1", message, link)
        assert html.index("Watch the session") < html.index("Happy building,")

    def test_unknown_content_keeps_the_default_button_and_no_sign_off(self):
        html = self.render("OTHER#1", "Hello", "https://dsb.example/x")
        assert "View on Platform" in html
        assert "Happy building" not in html

    def test_titles_with_markdown_characters_render_literally(self):
        _, message, _ = build_walkthrough_message(
            wt("a", title="Terraform_Cloud *Guide*")
        )
        html = self.render("WALKTHROUGH#a", message)
        assert "<strong>Terraform_Cloud *Guide*</strong>" in html

    def test_html_in_description_does_not_reach_the_email(self):
        _, message, _ = build_walkthrough_message(
            wt("a", description="<img src=x onerror=alert(1)> hello")
        )
        html = self.render("WALKTHROUGH#a", message)
        assert "onerror" not in html.replace("&lt;img src=x onerror=alert(1)&gt;", "")
        assert "<img src=x" not in html


class TestEmailExtras:
    def test_extras_per_content_type(self):
        walk = AnnouncementService._email_extras("WALKTHROUGH#abc")
        vid = AnnouncementService._email_extras("VIDEO#abc")
        assert walk["cta_label"] == "Start the walkthrough"
        assert vid["cta_label"] == "Watch the session"
        assert (
            walk["signoff_lines"]
            == vid["signoff_lines"]
            == [
                "Happy building,",
                "The DevSec Blueprint",
            ]
        )
        assert AnnouncementService._email_extras("NOPE#1") == {}

    def test_extras_are_copies_so_callers_cannot_change_the_defaults(self):
        extras = AnnouncementService._email_extras("VIDEO#abc")
        extras["cta_label"] = "changed"
        assert (
            AnnouncementService._email_extras("VIDEO#abc")["cta_label"]
            == "Watch the session"
        )

    def test_deliver_sends_extras_to_the_email_only(self):
        with ledger() as (svc, m):
            svc.announce_video(video())
            stored = m.broadcasts.create_broadcast.call_args.kwargs
            assert "cta_label" not in stored and "signoff_lines" not in stored

            sent = m.emails.call_args.args[0]
            assert sent["cta_label"] == "Watch the session"
            assert sent["signoff_lines"] == ["Happy building,", "The DevSec Blueprint"]
            assert sent["title"] == "New video: Intro to DevSecOps"

    def test_walkthrough_delivery_uses_the_walkthrough_button(self):
        with ledger(announcement_settle_minutes=0) as (svc, m):
            with patch_registry([wt("base")])[0]:
                svc.scan_walkthroughs()
            with patch_registry([wt("base"), wt("fresh")])[0]:
                svc.scan_walkthroughs()
            sent = m.emails.call_args.args[0]
            assert sent["cta_label"] == "Start the walkthrough"
            kwargs = m.broadcasts.create_broadcast.call_args.kwargs
            assert kwargs["message"].startswith(
                "**Your next hands-on walkthrough is here.**"
            )


def test_video_item_to_fields_converts_dynamodb_item():
    item = {
        "id": {"S": "v1"},
        "title": {"S": "T"},
        "slug": {"S": "t"},
        "description": {"S": "D"},
        "instructor": {"S": "I"},
        "durationSeconds": {"N": "120"},
        "tags": {"L": [{"S": "a"}, {"S": "b"}]},
        "accessTier": {"S": "FREE"},
        "status": {"S": "PUBLISHED"},
    }
    fields = video_item_to_fields(item)
    assert fields["duration_seconds"] == 120
    assert fields["tags"] == ["a", "b"]
    assert fields["access_tier"] == "FREE"
    assert fields["status"] == "PUBLISHED"


# ---------------------------------------------------------------------------
# Ledger primitives
# ---------------------------------------------------------------------------


class TestLedger:
    def test_record_new_is_idempotent(self):
        with ledger() as (svc, _):
            assert svc._record_new("VIDEO#1", "video", "1", "T", "SENDING") is True
            assert svc._record_new("VIDEO#1", "video", "1", "T", "SENDING") is False

    def test_second_claim_fails(self):
        with ledger() as (svc, _):
            svc._record_new("WALKTHROUGH#a", "walkthrough", "a", "T", "PENDING")
            assert svc._claim("WALKTHROUGH#a", ("PENDING",)) is True
            assert svc._claim("WALKTHROUGH#a", ("PENDING",)) is False
            assert record(svc, "WALKTHROUGH#a")["status"] == "SENDING"
            assert record(svc, "WALKTHROUGH#a")["attempts"] == 1

    @pytest.mark.parametrize("status", ["SENDING", "SENT", "BASELINED"])
    def test_cannot_claim_already_processed(self, status):
        with ledger() as (svc, _):
            svc._record_new("VIDEO#1", "video", "1", "T", status)
            assert svc._claim("VIDEO#1", ("PENDING", "FAILED")) is False

    def test_failed_can_be_claimed_and_attempts_increment(self):
        with ledger() as (svc, _):
            svc._record_new("VIDEO#1", "video", "1", "T", "SENDING")
            svc._mark_failed("VIDEO#1", "boom")
            assert svc._claim("VIDEO#1", ("FAILED",)) is True
            rec = record(svc, "VIDEO#1")
            assert rec["status"] == "SENDING"
            assert rec["attempts"] == 2
            assert rec["last_error"] is None  # cleared on re-claim

    def test_status_gsi_stays_in_sync(self):
        with ledger() as (svc, _):
            svc._record_new("VIDEO#1", "video", "1", "T", "SENDING")
            assert [r["content_key"] for r in svc._query_status("SENDING")] == [
                "VIDEO#1"
            ]
            svc._mark_sent("VIDEO#1", "b1")
            assert svc._query_status("SENDING") == []
            sent = svc._query_status("SENT")
            assert sent[0]["broadcast_id"] == "b1"
            assert sent[0]["sent_at"]

    def test_list_filter_and_failed_count(self):
        with ledger() as (svc, _):
            svc._record_new("VIDEO#1", "video", "1", "One", "SENDING")
            svc._mark_failed("VIDEO#1", "x")
            svc._record_new("VIDEO#2", "video", "2", "Two", "SENDING")
            svc._mark_sent("VIDEO#2", "b")
            assert svc.failed_count() == 1
            assert len(svc.list_announcements()) == 2
            assert [r["content_key"] for r in svc.list_announcements("FAILED")] == [
                "VIDEO#1"
            ]

    def test_list_is_newest_first(self):
        with ledger() as (svc, _):
            svc._record_new("VIDEO#old", "video", "old", "Old", "SENT")
            age(svc, "VIDEO#old", days=2)
            svc._record_new("VIDEO#new", "video", "new", "New", "SENT")
            keys = [r["content_key"] for r in svc.list_announcements()]
            assert keys == ["VIDEO#new", "VIDEO#old"]


# ---------------------------------------------------------------------------
# Video announcements
# ---------------------------------------------------------------------------


class TestAnnounceVideo:
    def test_disabled_flag_does_nothing(self):
        with ledger(announcements_enabled=False) as (svc, m):
            svc.announce_video(video())
            assert svc.list_announcements() == []
            m.broadcasts.create_broadcast.assert_not_called()
            m.emails.assert_not_called()

    def test_missing_table_does_nothing(self):
        with ledger(announcements_table="") as (svc, m):
            svc.announce_video(video())
            m.broadcasts.create_broadcast.assert_not_called()

    def test_sends_broadcast_and_marks_sent(self):
        with ledger() as (svc, m):
            svc.announce_video(video())
            m.broadcasts.create_broadcast.assert_called_once()
            kwargs = m.broadcasts.create_broadcast.call_args.kwargs
            assert kwargs["created_by"] == AUTO_ANNOUNCE_USER
            assert kwargs["title"] == "New video: Intro to DevSecOps"
            assert (
                kwargs["link"]
                == "https://dsb.example/videos/preview/intro-to-devsecops"
            )
            m.emails.assert_called_once()

            rec = record(svc, "VIDEO#vid-1")
            assert rec["status"] == "SENT"
            assert rec["broadcast_id"]
            assert rec["sent_at"]
            assert rec["attempts"] == 1
            assert rec["content_type"] == "video"

    def test_repeat_announce_is_a_no_op(self):
        with ledger() as (svc, m):
            for _ in range(3):
                svc.announce_video(video())
            assert m.broadcasts.create_broadcast.call_count == 1
            assert m.emails.call_count == 1

    def test_different_videos_each_announced(self):
        with ledger() as (svc, m):
            svc.announce_video(video(id="a", slug="a"))
            svc.announce_video(video(id="b", slug="b"))
            assert m.emails.call_count == 2

    def test_broadcast_creation_failure_marks_failed_without_emailing(self):
        with ledger() as (svc, m):
            m.broadcasts.create_broadcast.side_effect = RuntimeError("ddb down")
            svc.announce_video(video())
            rec = record(svc, "VIDEO#vid-1")
            assert rec["status"] == "FAILED"
            assert "ddb down" in rec["last_error"]
            assert rec["auto_retry"] is True
            m.emails.assert_not_called()

    def test_email_exception_still_marks_sent_with_note(self):
        with ledger() as (svc, m):
            m.emails.side_effect = RuntimeError("ses exploded")
            svc.announce_video(video())
            rec = record(svc, "VIDEO#vid-1")
            assert rec["status"] == "SENT"
            assert "ses exploded" in rec["last_error"]

    def test_partial_email_failures_are_noted_but_sent(self):
        with ledger() as (svc, m):
            m.emails.return_value = {"sent": 8, "failed": 2, "total": 10}
            svc.announce_video(video())
            rec = record(svc, "VIDEO#vid-1")
            assert rec["status"] == "SENT"
            assert "2 of 10" in rec["last_error"]

    def test_email_not_started_is_noted(self):
        with ledger() as (svc, m):
            m.emails.return_value = {
                "sent": 0,
                "failed": 0,
                "total": 0,
                "error": "template load failed",
            }
            svc.announce_video(video())
            rec = record(svc, "VIDEO#vid-1")
            assert rec["status"] == "SENT"
            assert "template load failed" in rec["last_error"]

    def test_never_raises(self):
        with ledger() as (svc, _):
            svc.announce_video({"title": "no id"})  # KeyError internally


# ---------------------------------------------------------------------------
# Walkthrough scan
# ---------------------------------------------------------------------------


class TestScanWalkthroughs:
    def test_disabled_flag_writes_nothing(self):
        with ledger(announcements_enabled=False) as (svc, m):
            p, registry = patch_registry([wt("a")])
            with p:
                stats = svc.scan_walkthroughs()
            assert stats == {
                "baselined": 0,
                "recorded": 0,
                "announced": 0,
                "expired": 0,
            }
            registry.get_all_walkthrough_entries.assert_not_called()
            assert svc.list_announcements() == []
            assert svc._baseline_done() is False

    def test_first_run_baselines_without_announcing(self):
        with ledger() as (svc, m):
            p, _ = patch_registry([wt("a"), wt("b")])
            with p:
                stats = svc.scan_walkthroughs()
            assert stats["baselined"] == 2
            assert stats["announced"] == 0
            assert {r["status"] for r in svc.list_announcements()} == {"BASELINED"}
            assert svc._baseline_done() is True
            m.broadcasts.create_broadcast.assert_not_called()

    def test_new_walkthrough_waits_for_settle_delay(self):
        with ledger() as (svc, m):
            with patch_registry([wt("a")])[0]:
                svc.scan_walkthroughs()  # baseline
            with patch_registry([wt("a"), wt("b")])[0]:
                stats = svc.scan_walkthroughs()
            assert stats["recorded"] == 1 and stats["announced"] == 0
            assert record(svc, "WALKTHROUGH#b")["status"] == "PENDING"
            m.broadcasts.create_broadcast.assert_not_called()

    def test_announces_after_settle_delay(self):
        with ledger() as (svc, m):
            with patch_registry([wt("a")])[0]:
                svc.scan_walkthroughs()
            entries = [wt("a"), wt("b")]
            with patch_registry(entries)[0]:
                svc.scan_walkthroughs()
                age(svc, "WALKTHROUGH#b", minutes=20)
                stats = svc.scan_walkthroughs()
            assert stats["announced"] == 1
            kwargs = m.broadcasts.create_broadcast.call_args.kwargs
            assert kwargs["title"] == "New walkthrough: Walkthrough b"
            assert kwargs["link"] == "https://dsb.example/walkthroughs/preview/b"
            assert kwargs["created_by"] == AUTO_ANNOUNCE_USER
            assert record(svc, "WALKTHROUGH#b")["status"] == "SENT"
            # The baselined one is never announced
            assert record(svc, "WALKTHROUGH#a")["status"] == "BASELINED"

    def test_zero_settle_announces_immediately(self):
        with ledger(announcement_settle_minutes=0) as (svc, m):
            with patch_registry([wt("a")])[0]:
                svc.scan_walkthroughs()
            with patch_registry([wt("a"), wt("b")])[0]:
                stats = svc.scan_walkthroughs()
            assert stats["recorded"] == 1 and stats["announced"] == 1

    def test_not_announced_twice_across_scans(self):
        with ledger(announcement_settle_minutes=0) as (svc, m):
            with patch_registry([wt("a")])[0]:
                svc.scan_walkthroughs()
            with patch_registry([wt("a"), wt("b")])[0]:
                for _ in range(4):
                    svc.scan_walkthroughs()
            assert m.broadcasts.create_broadcast.call_count == 1

    def test_removed_while_pending_is_never_announced(self):
        with ledger() as (svc, m):
            with patch_registry([wt("a")])[0]:
                svc.scan_walkthroughs()
            with patch_registry([wt("a"), wt("b")])[0]:
                svc.scan_walkthroughs()
            age(svc, "WALKTHROUGH#b", minutes=60)
            with patch_registry([wt("a")])[0]:
                stats = svc.scan_walkthroughs()
            assert stats["announced"] == 0
            assert record(svc, "WALKTHROUGH#b")["status"] == "PENDING"
            m.broadcasts.create_broadcast.assert_not_called()

    def test_edits_to_existing_walkthrough_do_not_announce(self):
        with ledger(announcement_settle_minutes=0) as (svc, m):
            with patch_registry([wt("a", title="Old")])[0]:
                svc.scan_walkthroughs()
            with patch_registry([wt("a", title="Brand new title", description="x")])[0]:
                stats = svc.scan_walkthroughs()
            assert stats["recorded"] == 0 and stats["announced"] == 0
            m.broadcasts.create_broadcast.assert_not_called()

    def test_empty_registry_does_nothing(self):
        with ledger() as (svc, m):
            with patch_registry([])[0]:
                stats = svc.scan_walkthroughs()
            assert stats["baselined"] == 0
            assert (
                svc._baseline_done() is False
            )  # a later real registry still baselines

    def test_empty_registry_after_baseline_does_not_touch_ledger(self):
        with ledger() as (svc, m):
            with patch_registry([wt("a")])[0]:
                svc.scan_walkthroughs()
            with patch_registry([])[0]:
                svc.scan_walkthroughs()
            assert record(svc, "WALKTHROUGH#a")["status"] == "BASELINED"

    def test_registry_error_does_not_raise(self):
        with ledger() as (svc, _):
            with patch_registry(RuntimeError("s3 down"))[0]:
                svc.scan_walkthroughs()
            with patch.object(mod, "get_registry_service", side_effect=Exception("x")):
                svc.scan_walkthroughs()
            assert svc.list_announcements() == []

    def test_missing_registry_bucket_does_nothing(self):
        with ledger(content_registry_bucket="") as (svc, _):
            stats = svc.scan_walkthroughs()
            assert stats["baselined"] == 0
            assert svc._baseline_done() is False

    def test_failed_item_is_retried_until_max_attempts(self):
        with ledger(announcement_settle_minutes=0, announcement_max_attempts=2) as (
            svc,
            m,
        ):
            with patch_registry([wt("a")])[0]:
                svc.scan_walkthroughs()
            entries = [wt("a"), wt("b")]
            m.broadcasts.create_broadcast.side_effect = RuntimeError("down")
            with patch_registry(entries)[0]:
                svc.scan_walkthroughs()  # attempt 1 fails
                assert record(svc, "WALKTHROUGH#b")["status"] == "FAILED"
                svc.scan_walkthroughs()  # attempt 2 fails
                assert record(svc, "WALKTHROUGH#b")["attempts"] == 2
                svc.scan_walkthroughs()  # limit reached: no third attempt
            assert record(svc, "WALKTHROUGH#b")["attempts"] == 2
            assert m.broadcasts.create_broadcast.call_count == 2

    def test_failed_item_recovers_when_service_returns(self):
        with ledger(announcement_settle_minutes=0) as (svc, m):
            with patch_registry([wt("a")])[0]:
                svc.scan_walkthroughs()
            entries = [wt("a"), wt("b")]
            m.broadcasts.create_broadcast.side_effect = [
                RuntimeError("down"),
                {"broadcast_id": "ok"},
            ]
            with patch_registry(entries)[0]:
                svc.scan_walkthroughs()
                svc.scan_walkthroughs()
            rec = record(svc, "WALKTHROUGH#b")
            assert rec["status"] == "SENT"
            assert rec["broadcast_id"] == "ok"

    def test_stale_claim_is_flagged_and_not_auto_retried(self):
        with ledger() as (svc, m):
            with patch_registry([wt("a")])[0]:
                svc.scan_walkthroughs()
            # Simulate a process that died mid-send 45 minutes ago.
            svc._record_new("VIDEO#v", "video", "v", "V", "SENDING")
            age(svc, "VIDEO#v", minutes=45)
            with patch_registry([wt("a")])[0]:
                stats = svc.scan_walkthroughs()
                svc.scan_walkthroughs()
            assert stats["expired"] == 1
            rec = record(svc, "VIDEO#v")
            assert rec["status"] == "FAILED"
            assert rec["auto_retry"] is False
            assert "Stale claim" in rec["last_error"]
            m.broadcasts.create_broadcast.assert_not_called()

    def test_recent_claim_is_not_expired(self):
        with ledger() as (svc, _):
            with patch_registry([wt("a")])[0]:
                svc.scan_walkthroughs()
                svc._record_new("VIDEO#v", "video", "v", "V", "SENDING")
                stats = svc.scan_walkthroughs()
            assert stats["expired"] == 0
            assert record(svc, "VIDEO#v")["status"] == "SENDING"


# ---------------------------------------------------------------------------
# Admin actions
# ---------------------------------------------------------------------------


class TestBaseline:
    def test_baselines_unknown_and_pending_but_not_sent(self):
        with ledger(announcement_settle_minutes=60) as (svc, m):
            with patch_registry([wt("a")])[0]:
                svc.scan_walkthroughs()  # baseline a
            svc._record_new("WALKTHROUGH#sent", "walkthrough", "sent", "S", "SENT")
            with patch_registry([wt("a"), wt("pend")])[0]:
                svc.scan_walkthroughs()  # pend -> PENDING
            assert record(svc, "WALKTHROUGH#pend")["status"] == "PENDING"

            entries = [wt("a"), wt("pend"), wt("sent"), wt("new")]
            with patch_registry(entries)[0]:
                changed = svc.baseline_walkthroughs()
            assert changed == 2  # pend (PENDING -> BASELINED) + new
            assert record(svc, "WALKTHROUGH#pend")["status"] == "BASELINED"
            assert record(svc, "WALKTHROUGH#new")["status"] == "BASELINED"
            assert record(svc, "WALKTHROUGH#sent")["status"] == "SENT"

    def test_works_when_feature_flag_is_off(self):
        with ledger(announcements_enabled=False) as (svc, _):
            with patch_registry([wt("a")])[0]:
                assert svc.baseline_walkthroughs() == 1
            assert svc._baseline_done() is True

    def test_prevents_first_scan_baseline_from_swallowing_new_items(self):
        with ledger(announcement_settle_minutes=0) as (svc, m):
            with patch_registry([wt("a")])[0]:
                svc.baseline_walkthroughs()
            with patch_registry([wt("a"), wt("b")])[0]:
                stats = svc.scan_walkthroughs()
            assert stats["baselined"] == 0
            assert stats["announced"] == 1

    def test_empty_registry_raises(self):
        with ledger() as (svc, _):
            with patch_registry([])[0]:
                with pytest.raises(RuntimeError):
                    svc.baseline_walkthroughs()

    def test_registry_failure_raises_runtime_error(self):
        with ledger() as (svc, _):
            with patch.object(mod, "get_registry_service", side_effect=Exception("x")):
                with pytest.raises(RuntimeError):
                    svc.baseline_walkthroughs()


class TestBeginRetry:
    def test_unknown_key_not_found(self):
        with ledger() as (svc, _):
            with pytest.raises(AnnouncementNotFound):
                svc.begin_retry("VIDEO#nope")

    def test_only_failed_records_can_be_retried(self):
        with ledger() as (svc, _):
            svc._record_new("VIDEO#1", "video", "1", "T", "SENT")
            with pytest.raises(AnnouncementConflict):
                svc.begin_retry("VIDEO#1")

    def test_failed_video_is_claimed_and_message_returned(self):
        with ledger() as (svc, _):
            svc._record_new("VIDEO#vid-1", "video", "vid-1", "T", "SENDING")
            svc._mark_failed("VIDEO#vid-1", "boom")
            item = {
                "id": {"S": "vid-1"},
                "title": {"S": "Intro"},
                "slug": {"S": "intro"},
                "status": {"S": "PUBLISHED"},
                "accessTier": {"S": "FREE"},
            }
            db = MagicMock()
            db.get_video.return_value = item
            with patch.object(mod, "VideoMetadataDB", return_value=db):
                title, message, link = svc.begin_retry("VIDEO#vid-1")
            assert title == "New video: Intro"
            assert link.endswith("/videos/preview/intro")
            assert record(svc, "VIDEO#vid-1")["status"] == "SENDING"

    def test_unpublished_video_cannot_be_retried(self):
        with ledger() as (svc, _):
            svc._record_new("VIDEO#vid-1", "video", "vid-1", "T", "SENDING")
            svc._mark_failed("VIDEO#vid-1", "boom")
            db = MagicMock()
            db.get_video.return_value = {
                "id": {"S": "vid-1"},
                "status": {"S": "ARCHIVED"},
            }
            with patch.object(mod, "VideoMetadataDB", return_value=db):
                with pytest.raises(AnnouncementConflict):
                    svc.begin_retry("VIDEO#vid-1")
            assert record(svc, "VIDEO#vid-1")["status"] == "FAILED"

    def test_missing_video_cannot_be_retried(self):
        with ledger() as (svc, _):
            svc._record_new("VIDEO#vid-1", "video", "vid-1", "T", "SENDING")
            svc._mark_failed("VIDEO#vid-1", "boom")
            db = MagicMock()
            db.get_video.return_value = None
            with patch.object(mod, "VideoMetadataDB", return_value=db):
                with pytest.raises(AnnouncementConflict):
                    svc.begin_retry("VIDEO#vid-1")

    def test_failed_walkthrough_retry_and_deliver(self):
        with ledger() as (svc, m):
            svc._record_new("WALKTHROUGH#a", "walkthrough", "a", "T", "PENDING")
            svc._claim("WALKTHROUGH#a", ("PENDING",))
            svc._mark_failed("WALKTHROUGH#a", "boom", auto_retry=False)
            with patch_registry([wt("a")])[0]:
                msg = svc.begin_retry("WALKTHROUGH#a")
            svc.deliver("WALKTHROUGH#a", *msg)
            assert record(svc, "WALKTHROUGH#a")["status"] == "SENT"

    def test_removed_walkthrough_cannot_be_retried(self):
        with ledger() as (svc, _):
            svc._record_new("WALKTHROUGH#a", "walkthrough", "a", "T", "SENDING")
            svc._mark_failed("WALKTHROUGH#a", "boom")
            with patch_registry([wt("other")])[0]:
                with pytest.raises(AnnouncementConflict):
                    svc.begin_retry("WALKTHROUGH#a")

    def test_double_retry_second_loses(self):
        with ledger() as (svc, _):
            svc._record_new("WALKTHROUGH#a", "walkthrough", "a", "T", "SENDING")
            svc._mark_failed("WALKTHROUGH#a", "boom")
            with patch_registry([wt("a")])[0]:
                svc.begin_retry("WALKTHROUGH#a")
                with pytest.raises(AnnouncementConflict):
                    svc.begin_retry("WALKTHROUGH#a")


# ---------------------------------------------------------------------------
# Idempotency property
# ---------------------------------------------------------------------------


@hyp_settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    ops=st.lists(
        st.sampled_from(["announce", "scan"]),
        min_size=1,
        max_size=10,
    )
)
def test_each_content_key_is_emailed_at_most_once(ops):
    """For any interleaving of triggers, a content key is emailed at most once."""
    with ledger(announcement_settle_minutes=0) as (svc, m):
        with patch_registry([wt("base")])[0]:
            svc.scan_walkthroughs()  # baseline
        entries = [wt("base"), wt("fresh")]
        for op in ops:
            if op == "announce":
                svc.announce_video(video())
            else:
                with patch_registry(entries)[0]:
                    svc.scan_walkthroughs()

        titles = [
            c.kwargs["title"] for c in m.broadcasts.create_broadcast.call_args_list
        ]
        assert titles.count("New video: Intro to DevSecOps") <= 1
        assert titles.count("New walkthrough: Walkthrough fresh") <= 1
        assert "New walkthrough: Walkthrough base" not in titles
        assert m.emails.call_count == len(titles)
