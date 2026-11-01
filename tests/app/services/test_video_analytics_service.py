"""Tests for app.services.video_analytics_service.

Covers the pure aggregation, the paced/bounded scan (against moto), and the
caching behavior: fresh/stale/blocking paths, single-flight computation under
concurrency, and stale-on-failure.
"""

import json
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import boto3
import pytest
from hypothesis import given, settings as hyp_settings, strategies as st
from moto import mock_aws

from app.services import video_analytics_service as mod
from app.services.video_analytics_service import (
    AnalyticsUnavailable,
    VideoAnalyticsService,
    aggregate,
    parse_progress_item,
)

NOW = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


def ago(**delta) -> str:
    return (NOW - timedelta(**delta)).isoformat()


def vid(vid_id, title=None, tier="BUILDER", status="PUBLISHED"):
    return {
        "id": vid_id,
        "title": title or f"Video {vid_id}",
        "slug": f"slug-{vid_id}",
        "status": status,
        "access_tier": tier,
    }


def rec(user, video, best=50, completed=False, when=None):
    return {
        "user_id": user,
        "video_id": video,
        "best": best,
        "completed": completed,
        "last_watched_at": when if when is not None else ago(days=1),
    }


@pytest.fixture(autouse=True)
def fresh_cache(monkeypatch):
    mod.reset_cache()
    monkeypatch.setattr(mod, "SCAN_PAUSE_SECONDS", 0)
    yield
    mod.reset_cache()


# ---------------------------------------------------------------------------
# parse_progress_item
# ---------------------------------------------------------------------------


class TestParseProgressItem:
    def base(self, **extra):
        item = {"PK": {"S": "USER#u1"}, "SK": {"S": "VIDEO#v1"}}
        item.update(extra)
        return item

    def test_new_style_record_uses_best_and_sticky_flag(self):
        item = self.base(
            percentComplete={"N": "20"},
            maxPercentComplete={"N": "95"},
            completed={"BOOL": False},
            everCompleted={"BOOL": True},
            lastWatchedAt={"S": "2026-01-01T00:00:00+00:00"},
        )
        assert parse_progress_item(item) == {
            "user_id": "u1",
            "video_id": "v1",
            "best": 95,
            "completed": True,
            "last_watched_at": "2026-01-01T00:00:00+00:00",
        }

    def test_legacy_record_falls_back_to_latest_values(self):
        parsed = parse_progress_item(
            self.base(percentComplete={"N": "72"}, completed={"BOOL": False})
        )
        assert parsed["best"] == 72
        assert parsed["completed"] is False
        assert parsed["last_watched_at"] is None

    def test_legacy_completed_record(self):
        parsed = parse_progress_item(
            self.base(percentComplete={"N": "100"}, completed={"BOOL": True})
        )
        assert parsed["completed"] is True

    def test_explicit_false_sticky_flag_wins_over_completed(self):
        parsed = parse_progress_item(
            self.base(everCompleted={"BOOL": False}, completed={"BOOL": True})
        )
        assert parsed["completed"] is False

    @pytest.mark.parametrize(
        "item",
        [
            {"PK": {"S": "USER#u"}, "SK": {"S": "CONTENT#x"}},
            {"PK": {"S": "BROADCAST"}, "SK": {"S": "VIDEO#v"}},
            {"PK": {"S": "USER#u"}},
            {},
        ],
    )
    def test_unrelated_items_are_ignored(self, item):
        assert parse_progress_item(item) is None

    def test_values_are_clamped_and_garbage_tolerated(self):
        assert (
            parse_progress_item(self.base(percentComplete={"N": "250"}))["best"] == 100
        )
        assert parse_progress_item(self.base(percentComplete={"N": "-5"}))["best"] == 0
        assert parse_progress_item(self.base(percentComplete={"N": "abc"}))["best"] == 0
        assert parse_progress_item(self.base())["best"] == 0


# ---------------------------------------------------------------------------
# aggregate
# ---------------------------------------------------------------------------


