"""
Badge service for calculating and managing user badges.

This module provides functions to determine which badges a user has earned
based on their progress data, streaks, and completion statistics.
"""

import os
import logging
import traceback
from typing import Dict, List, Any
from datetime import datetime, timezone
from services.dynamo import get_walkthrough_progress
from services.content_registry import get_registry_service

logger = logging.getLogger(__name__)

# Page IDs that belong to each learning path (from modules.json).
# Used to count per-path completions when checking path_completion badges.
PATH_PAGE_IDS = {
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
    },  # 17 pages
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
    },  # 41 pages
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
    },  # 40 pages
}

# Badge definitions with earning criteria
BADGE_DEFINITIONS = [
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
        "threshold": 9,  # Total number of other badges (b1-b9)
    },
]


def check_badge_earned(
    badge: Dict[str, Any],
    stats: Dict[str, Any],
    progress_items: List[Dict[str, Any]],
) -> bool:
    """
    Check if a badge has been earned based on criteria.

    Args:
        badge: Badge definition with criteria and threshold
        stats: User statistics (streaks, completion, etc.)
        progress_items: List of completed content items

    Returns:
        True if badge criteria is met, False otherwise
    """

    criteria = badge.get("criteria")
    threshold = badge.get("threshold")

    logger.info(
        f"Checking badge {badge.get('id')} - {badge.get('title')}: criteria={criteria}, threshold={threshold}"
    )
    logger.info(f"Stats: {stats}")
    logger.info(f"Progress items count: {len(progress_items)}")

    if criteria == "completed_count":
        completed = stats.get("completed_count", 0)
        result = completed >= threshold
        logger.info(f"completed_count check: {completed} >= {threshold} = {result}")
        return result

    elif criteria == "path_completion":
        # Check if user has completed all pages for this learning path.
        # Uses PATH_PAGE_IDS to count how many of the path's pages appear
        # in the user's completed progress items.

        path_pages = PATH_PAGE_IDS.get(threshold)
        if not path_pages:
            logger.warning(f"Unknown path threshold: {threshold}")
            return False

        # Collect completed content_ids
        completed_ids = {
            item.get("content_id")
            for item in progress_items
            if item.get("status") == "complete"
        }

        # Count how many pages from this path the user has completed
        completed_path_count = len(completed_ids & path_pages)
        required_count = len(path_pages)

        result = completed_path_count >= required_count
        logger.info(
            f"{threshold} badge: {completed_path_count}/{required_count} path pages completed, "
            f"earned: {result}"
        )
        return result

    elif criteria == "walkthrough_difficulty":
        # Check if user has completed a walkthrough of the specified difficulty
        # Walkthrough progress is fetched separately and added to progress_items
        # with content_id format "walkthrough/{id}" and difficulty field
        # Walkthroughs use status "completed" (not "complete")
        completed_walkthroughs = [
            item
            for item in progress_items
            if item.get("content_id", "").startswith("walkthrough/")
            and item.get("status") == "completed"
            and item.get("difficulty", "").lower()
            == threshold.lower()  # Case-insensitive comparison
        ]

        logger.info(
            f"Walkthrough check for {threshold}: found {len(completed_walkthroughs)} walkthroughs"
        )
        logger.info(
            f"All walkthrough items: {[item for item in progress_items if item.get('content_id', '').startswith('walkthrough/')]}"
        )
        return len(completed_walkthroughs) > 0

    elif criteria == "perfect_quiz":
        # Check if user has achieved a perfect score (100%) on any quiz
        perfect_score_achieved = stats.get("perfect_quiz_achieved", False)
        logger.info(f"perfect_quiz check: {perfect_score_achieved}")
        return perfect_score_achieved

    elif criteria == "capstone_submission":
        # Check if user has submitted at least one capstone project
        capstone_submissions = stats.get("capstone_submissions", 0)
        result = capstone_submissions >= threshold
        logger.info(
            f"capstone_submission check: {capstone_submissions} >= {threshold} = {result}"
        )
        return result

    elif criteria == "all_badges":
        # Check if user has earned all other badges (excluding this one)
        earned_count = stats.get("badges_earned", 0)
        result = earned_count >= threshold
        logger.info(f"all_badges check: {earned_count} >= {threshold} = {result}")
        return result

    return False


