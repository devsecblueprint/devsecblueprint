"""Automatic content announcements (videos and walkthroughs).

When a video is published, or a new walkthrough appears in the content
registry, this service creates a broadcast (in-app modal + email to all
users) exactly once per item.

Idempotency is enforced by a DynamoDB "announcement ledger" keyed by content
key. An item must be *claimed* with a conditional write before anything is
sent, so repeated triggers (double clicks, scheduler overlap, restarts,
repeated deploys) cannot produce duplicate announcements.

Ledger schema (ANNOUNCEMENTS_TABLE):
    PK: "CONTENT#VIDEO#<video_id>" | "CONTENT#WALKTHROUGH#<walkthrough_id>"
    SK: "ANNOUNCEMENT"
    status: PENDING | SENDING | SENT | FAILED | BASELINED
    GSI1PK: "STATUS#<status>", GSI1SK: first_seen_at   (index "GSI1")

    A sentinel item (PK "META#WALKTHROUGH_BASELINE") records that the initial
    walkthrough baseline has been taken. It has no GSI keys, so it never shows
    up in status listings.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings
from app.config.settings import get_settings
from app.services.broadcast_email import send_broadcast_emails
from app.services.broadcast_service import BroadcastService
from app.services.content_registry import get_registry_service
from app.services.video_metadata_db import VideoMetadataDB, get_access_tier

logger = logging.getLogger(__name__)

AUTO_ANNOUNCE_USER = "system:auto-announce"

SORT_KEY = "ANNOUNCEMENT"
BASELINE_SENTINEL_PK = "META#WALKTHROUGH_BASELINE"
GSI_NAME = "GSI1"

STATUS_PENDING = "PENDING"
STATUS_SENDING = "SENDING"
STATUS_SENT = "SENT"
STATUS_FAILED = "FAILED"
STATUS_BASELINED = "BASELINED"
ALL_STATUSES = (
    STATUS_PENDING,
    STATUS_SENDING,
    STATUS_SENT,
    STATUS_FAILED,
    STATUS_BASELINED,
)

MAX_ERROR_LENGTH = 500
MAX_TOPICS = 6

CONTENT_TYPE_VIDEO = "video"
CONTENT_TYPE_WALKTHROUGH = "walkthrough"

Message = tuple[str, str, str]  # (title, markdown message, link)

# ---------------------------------------------------------------------------
# Announcement copy. Everything people read that is not content metadata lives
# here, so changing the tone (for example a personal "I've added..." opening
# signed by a person) is an edit to this block only.
# ---------------------------------------------------------------------------

OPENING_WALKTHROUGH = "**Your next hands-on walkthrough is here.**"
OPENING_VIDEO = "**A new session is here.**"
CLOSING_WALKTHROUGH = "Ready to put it into practice?"
CLOSING_VIDEO = "Ready to watch?"
SIGNOFF_LINES = ["Happy building,", "The DevSec Blueprint"]

# Email-only extras per content type: the button label and the sign-off that
# follows the button. The in-app modal keeps its own button and has no sign-off.
EMAIL_EXTRAS = {
    "WALKTHROUGH": {
        "cta_label": "Start the walkthrough",
        "signoff_lines": SIGNOFF_LINES,
    },
    "VIDEO": {"cta_label": "Watch the session", "signoff_lines": SIGNOFF_LINES},
}


class AnnouncementNotFound(Exception):
    """Raised when an announcement ledger record does not exist."""


class AnnouncementConflict(Exception):
    """Raised when an announcement cannot be acted on in its current state."""


# ---------------------------------------------------------------------------
# Message builders (pure functions)
# ---------------------------------------------------------------------------


def _neutralize_html(text: str) -> str:
    """Escape angle brackets so author text can't inject raw HTML.

    The broadcast email renderer passes raw HTML in markdown through, so any
    content that originates outside the admin broadcast form is neutralized.
    """
    return (text or "").replace("<", "&lt;").replace(">", "&gt;")


def _join_url(base_url: str, path: str) -> str:
    base = (base_url or "").rstrip("/")
    return f"{base}{path}"


_MARKDOWN_SPECIALS = str.maketrans({c: "\\" + c for c in "\\*_[]`"})


def _escape_markdown(text: str) -> str:
    """Escape characters that would turn plain text (a title) into formatting."""
    return (text or "").translate(_MARKDOWN_SPECIALS)


def _blocks(*blocks: str) -> str:
    """Join non-empty blocks with a blank line between them."""
    return "\n\n".join(b.strip() for b in blocks if b and b.strip())


def _lines(*lines: str) -> str:
    """Join non-empty lines with a markdown hard line break (two spaces)."""
    return "  \n".join(line for line in lines if line)


def build_video_message(video: dict[str, Any], base_url: str = "") -> Message:
    """Build the (title, markdown, link) triple for a published video.

    Layout: opening line, title, description, details, access line, closing
    question. The description is the full text entered in the video editor.

    Args:
        video: Dict with title, slug, description, instructor,
            duration_seconds, tags, and access_tier.
        base_url: Site origin used to make the link absolute.
    """
    raw_title = (video.get("title") or "").strip() or "New session"
    title = f"New video: {raw_title}"

    details: list[str] = []
    instructor = (video.get("instructor") or "").strip()
    if instructor:
        details.append(f"**Instructor:** {_neutralize_html(instructor)}")

    seconds = int(video.get("duration_seconds") or 0)
    if seconds > 0:
        details.append(f"**Length:** {max(1, round(seconds / 60))} min")

    topics = [
        t.strip()
        for t in (video.get("tags") or [])
        if t and t.strip() and not t.strip().lower().startswith("instructor:")
    ][:MAX_TOPICS]
    if topics:
        details.append(f"**Topics:** {_neutralize_html(', '.join(topics))}")

    tier = str(video.get("access_tier") or "BUILDER").upper()
    tier_line = (
        "Free for all members." if tier == "FREE" else "Available to Builder members."
    )

    message = _blocks(
        OPENING_VIDEO,
        f"**{_escape_markdown(raw_title)}**",
        _neutralize_html(video.get("description") or ""),
        _lines(*details),
        tier_line,
        CLOSING_VIDEO,
    )
    link = _join_url(base_url, f"/videos/preview/{video.get('slug', '')}")
    return title, message, link


def _format_minutes(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} min"
    hours, rest = divmod(minutes, 60)
    return f"{hours} hr {rest} min" if rest else f"{hours} hr"


def build_walkthrough_message(entry: dict[str, Any], base_url: str = "") -> Message:
    """Build the (title, markdown, link) triple for a new walkthrough.

    Layout: opening line, title, description, level and time, closing
    question.

    Args:
        entry: Registry walkthrough entry (with ``id``), including title,
            description, difficulty, and estimated_time (minutes).
        base_url: Site origin used to make the link absolute.
    """
    raw_title = (entry.get("title") or "").strip() or entry.get("id", "Walkthrough")
    title = f"New walkthrough: {raw_title}"

    facts: list[str] = []
    difficulty = (entry.get("difficulty") or "").strip()
    if difficulty:
        facts.append(f"**Level:** {_neutralize_html(difficulty)}")
    minutes = entry.get("estimated_time")
    if isinstance(minutes, (int, float)) and minutes > 0:
        facts.append(f"**Estimated time:** {_format_minutes(int(minutes))}")

    message = _blocks(
        OPENING_WALKTHROUGH,
        f"**{_escape_markdown(raw_title)}**",
        _neutralize_html(entry.get("description") or ""),
        _lines(*facts),
        CLOSING_WALKTHROUGH,
    )
    link = _join_url(base_url, f"/walkthroughs/preview/{entry.get('id', '')}")
    return title, message, link


def video_item_to_fields(item: dict[str, Any]) -> dict[str, Any]:
    """Convert a videos-table DynamoDB item to the plain dict the builders use."""

    def s(key: str) -> str:
        return item.get(key, {}).get("S", "")

    try:
        duration = int(item.get("durationSeconds", {}).get("N", "0"))
    except ValueError:
        duration = 0
    return {
        "id": s("id"),
        "title": s("title"),
        "slug": s("slug"),
        "description": s("description"),
        "instructor": s("instructor"),
        "duration_seconds": duration,
        "tags": [t.get("S", "") for t in item.get("tags", {}).get("L", [])],
        "access_tier": get_access_tier(item).value,
        "status": s("status"),
    }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_conditional_failure(error: ClientError) -> bool:
    return (
        error.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException"
    )


class AnnouncementService:
    """Ledger-backed automatic announcements."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = boto3.client("dynamodb")

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    @property
    def _table(self) -> str:
        return self._settings.announcements_table

    @property
    def enabled(self) -> bool:
        """True only when the feature flag is on and the table is configured."""
        return bool(self._settings.announcements_enabled and self._table)

    @property
    def _base_url(self) -> str:
        return self._settings.frontend_origin

    @staticmethod
    def _pk(content_key: str) -> str:
        return f"CONTENT#{content_key}"

    def _key(self, content_key: str) -> dict[str, Any]:
        return {"PK": {"S": self._pk(content_key)}, "SK": {"S": SORT_KEY}}

    # ------------------------------------------------------------------
    # Ledger operations
    # ------------------------------------------------------------------

    def _record_new(
        self,
        content_key: str,
        content_type: str,
        content_id: str,
        title: str,
        status: str,
    ) -> bool:
        """Create a ledger record. Returns False if one already exists."""
        now = _now().isoformat()
        item: dict[str, Any] = {
            **self._key(content_key),
            "content_key": {"S": content_key},
            "content_type": {"S": content_type},
            "content_id": {"S": content_id},
            "title": {"S": title or content_id},
            "status": {"S": status},
            "first_seen_at": {"S": now},
            "attempts": {"N": "1" if status == STATUS_SENDING else "0"},
            "GSI1PK": {"S": f"STATUS#{status}"},
            "GSI1SK": {"S": now},
        }
        if status == STATUS_SENDING:
            item["claimed_at"] = {"S": now}
        try:
            self._client.put_item(
                TableName=self._table,
                Item=item,
                ConditionExpression="attribute_not_exists(PK)",
            )
            return True
        except ClientError as e:
            if _is_conditional_failure(e):
                return False
            raise

    def _claim(self, content_key: str, expected: tuple[str, ...]) -> bool:
        """Atomically move a record to SENDING. Returns False if not claimable."""
        values: dict[str, Any] = {
            ":sending": {"S": STATUS_SENDING},
            ":gsi": {"S": f"STATUS#{STATUS_SENDING}"},
            ":now": {"S": _now().isoformat()},
            ":zero": {"N": "0"},
            ":one": {"N": "1"},
        }
        placeholders = []
        for i, status in enumerate(expected):
            placeholders.append(f":e{i}")
            values[f":e{i}"] = {"S": status}
        try:
            self._client.update_item(
                TableName=self._table,
                Key=self._key(content_key),
                UpdateExpression=(
                    "SET #s = :sending, GSI1PK = :gsi, claimed_at = :now, "
                    "attempts = if_not_exists(attempts, :zero) + :one "
                    "REMOVE last_error"
                ),
                ConditionExpression=f"#s IN ({', '.join(placeholders)})",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues=values,
            )
            return True
        except ClientError as e:
            if _is_conditional_failure(e):
                return False
            raise

    def _mark_sent(
        self, content_key: str, broadcast_id: str, note: str | None = None
    ) -> None:
        values: dict[str, Any] = {
            ":sent": {"S": STATUS_SENT},
            ":gsi": {"S": f"STATUS#{STATUS_SENT}"},
            ":now": {"S": _now().isoformat()},
            ":bid": {"S": broadcast_id},
        }
        expression = (
            "SET #s = :sent, GSI1PK = :gsi, sent_at = :now, broadcast_id = :bid"
        )
        if note:
            expression += ", last_error = :err"
            values[":err"] = {"S": note[:MAX_ERROR_LENGTH]}
        else:
            expression += " REMOVE last_error"
        self._client.update_item(
            TableName=self._table,
            Key=self._key(content_key),
            UpdateExpression=expression,
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues=values,
        )

    def _mark_failed(
        self, content_key: str, error: str, auto_retry: bool = True
    ) -> None:
        self._client.update_item(
            TableName=self._table,
            Key=self._key(content_key),
            UpdateExpression=(
                "SET #s = :failed, GSI1PK = :gsi, last_error = :err, "
                "auto_retry = :retry"
            ),
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":failed": {"S": STATUS_FAILED},
                ":gsi": {"S": f"STATUS#{STATUS_FAILED}"},
                ":err": {"S": error[:MAX_ERROR_LENGTH]},
                ":retry": {"BOOL": auto_retry},
            },
        )

    def _expire_claim(self, content_key: str, claimed_at: str) -> bool:
        """Mark a stale SENDING claim FAILED (no auto-retry). Race-safe."""
        try:
            self._client.update_item(
                TableName=self._table,
                Key=self._key(content_key),
                UpdateExpression=(
                    "SET #s = :failed, GSI1PK = :gsi, last_error = :err, "
                    "auto_retry = :retry"
                ),
                ConditionExpression="#s = :sending AND claimed_at = :claimed",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":failed": {"S": STATUS_FAILED},
                    ":gsi": {"S": f"STATUS#{STATUS_FAILED}"},
                    ":err": {
                        "S": "Stale claim: delivery state unknown. "
                        "Check broadcast history before retrying."
                    },
                    ":retry": {"BOOL": False},
                    ":sending": {"S": STATUS_SENDING},
                    ":claimed": {"S": claimed_at},
                },
            )
            return True
        except ClientError as e:
            if _is_conditional_failure(e):
                return False
            raise

    def _get(self, content_key: str) -> dict[str, Any] | None:
        response = self._client.get_item(
            TableName=self._table, Key=self._key(content_key), ConsistentRead=True
        )
        item = response.get("Item")
        return self._item_to_record(item) if item else None

    @staticmethod
    def _item_to_record(item: dict[str, Any]) -> dict[str, Any]:
        def s(key: str) -> str | None:
            value = item.get(key, {}).get("S")
            return value if value else None

        try:
            attempts = int(item.get("attempts", {}).get("N", "0"))
        except ValueError:
            attempts = 0
        return {
            "content_key": s("content_key") or "",
            "content_type": s("content_type") or "",
            "content_id": s("content_id") or "",
            "title": s("title") or "",
            "status": s("status") or "",
            "first_seen_at": s("first_seen_at") or "",
            "claimed_at": s("claimed_at"),
            "sent_at": s("sent_at"),
            "broadcast_id": s("broadcast_id"),
            "attempts": attempts,
            "last_error": s("last_error"),
            # Absent means a normal failure, which is eligible for auto-retry.
            "auto_retry": item.get("auto_retry", {}).get("BOOL", True),
        }

    def _query_status(self, status: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        last_key = None
        while True:
            params: dict[str, Any] = {
                "TableName": self._table,
                "IndexName": GSI_NAME,
                "KeyConditionExpression": "GSI1PK = :pk",
                "ExpressionAttributeValues": {":pk": {"S": f"STATUS#{status}"}},
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key
            response = self._client.query(**params)
            records.extend(
                self._item_to_record(item) for item in response.get("Items", [])
            )
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
        return records

    # ------------------------------------------------------------------
    # Admin-facing queries
    # ------------------------------------------------------------------

    def list_announcements(self, status: str | None = None) -> list[dict[str, Any]]:
        """List ledger records, newest first, optionally filtered by status."""
        statuses = [status] if status else list(ALL_STATUSES)
        records: list[dict[str, Any]] = []
        for st in statuses:
            records.extend(self._query_status(st))
        records.sort(key=lambda r: r["first_seen_at"], reverse=True)
        return records

    def failed_count(self) -> int:
        """Number of FAILED records (GSI count query)."""
        total = 0
        last_key = None
        while True:
            params: dict[str, Any] = {
                "TableName": self._table,
                "IndexName": GSI_NAME,
                "KeyConditionExpression": "GSI1PK = :pk",
                "ExpressionAttributeValues": {":pk": {"S": f"STATUS#{STATUS_FAILED}"}},
                "Select": "COUNT",
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key
            response = self._client.query(**params)
            total += response.get("Count", 0)
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
        return total

    # ------------------------------------------------------------------
    # Delivery
    # ------------------------------------------------------------------

    def deliver(self, content_key: str, title: str, message: str, link: str) -> None:
        """Create the broadcast, send emails, and update the ledger.

        The record MUST already be claimed (SENDING). Never raises.

        A failure before the broadcast exists marks the record FAILED (eligible
        for retry). Once the broadcast exists the record is marked SENT even if
        email delivery had problems, because a resend would duplicate mail for
        the recipients who already received it.
        """
        try:
            broadcast = BroadcastService(self._settings).create_broadcast(
                title=title,
                message=message,
                created_by=AUTO_ANNOUNCE_USER,
                link=link,
            )
        except Exception as e:
            logger.exception("Announcement %s: broadcast creation failed", content_key)
            self._safe_mark_failed(content_key, f"Broadcast creation failed: {e}")
            return

        note: str | None = None
        counts: dict[str, Any] = {}
        try:
            email_broadcast = {**broadcast, **self._email_extras(content_key)}
            counts = send_broadcast_emails(email_broadcast, self._settings) or {}
        except Exception as e:
            logger.exception("Announcement %s: email delivery error", content_key)
            note = f"Email delivery error: {e}"
        else:
            if counts.get("error"):
                note = f"Email delivery did not start: {counts['error']}"
            elif counts.get("failed"):
                note = (
                    f"{counts['failed']} of {counts.get('total', '?')} "
                    "emails failed to send"
                )

        try:
            self._mark_sent(content_key, broadcast["broadcast_id"], note)
        except Exception:
            # Left in SENDING; the stale-claim sweep will flag it for review.
            logger.exception(
                "Announcement %s: failed to record SENT (broadcast %s)",
                content_key,
                broadcast.get("broadcast_id"),
            )
            return

        logger.info(
            "Announcement sent: key=%s broadcast_id=%s emails_sent=%s emails_failed=%s",
            content_key,
            broadcast.get("broadcast_id"),
            counts.get("sent", "n/a"),
            counts.get("failed", "n/a"),
        )

    @staticmethod
    def _email_extras(content_key: str) -> dict[str, Any]:
        """Email-only button label and sign-off for this kind of content."""
        kind = content_key.split("#", 1)[0]
        return dict(EMAIL_EXTRAS.get(kind, {}))

    def _safe_mark_failed(
        self, content_key: str, error: str, auto_retry: bool = True
    ) -> None:
        try:
            self._mark_failed(content_key, error, auto_retry)
        except Exception:
            logger.exception("Announcement %s: failed to record FAILED", content_key)

    # ------------------------------------------------------------------
    # Video trigger
    # ------------------------------------------------------------------

    def announce_video(self, video: dict[str, Any]) -> None:
        """Announce a newly published video. Safe to call repeatedly; never raises.

        This is a blocking call (serial email sends). Call it from a
        synchronous FastAPI BackgroundTask so it runs in the thread pool.
        """
        if not self.enabled:
            return
        try:
            video_id = video["id"]
            content_key = f"VIDEO#{video_id}"
            title, message, link = build_video_message(video, self._base_url)
            created = self._record_new(
                content_key,
                CONTENT_TYPE_VIDEO,
                video_id,
                video.get("title", ""),
                STATUS_SENDING,
            )
            if not created:
                logger.info("Announcement skipped (already recorded): %s", content_key)
                return
            self.deliver(content_key, title, message, link)
        except Exception:
            logger.exception("Video announcement failed for %s", video.get("id"))

    # ------------------------------------------------------------------
    # Walkthrough scan
    # ------------------------------------------------------------------

    def _load_walkthrough_entries(self) -> dict[str, dict[str, Any]]:
        bucket = self._settings.content_registry_bucket
        if not bucket:
            return {}
        registry = get_registry_service(bucket)
        return {e["id"]: e for e in registry.get_all_walkthrough_entries()}

    def _baseline_done(self) -> bool:
        response = self._client.get_item(
            TableName=self._table,
            Key={"PK": {"S": BASELINE_SENTINEL_PK}, "SK": {"S": SORT_KEY}},
            ConsistentRead=True,
        )
        return "Item" in response

    def _set_baseline_done(self) -> None:
        self._client.put_item(
            TableName=self._table,
            Item={
                "PK": {"S": BASELINE_SENTINEL_PK},
                "SK": {"S": SORT_KEY},
                "completed_at": {"S": _now().isoformat()},
            },
        )

    def _baseline_entries(self, entries: dict[str, dict[str, Any]]) -> int:
        """Record every registry walkthrough as BASELINED (or PENDING -> BASELINED)."""
        changed = 0
        for walkthrough_id, entry in entries.items():
            key = f"WALKTHROUGH#{walkthrough_id}"
            if self._record_new(
                key,
                CONTENT_TYPE_WALKTHROUGH,
                walkthrough_id,
                entry.get("title", ""),
                STATUS_BASELINED,
            ):
                changed += 1
                continue
            try:
                self._client.update_item(
                    TableName=self._table,
                    Key=self._key(key),
                    UpdateExpression="SET #s = :b, GSI1PK = :gsi",
                    ConditionExpression="#s = :pending",
                    ExpressionAttributeNames={"#s": "status"},
                    ExpressionAttributeValues={
                        ":b": {"S": STATUS_BASELINED},
                        ":gsi": {"S": f"STATUS#{STATUS_BASELINED}"},
                        ":pending": {"S": STATUS_PENDING},
                    },
                )
                changed += 1
            except ClientError as e:
                if not _is_conditional_failure(e):
                    raise
        return changed

    def baseline_walkthroughs(self) -> int:
        """Admin action: mark all current registry walkthroughs as announced.

        Does not require the feature flag, so it can be run before enabling.

        Raises:
            RuntimeError: If the registry is unavailable or has no walkthroughs.
        """
        try:
            entries = self._load_walkthrough_entries()
        except Exception as e:
            raise RuntimeError(f"Content registry unavailable: {e}") from e
        if not entries:
            raise RuntimeError("Content registry has no walkthroughs")
        changed = self._baseline_entries(entries)
        self._set_baseline_done()
        logger.info("Walkthrough baseline complete: %d records changed", changed)
        return changed

    def scan_walkthroughs(self) -> dict[str, int]:
        """Detect new walkthroughs in the registry and announce them.

        Returns counters describing what happened (useful for logs and tests).
        Never raises.
        """
        stats = {"baselined": 0, "recorded": 0, "announced": 0, "expired": 0}
        if not self.enabled:
            return stats
        try:
            return self._scan_walkthroughs(stats)
        except Exception:
            logger.exception("Walkthrough announcement scan failed")
            return stats

    def _scan_walkthroughs(self, stats: dict[str, int]) -> dict[str, int]:
        try:
            entries = self._load_walkthrough_entries()
        except Exception:
            logger.exception("Walkthrough scan skipped: registry unavailable")
            return stats
        if not entries:
            logger.warning("Walkthrough scan skipped: registry has no walkthroughs")
            return stats

        # First run: record everything that already exists without announcing.
        if not self._baseline_done():
            stats["baselined"] = self._baseline_entries(entries)
            self._set_baseline_done()
            logger.info(
                "Walkthrough baseline taken: %d walkthroughs", stats["baselined"]
            )
            return stats

        # Known walkthrough records, keyed by content key.
        records: dict[str, dict[str, Any]] = {}
        for status in ALL_STATUSES:
            for record in self._query_status(status):
                if record["content_type"] == CONTENT_TYPE_WALKTHROUGH:
                    records[record["content_key"]] = record

        # Newly seen walkthroughs start as PENDING.
        for walkthrough_id, entry in entries.items():
            key = f"WALKTHROUGH#{walkthrough_id}"
            if key in records:
                continue
            if self._record_new(
                key,
                CONTENT_TYPE_WALKTHROUGH,
                walkthrough_id,
                entry.get("title", ""),
                STATUS_PENDING,
            ):
                stats["recorded"] += 1
                records[key] = {
                    "content_key": key,
                    "content_id": walkthrough_id,
                    "status": STATUS_PENDING,
                    "first_seen_at": _now().isoformat(),
                    "attempts": 0,
                    "auto_retry": True,
                }

        settle = timedelta(minutes=self._settings.announcement_settle_minutes)
        now = _now()
        for key, record in records.items():
            walkthrough_id = record["content_id"]
            entry = entries.get(walkthrough_id)
            if entry is None:
                # Removed from the registry: never announce a missing item.
                continue

            if record["status"] == STATUS_PENDING:
                first_seen = datetime.fromisoformat(record["first_seen_at"])
                if now - first_seen < settle:
                    continue
                expected: tuple[str, ...] = (STATUS_PENDING,)
            elif (
                record["status"] == STATUS_FAILED
                and record.get("auto_retry", True)
                and record["attempts"] < self._settings.announcement_max_attempts
            ):
                expected = (STATUS_FAILED,)
            else:
                continue

            if not self._claim(key, expected):
                continue
            title, message, link = build_walkthrough_message(entry, self._base_url)
            self.deliver(key, title, message, link)
            stats["announced"] += 1

        stats["expired"] = self._expire_stale_claims()
        return stats

    def _expire_stale_claims(self) -> int:
        """Flag SENDING records that outlived the claim window as FAILED."""
        window = timedelta(minutes=self._settings.announcement_stale_claim_minutes)
        cutoff = _now() - window
        expired = 0
        for record in self._query_status(STATUS_SENDING):
            claimed_at = record.get("claimed_at")
            if not claimed_at:
                continue
            if datetime.fromisoformat(claimed_at) < cutoff:
                if self._expire_claim(record["content_key"], claimed_at):
                    expired += 1
                    logger.warning(
                        "Announcement %s has a stale claim; marked FAILED for review",
                        record["content_key"],
                    )
        return expired

    # ------------------------------------------------------------------
    # Admin retry
    # ------------------------------------------------------------------

    def _resolve_message(self, record: dict[str, Any]) -> Message:
        content_type = record["content_type"]
        content_id = record["content_id"]
        if content_type == CONTENT_TYPE_VIDEO:
            item = VideoMetadataDB(self._settings).get_video(content_id)
            fields = video_item_to_fields(item) if item else None
            if not fields or fields["status"] != "PUBLISHED":
                raise AnnouncementConflict("Video is no longer published")
            return build_video_message(fields, self._base_url)
        if content_type == CONTENT_TYPE_WALKTHROUGH:
            try:
                entries = self._load_walkthrough_entries()
            except Exception as e:
                raise AnnouncementConflict(f"Content registry unavailable: {e}")
            entry = entries.get(content_id)
            if entry is None:
                raise AnnouncementConflict("Walkthrough is no longer in the registry")
            return build_walkthrough_message(entry, self._base_url)
        raise AnnouncementConflict(f"Unsupported content type: {content_type}")

    def begin_retry(self, content_key: str) -> Message:
        """Validate and claim a FAILED record for retry.

        Returns the message to deliver; the caller then runs ``deliver`` (for
        example as a BackgroundTask).

        Raises:
            AnnouncementNotFound: No such record.
            AnnouncementConflict: Not FAILED, content gone, or already claimed.
        """
        record = self._get(content_key)
        if record is None:
            raise AnnouncementNotFound(content_key)
        if record["status"] != STATUS_FAILED:
            raise AnnouncementConflict("Only FAILED announcements can be retried")
        message = self._resolve_message(record)
        if not self._claim(content_key, (STATUS_FAILED,)):
            raise AnnouncementConflict("Announcement is already being processed")
        return message


# ---------------------------------------------------------------------------
# Scheduler entry point
# ---------------------------------------------------------------------------


def run_announcement_scan() -> None:
    """APScheduler job: scan for new walkthroughs and announce them."""
    settings = get_settings()
    AnnouncementService(settings).scan_walkthroughs()