class TestAggregate:
    def test_per_video_stats(self):
        videos = [vid("a")]
        records = [
            rec("u1", "a", best=100, completed=True, when=ago(days=2)),
            rec("u2", "a", best=50, completed=False, when=ago(hours=1)),
            rec("u3", "a", best=30, completed=False, when=ago(days=40)),
        ]
        result = aggregate(videos, records, NOW)
        v = result["videos"][0]
        assert v["unique_viewers"] == 3
        assert v["completed"] == 1
        assert v["completion_rate"] == 33
        assert v["avg_best_progress"] == 60  # (100 + 50 + 30) / 3
        assert v["last_watched_at"] == ago(hours=1)
        assert v["access_tier"] == "BUILDER"

    def test_video_with_no_viewers_is_listed_with_zeros(self):
        result = aggregate([vid("a"), vid("b")], [rec("u1", "a")], NOW)
        by_id = {v["id"]: v for v in result["videos"]}
        assert by_id["b"]["unique_viewers"] == 0
        assert by_id["b"]["completed"] == 0
        assert by_id["b"]["completion_rate"] == 0
        assert by_id["b"]["avg_best_progress"] == 0
        assert by_id["b"]["last_watched_at"] is None

    def test_no_data_at_all(self):
        result = aggregate([], [], NOW)
        assert result["videos"] == []
        assert result["top_videos"] == []
        assert result["totals"] == {
            "distinct_viewers": 0,
            "active_7d": 0,
            "active_30d": 0,
            "completions": 0,
            "completion_rate": 0,
        }
        assert set(result["by_tier"]) == {"FREE", "BUILDER"}

    def test_progress_for_unknown_videos_is_ignored_everywhere(self):
        result = aggregate(
            [vid("a")], [rec("ghost", "deleted", best=100, completed=True)], NOW
        )
        assert result["totals"]["distinct_viewers"] == 0
        assert result["totals"]["active_7d"] == 0
        assert result["totals"]["completions"] == 0
        assert result["videos"][0]["unique_viewers"] == 0

    def test_member_watching_several_videos_counts_once_in_distinct_totals(self):
        videos = [vid("a"), vid("b"), vid("c")]
        records = [rec("u1", "a"), rec("u1", "b"), rec("u1", "c"), rec("u2", "a")]
        totals = aggregate(videos, records, NOW)["totals"]
        assert totals["distinct_viewers"] == 2
        assert totals["active_7d"] == 2

    def test_active_windows_are_per_member_and_inclusive(self):
        videos = [vid("a")]
        records = [
            rec("in7", "a", when=ago(days=7)),  # exactly on the boundary -> included
            rec("in30", "a", when=ago(days=20)),
            rec("edge30", "a", when=ago(days=30)),
            rec("old", "a", when=ago(days=31)),
            rec("never", "a", when=""),
            rec("bad", "a", when="not-a-date"),
        ]
        totals = aggregate(videos, records, NOW)["totals"]
        assert totals["active_7d"] == 1
        assert totals["active_30d"] == 3
        assert totals["distinct_viewers"] == 6

    def test_recent_activity_on_any_video_makes_member_active(self):
        videos = [vid("a"), vid("b")]
        records = [rec("u1", "a", when=ago(days=90)), rec("u1", "b", when=ago(days=1))]
        assert aggregate(videos, records, NOW)["totals"]["active_7d"] == 1

    def test_naive_timestamps_are_treated_as_utc(self):
        naive = (NOW - timedelta(days=1)).replace(tzinfo=None).isoformat()
        totals = aggregate([vid("a")], [rec("u1", "a", when=naive)], NOW)["totals"]
        assert totals["active_7d"] == 1

    def test_overall_completion_rate_is_over_member_video_pairs(self):
        videos = [vid("a"), vid("b")]
        records = [
            rec("u1", "a", completed=True),
            rec("u2", "a", completed=True),
            rec("u1", "b", completed=False),
            rec("u2", "b", completed=False),
        ]
        totals = aggregate(videos, records, NOW)["totals"]
        assert totals["completions"] == 2
        assert totals["completion_rate"] == 50

    def test_tier_split_and_unknown_tier_fails_closed_to_builder(self):
        videos = [
            vid("f", tier="FREE"),
            vid("b", tier="BUILDER"),
            vid("x", tier="WEIRD"),
        ]
        records = [
            rec("u1", "f", completed=True),
            rec("u2", "f"),
            rec("u1", "b", completed=True),
            rec("u1", "x"),
        ]
        result = aggregate(videos, records, NOW)
        assert result["by_tier"]["FREE"] == {
            "viewers": 2,
            "completions": 1,
            "completion_rate": 50,
        }
        assert result["by_tier"]["BUILDER"] == {
            "viewers": 2,
            "completions": 1,
            "completion_rate": 50,
        }
        assert {v["id"]: v["access_tier"] for v in result["videos"]}["x"] == "BUILDER"

    def test_top_videos_ordering_ties_and_limit(self):
        videos = [vid(str(i), title=f"T{i}") for i in range(8)]
        records = []
        # video i gets i viewers (video 0 has none)
        for i in range(1, 8):
            for u in range(i):
                records.append(rec(f"u{u}", str(i)))
        result = aggregate(videos, records, NOW)
        top_ids = [v["id"] for v in result["top_videos"]]
        assert top_ids == ["7", "6", "5", "4", "3"]
        assert "0" not in top_ids  # zero-viewer videos never appear in the top list

    def test_top_videos_tie_breaks_by_completion_rate_then_title(self):
        videos = [
            vid("a", title="Zeta"),
            vid("b", title="Alpha"),
            vid("c", title="Beta"),
        ]
        records = [
            rec("u1", "a", completed=True),
            rec("u1", "b", completed=False),
            rec("u1", "c", completed=False),
        ]
        top = [v["title"] for v in aggregate(videos, records, NOW)["top_videos"]]
        assert top == ["Zeta", "Alpha", "Beta"]  # completion first, then title

    def test_default_video_order_is_viewers_desc_then_title(self):
        videos = [
            vid("a", title="b-video"),
            vid("b", title="a-video"),
            vid("c", title="c-video"),
        ]
        records = [rec("u1", "c"), rec("u2", "c"), rec("u1", "a"), rec("u1", "b")]
        order = [v["id"] for v in aggregate(videos, records, NOW)["videos"]]
        assert order == ["c", "b", "a"]

    def test_duplicate_member_video_records_count_once(self):
        records = [rec("u1", "a", best=10), rec("u1", "a", best=90)]
        v = aggregate([vid("a")], records, NOW)["videos"][0]
        assert v["unique_viewers"] == 1

    def test_output_contains_no_member_identifiers(self):
        records = [rec("secret-member-id-123", "a", completed=True)]
        payload = json.dumps(aggregate([vid("a")], records, NOW))
        assert "secret-member-id-123" not in payload


