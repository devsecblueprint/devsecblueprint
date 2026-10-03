"""Unit tests for app.services.progress_db.ProgressDB.

Covers progress save/delete/query, user stats aggregation incl. streak math,
capstone submission/review, last-active, delete-all, badges delegation, and
Builder Journey operations (incl. the conditional meta-write path).
"""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import progress_db as mod
from app.services.progress_db import ProgressDB


def _client_error(code: str = "InternalServerError") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


@pytest.fixture
def service():
    client = MagicMock()
    settings = MagicMock(
        progress_table="test-progress",
        user_state_table="test-user-state",
        content_registry_bucket="bucket",
        total_module_pages=100,
    )
    with patch.object(mod.boto3, "client", return_value=client):
        svc = ProgressDB(settings)
    svc._client = client
    return svc


class TestSaveDeleteProgress:
    def test_save_puts_item(self, service):
        service.save_progress("u", "intro")
        item = service._client.put_item.call_args.kwargs["Item"]
        assert item["PK"] == {"S": "USER#u"}
        assert item["SK"] == {"S": "CONTENT#intro"}
        assert item["status"] == {"S": "complete"}

    def test_save_raises_on_error(self, service):
        service._client.put_item.side_effect = _client_error("ValidationException")
        with pytest.raises(Exception, match="Failed to save progress"):
            service.save_progress("u", "intro")

    def test_delete_calls_delete_item(self, service):
        service.delete_progress("u", "intro")
        key = service._client.delete_item.call_args.kwargs["Key"]
        assert key["SK"] == {"S": "CONTENT#intro"}

    def test_delete_raises_on_error(self, service):
        service._client.delete_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.delete_progress("u", "intro")


class TestGetUserProgress:
    def test_parses_items(self, service):
        service._client.query.return_value = {
            "Items": [
                {"SK": {"S": "CONTENT#intro"}, "status": {"S": "complete"}, "completed_at": {"S": "2026-01-01"}}
            ]
        }
        result = service.get_user_progress("u")
        assert result == [{"content_id": "intro", "status": "complete", "completed_at": "2026-01-01"}]

    def test_resource_not_found_returns_empty(self, service):
        service._client.query.side_effect = _client_error("ResourceNotFoundException")
        assert service.get_user_progress("u") == []

    def test_other_error_raises(self, service):
        service._client.query.side_effect = _client_error("InternalServerError")
        with pytest.raises(Exception, match="Failed to query progress"):
            service.get_user_progress("u")


class TestStreakMath:
    def test_no_items_zero_streaks(self, service):
        assert service._calculate_streaks([]) == {"current_streak": 0, "longest_streak": 0}

    def test_items_without_valid_dates(self, service):
        result = service._calculate_streaks([{"content_id": "x"}])  # no completed_at
        assert result == {"current_streak": 0, "longest_streak": 0}

    def test_consecutive_days_streak(self, service):
        today = datetime.now(timezone.utc).date()
        items = [
            {"completed_at": today.isoformat()},
            {"completed_at": (today - timedelta(days=1)).isoformat()},
            {"completed_at": (today - timedelta(days=2)).isoformat()},
        ]
        result = service._calculate_streaks(items)
        assert result["current_streak"] == 3
        assert result["longest_streak"] == 3

    def test_broken_streak(self, service):
        today = datetime.now(timezone.utc).date()
        items = [
            {"completed_at": today.isoformat()},
            {"completed_at": (today - timedelta(days=5)).isoformat()},
            {"completed_at": (today - timedelta(days=6)).isoformat()},
        ]
        result = service._calculate_streaks(items)
        assert result["current_streak"] == 1
        assert result["longest_streak"] == 2

    def test_completion_percentage_capped(self, service):
        assert service._calculate_completion_percentage(50) == 50
        assert service._calculate_completion_percentage(200) == 100

    def test_completion_percentage_zero_total(self, service):
        service._settings.total_module_pages = 0
        assert service._calculate_completion_percentage(5) == 0


