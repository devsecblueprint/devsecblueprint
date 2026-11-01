"""Video viewing analytics for the admin Video Analytics page.

Aggregates the per-member playback progress records
(``USER#<id>`` / ``VIDEO#<id>`` in the progress table) into per-video and
library-wide statistics. Only aggregate numbers are produced: member
identifiers are used to count distinct viewers and are never returned.

Because the progress table has no index by video, the data is read with a
scan. To keep that from hurting the rest of the application:

* the scan is bounded and paced (small pages, a pause between pages, eventually
  consistent reads, a projection of only the needed attributes, and an overall
  time budget);
* only one computation runs at a time (single-flight);
* results are cached with stale-while-revalidate semantics, so most requests
  never touch the table, and nothing runs on a timer when nobody is looking;
* callers run this from a plain (non-async) route so it executes in the thread
  pool and never blocks the event loop.
"""

import logging
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3

from app.config import Settings
from app.services.video_metadata_db import get_access_tier

logger = logging.getLogger(__name__)

# Cache windows (seconds)
FRESH_SECONDS = 5 * 60
STALE_MAX_SECONDS = 60 * 60

# Scan limits
SCAN_PAGE_LIMIT = 500
SCAN_PAUSE_SECONDS = 0.05
SCAN_BUDGET_SECONDS = 20.0

TOP_VIDEOS = 5
TIERS = ("FREE", "BUILDER")


class AnalyticsUnavailable(Exception):
    """Raised when no analytics can be produced and none are cached."""


# ---------------------------------------------------------------------------
# Module-level cache (the route builds a new service per request)
# ---------------------------------------------------------------------------

_state_lock = threading.Lock()  # guards _state
_compute_lock = threading.Lock()  # single-flight: held while computing
_state: dict[str, Any] = {"result": None, "ts": 0.0, "generated_at": None}


def reset_cache() -> None:
    """Clear the cache (used by tests)."""
    with _state_lock:
        _state.update(result=None, ts=0.0, generated_at=None)


# ---------------------------------------------------------------------------
# Pure aggregation
# ---------------------------------------------------------------------------


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _pct(part: int, whole: int) -> int:
    return round(part / whole * 100) if whole > 0 else 0


def parse_progress_item(item: dict[str, Any]) -> dict[str, Any] | None:
    """Convert a progress-table item to a plain record, or None if unusable.

    Uses the best-progress and sticky-completed fields when present and falls
    back to the latest percent and completed flag for older records.
    """
    pk = item.get("PK", {}).get("S", "")
    sk = item.get("SK", {}).get("S", "")
    if not pk.startswith("USER#") or not sk.startswith("VIDEO#"):
        return None

    def number(name: str) -> int | None:
        raw = item.get(name, {}).get("N")
        if raw is None:
            return None
        try:
            return int(float(raw))
        except ValueError:
            return None

    best = number("maxPercentComplete")
    if best is None:
        best = number("percentComplete") or 0
    best = max(0, min(100, best))

    if "everCompleted" in item:
        completed = bool(item["everCompleted"].get("BOOL", False))
    else:
        completed = bool(item.get("completed", {}).get("BOOL", False))

    return {
        "user_id": pk[len("USER#") :],
        "video_id": sk[len("VIDEO#") :],
        "best": best,
        "completed": completed,
        "last_watched_at": item.get("lastWatchedAt", {}).get("S"),
    }