@hyp_settings(max_examples=60, deadline=None)
@given(
    records=st.lists(
        st.fixed_dictionaries(
            {
                "user_id": st.sampled_from([f"u{i}" for i in range(6)]),
                "video_id": st.sampled_from(["a", "b", "c", "ghost"]),
                "best": st.integers(min_value=0, max_value=100),
                "completed": st.booleans(),
                "last_watched_at": st.one_of(
                    st.none(), st.sampled_from([ago(days=d) for d in (0, 3, 10, 45)])
                ),
            }
        ),
        max_size=40,
    )
)
def test_aggregate_invariants(records):
    videos = [vid("a"), vid("b", tier="FREE"), vid("c")]
    result = aggregate(videos, records, NOW)
    pairs = 0
    for v in result["videos"]:
        assert 0 <= v["completion_rate"] <= 100
        assert 0 <= v["avg_best_progress"] <= 100
        assert v["completed"] <= v["unique_viewers"]
        pairs += v["unique_viewers"]
    t = result["totals"]
    assert 0 <= t["completion_rate"] <= 100
    assert t["distinct_viewers"] <= len(records)
    assert t["active_7d"] <= t["active_30d"] <= t["distinct_viewers"]
    assert t["completions"] <= pairs
    assert sum(x["viewers"] for x in result["by_tier"].values()) == pairs
    assert len(result["top_videos"]) <= 5