def get_earned_date(badge_id: str, progress_items: List[Dict[str, Any]]) -> str | None:
    """
    Determine when a badge was earned based on progress history.

    Args:
        badge_id: Badge identifier
        progress_items: List of completed content items with timestamps

    Returns:
        ISO timestamp of when badge was earned, or None if not earned
    """
    if not progress_items:
        return None

    # For simplicity, use the timestamp of the item that triggered the badge
    # Sort by completed_at and get the relevant timestamp
    sorted_items = sorted(
        progress_items, key=lambda x: x.get("completed_at", ""), reverse=True
    )

    if sorted_items:
        # Return the most recent completion date as earned date
        return sorted_items[0].get("completed_at")

    return None


def calculate_user_badges(
    stats: Dict[str, Any], progress_items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Calculate which badges a user has earned.

    Args:
        stats: User statistics (current_streak, longest_streak, etc.)
        progress_items: List of completed content items

    Returns:
        List of badge objects with earned status and earned_date
    """
    badges = []

    # Fetch walkthrough progress to check walkthrough-based badges
    user_id = stats.get("user_id")
    walkthrough_progress = []

    logger.info(f"Calculating badges for user {user_id}")
    logger.info(f"Progress items: {len(progress_items)}")

    if user_id:
        try:
            # Get S3 bucket from environment
            s3_bucket = os.environ.get("CONTENT_REGISTRY_BUCKET")
            if not s3_bucket:
                logger.error("CONTENT_REGISTRY_BUCKET environment variable not set")
                raise ValueError("CONTENT_REGISTRY_BUCKET not configured")

            registry_service = get_registry_service(s3_bucket)

            # Get all walkthroughs from content registry
            all_walkthroughs = []
            if registry_service._registry:
                for entry_id, entry_data in registry_service._registry.get(
                    "entries", {}
                ).items():
                    if entry_data.get("content_type") == "walkthrough":
                        all_walkthroughs.append(
                            {
                                "id": entry_id,
                                "difficulty": entry_data.get("difficulty", ""),
                            }
                        )

            logger.info(
                f"Found {len(all_walkthroughs)} walkthroughs in content registry"
            )

            # Check progress for each walkthrough
            for wt in all_walkthroughs:
                progress = get_walkthrough_progress(user_id, wt["id"])
                logger.info(
                    f"Checking walkthrough {wt['id']}: difficulty={wt.get('difficulty')}, progress={progress}"
                )
                if progress and progress.get("status") == "completed":
                    walkthrough_progress.append(
                        {
                            "content_id": f"walkthrough/{wt['id']}",
                            "status": "completed",
                            "completed_at": progress.get("completed_at", ""),
                            "difficulty": wt["difficulty"],
                        }
                    )
            logger.info(f"Found {len(walkthrough_progress)} completed walkthroughs")
            logger.info(f"Walkthrough progress details: {walkthrough_progress}")
        except Exception as e:
            logger.error(f"Failed to fetch walkthrough progress: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            pass

    # Combine regular progress with walkthrough progress
    all_progress = progress_items + walkthrough_progress

    logger.info(f"Total progress items (including walkthroughs): {len(all_progress)}")

    # First pass: calculate all badges except "all_badges" badge
    badges = []
    for badge_def in BADGE_DEFINITIONS:
        if badge_def.get("criteria") == "all_badges":
            continue

        earned = check_badge_earned(badge_def, stats, all_progress)
        earned_date = None

        if earned:
            earned_date = get_earned_date(badge_def["id"], all_progress)

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

    # Count earned badges from first pass
    earned_count = sum(1 for b in badges if b["earned"])

    # Second pass: check "all_badges" badge with earned count
    stats_with_badges = {**stats, "badges_earned": earned_count}

    for badge_def in BADGE_DEFINITIONS:
        if badge_def.get("criteria") != "all_badges":
            continue

        earned = check_badge_earned(badge_def, stats_with_badges, all_progress)
        earned_date = None

        if earned:
            earned_date = get_earned_date(badge_def["id"], all_progress)

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

    earned_badges = [b for b in badges if b["earned"]]
    logger.info(f"Total badges earned: {len(earned_badges)}/{len(badges)}")
    logger.info(f"Earned badges: {[b['title'] for b in earned_badges]}")

    return badges


def get_badges_earned_count(badges: List[Dict[str, Any]]) -> int:
    """
    Count how many badges have been earned.

    Args:
        badges: List of badge objects

    Returns:
        Number of earned badges
    """
    return sum(1 for badge in badges if badge.get("earned", False))
