"""Unit tests for app.services.admin_service.AdminService.

Covers registered-user and progress scans (with pagination), capstone
submission listing/review, user stats aggregation, contributor-role mapping,
and walkthrough access-tier management. DynamoDB is mocked.
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import admin_service as mod
from app.services.admin_service import AdminService


def _client_error(code: str = "InternalServerError") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


@pytest.fixture
def service():
    client = MagicMock()
    with patch.object(mod.boto3, "client", return_value=client):
        settings = MagicMock(
            progress_table="test-progress",
            membership_table="test-membership",
            total_module_pages=100,
        )
        svc = AdminService(settings)
    svc._client = client
    return svc


class TestRegisteredUsers:
    def test_scans_profile_records_with_pagination(self, service):
        service._client.scan.side_effect = [
            {
                "Items": [
                    {
                        "PK": {"S": "USER#u1"},
                        "SK": {"S": "PROFILE"},
                        "username": {"S": "Alice"},
                    }
                ],
                "LastEvaluatedKey": {"PK": {"S": "USER#u1"}},
            },
            {
                "Items": [
                    {
                        "PK": {"S": "USER#u2"},
                        "SK": {"S": "PROFILE"},
                        "username": {"S": "Bob"},
                    },
                    {"PK": {"S": "NOTUSER#x"}, "SK": {"S": "PROFILE"}},  # filtered out
                ]
            },
        ]
        users = service.get_all_registered_users()
        assert [u["user_id"] for u in users] == ["u1", "u2"]
        assert users[0]["username"] == "Alice"


class TestCapstoneSubmissions:
    def test_lists_sorted_desc_and_paginates_result(self, service):
        service._client.scan.return_value = {
            "Items": [
                {
                    "PK": {"S": "USER#a"},
                    "SK": {"S": "CAPSTONE_SUBMISSION#c1"},
                    "submitted_at": {"S": "2026-01-01"},
                },
                {
                    "PK": {"S": "USER#b"},
                    "SK": {"S": "CAPSTONE_SUBMISSION#c2"},
                    "submitted_at": {"S": "2026-03-01"},
                },
                {
                    "PK": {"S": "USER#c"},
                    "SK": {"S": "CAPSTONE_SUBMISSION#c3"},
                    "submitted_at": {"S": "2026-02-01"},
                },
            ]
        }
        page, total = service.get_capstone_submissions(page=1, page_size=2)
        assert total == 3
        # Sorted desc by submitted_at, first page of 2
        assert [s["content_id"] for s in page] == ["c2", "c3"]

    def test_get_single_submission(self, service):
        service._client.get_item.return_value = {
            "Item": {"repo_url": {"S": "https://r"}, "status": {"S": "pending"}}
        }
        result = service.get_capstone_submission("u", "c1")
        assert result["repo_url"] == "https://r"
        assert result["status"] == "pending"

    def test_get_single_submission_missing(self, service):
        service._client.get_item.return_value = {}
        assert service.get_capstone_submission("u", "c1") is None

    def test_get_single_submission_error_returns_none(self, service):
        service._client.get_item.side_effect = _client_error()
        assert service.get_capstone_submission("u", "c1") is None

    def test_save_review_puts_item(self, service):
        service.save_capstone_review("u", "c1", "great", "admin")
        item = service._client.put_item.call_args.kwargs["Item"]
        assert item["SK"]["S"] == "CAPSTONE_REVIEW#c1"
        assert item["feedback"]["S"] == "great"

    def test_save_review_raises_on_error(self, service):
        service._client.put_item.side_effect = _client_error("ValidationException")
        with pytest.raises(Exception, match="Failed to save review"):
            service.save_capstone_review("u", "c1", "f", "admin")

    def test_update_status(self, service):
        service.update_capstone_submission_status("u", "c1", "reviewed")
        call = service._client.update_item.call_args.kwargs
        assert call["ExpressionAttributeValues"][":status"]["S"] == "reviewed"

    def test_update_status_raises_on_error(self, service):
        service._client.update_item.side_effect = _client_error("ValidationException")
        with pytest.raises(Exception, match="Failed to update submission status"):
            service.update_capstone_submission_status("u", "c1", "x")

    def test_get_review(self, service):
        service._client.get_item.return_value = {
            "Item": {"feedback": {"S": "good"}, "reviewed_by": {"S": "admin"}}
        }
        result = service.get_capstone_review("u", "c1")
        assert result["feedback"] == "good"

    def test_get_review_missing(self, service):
        service._client.get_item.return_value = {}
        assert service.get_capstone_review("u", "c1") is None


class TestUserStats:
    def test_aggregates_counts(self, service):
        def query(**kwargs):
            sk = kwargs["ExpressionAttributeValues"][":sk"]["S"]
            if sk == "CONTENT#":
                return {"Count": 48}
            if sk == "MODULE#":
                return {"Items": [{"score": {"N": "100"}}, {"score": {"N": "80"}}]}
            if sk == "WALKTHROUGH#":
                return {
                    "Items": [
                        {"status": {"S": "completed"}},
                        {"status": {"S": "in_progress"}},
                    ]
                }
            if sk == "CAPSTONE_SUBMISSION#":
                return {"Count": 2}
            return {}

        service._client.query.side_effect = query
        stats = service.get_user_stats("u")
        assert stats["completed_count"] == 48
        assert stats["overall_completion"] == 48  # 48/100
        assert stats["quizzes_passed"] == 2
        assert stats["perfect_quiz_achieved"] is True
        assert stats["walkthroughs_completed"] == 1
        assert stats["capstone_submissions"] == 2

    def test_handles_query_errors_gracefully(self, service):
        service._client.query.side_effect = _client_error()
        stats = service.get_user_stats("u")
        assert stats["completed_count"] == 0
        assert stats["overall_completion"] == 0

    def test_get_user_progress(self, service):
        service._client.query.return_value = {
            "Items": [
                {
                    "SK": {"S": "CONTENT#intro"},
                    "status": {"S": "complete"},
                    "completed_at": {"S": "2026-01-01"},
                }
            ]
        }
        result = service.get_user_progress("u")
        assert result == [
            {"content_id": "intro", "status": "complete", "completed_at": "2026-01-01"}
        ]

    def test_get_user_profile_found(self, service):
        service._client.get_item.return_value = {"Item": {"username": {"S": "Alice"}}}
        result = service.get_user_profile("u")
        assert result is not None
        assert result["user_id"] == "u"

    def test_get_user_profile_missing(self, service):
        service._client.get_item.return_value = {}
        assert service.get_user_profile("u") is None


class TestWalkthroughStats:
    def test_counts_and_popularity(self, service):
        service._client.scan.return_value = {
            "Items": [
                {"SK": {"S": "WALKTHROUGH#wt1"}, "status": {"S": "completed"}},
                {"SK": {"S": "WALKTHROUGH#wt1"}, "status": {"S": "in_progress"}},
                {"SK": {"S": "WALKTHROUGH#wt2"}, "status": {"S": "completed"}},
            ]
        }
        stats = service.get_walkthrough_statistics()
        assert stats["completed_count"] == 2
        assert stats["in_progress_count"] == 1
        assert stats["most_popular_walkthrough"] == "wt1"  # appears twice

    def test_no_data(self, service):
        service._client.scan.return_value = {"Items": []}
        stats = service.get_walkthrough_statistics()
        assert stats["most_popular_walkthrough"] is None


class TestContributorRole:
    def test_get_found(self, service):
        service._client.get_item.return_value = {
            "Item": {"role": {"S": "contributor"}, "assigned_by": {"S": "admin"}}
        }
        result = service.get_contributor_role("u")
        assert result["role"] == "contributor"

    def test_get_missing(self, service):
        service._client.get_item.return_value = {}
        assert service.get_contributor_role("u") is None

    def test_get_error_returns_none(self, service):
        service._client.get_item.side_effect = _client_error()
        assert service.get_contributor_role("u") is None

    def test_set_valid_role(self, service):
        result = service.set_contributor_role(
            "u", "contributor", "admin", note="trusted"
        )
        assert result["role"] == "contributor"
        assert result["note"] == "trusted"
        item = service._client.put_item.call_args.kwargs["Item"]
        assert item["note"]["S"] == "trusted"

    def test_set_invalid_role_raises(self, service):
        with pytest.raises(ValueError, match="Invalid role"):
            service.set_contributor_role("u", "superadmin", "admin")

    def test_delete_success(self, service):
        assert service.delete_contributor_role("u") is True

    def test_delete_error_returns_false(self, service):
        service._client.delete_item.side_effect = _client_error()
        assert service.delete_contributor_role("u") is False


class TestAccessTier:
    def test_get_defaults_free(self, service):
        service._client.get_item.return_value = {}
        assert service.get_walkthrough_access_tier("wt1") == "FREE"

    def test_get_returns_stored_tier(self, service):
        service._client.get_item.return_value = {
            "Item": {"access_tier": {"S": "BUILDER"}}
        }
        assert service.get_walkthrough_access_tier("wt1") == "BUILDER"

    def test_get_error_defaults_free(self, service):
        service._client.get_item.side_effect = _client_error()
        assert service.get_walkthrough_access_tier("wt1") == "FREE"

    def test_set_valid_tier(self, service):
        result = service.set_walkthrough_access_tier("wt1", "BUILDER", "admin")
        assert result["access_tier"] == "BUILDER"
        assert result["walkthrough_id"] == "wt1"

    def test_set_invalid_tier_raises(self, service):
        with pytest.raises(ValueError, match="Invalid access tier"):
            service.set_walkthrough_access_tier("wt1", "PREMIUM", "admin")

    def test_get_all_tiers(self, service):
        service._client.query.return_value = {
            "Items": [
                {"SK": {"S": "WT#wt1"}, "access_tier": {"S": "BUILDER"}},
                {"SK": {"S": "WT#wt2"}, "access_tier": {"S": "FREE"}},
            ]
        }
        tiers = service.get_all_walkthrough_access_tiers()
        assert tiers == {"wt1": "BUILDER", "wt2": "FREE"}
