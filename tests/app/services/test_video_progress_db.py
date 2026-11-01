"""Unit tests for app.services.video_progress_db.VideoProgressDB.

The service constructs a boto3 DynamoDB client in __init__. Tests patch the
module's boto3.client so no real AWS calls happen, then reassign svc._client
to the mock for direct call assertions.
"""

import boto3
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import video_progress_db as mod
from app.services.video_progress_db import VideoProgressDB


def _client_error(code: str = "InternalServerError") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


@pytest.fixture
def service():
    client = MagicMock()
    settings = MagicMock(progress_table="test-progress")
    with patch.object(mod.boto3, "client", return_value=client):
        svc = VideoProgressDB(settings)
    svc._client = client
    return svc


class TestGetProgress:
    def test_returns_item(self, service):
        service._client.get_item.return_value = {"Item": {"PK": {"S": "USER#u"}}}
        result = service.get_progress("u", "v")
        assert result == {"PK": {"S": "USER#u"}}
        service._client.get_item.assert_called_once_with(
            TableName="test-progress",
            Key={
                "PK": {"S": "USER#u"},
                "SK": {"S": "VIDEO#v"},
            },
        )

    def test_returns_none_when_absent(self, service):
        service._client.get_item.return_value = {}
        assert service.get_progress("u", "v") is None

    def test_client_error_raises(self, service):
        service._client.get_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_progress("u", "v")


def _data(percent, completed=None, position=None, when="2026-01-03T00:00:00+00:00"):
    return {
        "position_seconds": position if position is not None else float(percent),
        "duration_seconds": 100,
        "percent_complete": percent,
        "completed": percent >= 90 if completed is None else completed,
        "last_watched_at": when,
        "updated_at": when,
    }


