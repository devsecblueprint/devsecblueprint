"""APScheduler setup and Discord reconciliation job.

The scheduler is started/stopped by the FastAPI lifespan context manager
in main.py. The reconciliation job runs every 5 minutes, comparing
DynamoDB membership records against actual Discord roles and syncing
any differences.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

import logging

from app.services.discord_sync import reconcile_all_members

logger = logging.getLogger("app.scheduler")


async def run_reconciliation() -> None:
    """Run Discord role reconciliation.

    Compares DynamoDB membership records against actual Discord roles
    and syncs any differences. Called by apscheduler every 5 minutes.

    On success, logs a summary of roles added, removed, or unchanged.
    On failure, logs the error without re-raising so the scheduler
    continues running on the next interval.

    Requirements: 6.1, 6.2, 6.4, 6.5
    """
    try:
        result = await reconcile_all_members()
        logger.info(
            "Reconciliation completed",
            extra={
                "roles_added": result.get("added", 0),
                "roles_removed": result.get("removed", 0),
                "unchanged": result.get("unchanged", 0),
                "skipped": result.get("skipped", 0),
                "failed": result.get("failed", 0),
            },
        )
    except Exception as exc:
        logger.error(
            "Reconciliation failed",
            extra={"error": str(exc), "error_type": type(exc).__name__},
        )
