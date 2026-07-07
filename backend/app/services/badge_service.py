"""Badge service — calculates which badges a user has earned.

Ported from backend/services/badge_service.py. Self-contained with no
legacy imports. Badge criteria are checked against user stats and progress.
"""

import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.services.content_registry import get_registry_service

logger = logging.getLogger(__name__)

# Page IDs per learning path (for path_completion badges)
PATH_PAGE_IDS: dict[str, set[str]] = {
    "know_before_you_go": {
        "the-prerequisite-blueprint",
        "the-source-version-control",
        "the-logic-programming-concepts",
        "the-foundation-linux-fundamentals",
        "the-highway-networking-basics",
        "the-guardrail-security-fundamentals",
        "the-philosophy-devops-culture",
        "the-assembly-line-cicd",
        "the-horizon-cloud-computing",
        "the-foundation-of-professional-success",
        "precision-in-communication",
        "principles-of-collaboration",
        "cultivating-adaptability",
        "systematic-problem-solving",
        "navigating-conflict",
        "essential-learning-resources",
        "achieving-professional-balance",
    },
    "devsecops": {
        "the-traditional-line-sdlc",
        "the-threat-why-appsec-matters",
        "the-six-stations-ssdlc",
        "the-knowledge-hub-ssdlc",
        "the-factory-badge-ssdlc",
        "the-master-architect-ssdlc",
        "the-invisible-shield",
        "the-evolution-ssdlc",
        "the-broken-lock-owasp-top-10",
        "the-x-ray-sast",
        "the-stress-test-dast",
        "the-hybrid-sast-and-dast",
        "the-playground-hands-on-labs",
        "the-credentials-growth",
        "the-video-archive-appsec",
        "the-culture-shift-devsecops",
        "the-first-line-secure-coding",
        "the-lifecycle-secure-coding",
        "the-patterns-secure-coding",
        "the-arsenal-secure-coding",
        "the-wisdom-archive-secure-coding",
        "the-capstone-challenge-secure-coding",
        "the-hidden-fracture-secure-coding",
        "the-four-pillars-devsecops",
        "the-visual-archive-devsecops",
        "the-pros-bookshelf-devsecops",
        "the-integration-mission-devsecops",
        "the-scouting-mission-threat-modeling",
        "the-heartbeat-threat-modeling",
        "the-scouting-manual-threat-modeling",
        "the-map-threat-modeling",
        "the-scouts-library-threat-modeling",
        "the-solo-mission-threat-modeling",
        "the-shipping-crate-container-security",
        "the-cracks-in-the-hull-container-security",
        "build-ship-run-container-security",
        "the-captains-rules-container-security",
        "the-toolbelt-container-security",
        "the-navigators-library-container-security",
        "the-maiden-voyage-container-security",
        "devsecops-capstone",
    },
    "cloud_security_development": {
        "the-bridge-cloud-security-development",
        "the-anatomy-of-defense-cloud-security-development",
        "infrastructure-vs-lifecycle-cloud-security-development",
        "the-professionals-map-cloud-security-development",
        "the-gatekeeper-iam-fundamentals",
        "the-cracks-in-the-key-iam-fundamentals",
        "the-iam-lifecycle-iam-fundamentals",
        "best-practices-and-providers-iam-fundamentals",
        "the-master-key-library-iam-fundamentals",
        "the-hardening-mission-iam-fundamentals",
        "the-control-plane-api-patterns",
        "the-exposed-front-door-api-patterns",
        "the-secure-blueprint-api-patterns",
        "the-automation-playbook-api-patterns",
        "the-inventory-mission-api-patterns",
        "the-vault-secrets-and-config",
        "the-leaking-key-secrets-and-config",
        "the-four-pillars-secrets-and-config",
        "the-cloud-banks-secrets-and-config",
        "the-locksmiths-library-secrets-and-config",
        "the-vault-operation-secrets-and-config",
        "the-observability-layer-logging-events",
        "the-blind-spots-logging-events",
        "the-visibility-lifecycle-logging-events",
        "cloud-native-sources-logging-events",
        "the-observers-library-logging-events",
        "the-awareness-mission-logging-events",
        "the-automated-conductor-serverless-orchestration",
        "the-logic-of-action-serverless-orchestration",
        "the-toolkit-serverless-orchestration",
        "the-hands-of-the-team-serverless-orchestration",
        "the-architects-rules-serverless-orchestration",
        "the-automation-mission-serverless-orchestration",
        "the-conveyor-belt-iac-security",
        "the-rules-of-the-road-iac-security",
        "the-foundation-layers-iac-security",
        "the-drift-and-the-risk-iac-security",
        "the-verified-highway-iac-security",
        "the-blueprint-library-iac-security",
        "cloud_security_development-capstone",
    },
}