class TestUserStats:
    def test_aggregates(self, service):
        today = datetime.now(timezone.utc).date().isoformat()

        def query(**kwargs):
            sk = kwargs["ExpressionAttributeValues"][":sk_prefix"]["S"]
            if sk == "CONTENT#":
                return {"Items": [{"SK": {"S": "CONTENT#a"}, "completed_at": {"S": today}}]}
            if sk == "MODULE#":
                if kwargs.get("Select") == "COUNT":
                    return {"Count": 3}
                return {"Items": [{"score": {"N": "100"}}]}
            if sk == "WALKTHROUGH#":
                return {"Items": [{"status": {"S": "completed"}}]}
            if sk == "CAPSTONE_SUBMISSION#":
                return {"Count": 1}
            return {}

        service._client.query.side_effect = query
        stats = service.get_user_stats("u")
        assert stats["completed_count"] == 1
        assert stats["quizzes_passed"] == 3
        assert stats["walkthroughs_completed"] == 1
        assert stats["perfect_quiz_achieved"] is True
        assert stats["capstone_submissions"] == 1
        assert stats["current_streak"] == 1

    def test_count_helpers_swallow_errors(self, service):
        service._client.query.side_effect = _client_error()
        assert service._count_quizzes_passed("u") == 0
        assert service._count_walkthroughs_completed("u") == 0
        assert service._check_perfect_quiz("u") is False
        assert service._count_capstone_submissions("u") == 0


class TestRecentActivities:
    def test_sorts_and_limits(self, service):
        service._client.query.return_value = {
            "Items": [
                {"SK": {"S": "CONTENT#a"}, "completed_at": {"S": "2026-01-01"}},
                {"SK": {"S": "CONTENT#b"}, "completed_at": {"S": "2026-03-01"}},
                {"SK": {"S": "CONTENT#c"}, "completed_at": {"S": "2026-02-01"}},
            ]
        }
        result = service.get_recent_activities("u", limit=2)
        assert [r["content_id"] for r in result] == ["b", "c"]

    def test_empty(self, service):
        service._client.query.return_value = {"Items": []}
        assert service.get_recent_activities("u") == []


class TestCapstone:
    def test_save_submission(self, service):
        service.save_capstone_submission("u", "cap", "https://r", "ghuser", "repo", bitbucket_username="bb")
        item = service._client.put_item.call_args.kwargs["Item"]
        assert item["SK"] == {"S": "CAPSTONE_SUBMISSION#cap"}
        assert item["status"] == {"S": "pending_review"}
        assert item["bitbucket_username"] == {"S": "bb"}

    def test_save_submission_raises(self, service):
        service._client.put_item.side_effect = _client_error()
        with pytest.raises(Exception, match="Failed to save capstone submission"):
            service.save_capstone_submission("u", "cap", "r", "g", "rn")

    def test_get_submission(self, service):
        service._client.get_item.return_value = {"Item": {"repo_url": {"S": "https://r"}, "status": {"S": "pending"}}}
        result = service.get_capstone_submission("u", "cap")
        assert result["repo_url"] == "https://r"

    def test_get_submission_missing(self, service):
        service._client.get_item.return_value = {}
        assert service.get_capstone_submission("u", "cap") is None

    def test_get_submission_raises(self, service):
        service._client.get_item.side_effect = _client_error()
        with pytest.raises(Exception, match="Failed to get capstone submission"):
            service.get_capstone_submission("u", "cap")

    def test_get_review(self, service):
        service._client.get_item.return_value = {"Item": {"feedback": {"S": "good"}}}
        assert service.get_capstone_review("u", "cap")["feedback"] == "good"

    def test_get_review_missing(self, service):
        service._client.get_item.return_value = {}
        assert service.get_capstone_review("u", "cap") is None

    def test_get_review_raises(self, service):
        service._client.get_item.side_effect = _client_error()
        with pytest.raises(Exception, match="Failed to get capstone review"):
            service.get_capstone_review("u", "cap")


class TestLastActive:
    def test_save(self, service):
        service.save_last_active("u", "p1", "/learn/x")
        kwargs = service._client.put_item.call_args.kwargs
        assert kwargs["TableName"] == "test-user-state"
        assert kwargs["Item"]["page_id"] == {"S": "p1"}

    def test_save_raises(self, service):
        service._client.put_item.side_effect = _client_error()
        with pytest.raises(Exception, match="Failed to save last active"):
            service.save_last_active("u", "p", "s")

    def test_get_found(self, service):
        service._client.get_item.return_value = {"Item": {"page_id": {"S": "p1"}, "page_slug": {"S": "/x"}}}
        assert service.get_last_active("u") == {"page_id": "p1", "page_slug": "/x"}

    def test_get_missing_returns_nones(self, service):
        service._client.get_item.return_value = {}
        assert service.get_last_active("u") == {"page_id": None, "page_slug": None}

    def test_get_raises(self, service):
        service._client.get_item.side_effect = _client_error()
        with pytest.raises(Exception, match="Failed to get last active"):
            service.get_last_active("u")


