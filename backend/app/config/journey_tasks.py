"""Builder Journey task configuration.

Defines the canonical list of valid journey task IDs, phase assignments,
auto-completion mappings, and content IDs used for auto-completion checks.

This must stay in sync with the frontend data file:
frontend/lib/data/builder-journey.ts
"""

from typing import Literal

TierType = Literal["FREE", "BUILDER"]

# ------------------------------------------------------------------
# Master phase definition with tier annotations (single source of truth)
# ------------------------------------------------------------------

JOURNEY_PHASES_ANNOTATED: dict[int, list[dict]] = {
    1: [
        {"id": "connect-discord", "tiers": ["FREE", "BUILDER"]},
        {"id": "verify-builder-role", "tiers": ["BUILDER"]},
        {"id": "complete-builder-profile", "tiers": ["FREE", "BUILDER"]},
        {"id": "review-community-guidelines", "tiers": ["FREE", "BUILDER"]},
        {"id": "explore-builder-dashboard", "tiers": ["FREE", "BUILDER"]},
        {"id": "learn-platform-organization", "tiers": ["FREE", "BUILDER"]},
    ],
    2: [
        {"id": "introduce-yourself-discord", "tiers": ["FREE", "BUILDER"]},
        {"id": "attend-first-office-hours", "tiers": ["BUILDER"]},
        {"id": "participate-builder-session", "tiers": ["BUILDER"]},
        {"id": "join-technical-discussion", "tiers": ["FREE", "BUILDER"]},
    ],
    3: [
        {"id": "complete-prerequisites-path", "tiers": ["FREE", "BUILDER"]},
        {"id": "complete-prerequisite-quizzes", "tiers": ["FREE", "BUILDER"]},
        {"id": "complete-introductory-activities", "tiers": ["FREE", "BUILDER"]},
        {"id": "review-engineering-specializations", "tiers": ["FREE", "BUILDER"]},
    ],
    4: [
        {"id": "select-primary-learning-path", "tiers": ["BUILDER"]},
        {"id": "begin-first-walkthrough", "tiers": ["BUILDER"]},
        {"id": "complete-first-hands-on-project", "tiers": ["BUILDER"]},
        {"id": "complete-first-mini-capstone", "tiers": ["BUILDER"]},
        {"id": "begin-reading-content", "tiers": ["FREE"]},
        {"id": "review-learning-path-overview", "tiers": ["FREE"]},
    ],
    5: [
        {"id": "complete-additional-walkthroughs", "tiers": ["BUILDER"]},
        {"id": "submit-first-capstone", "tiers": ["BUILDER"]},
        {"id": "continue-learning-path", "tiers": ["BUILDER"]},
        {"id": "participate-builder-events", "tiers": ["BUILDER"]},
        {"id": "establish-learning-goals", "tiers": ["BUILDER"]},
        {"id": "continue-reading-content", "tiers": ["FREE"]},
        {"id": "participate-free-events", "tiers": ["FREE"]},
        {"id": "set-learning-goals", "tiers": ["FREE"]},
        {"id": "explore-upgrade-options", "tiers": ["FREE"]},
    ],
}


# ------------------------------------------------------------------
# Derived tier-specific exports
# ------------------------------------------------------------------


def _filter_phases_by_tier(tier: TierType) -> dict[int, list[str]]:
    """Filter annotated phases to produce a tier-specific phase dict."""
    result: dict[int, list[str]] = {}
    for phase_num, tasks in JOURNEY_PHASES_ANNOTATED.items():
        filtered = [t["id"] for t in tasks if tier in t["tiers"]]
        if filtered:
            result[phase_num] = filtered
    return result


# Tier-specific phase dictionaries
FREE_JOURNEY_PHASES: dict[int, list[str]] = _filter_phases_by_tier("FREE")
BUILDER_JOURNEY_PHASES: dict[int, list[str]] = _filter_phases_by_tier("BUILDER")