# Badge definitions
BADGE_DEFINITIONS: list[dict[str, Any]] = [
    {
        "id": "b1",
        "title": "First Steps",
        "description": "Complete your first lesson",
        "icon": "🎯",
        "criteria": "completed_count",
        "threshold": 1,
    },
    {
        "id": "b2",
        "title": "DevSecOps Guru",
        "description": "Complete DevSecOps path",
        "icon": "🛡️",
        "criteria": "path_completion",
        "threshold": "devsecops",
    },
    {
        "id": "b3",
        "title": "Cloud Security Developer",
        "description": "Complete Cloud Security Development path",
        "icon": "☁️",
        "criteria": "path_completion",
        "threshold": "cloud_security_development",
    },
    {
        "id": "b4",
        "title": "Walkthrough Newbie",
        "description": "Complete beginner walkthrough",
        "icon": "🌱",
        "criteria": "walkthrough_difficulty",
        "threshold": "Beginner",
    },
    {
        "id": "b5",
        "title": "Walkthrough Pro",
        "description": "Complete intermediate walkthrough",
        "icon": "⚡",
        "criteria": "walkthrough_difficulty",
        "threshold": "Intermediate",
    },
    {
        "id": "b6",
        "title": "Walkthrough Expert",
        "description": "Complete expert level walkthrough",
        "icon": "🏆",
        "criteria": "walkthrough_difficulty",
        "threshold": "Advanced",
    },
    {
        "id": "b7",
        "title": "Foundation Builder",
        "description": "Complete Know Before You Go Path",
        "icon": "🧱",
        "criteria": "path_completion",
        "threshold": "know_before_you_go",
    },
    {
        "id": "b8",
        "title": "Perfect Score",
        "description": "Get 100% on any quiz",
        "icon": "💯",
        "criteria": "perfect_quiz",
        "threshold": 100,
    },
    {
        "id": "b9",
        "title": "Capstone Champion",
        "description": "Submit a capstone project",
        "icon": "🎓",
        "criteria": "capstone_submission",
        "threshold": 1,
    },
    {
        "id": "b10",
        "title": "Completionist",
        "description": "Earn all other badges",
        "icon": "👑",
        "criteria": "all_badges",
        "threshold": 9,
    },
]


def check_badge_earned(
    badge: dict[str, Any],
    stats: dict[str, Any],
    progress_items: list[dict[str, Any]],
) -> bool:
    """Check if a single badge's criteria are met."""
    criteria = badge.get("criteria")
    threshold = badge.get("threshold")

    if criteria == "completed_count":
        return stats.get("completed_count", 0) >= threshold

    elif criteria == "path_completion":
        path_pages = PATH_PAGE_IDS.get(threshold)
        if not path_pages:
            return False
        completed_ids = {
            item.get("content_id")
            for item in progress_items
            if item.get("status") == "complete"
        }
        return len(completed_ids & path_pages) >= len(path_pages)

    elif criteria == "walkthrough_difficulty":
        return any(
            item.get("content_id", "").startswith("walkthrough/")
            and item.get("status") == "completed"
            and item.get("difficulty", "").lower() == threshold.lower()
            for item in progress_items
        )

    elif criteria == "perfect_quiz":
        return stats.get("perfect_quiz_achieved", False)

    elif criteria == "capstone_submission":
        return stats.get("capstone_submissions", 0) >= threshold

    elif criteria == "all_badges":
        return stats.get("badges_earned", 0) >= threshold

    return False


