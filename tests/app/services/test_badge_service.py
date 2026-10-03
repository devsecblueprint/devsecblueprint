"""Unit tests for app.services.badge_service.

Covers:
- check_badge_earned for every criteria branch (completed_count,
  path_completion present/missing/incomplete, walkthrough_difficulty,
  perfect_quiz, capstone_submission, all_badges, unknown criteria).
- _get_walkthrough_progress_items success, empty registry, per-item ClientError
  (skipped), and outer Exception handling.
- calculate_user_badges two-pass logic (first-pass badges + all_badges),
  earned_date derivation, and the guard that skips walkthrough fetch when
  identifiers are missing.
- get_badges_earned_count.
"""

from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from app.services import badge_service as mod
from app.services.badge_service import (
    BADGE_DEFINITIONS,
    PATH_PAGE_IDS,
    calculate_user_badges,
    check_badge_earned,
    get_badges_earned_count,
)


def _badge(criteria, threshold):
    return {"id": "x", "title": "t", "description": "d", "icon": "i",
            "criteria": criteria, "threshold": threshold}


class TestCheckBadgeEarnedCompletedCount:
    def test_meets_threshold(self):
        assert check_badge_earned(_badge("completed_count", 1), {"completed_count": 1}, []) is True

    def test_below_threshold(self):
        assert check_badge_earned(_badge("completed_count", 5), {"completed_count": 2}, []) is False


class TestCheckBadgeEarnedPathCompletion:
    def test_unknown_path_returns_false(self):
        assert check_badge_earned(_badge("path_completion", "nope"), {}, []) is False

    def test_all_pages_complete(self):
        pages = PATH_PAGE_IDS["career_strategy"]
        progress = [{"content_id": p, "status": "complete"} for p in pages]
        assert check_badge_earned(_badge("path_completion", "career_strategy"), {}, progress) is True

    def test_partial_pages_incomplete(self):
        pages = list(PATH_PAGE_IDS["career_strategy"])
        progress = [{"content_id": pages[0], "status": "complete"}]
        assert check_badge_earned(_badge("path_completion", "career_strategy"), {}, progress) is False


class TestCheckBadgeEarnedWalkthroughDifficulty:
    def test_matching_difficulty(self):
        progress = [{
            "content_id": "walkthrough/w1",
            "status": "completed",
            "difficulty": "beginner",
        }]
        assert check_badge_earned(_badge("walkthrough_difficulty", "Beginner"), {}, progress) is True

    def test_no_match(self):
        progress = [{
            "content_id": "walkthrough/w1",
            "status": "completed",
            "difficulty": "advanced",
        }]
        assert check_badge_earned(_badge("walkthrough_difficulty", "Beginner"), {}, progress) is False


class TestCheckBadgeEarnedOther:
    def test_perfect_quiz(self):
        assert check_badge_earned(_badge("perfect_quiz", 100), {"perfect_quiz_achieved": True}, []) is True
        assert check_badge_earned(_badge("perfect_quiz", 100), {}, []) is False

    def test_capstone_submission(self):
        assert check_badge_earned(_badge("capstone_submission", 1), {"capstone_submissions": 1}, []) is True
        assert check_badge_earned(_badge("capstone_submission", 1), {"capstone_submissions": 0}, []) is False

    def test_all_badges(self):
        assert check_badge_earned(_badge("all_badges", 10), {"badges_earned": 10}, []) is True
        assert check_badge_earned(_badge("all_badges", 10), {"badges_earned": 3}, []) is False

    def test_unknown_criteria(self):
        assert check_badge_earned(_badge("mystery", 1), {}, []) is False