# Tier-specific valid task ID sets
FREE_VALID_TASK_IDS: set[str] = {
    task_id for tasks in FREE_JOURNEY_PHASES.values() for task_id in tasks
}
BUILDER_VALID_TASK_IDS: set[str] = {
    task_id for tasks in BUILDER_JOURNEY_PHASES.values() for task_id in tasks
}

# Tier-specific total task counts
FREE_TOTAL_JOURNEY_TASKS: int = len(FREE_VALID_TASK_IDS)
BUILDER_TOTAL_JOURNEY_TASKS: int = len(BUILDER_VALID_TASK_IDS)

# Tier-specific reverse lookups: task_id → phase number
FREE_TASK_TO_PHASE: dict[str, int] = {
    task_id: phase for phase, tasks in FREE_JOURNEY_PHASES.items() for task_id in tasks
}
BUILDER_TASK_TO_PHASE: dict[str, int] = {
    task_id: phase
    for phase, tasks in BUILDER_JOURNEY_PHASES.items()
    for task_id in tasks
}

# ------------------------------------------------------------------
# Backward-compatible aliases (point to Builder-tier data)
# ------------------------------------------------------------------

JOURNEY_PHASES = BUILDER_JOURNEY_PHASES
VALID_TASK_IDS = BUILDER_VALID_TASK_IDS
TOTAL_JOURNEY_TASKS = BUILDER_TOTAL_JOURNEY_TASKS
TASK_TO_PHASE = BUILDER_TASK_TO_PHASE


# ------------------------------------------------------------------
# Auto-completion mappings
# ------------------------------------------------------------------


class AutoCompleteCondition:
    """Types of auto-completion conditions."""

    DISCORD_CONNECTED = "discord_connected"
    PREREQUISITES_COMPLETE = "prerequisites_complete"
    QUIZZES_COMPLETE = "quizzes_complete"
    CAPSTONE_SUBMITTED = "capstone_submitted"
    WALKTHROUGH_STARTED = "walkthrough_started"


# task_id → auto-complete condition type
AUTO_COMPLETE_MAPPINGS: dict[str, str] = {
    "connect-discord": AutoCompleteCondition.DISCORD_CONNECTED,
    "complete-prerequisites-path": AutoCompleteCondition.PREREQUISITES_COMPLETE,
    "complete-prerequisite-quizzes": AutoCompleteCondition.QUIZZES_COMPLETE,
    "submit-first-capstone": AutoCompleteCondition.CAPSTONE_SUBMITTED,
    "begin-first-walkthrough": AutoCompleteCondition.WALKTHROUGH_STARTED,
}


# ------------------------------------------------------------------
# Content IDs for auto-completion checks
# ------------------------------------------------------------------

# Content IDs that make up the Prerequisites learning path.
# When ALL of these are marked complete in the progress table,
# the "complete-prerequisites-path" task auto-completes.
PREREQUISITE_CONTENT_IDS: set[str] = {
    "prerequisites-linux-fundamentals",
    "prerequisites-networking-basics",
    "prerequisites-cloud-computing-intro",
    "prerequisites-version-control",
    "prerequisites-scripting-basics",
}

# Quiz content IDs within the prerequisites path.
# When ALL of these are marked complete, the
# "complete-prerequisite-quizzes" task auto-completes.
PREREQUISITE_QUIZ_IDS: set[str] = {
    "quiz-linux-fundamentals",
    "quiz-networking-basics",
    "quiz-cloud-computing-intro",
    "quiz-version-control",
    "quiz-scripting-basics",
}

# Walkthrough content IDs. When ANY of these are marked complete,
# the "begin-first-walkthrough" task auto-completes.
WALKTHROUGH_CONTENT_IDS: set[str] = {
    "walkthrough-cloud-security-fundamentals",
    "walkthrough-devsecops-pipeline",
    "walkthrough-container-security",
    "walkthrough-infrastructure-as-code",
    "walkthrough-application-security",
}