def _get_walkthrough_progress_items(
    user_id: str, table_name: str, s3_bucket: str
) -> list[dict[str, Any]]:
    """Fetch completed walkthroughs from DynamoDB + content registry.

    Queries the content registry for all walkthroughs and their difficulty,
    then checks user's WALKTHROUGH# records in DynamoDB for completion.
    """
    walkthrough_progress: list[dict[str, Any]] = []

    try:
        registry = get_registry_service(s3_bucket)
        all_walkthroughs = registry.get_all_walkthroughs()

        if not all_walkthroughs:
            return []

        dynamodb = boto3.client("dynamodb")

        for wt in all_walkthroughs:
            try:
                response = dynamodb.get_item(
                    TableName=table_name,
                    Key={
                        "PK": {"S": f"USER#{user_id}"},
                        "SK": {"S": f"WALKTHROUGH#{wt['id']}"},
                    },
                )
                item = response.get("Item")
                if item and item.get("status", {}).get("S") == "completed":
                    walkthrough_progress.append(
                        {
                            "content_id": f"walkthrough/{wt['id']}",
                            "status": "completed",
                            "completed_at": item.get("completed_at", {}).get("S", ""),
                            "difficulty": wt["difficulty"],
                        }
                    )
            except ClientError:
                continue

    except Exception as e:
        logger.error("Failed to fetch walkthrough progress for badges: %s", e)

    return walkthrough_progress


def calculate_user_badges(
    stats: dict[str, Any],
    progress_items: list[dict[str, Any]],
    table_name: str = "",
    s3_bucket: str = "",
) -> list[dict[str, Any]]:
    """Calculate all badges for a user.

    Args:
        stats: User statistics dict (must include user_id).
        progress_items: List of completed content items.
        table_name: DynamoDB progress table name (for walkthrough queries).
        s3_bucket: Content registry S3 bucket (for walkthrough difficulty lookup).

    Returns:
        List of badge dicts with earned status.
    """
    user_id = stats.get("user_id", "")

    # Fetch walkthrough progress for difficulty-based badges
    walkthrough_progress: list[dict[str, Any]] = []
    if user_id and table_name and s3_bucket:
        walkthrough_progress = _get_walkthrough_progress_items(
            user_id, table_name, s3_bucket
        )

    all_progress = progress_items + walkthrough_progress

    # First pass: all badges except "all_badges"
    badges: list[dict[str, Any]] = []
    for badge_def in BADGE_DEFINITIONS:
        if badge_def.get("criteria") == "all_badges":
            continue
        earned = check_badge_earned(badge_def, stats, all_progress)
        earned_date = None
        if earned and all_progress:
            sorted_items = sorted(
                all_progress, key=lambda x: x.get("completed_at", ""), reverse=True
            )
            earned_date = sorted_items[0].get("completed_at") if sorted_items else None

        badges.append(
            {
                "id": badge_def["id"],
                "title": badge_def["title"],
                "description": badge_def["description"],
                "icon": badge_def["icon"],
                "earned": earned,
                "earned_date": earned_date,
            }
        )

    # Second pass: "all_badges" badge
    earned_count = sum(1 for b in badges if b["earned"])
    stats_with_badges = {**stats, "badges_earned": earned_count}

    for badge_def in BADGE_DEFINITIONS:
        if badge_def.get("criteria") != "all_badges":
            continue
        earned = check_badge_earned(badge_def, stats_with_badges, all_progress)
        earned_date = None
        if earned and all_progress:
            sorted_items = sorted(
                all_progress, key=lambda x: x.get("completed_at", ""), reverse=True
            )
            earned_date = sorted_items[0].get("completed_at") if sorted_items else None

        badges.append(
            {
                "id": badge_def["id"],
                "title": badge_def["title"],
                "description": badge_def["description"],
                "icon": badge_def["icon"],
                "earned": earned,
                "earned_date": earned_date,
            }
        )

    return badges


def get_badges_earned_count(badges: list[dict[str, Any]]) -> int:
    """Count how many badges are earned."""
    return sum(1 for b in badges if b.get("earned", False))