class TestDeleteAll:
    def test_deletes_each_item(self, service):
        service._client.query.return_value = {
            "Items": [
                {"PK": {"S": "USER#u"}, "SK": {"S": "CONTENT#a"}},
                {"PK": {"S": "USER#u"}, "SK": {"S": "MODULE#b"}},
            ]
        }
        service.delete_all_user_progress("u")
        assert service._client.delete_item.call_count == 2

    def test_raises_on_error(self, service):
        service._client.query.side_effect = _client_error()
        with pytest.raises(Exception, match="Failed to delete progress"):
            service.delete_all_user_progress("u")


class TestBadgesDelegation:
    def test_delegates_to_badge_service(self, service):
        with patch("app.services.badge_service.calculate_user_badges", return_value=[{"id": "b1"}]) as calc, \
                patch.object(service, "get_user_progress", return_value=[]), \
                patch.object(service, "get_user_stats", return_value={}):
            result = service.get_user_badges("u")
        assert result == [{"id": "b1"}]
        assert calc.call_args.kwargs["table_name"] == "test-progress"
        assert calc.call_args.kwargs["s3_bucket"] == "bucket"


class TestJourney:
    def test_get_journey_progress(self, service):
        service._client.query.return_value = {
            "Items": [
                {"SK": {"S": "JOURNEY#task1"}, "status": {"S": "completed"}, "phase": {"N": "2"}, "auto_completed": {"BOOL": True}}
            ]
        }
        result = service.get_journey_progress("u")
        assert result[0]["task_id"] == "task1"
        assert result[0]["phase"] == 2
        assert result[0]["auto_completed"] is True

    def test_get_journey_resource_not_found(self, service):
        service._client.query.side_effect = _client_error("ResourceNotFoundException")
        assert service.get_journey_progress("u") == []

    def test_get_journey_other_error_raises(self, service):
        service._client.query.side_effect = _client_error("InternalServerError")
        with pytest.raises(Exception, match="Failed to query journey progress"):
            service.get_journey_progress("u")

    def test_save_task(self, service):
        service.save_journey_task("u", "task1", phase=3, auto_completed=True)
        item = service._client.put_item.call_args.kwargs["Item"]
        assert item["SK"] == {"S": "JOURNEY#task1"}
        assert item["phase"] == {"N": "3"}

    def test_save_task_raises(self, service):
        service._client.put_item.side_effect = _client_error()
        with pytest.raises(Exception, match="Failed to save journey task"):
            service.save_journey_task("u", "t", 1)

    def test_is_task_complete_true(self, service):
        service._client.get_item.return_value = {"Item": {"SK": {"S": "JOURNEY#t"}}}
        assert service.is_journey_task_complete("u", "t") is True

    def test_is_task_complete_false(self, service):
        service._client.get_item.return_value = {}
        assert service.is_journey_task_complete("u", "t") is False

    def test_is_task_complete_error_false(self, service):
        service._client.get_item.side_effect = _client_error()
        assert service.is_journey_task_complete("u", "t") is False

    def test_delete_task(self, service):
        service.delete_journey_task("u", "t")
        assert service._client.delete_item.called

    def test_delete_task_raises(self, service):
        service._client.delete_item.side_effect = _client_error()
        with pytest.raises(Exception, match="Failed to delete journey task"):
            service.delete_journey_task("u", "t")

    def test_save_meta_new(self, service):
        ts = service.save_journey_meta("u")
        assert ts  # returns timestamp
        kwargs = service._client.put_item.call_args.kwargs
        assert kwargs["ConditionExpression"] == "attribute_not_exists(PK)"

    def test_save_meta_existing_returns_stored(self, service):
        service._client.put_item.side_effect = _client_error("ConditionalCheckFailedException")
        service._client.get_item.return_value = {"Item": {"started_at": {"S": "2026-01-01"}}}
        ts = service.save_journey_meta("u")
        assert ts == "2026-01-01"

    def test_save_meta_other_error_raises(self, service):
        service._client.put_item.side_effect = _client_error("ValidationException")
        with pytest.raises(Exception, match="Failed to save journey meta"):
            service.save_journey_meta("u")