# ---------------------------------------------------------------------------
# Scan against moto
# ---------------------------------------------------------------------------


def make_settings():
    return SimpleNamespace(progress_table="progress", videos_table="videos")


@pytest.fixture
def aws():
    env = {
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_DEFAULT_REGION": "us-east-2",
    }
    with patch.dict(os.environ, env), mock_aws():
        raw = boto3.client("dynamodb", region_name="us-east-2")
        for name in ("progress", "videos"):
            raw.create_table(
                TableName=name,
                BillingMode="PAY_PER_REQUEST",
                AttributeDefinitions=[
                    {"AttributeName": "PK", "AttributeType": "S"},
                    {"AttributeName": "SK", "AttributeType": "S"},
                ],
                KeySchema=[
                    {"AttributeName": "PK", "KeyType": "HASH"},
                    {"AttributeName": "SK", "KeyType": "RANGE"},
                ],
            )
        yield raw


def put_video(raw, vid_id, tier="BUILDER", status="PUBLISHED"):
    raw.put_item(
        TableName="videos",
        Item={
            "PK": {"S": f"VIDEO#{vid_id}"},
            "SK": {"S": "METADATA"},
            "id": {"S": vid_id},
            "title": {"S": f"Title {vid_id}"},
            "slug": {"S": f"slug-{vid_id}"},
            "status": {"S": status},
            "accessTier": {"S": tier},
            "description": {"S": "not needed"},
        },
    )


def put_progress(raw, user, video, pct=50, completed=False, **extra):
    item = {
        "PK": {"S": f"USER#{user}"},
        "SK": {"S": f"VIDEO#{video}"},
        "percentComplete": {"N": str(pct)},
        "completed": {"BOOL": completed},
        "lastWatchedAt": {"S": datetime.now(timezone.utc).isoformat()},
    }
    item.update(extra)
    raw.put_item(TableName="progress", Item=item)


class CountingClient:
    """Wraps a real client, counting and optionally slowing scans."""

    def __init__(self, raw, delay=0.0):
        self.raw = raw
        self.delay = delay
        self.scans = []
        self._lock = threading.Lock()

    def scan(self, **kwargs):
        with self._lock:
            self.scans.append(kwargs)
        if self.delay:
            time.sleep(self.delay)
        return self.raw.scan(**kwargs)

    def progress_scans(self):
        return [s for s in self.scans if s["TableName"] == "progress"]