@pytest.fixture
def real():
    """VideoProgressDB over moto DynamoDB, wrapped to count client calls."""
    import os
    from moto import mock_aws

    env = {
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_DEFAULT_REGION": "us-east-2",
    }
    with patch.dict(os.environ, env), mock_aws():
        raw = boto3.client("dynamodb", region_name="us-east-2")
        raw.create_table(
            TableName="test-progress",
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
        svc = VideoProgressDB(MagicMock(progress_table="test-progress"))
        svc._client = MagicMock(wraps=raw)
        svc.raw = raw
        yield svc


def _item(svc, user="u", video="v"):
    return svc.raw.get_item(
        TableName="test-progress",
        Key={"PK": {"S": f"USER#{user}"}, "SK": {"S": f"VIDEO#{video}"}},
    )["Item"]


def _n(item, name):
    return int(float(item[name]["N"]))


class TestSaveProgress:
    """Progress writes: best-progress high-water mark, sticky completion, no reads."""

    def test_first_save_creates_record_with_all_fields(self, real):
        real.save_progress("u", "v", _data(20, position=20.5))
        item = _item(real)
        assert item["positionSeconds"] == {"N": "20.5"}
        assert item["durationSeconds"] == {"N": "100"}
        assert _n(item, "percentComplete") == 20
        assert item["completed"] == {"BOOL": False}
        assert item["lastWatchedAt"] == {"S": "2026-01-03T00:00:00+00:00"}
        assert item["updatedAt"] == {"S": "2026-01-03T00:00:00+00:00"}
        assert _n(item, "maxPercentComplete") == 20
        assert "everCompleted" not in item  # never completed -> not set

    def test_watching_forward_is_one_write_and_no_reads(self, real):
        for pct in (10, 25, 40, 60):
            real.save_progress("u", "v", _data(pct))
        assert real._client.update_item.call_count == 4  # exactly one write per save
        real._client.get_item.assert_not_called()
        real._client.query.assert_not_called()
        real._client.scan.assert_not_called()
        real._client.put_item.assert_not_called()
        assert _n(_item(real), "maxPercentComplete") == 60

    def test_seeking_back_keeps_best_but_updates_current_position(self, real):
        real.save_progress("u", "v", _data(70))
        real._client.update_item.reset_mock()
        real.save_progress("u", "v", _data(30, position=30.0))
        item = _item(real)
        assert _n(item, "maxPercentComplete") == 70  # high-water mark kept
        assert _n(item, "percentComplete") == 30  # Continue watching sees latest
        assert item["positionSeconds"] == {"N": "30.0"}
        # one failed conditional attempt + one fallback write, still no reads
        assert real._client.update_item.call_count == 2
        real._client.get_item.assert_not_called()

    def test_best_progress_never_decreases(self, real):
        for pct in (50, 80, 20, 65, 10, 79):
            real.save_progress("u", "v", _data(pct))
        assert _n(_item(real), "maxPercentComplete") == 80

    def test_equal_percent_does_not_change_best(self, real):
        real.save_progress("u", "v", _data(40))
        real.save_progress("u", "v", _data(40))
        assert _n(_item(real), "maxPercentComplete") == 40

    def test_completion_is_sticky_when_viewer_seeks_back(self, real):
        real.save_progress("u", "v", _data(95))
        assert _item(real)["everCompleted"] == {"BOOL": True}
        real.save_progress("u", "v", _data(20))
        item = _item(real)
        assert item["completed"] == {"BOOL": False}  # latest state, as before
        assert item["everCompleted"] == {"BOOL": True}  # sticky
        assert _n(item, "maxPercentComplete") == 95

    def test_sticky_flag_survives_many_low_saves(self, real):
        real.save_progress("u", "v", _data(100))
        for pct in (5, 0, 50, 89):
            real.save_progress("u", "v", _data(pct))
        assert _item(real)["everCompleted"] == {"BOOL": True}

    def test_rewatch_completion_after_dip_stays_true(self, real):
        real.save_progress("u", "v", _data(100))
        real.save_progress("u", "v", _data(50))
        real.save_progress("u", "v", _data(92))  # behind best but completed again
        item = _item(real)
        assert item["everCompleted"] == {"BOOL": True}
        assert _n(item, "maxPercentComplete") == 100

    def test_exactly_threshold_counts(self, real):
        real.save_progress("u", "v", _data(90))
        assert _item(real)["everCompleted"] == {"BOOL": True}

    def test_save_never_erases_other_fields(self, real):
        real.save_progress("u", "v", _data(95))
        real.save_progress("u", "v", _data(10))
        item = _item(real)
        for field in (
            "positionSeconds",
            "durationSeconds",
            "percentComplete",
            "completed",
            "lastWatchedAt",
            "updatedAt",
            "maxPercentComplete",
            "everCompleted",
        ):
            assert field in item

    def test_users_and_videos_are_independent(self, real):
        real.save_progress("a", "v1", _data(95))
        real.save_progress("a", "v2", _data(10))
        real.save_progress("b", "v1", _data(30))
        assert _item(real, "a", "v1")["everCompleted"] == {"BOOL": True}
        assert "everCompleted" not in _item(real, "a", "v2")
        assert "everCompleted" not in _item(real, "b", "v1")
        assert _n(_item(real, "b", "v1"), "maxPercentComplete") == 30

    # --- legacy records (written before these fields existed) ---

    def _legacy(self, svc, percent, completed):
        svc.raw.put_item(
            TableName="test-progress",
            Item={
                "PK": {"S": "USER#u"},
                "SK": {"S": "VIDEO#v"},
                "positionSeconds": {"N": str(percent)},
                "durationSeconds": {"N": "100"},
                "percentComplete": {"N": str(percent)},
                "completed": {"BOOL": completed},
                "lastWatchedAt": {"S": "2025-12-01T00:00:00+00:00"},
                "updatedAt": {"S": "2025-12-01T00:00:00+00:00"},
            },
        )

    def test_legacy_completed_record_then_seek_back_keeps_completion(self, real):
        self._legacy(real, 100, True)
        real.save_progress("u", "v", _data(20))
        item = _item(real)
        assert _n(item, "maxPercentComplete") == 100  # seeded from old percent
        assert item["everCompleted"] == {"BOOL": True}  # seeded from old completed
        assert _n(item, "percentComplete") == 20

    def test_legacy_in_progress_record_then_seek_back(self, real):
        self._legacy(real, 60, False)
        real.save_progress("u", "v", _data(40))
        item = _item(real)
        assert _n(item, "maxPercentComplete") == 60
        assert item["everCompleted"] == {"BOOL": False}

    def test_legacy_record_moving_forward_upgrades_in_one_write(self, real):
        self._legacy(real, 60, False)
        real._client.update_item.reset_mock()
        real.save_progress("u", "v", _data(75))
        assert real._client.update_item.call_count == 1
        assert _n(_item(real), "maxPercentComplete") == 75

    def test_legacy_completed_record_finishing_again(self, real):
        self._legacy(real, 95, True)
        real.save_progress("u", "v", _data(100))
        item = _item(real)
        assert _n(item, "maxPercentComplete") == 100
        assert item["everCompleted"] == {"BOOL": True}

    # --- failure handling (mocked client) ---

    def test_unexpected_best_progress_failure_still_saves_progress(self, service):
        service._client.update_item.side_effect = [
            _client_error("ProvisionedThroughputExceededException"),
            {},
        ]
        service.save_progress("u", "v", _data(95))
        assert service._client.update_item.call_count == 2
        fallback = service._client.update_item.call_args.kwargs
        expr = fallback["UpdateExpression"]
        assert "positionSeconds = :pos" in expr
        assert "everCompleted = :true" in expr
        # the safe fallback must not reference attributes that may not exist
        assert "if_not_exists" not in expr
        assert "ConditionExpression" not in fallback

    def test_behind_best_fallback_preserves_high_water_mark(self, service):
        service._client.update_item.side_effect = [
            _client_error("ConditionalCheckFailedException"),
            {},
        ]
        service.save_progress("u", "v", _data(30))
        expr = service._client.update_item.call_args.kwargs["UpdateExpression"]
        assert (
            "maxPercentComplete = if_not_exists(maxPercentComplete, percentComplete)"
            in expr
        )
        assert "everCompleted = if_not_exists(everCompleted, completed)" in expr
        assert "maxPercentComplete = :pct" not in expr  # never overwritten

    def test_progress_fields_failure_raises(self, service):
        service._client.update_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.save_progress("u", "v", _data(50))

    def test_never_uses_whole_record_put(self, service):
        service.save_progress("u", "v", _data(50))
        service._client.put_item.assert_not_called()

    def test_continue_watching_query_still_returns_saved_items(self, real):
        real.save_progress("u", "a", _data(40))
        real.save_progress("u", "b", _data(95))
        items = real.get_user_video_progress("u")
        assert {i["SK"]["S"] for i in items} == {"VIDEO#a", "VIDEO#b"}
        by = {i["SK"]["S"]: i for i in items}
        assert by["VIDEO#a"]["percentComplete"] == {"N": "40"}
        assert by["VIDEO#b"]["completed"] == {"BOOL": True}


class TestGetUserVideoProgress:
    def test_returns_items(self, service):
        items = [{"SK": {"S": "VIDEO#a"}}, {"SK": {"S": "VIDEO#b"}}]
        service._client.query.return_value = {"Items": items}
        result = service.get_user_video_progress("u")
        assert result == items
        kwargs = service._client.query.call_args.kwargs
        assert kwargs["TableName"] == "test-progress"
        assert kwargs["ExpressionAttributeValues"][":pk"] == {"S": "USER#u"}
        assert kwargs["ExpressionAttributeValues"][":sk_prefix"] == {"S": "VIDEO#"}

    def test_returns_empty_when_no_items(self, service):
        service._client.query.return_value = {}
        assert service.get_user_video_progress("u") == []

    def test_client_error_raises(self, service):
        service._client.query.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_user_video_progress("u")