def aggregate(
    videos: list[dict[str, Any]],
    records: list[dict[str, Any]],
    now: datetime,
) -> dict[str, Any]:
    """Aggregate progress records into per-video stats and library totals.

    Args:
        videos: Dicts with id, title, slug, status, access_tier.
        records: Dicts from ``parse_progress_item``.
        now: Reference time for the 7 and 30 day windows.
    """
    known = {v["id"]: v for v in videos}
    per_video: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["video_id"] in known:  # progress for deleted videos is ignored
            per_video[record["video_id"]].append(record)

    cutoff_7d = now - timedelta(days=7)
    cutoff_30d = now - timedelta(days=30)
    distinct: set[str] = set()
    active_7d: set[str] = set()
    active_30d: set[str] = set()
    tier_viewers = {t: 0 for t in TIERS}
    tier_completed = {t: 0 for t in TIERS}
    total_pairs = 0
    total_completed = 0

    items: list[dict[str, Any]] = []
    for video in videos:
        rows = per_video.get(video["id"], [])
        # One row per member per video (the table key guarantees it, but be safe)
        by_user = {r["user_id"]: r for r in rows}
        rows = list(by_user.values())

        viewers = len(rows)
        completed = sum(1 for r in rows if r["completed"])
        avg_best = round(sum(r["best"] for r in rows) / viewers) if viewers else 0

        last_watched: tuple[datetime, str] | None = None
        for r in rows:
            distinct.add(r["user_id"])
            when = _parse_time(r["last_watched_at"])
            if when is None:
                continue
            if last_watched is None or when > last_watched[0]:
                last_watched = (when, r["last_watched_at"])
            if when >= cutoff_30d:
                active_30d.add(r["user_id"])
            if when >= cutoff_7d:
                active_7d.add(r["user_id"])

        tier = video["access_tier"] if video["access_tier"] in TIERS else "BUILDER"
        tier_viewers[tier] += viewers
        tier_completed[tier] += completed
        total_pairs += viewers
        total_completed += completed

        items.append(
            {
                "id": video["id"],
                "title": video["title"],
                "slug": video["slug"],
                "status": video["status"],
                "access_tier": tier,
                "unique_viewers": viewers,
                "completed": completed,
                "completion_rate": _pct(completed, viewers),
                "avg_best_progress": avg_best,
                "last_watched_at": last_watched[1] if last_watched else None,
            }
        )

    items.sort(key=lambda i: (-i["unique_viewers"], i["title"].lower()))
    top = sorted(
        (i for i in items if i["unique_viewers"] > 0),
        key=lambda i: (-i["unique_viewers"], -i["completion_rate"], i["title"].lower()),
    )[:TOP_VIDEOS]

    return {
        "totals": {
            "distinct_viewers": len(distinct),
            "active_7d": len(active_7d),
            "active_30d": len(active_30d),
            "completions": total_completed,
            "completion_rate": _pct(total_completed, total_pairs),
        },
        "by_tier": {
            t: {
                "viewers": tier_viewers[t],
                "completions": tier_completed[t],
                "completion_rate": _pct(tier_completed[t], tier_viewers[t]),
            }
            for t in TIERS
        },
        "top_videos": top,
        "videos": items,
    }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class VideoAnalyticsService:
    """Computes and caches video analytics."""

    def __init__(self, settings: Settings, client: Any = None) -> None:
        self._settings = settings
        self._client = client or boto3.client("dynamodb")

    # -- data access ------------------------------------------------------

    def _scan_videos(self) -> list[dict[str, Any]]:
        videos: list[dict[str, Any]] = []
        last_key = None
        while True:
            params: dict[str, Any] = {
                "TableName": self._settings.videos_table,
                "FilterExpression": "SK = :sk",
                "ExpressionAttributeValues": {":sk": {"S": "METADATA"}},
                "ProjectionExpression": "#id, title, slug, #st, accessTier",
                "ExpressionAttributeNames": {"#id": "id", "#st": "status"},
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key
            response = self._client.scan(**params)
            for item in response.get("Items", []):
                videos.append(
                    {
                        "id": item.get("id", {}).get("S", ""),
                        "title": item.get("title", {}).get("S", ""),
                        "slug": item.get("slug", {}).get("S", ""),
                        "status": item.get("status", {}).get("S", ""),
                        "access_tier": get_access_tier(item).value,
                    }
                )
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                return [v for v in videos if v["id"]]
            time.sleep(SCAN_PAUSE_SECONDS)

    def _scan_progress(self) -> tuple[list[dict[str, Any]], int]:
        """Paced, bounded scan of video progress records.

        Returns the parsed records and the number of items the scan examined.
        Raises TimeoutError if the time budget is exceeded.
        """
        started = time.monotonic()
        records: list[dict[str, Any]] = []
        scanned = 0
        last_key = None
        while True:
            params: dict[str, Any] = {
                "TableName": self._settings.progress_table,
                "FilterExpression": "begins_with(SK, :p)",
                "ExpressionAttributeValues": {":p": {"S": "VIDEO#"}},
                "ProjectionExpression": (
                    "PK, SK, percentComplete, maxPercentComplete, "
                    "completed, everCompleted, lastWatchedAt"
                ),
                "Limit": SCAN_PAGE_LIMIT,
                # Eventually consistent reads (the default) cost half as much.
                "ConsistentRead": False,
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key
            response = self._client.scan(**params)
            scanned += response.get("ScannedCount", 0)
            for item in response.get("Items", []):
                parsed = parse_progress_item(item)
                if parsed:
                    records.append(parsed)
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                return records, scanned
            if time.monotonic() - started > SCAN_BUDGET_SECONDS:
                raise TimeoutError(
                    f"Progress scan exceeded {SCAN_BUDGET_SECONDS:.0f}s budget"
                )
            time.sleep(SCAN_PAUSE_SECONDS)

    # -- computation ------------------------------------------------------

    def _compute(self) -> tuple[dict[str, Any], str]:
        started = time.monotonic()
        videos = self._scan_videos()
        records, scanned = self._scan_progress()
        now = datetime.now(timezone.utc)
        result = aggregate(videos, records, now)
        logger.info(
            "Video analytics computed: duration=%.2fs items_scanned=%d "
            "progress_records=%d videos=%d",
            time.monotonic() - started,
            scanned,
            len(records),
            len(videos),
        )
        return result, now.isoformat()

    def _store(self, result: dict[str, Any], generated_at: str) -> None:
        with _state_lock:
            _state.update(result=result, ts=time.time(), generated_at=generated_at)

    @staticmethod
    def _snapshot() -> tuple[dict[str, Any] | None, float, str | None]:
        with _state_lock:
            return _state["result"], _state["ts"], _state["generated_at"]

    @staticmethod
    def _response(result: dict[str, Any], generated_at: str | None, stale: bool):
        return {"generated_at": generated_at, "stale": stale, **result}

    def _refresh_in_background(self) -> None:
        """Start one background refresh unless one is already running."""

        def work() -> None:
            if not _compute_lock.acquire(blocking=False):
                return  # another refresh is already in flight
            try:
                result, generated_at = self._compute()
                self._store(result, generated_at)
            except Exception:
                logger.exception("Background video analytics refresh failed")
            finally:
                _compute_lock.release()

        threading.Thread(
            target=work, name="video-analytics-refresh", daemon=True
        ).start()

    # -- public -----------------------------------------------------------

    def get_analytics(self) -> dict[str, Any]:
        """Return analytics, computing only when the cache cannot serve them.

        Raises:
            AnalyticsUnavailable: Nothing cached and the computation failed.
        """
        result, ts, generated_at = self._snapshot()
        if result is not None:
            age = time.time() - ts
            if age < FRESH_SECONDS:
                return self._response(result, generated_at, stale=False)
            if age < STALE_MAX_SECONDS:
                self._refresh_in_background()
                return self._response(result, generated_at, stale=True)

        # Nothing usable: wait for a (single) fresh computation.
        with _compute_lock:
            # Another request may have refreshed while we waited for the lock.
            result_now, ts_now, generated_now = self._snapshot()
            if result_now is not None and time.time() - ts_now < FRESH_SECONDS:
                return self._response(result_now, generated_now, stale=False)
            try:
                fresh, fresh_at = self._compute()
            except Exception as e:
                logger.exception("Video analytics computation failed")
                if result_now is not None:
                    return self._response(result_now, generated_now, stale=True)
                raise AnalyticsUnavailable(str(e)) from e
            self._store(fresh, fresh_at)
            return self._response(fresh, fresh_at, stale=False)