class TestScan:
    def test_end_to_end_with_mixed_records(self, aws):
        put_video(aws, "v1", tier="FREE")
        put_video(aws, "v2")
        put_progress(
            aws,
            "u1",
            "v1",
            100,
            True,
            maxPercentComplete={"N": "100"},
            everCompleted={"BOOL": True},
        )
        put_progress(aws, "u2", "v1", 40)
        put_progress(aws, "u1", "v2", 70)
        put_progress(aws, "u1", "deleted-video", 100, True)
        # unrelated items in the shared progress table must be ignored
        aws.put_item(
            TableName="progress",
            Item={"PK": {"S": "USER#u1"}, "SK": {"S": "CONTENT#intro"}},
        )
        aws.put_item(
            TableName="progress",
            Item={"PK": {"S": "USER#u1"}, "SK": {"S": "JOURNEY#x"}},
        )
        aws.put_item(
            TableName="progress",
            Item={"PK": {"S": "PROFILE#u1"}, "SK": {"S": "VIDEO#v1"}},
        )

        result = VideoAnalyticsService(make_settings()).get_analytics()

        assert result["stale"] is False
        assert result["generated_at"]
        assert result["totals"]["distinct_viewers"] == 2
        by_id = {v["id"]: v for v in result["videos"]}
        assert by_id["v1"]["unique_viewers"] == 2
        assert by_id["v1"]["completed"] == 1
        assert by_id["v2"]["unique_viewers"] == 1
        assert result["by_tier"]["FREE"]["viewers"] == 2

    def test_scan_is_paced_projected_and_eventually_consistent(self, aws, monkeypatch):
        monkeypatch.setattr(mod, "SCAN_PAGE_LIMIT", 3)
        put_video(aws, "v1")
        for i in range(10):
            put_progress(aws, f"u{i}", "v1")
        client = CountingClient(aws)

        result = VideoAnalyticsService(make_settings(), client=client).get_analytics()

        assert result["videos"][0]["unique_viewers"] == 10  # every page was read
        scans = client.progress_scans()
        assert len(scans) >= 4  # 10+ items at 3 per page
        for scan in scans:
            assert scan["Limit"] == 3
            assert scan["ConsistentRead"] is False
            assert "ProjectionExpression" in scan
            assert "lastWatchedAt" in scan["ProjectionExpression"]
            assert "description" not in scan["ProjectionExpression"]

    def test_pauses_between_pages(self, aws, monkeypatch):
        monkeypatch.setattr(mod, "SCAN_PAGE_LIMIT", 2)
        monkeypatch.setattr(mod, "SCAN_PAUSE_SECONDS", 0.01)
        put_video(aws, "v1")
        for i in range(6):
            put_progress(aws, f"u{i}", "v1")
        with patch.object(mod.time, "sleep") as sleep:
            VideoAnalyticsService(make_settings()).get_analytics()
        assert sleep.call_count >= 2
        assert all(c.args == (0.01,) for c in sleep.call_args_list)

    def test_time_budget_aborts_a_slow_scan(self, aws, monkeypatch):
        monkeypatch.setattr(mod, "SCAN_PAGE_LIMIT", 2)
        monkeypatch.setattr(mod, "SCAN_BUDGET_SECONDS", -1)
        put_video(aws, "v1")
        for i in range(6):
            put_progress(aws, f"u{i}", "v1")
        client = CountingClient(aws)
        with pytest.raises(AnalyticsUnavailable):
            VideoAnalyticsService(make_settings(), client=client).get_analytics()
        assert len(client.progress_scans()) == 1  # stopped after the first page

    def test_empty_tables(self, aws):
        result = VideoAnalyticsService(make_settings()).get_analytics()
        assert result["videos"] == []
        assert result["totals"]["distinct_viewers"] == 0


# ---------------------------------------------------------------------------
# Caching: fresh / stale-while-revalidate / blocking / single-flight
# ---------------------------------------------------------------------------


def set_cache(age_seconds, result=None):
    with mod._state_lock:
        mod._state.update(
            result=result
            or {"totals": {}, "by_tier": {}, "top_videos": [], "videos": []},
            ts=time.time() - age_seconds,
            generated_at=ago(seconds=int(age_seconds)),
        )


