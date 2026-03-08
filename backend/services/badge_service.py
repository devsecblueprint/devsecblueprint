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
        # Check if user has completed the capstone for this learning path
        # Capstones are the final requirement, so completing the capstone means completing the path

        capstone_ids = {
            "devsecops": "devsecops-capstone",
            "cloud_security_development": "cloud_security_development-capstone",
            "know_before_you_go": None,  # No capstone for this path
        }

        capstone_id = capstone_ids.get(threshold)

        # For paths with capstones, check if capstone is completed
        if capstone_id:
            for item in progress_items:
                if (
                    item.get("status") == "complete"
                    and item.get("content_id") == capstone_id
                ):
                    logger.info(f"{threshold} badge earned: capstone completed")
                    return True
            logger.info(f"{threshold} badge not earned: capstone not completed")
            return False

        # For Know Before You Go (no capstone), count total completed pages
        # This path has 17 pages total (9 prerequisites + 8 soft skills)
        if threshold == "know_before_you_go":
            # Count all completed items (we can't easily filter by path without modules.json)
            # So we'll use a simple heuristic: if they have 17+ completions, they likely finished this path
            completed_count = len(
                [item for item in progress_items if item.get("status") == "complete"]
            )
            result = completed_count >= 17
            logger.info(
                f"know_before_you_go badge: {completed_count} total completions, earned: {result}"
            )
            return result

        return False

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
        # Quiz scores are stored in MODULE records with SK format "MODULE#{module_id}"
        # We need to check the stats or look for any quiz with score >= 100
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
        # This is checked by counting earned badges in the stats
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
    # We need to get the user_id from somewhere - for now we'll pass it through stats
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
                    # Add to progress items in walkthrough format
                    walkthrough_progress.append(
                        {
                            "content_id": f"walkthrough/{wt['id']}",
                            "status": "completed",
                            "completed_at": progress.get("completed_at", ""),
                            "difficulty": wt[
                                "difficulty"
                            ],  # Add difficulty for badge checking
                        }
                    )
            logger.info(f"Found {len(walkthrough_progress)} completed walkthroughs")
            logger.info(f"Walkthrough progress details: {walkthrough_progress}")
        except Exception as e:
            # If fetching walkthrough progress fails, continue without it
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
            # Skip the "all_badges" badge in first pass
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