class TestGetWalkthroughProgressItems:
    def test_returns_completed_walkthroughs(self):
        registry = MagicMock()
        registry.get_all_walkthroughs.return_value = [
            {"id": "w1", "difficulty": "Beginner"},
            {"id": "w2", "difficulty": "Advanced"},
        ]
        client = MagicMock()
        client.get_item.side_effect = [
            {"Item": {"status": {"S": "completed"}, "completed_at": {"S": "2026-01-01"}}},
            {"Item": {"status": {"S": "in_progress"}}},  # not completed -> skipped
        ]
        with patch.object(mod, "get_registry_service", return_value=registry), \
                patch.object(mod.boto3, "client", return_value=client):
            result = mod._get_walkthrough_progress_items("u", "tbl", "bucket")
        assert len(result) == 1
        assert result[0]["content_id"] == "walkthrough/w1"
        assert result[0]["difficulty"] == "Beginner"
        assert result[0]["completed_at"] == "2026-01-01"

    def test_empty_registry_returns_empty(self):
        registry = MagicMock()
        registry.get_all_walkthroughs.return_value = []
        with patch.object(mod, "get_registry_service", return_value=registry):
            assert mod._get_walkthrough_progress_items("u", "tbl", "bucket") == []

    def test_per_item_client_error_skipped(self):
        registry = MagicMock()
        registry.get_all_walkthroughs.return_value = [
            {"id": "w1", "difficulty": "Beginner"},
            {"id": "w2", "difficulty": "Advanced"},
        ]
        client = MagicMock()
        client.get_item.side_effect = [
            ClientError({"Error": {"Code": "X", "Message": "x"}}, "GetItem"),
            {"Item": {"status": {"S": "completed"}, "completed_at": {"S": "2026-02-02"}}},
        ]
        with patch.object(mod, "get_registry_service", return_value=registry), \
                patch.object(mod.boto3, "client", return_value=client):
            result = mod._get_walkthrough_progress_items("u", "tbl", "bucket")
        assert len(result) == 1
        assert result[0]["content_id"] == "walkthrough/w2"

    def test_outer_exception_returns_empty(self):
        with patch.object(mod, "get_registry_service", side_effect=RuntimeError("boom")):
            assert mod._get_walkthrough_progress_items("u", "tbl", "bucket") == []


class TestCalculateUserBadges:
    def test_returns_all_badge_definitions(self):
        badges = calculate_user_badges({"user_id": "u", "completed_count": 0}, [])
        assert len(badges) == len(BADGE_DEFINITIONS)
        ids = {b["id"] for b in badges}
        assert ids == {d["id"] for d in BADGE_DEFINITIONS}

    def test_first_steps_earned_with_date(self):
        progress = [{"content_id": "c1", "status": "complete", "completed_at": "2026-05-01"}]
        badges = calculate_user_badges({"user_id": "u", "completed_count": 3}, progress)
        first = next(b for b in badges if b["id"] == "b1")
        assert first["earned"] is True
        assert first["earned_date"] == "2026-05-01"

    def test_earned_without_progress_has_no_date(self):
        badges = calculate_user_badges({"user_id": "u", "completed_count": 3}, [])
        first = next(b for b in badges if b["id"] == "b1")
        assert first["earned"] is True
        assert first["earned_date"] is None

    def test_all_badges_awarded_when_everything_earned(self):
        # Earn b1 (completed_count), b4/b5/b6 (walkthroughs), b8 (perfect quiz),
        # b9 (capstone), and all three learning paths + career strategy.
        progress = []
        for path in ("know_before_you_go", "devsecops",
                     "cloud_security_development", "career_strategy"):
            for page in PATH_PAGE_IDS[path]:
                progress.append({"content_id": page, "status": "complete",
                                 "completed_at": "2026-01-01"})
        for diff in ("beginner", "intermediate", "advanced"):
            progress.append({
                "content_id": f"walkthrough/{diff}",
                "status": "completed",
                "difficulty": diff,
                "completed_at": "2026-01-01",
            })
        stats = {
            "user_id": "u",
            "completed_count": 10,
            "perfect_quiz_achieved": True,
            "capstone_submissions": 1,
        }
        badges = calculate_user_badges(stats, progress)
        completionist = next(b for b in badges if b["id"] == "b10")
        assert completionist["earned"] is True

    def test_fetches_walkthrough_progress_when_identifiers_present(self):
        with patch.object(mod, "_get_walkthrough_progress_items", return_value=[]) as fetch:
            calculate_user_badges({"user_id": "u"}, [], table_name="tbl", s3_bucket="b")
        fetch.assert_called_once_with("u", "tbl", "b")

    def test_skips_walkthrough_fetch_without_identifiers(self):
        with patch.object(mod, "_get_walkthrough_progress_items") as fetch:
            calculate_user_badges({"user_id": "u"}, [])
        fetch.assert_not_called()


class TestGetBadgesEarnedCount:
    def test_counts_earned(self):
        badges = [{"earned": True}, {"earned": False}, {"earned": True}, {}]
        assert get_badges_earned_count(badges) == 2