def wait_until(predicate, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


class TestCaching:
    def test_fresh_result_is_served_without_scanning(self, aws):
        put_video(aws, "v1")
        client = CountingClient(aws)
        svc = VideoAnalyticsService(make_settings(), client=client)
        svc.get_analytics()
        scans_after_first = len(client.scans)
        for _ in range(5):
            assert svc.get_analytics()["stale"] is False
        assert len(client.scans) == scans_after_first  # no extra scans

    def test_cache_is_shared_across_service_instances(self, aws):
        put_video(aws, "v1")
        client = CountingClient(aws)
        VideoAnalyticsService(make_settings(), client=client).get_analytics()
        before = len(client.scans)
        VideoAnalyticsService(make_settings(), client=client).get_analytics()
        assert len(client.scans) == before

    def test_stale_result_is_served_immediately_with_one_background_refresh(self, aws):
        put_video(aws, "v1")
        set_cache(age_seconds=10 * 60)  # between 5 min and 1 h
        client = CountingClient(aws, delay=0.2)
        svc = VideoAnalyticsService(make_settings(), client=client)

        started = time.time()
        results = [svc.get_analytics() for _ in range(5)]
        assert time.time() - started < 0.15  # nobody waited for the scan
        assert all(r["stale"] is True for r in results)

        # exactly one refresh runs, then the cache is fresh again
        assert wait_until(
            lambda: len(client.progress_scans()) == 1 and not mod._compute_lock.locked()
        )
        assert svc.get_analytics()["stale"] is False
        assert len(client.progress_scans()) == 1

    def test_very_old_result_blocks_for_a_fresh_one(self, aws):
        put_video(aws, "v1")
        set_cache(age_seconds=2 * 60 * 60)
        result = VideoAnalyticsService(
            make_settings(), client=CountingClient(aws)
        ).get_analytics()
        assert result["stale"] is False
        assert [v["id"] for v in result["videos"]] == ["v1"]

    def test_concurrent_cold_requests_trigger_exactly_one_scan(self, aws):
        put_video(aws, "v1")
        put_progress(aws, "u1", "v1")
        client = CountingClient(aws, delay=0.2)
        results, errors = [], []

        def call():
            try:
                results.append(
                    VideoAnalyticsService(
                        make_settings(), client=client
                    ).get_analytics()
                )
            except Exception as e:  # pragma: no cover - failure path
                errors.append(e)

        threads = [threading.Thread(target=call) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(10)

        assert not errors
        assert len(results) == 10
        assert len(client.progress_scans()) == 1
        assert all(r["videos"][0]["unique_viewers"] == 1 for r in results)

    def test_failed_background_refresh_keeps_serving_stale(self, aws):
        set_cache(age_seconds=10 * 60)
        client = MagicMock()
        client.scan.side_effect = RuntimeError("dynamodb down")
        svc = VideoAnalyticsService(make_settings(), client=client)
        assert svc.get_analytics()["stale"] is True
        assert wait_until(lambda: client.scan.called and not mod._compute_lock.locked())
        again = svc.get_analytics()
        assert again["stale"] is True  # still the old data, still served

    def test_failed_blocking_refresh_serves_old_result_as_stale(self):
        set_cache(age_seconds=2 * 60 * 60)
        client = MagicMock()
        client.scan.side_effect = RuntimeError("dynamodb down")
        result = VideoAnalyticsService(make_settings(), client=client).get_analytics()
        assert result["stale"] is True

    def test_no_cache_and_failure_raises_unavailable(self):
        client = MagicMock()
        client.scan.side_effect = RuntimeError("dynamodb down")
        with pytest.raises(AnalyticsUnavailable):
            VideoAnalyticsService(make_settings(), client=client).get_analytics()

    def test_failure_is_not_cached_so_next_call_retries(self, aws):
        put_video(aws, "v1")
        bad = MagicMock()
        bad.scan.side_effect = RuntimeError("down")
        with pytest.raises(AnalyticsUnavailable):
            VideoAnalyticsService(make_settings(), client=bad).get_analytics()
        ok = VideoAnalyticsService(
            make_settings(), client=CountingClient(aws)
        ).get_analytics()
        assert ok["videos"][0]["id"] == "v1"

    def test_background_refresh_does_not_start_while_another_runs(self, aws):
        put_video(aws, "v1")
        set_cache(age_seconds=10 * 60)
        client = CountingClient(aws, delay=0.3)
        svc = VideoAnalyticsService(make_settings(), client=client)
        assert mod._compute_lock.acquire(blocking=False)  # simulate a refresh in flight
        try:
            for _ in range(5):
                svc.get_analytics()
            time.sleep(0.1)
            assert client.scans == []  # the in-flight refresh owns the scan
        finally:
            mod._compute_lock.release()
