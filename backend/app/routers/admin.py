"""Admin router — /admin/* routes.

Consolidates all admin endpoints from both Lambda functions:
- Discord admin operations (from membership Lambda)
- Analytics, submissions, registry, module health (from main Lambda)
- User management, sessions, exports (from main Lambda)
- Capstone review operations (from main Lambda)

All routes require JWT + admin privileges via Depends(require_admin).
Note: Testimonial admin routes (GET /admin/testimonials, PUT /admin/testimonials/{user_id}/status)
are in content.py and are NOT duplicated here.

Requirements: 4.3
"""

import csv
import io
import json
import logging
import math
import time as time_mod
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any

import boto3 as boto3_mod
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from app.auth.jwt import require_admin
from app.config import Settings
from app.dependencies import get_settings
from app.services.admin_discord import AdminDiscordService
from app.services.admin_service import AdminService
from app.services.membership_db import MembershipDB
from app.services.badge_service import calculate_user_badges, get_badges_earned_count
from app.services.content_registry import get_registry_service
from app.services.broadcast_service import BroadcastService
from app.services.broadcast_email import send_broadcast_emails
from app.services.notification_service import create_notification
from app.services.email import send_review_notification_to_learner
from app.services.progress_db import ProgressDB
from app.background.discord_tasks import enqueue_discord_sync

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Discord Admin Routes (from membership Lambda)
# ---------------------------------------------------------------------------


@router.get("/discord/users/{user_id}")
async def get_discord_user_detail(
    user_id: str,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get detailed Discord/membership info for a user.

    Returns membership tier, Stripe subscription status, and Discord
    connection details for the target user.
    """
    service = AdminDiscordService(settings)
    result = service.get_user_detail(user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(status_code=200, content=result)


@router.post("/discord/users/{user_id}/sync")
async def admin_trigger_sync(
    user_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Trigger a manual Discord role sync for a user.

    Enqueues the sync operation as a background task and writes an
    audit entry recording the admin action.
    """
    # Parse optional reason from body
    reason = "Admin triggered"
    try:
        body = await request.body()
        if body:
            payload = json.loads(body.decode("utf-8"))
            reason = payload.get("reason", reason)
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass

    admin_user_id = admin.get("sub", "unknown")
    service = AdminDiscordService(settings)
    result = service.trigger_sync(admin_user_id, user_id, reason)

    # Enqueue background sync task
    enqueue_discord_sync(background_tasks, user_id, "admin_sync", reason)

    return JSONResponse(status_code=200, content=result)


@router.delete("/discord/users/{user_id}/disconnect")
async def admin_disconnect_discord(
    user_id: str,
    request: Request,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Disconnect a user's Discord account (admin action).

    Requires a reason field in the request body (5-500 characters).
    Deactivates the connection in DynamoDB and attempts to remove
    managed roles from the Discord guild.
    """
    # Parse reason from body
    reason = ""
    try:
        body = await request.body()
        if body:
            payload = json.loads(body.decode("utf-8"))
            reason = payload.get("reason", "")
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass

    if not reason:
        raise HTTPException(status_code=400, detail="Reason is required")

    admin_user_id = admin.get("sub", "unknown")
    service = AdminDiscordService(settings)

    try:
        result = service.disconnect(admin_user_id, user_id, reason)
        return JSONResponse(status_code=200, content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/discord/users/{user_id}/audit")
async def get_discord_user_audit(
    user_id: str,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get audit log entries for a user (admin view).

    Returns up to 100 most recent audit entries in reverse chronological order.
    """
    service = AdminDiscordService(settings)
    entries = service.get_audit_log(user_id)
    return JSONResponse(status_code=200, content={"entries": entries})


# ---------------------------------------------------------------------------
# Analytics (from main Lambda)
# ---------------------------------------------------------------------------


@router.get("/analytics")
async def get_analytics(
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get system-wide analytics and statistics.

    Returns totals for registered users, progress, completions, streaks,
    badges, quizzes, registration timeline, and top learners.
    """
    try:
        svc = AdminService(settings)

        TOTAL_PAGES = settings.total_module_pages or 96

        all_progress = svc.get_all_users_progress()
        all_registered = svc.get_all_registered_users()
        total_capstone_submissions = svc.get_total_capstone_submissions_count()
        badge_stats = svc.get_all_badge_stats()
        quiz_stats = svc.get_all_quiz_stats()

        registered_user_ids = {user["user_id"] for user in all_registered}
        users_with_progress: set = set()
        users_completed: set = set()
        total_completions = 0
        user_completion_counts: dict[str, int] = {}
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        active_learners_7d: set = set()

        for item in all_progress:
            uid = item.get("user_id")
            if uid:
                users_with_progress.add(uid)
                total_completions += 1
                user_completion_counts[uid] = user_completion_counts.get(uid, 0) + 1
                if user_completion_counts[uid] >= TOTAL_PAGES:
                    users_completed.add(uid)
                completed_at_str = item.get("completed_at", "")
                if completed_at_str:
                    try:
                        completed_at = datetime.fromisoformat(
                            completed_at_str.replace("Z", "+00:00")
                        )
                        if completed_at >= seven_days_ago:
                            active_learners_7d.add(uid)
                    except Exception:
                        pass

        total_registered = len(registered_user_ids)
        avg_completion = 0
        if users_with_progress:
            total_pct = sum(
                min(100.0, (c / TOTAL_PAGES) * 100)
                for c in user_completion_counts.values()
            )
            avg_completion = round(total_pct / len(users_with_progress), 1)

        # Registration timeline (last 30 days)
        registration_by_date: dict[str, int] = defaultdict(int)
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)

        for user in all_registered:
            registered_at_str = user.get("registered_at", "")
            if registered_at_str:
                try:
                    registered_at = datetime.fromisoformat(
                        registered_at_str.replace("Z", "+00:00")
                    )
                    if registered_at >= thirty_days_ago:
                        date_key = registered_at.strftime("%Y-%m-%d")
                        registration_by_date[date_key] += 1
                except Exception:
                    pass

        registration_timeline = []
        for i in range(30):
            date = now - timedelta(days=29 - i)
            date_key = date.strftime("%Y-%m-%d")
            registration_timeline.append(
                {"date": date_key, "count": registration_by_date.get(date_key, 0)}
            )

        user_id_to_username = {
            user["user_id"]: user.get("github_username")
            or user.get("username", f"User {user['user_id'][:8]}")
            for user in all_registered
        }

        analytics_data = {
            "total_registered_users": total_registered,
            "active_sessions": 0,
            "users_with_progress": len(users_with_progress),
            "users_completed_all": len(users_completed),
            "active_learners_7d": len(active_learners_7d),
            "total_capstone_submissions": total_capstone_submissions,
            "average_completion_rate": avg_completion,
            "engagement_rate": (
                round((len(users_with_progress) / total_registered * 100), 1)
                if total_registered > 0
                else 0
            ),
            "badge_stats": badge_stats,
            "quiz_stats": quiz_stats,
            "registration_timeline": registration_timeline,
            "completion_by_user": [
                {
                    "user_id": uid,
                    "username": user_id_to_username.get(uid, f"User {uid[:8]}"),
                    "completed": count,
                    "percentage": min(100.0, round((count / TOTAL_PAGES) * 100, 1)),
                }
                for uid, count in sorted(
                    user_completion_counts.items(), key=lambda x: x[1], reverse=True
                )
            ][:10],
        }

        return JSONResponse(status_code=200, content=analytics_data)

    except Exception as e:
        logger.error("Error fetching analytics: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")


# ---------------------------------------------------------------------------
# Submissions (from main Lambda)
# ---------------------------------------------------------------------------


@router.get("/submissions")
async def get_submissions(
    request: Request,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get all capstone submissions with pagination.

    Query params: page (default 1), page_size (default 50, max 100).
    """
    try:
        page_str = request.query_params.get("page", "1")
        page_size_str = request.query_params.get("page_size", "50")

        try:
            page = int(page_str)
            page_size = int(page_size_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid pagination parameters")

        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be >= 1")
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=400, detail="Page size must be between 1 and 100"
            )

        svc = AdminService(settings)

        submissions, total_count = svc.get_capstone_submissions(page, page_size)

        total_pages = (
            (total_count + page_size - 1) // page_size if total_count > 0 else 0
        )

        # Enrich submissions with credential status so the frontend knows
        # whether "Grant Cert" should be disabled (already issued)
        from app.services.certification.db import CertificationDB

        cert_db = CertificationDB(settings)
        # Collect unique user_ids from this page of submissions
        unique_user_ids = list({s["user_id"] for s in submissions})
        # Build a map: user_id -> dict of pathway_id -> credential_id for active credentials
        user_active_creds: dict[str, dict[str, str]] = {}
        for uid in unique_user_ids:
            try:
                creds = cert_db.list_user_credentials(uid)
                for c in creds:
                    if c.get("credential_status") in ("ACTIVE", "RENEWAL_ELIGIBLE"):
                        user_active_creds.setdefault(uid, {})[c["pathway_id"]] = c[
                            "credential_id"
                        ]
            except Exception as e:
                logger.warning("Failed to fetch credentials for user %s: %s", uid, e)

        # content_id -> pathway_id mapping (same as frontend)
        content_to_pathway: dict[str, str] = {
            "devsecops-capstone": "devsecops-engineering",
            "cloud_security_development-capstone": "cloud-security-engineering",
        }

        # Attach has_active_credential flag and credential_id to each submission
        for sub in submissions:
            pathway_id = content_to_pathway.get(sub.get("content_id", ""))
            if pathway_id and sub["user_id"] in user_active_creds:
                matching_cred = user_active_creds[sub["user_id"]].get(pathway_id)
                if matching_cred:
                    sub["has_active_credential"] = True
                    sub["credential_id"] = matching_cred
                else:
                    sub["has_active_credential"] = False
                    sub["credential_id"] = None
            else:
                sub["has_active_credential"] = False
                sub["credential_id"] = None

        return JSONResponse(
            status_code=200,
            content={
                "submissions": submissions,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching submissions: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve submissions")


# ---------------------------------------------------------------------------
# Registry Status (from main Lambda)
# ---------------------------------------------------------------------------


@router.get("/registry-status")
async def get_registry_status(
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get content registry health and cache status."""
    try:
        s3_bucket = settings.content_registry_bucket
        if not s3_bucket:
            raise HTTPException(status_code=503, detail="Service unavailable")

        try:
            registry_service = get_registry_service(s3_bucket)
        except ValueError:
            raise HTTPException(status_code=503, detail="Service unavailable")

        if registry_service._registry is None:
            raise HTTPException(status_code=503, detail="Content registry unavailable")

        # Build status from registry data
        entry_count = len(registry_service._registry.get("entries", {}))
        schema_version = registry_service._registry.get("schema_version", "unknown")
        status_data = {
            "status": "healthy",
            "schema_version": schema_version,
            "entry_count": entry_count,
            "bucket": s3_bucket,
            "last_loaded_at": registry_service._last_loaded_at,
        }
        return JSONResponse(status_code=200, content=status_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching registry status: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Module Health (from main Lambda)
# ---------------------------------------------------------------------------


@router.get("/module-health")
async def get_module_health(
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get module validation metrics and health status."""
    try:
        s3_bucket = settings.content_registry_bucket
        if not s3_bucket:
            raise HTTPException(status_code=503, detail="Service unavailable")

        try:
            registry_service = get_registry_service(s3_bucket)
        except ValueError:
            raise HTTPException(status_code=503, detail="Service unavailable")

        if registry_service._registry is None:
            raise HTTPException(status_code=503, detail="Content registry unavailable")

        # Build module health from registry entries
        entries = registry_service._registry.get("entries", {})
        quizzes = [e for e in entries.values() if e.get("content_type") == "quiz"]
        walkthroughs = [
            e for e in entries.values() if e.get("content_type") == "walkthrough"
        ]
        health_data = {
            "status": "healthy",
            "total_entries": len(entries),
            "quizzes": len(quizzes),
            "walkthroughs": len(walkthroughs),
        }
        return JSONResponse(status_code=200, content=health_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching module health: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve module health")


# ---------------------------------------------------------------------------
# Walkthrough Statistics (from main Lambda)
# ---------------------------------------------------------------------------


@router.get("/walkthrough-statistics")
async def get_walkthrough_statistics(
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get aggregate walkthrough statistics across all users."""
    try:
        svc = AdminService(settings)
        statistics = svc.get_walkthrough_statistics()
        return JSONResponse(status_code=200, content=statistics)

    except Exception as e:
        logger.error("Error fetching walkthrough statistics: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


# ---------------------------------------------------------------------------
# User Search (from main Lambda)
# ---------------------------------------------------------------------------


@router.get("/users/search")
async def user_search(
    request: Request,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Search for users by username or GitHub username.

    Query params: q (required search query).
    """
    try:
        search_query = request.query_params.get("q", "").strip().lower()
        if not search_query:
            raise HTTPException(
                status_code=400, detail="Search query parameter 'q' is required"
            )

        svc = AdminService(settings)

        all_users = svc.get_all_registered_users()

        matching_users = []
        for user in all_users:
            username_match = search_query in user.get("username", "").lower()
            github_match = search_query in user.get("github_username", "").lower()

            if username_match or github_match:
                try:
                    stats = svc.get_user_stats(user["user_id"])
                    progress_items = svc.get_user_progress(user["user_id"])
                    badges = calculate_user_badges(
                        stats,
                        progress_items,
                        table_name=settings.progress_table,
                        s3_bucket=settings.content_registry_bucket,
                    )
                    badges_earned = get_badges_earned_count(badges)

                    user_data = {
                        "user_id": user["user_id"],
                        "username": user.get("username", ""),
                        "github_username": user.get("github_username", ""),
                        "avatar_url": user.get("avatar_url", ""),
                        "registered_at": user.get("registered_at", ""),
                        "last_login": user.get("last_login", ""),
                        "stats": {
                            "completed_count": stats.get("completed_count", 0),
                            "overall_completion": stats.get("overall_completion", 0),
                            "quizzes_passed": stats.get("quizzes_passed", 0),
                            "walkthroughs_completed": stats.get(
                                "walkthroughs_completed", 0
                            ),
                            "capstone_submissions": stats.get(
                                "capstone_submissions", 0
                            ),
                            "badges_earned": badges_earned,
                        },
                    }
                    matching_users.append(user_data)
                except Exception as e:
                    logger.warning(
                        "Failed to get stats for user %s: %s", user["user_id"], e
                    )
                    user_data = {
                        "user_id": user["user_id"],
                        "username": user.get("username", ""),
                        "github_username": user.get("github_username", ""),
                        "avatar_url": user.get("avatar_url", ""),
                        "registered_at": user.get("registered_at", ""),
                        "last_login": user.get("last_login", ""),
                        "stats": {
                            "completed_count": 0,
                            "overall_completion": 0,
                            "quizzes_passed": 0,
                            "walkthroughs_completed": 0,
                            "capstone_submissions": 0,
                            "badges_earned": 0,
                        },
                    }
                    matching_users.append(user_data)

        matching_users.sort(key=lambda x: x["stats"]["completed_count"], reverse=True)

        return JSONResponse(
            status_code=200,
            content={"users": matching_users, "total_results": len(matching_users)},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in user search: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Users List (from main Lambda)
# ---------------------------------------------------------------------------


@router.get("/users")
async def list_users(
    request: Request,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get paginated list of all registered users.

    Query params: page (default 1), page_size (default 20, max 100), search (optional).
    """
    try:
        try:
            page = int(request.query_params.get("page", "1"))
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid pagination parameters")

        try:
            page_size = int(request.query_params.get("page_size", "20"))
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid pagination parameters")

        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be >= 1")
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=400, detail="Page size must be between 1 and 100"
            )

        svc = AdminService(settings)
        all_users = svc.get_all_registered_users()

        # Single scan of membership table to get tiers and contributor roles
        dynamodb = boto3_mod.client("dynamodb")
        membership_table = settings.membership_table

        tier_map: dict[str, str] = {}  # user_id -> tier
        contributor_map: dict[str, str] = {}  # user_id -> role

        # Scan membership table for MEMBERSHIP and CONTRIBUTOR_ROLE records
        last_key = None
        while True:
            scan_params: dict[str, Any] = {
                "TableName": membership_table,
                "FilterExpression": "SK = :mem OR SK = :contrib",
                "ExpressionAttributeValues": {
                    ":mem": {"S": "MEMBERSHIP"},
                    ":contrib": {"S": "CONTRIBUTOR_ROLE"},
                },
                "ProjectionExpression": "PK, SK, membership_tier, #r",
                "ExpressionAttributeNames": {"#r": "role"},
            }
            if last_key:
                scan_params["ExclusiveStartKey"] = last_key

            try:
                response = dynamodb.scan(**scan_params)
                for item in response.get("Items", []):
                    pk = item.get("PK", {}).get("S", "")
                    sk = item.get("SK", {}).get("S", "")
                    uid = pk.replace("USER#", "") if pk.startswith("USER#") else ""
                    if not uid:
                        continue

                    if sk == "MEMBERSHIP":
                        tier_map[uid] = item.get("membership_tier", {}).get("S", "FREE")
                    elif sk == "CONTRIBUTOR_ROLE":
                        role_val = item.get("role", {}).get("S")
                        if role_val:
                            contributor_map[uid] = role_val

                last_key = response.get("LastEvaluatedKey")
                if not last_key:
                    break
            except Exception as e:
                logger.warning("Membership table scan for enrichment failed: %s", e)
                break

        # Scan progress table for CREDENTIAL# records to get certification counts
        # Credentials: PK=USER#{id}, SK=CREDENTIAL#{credential_id}
        credentials_map: dict[str, list[dict[str, str]]] = (
            {}
        )  # user_id -> list of cred info
        last_key = None
        while True:
            scan_params = {
                "TableName": settings.progress_table,
                "FilterExpression": "begins_with(SK, :cred_prefix)",
                "ExpressionAttributeValues": {
                    ":cred_prefix": {"S": "CREDENTIAL#"},
                },
                "ProjectionExpression": "PK, SK, credential_status, pathway_id, credential_id, issued_at",
            }
            if last_key:
                scan_params["ExclusiveStartKey"] = last_key

            try:
                response = dynamodb.scan(**scan_params)
                for item in response.get("Items", []):
                    pk = item.get("PK", {}).get("S", "")
                    uid = pk.replace("USER#", "") if pk.startswith("USER#") else ""
                    if not uid:
                        continue

                    cred_status = item.get("credential_status", {}).get("S", "")
                    pathway_id = item.get("pathway_id", {}).get("S", "")
                    credential_id = item.get("credential_id", {}).get("S", "")
                    issued_at = item.get("issued_at", {}).get("S", "")

                    credentials_map.setdefault(uid, []).append(
                        {
                            "credential_id": credential_id,
                            "pathway_id": pathway_id,
                            "credential_status": cred_status,
                            "issued_at": issued_at,
                        }
                    )

                last_key = response.get("LastEvaluatedKey")
                if not last_key:
                    break
            except Exception as e:
                logger.warning("Progress table scan for credentials failed: %s", e)
                break

        # Apply enrichment to all users
        for user in all_users:
            uid = user["user_id"]
            user["membership_tier"] = tier_map.get(uid, "FREE")
            user["contributor_role"] = contributor_map.get(uid) or None
            user_creds = credentials_map.get(uid, [])
            # Only count active or renewal-eligible credentials
            active_creds = [
                c
                for c in user_creds
                if c["credential_status"] in ("ACTIVE", "RENEWAL_ELIGIBLE")
            ]
            user["certifications"] = active_creds
            user["certifications_count"] = len(active_creds)

        # Optional filters: email and role
        email_filter = request.query_params.get("email", "").strip().lower()
        role_filter = request.query_params.get("role", "").strip()

        if email_filter:
            all_users = [
                u for u in all_users if email_filter in (u.get("email") or "").lower()
            ]

        if role_filter:
            if role_filter == "CONTRIBUTOR":
                all_users = [u for u in all_users if u.get("contributor_role")]
            elif role_filter == "BUILDER":
                all_users = [
                    u for u in all_users if u.get("membership_tier") == "BUILDER"
                ]
            elif role_filter == "FREE":
                all_users = [
                    u
                    for u in all_users
                    if (u.get("membership_tier") or "FREE") == "FREE"
                    and not u.get("contributor_role")
                ]

        # Optional server-side search (now includes role fields)
        search_query = request.query_params.get("search", "").strip().lower()
        if search_query:
            all_users = [
                u
                for u in all_users
                if search_query in u.get("username", "").lower()
                or search_query in u.get("github_username", "").lower()
                or search_query in u.get("gitlab_username", "").lower()
                or search_query in u.get("bitbucket_username", "").lower()
                or search_query in u.get("provider", "").lower()
                or search_query in (u.get("membership_tier") or "").lower()
                or search_query in (u.get("contributor_role") or "").lower()
                or search_query in (u.get("email") or "").lower()
            ]

        all_users.sort(key=lambda u: u.get("username", "").lower())

        total_count = len(all_users)
        total_pages = max(1, math.ceil(total_count / page_size))

        start = (page - 1) * page_size
        end = start + page_size
        users_page = all_users[start:end]

        return JSONResponse(
            status_code=200,
            content={
                "users": users_page,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing users: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve users")


# ---------------------------------------------------------------------------
# User Profile (admin view, from main Lambda)
# ---------------------------------------------------------------------------


@router.get("/users/{user_id}/profile")
async def get_admin_user_profile(
    user_id: str,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get detailed user profile with stats and badges (admin view)."""
    try:
        svc = AdminService(settings)

        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")

        user = svc.get_user_profile(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Compute stats with graceful degradation
        try:
            stats = svc.get_user_stats(user_id)
            progress_items = svc.get_user_progress(user_id)
            badges = calculate_user_badges(
                stats,
                progress_items,
                table_name=settings.progress_table,
                s3_bucket=settings.content_registry_bucket,
            )
        except Exception as e:
            logger.warning("Failed to compute stats for user %s: %s", user_id, e)
            stats = {
                "completed_count": 0,
                "overall_completion": 0,
                "quizzes_passed": 0,
                "walkthroughs_completed": 0,
                "capstone_submissions": 0,
                "current_streak": 0,
                "longest_streak": 0,
            }
            badges = []

        # Fetch walkthrough progress
        try:
            walkthrough_progress = svc.get_user_walkthrough_progress(user_id)
        except Exception as e:
            logger.warning(
                "Failed to get walkthrough progress for user %s: %s", user_id, e
            )
            walkthrough_progress = []

        # Fetch contributor role
        contributor_role = None
        try:
            contributor_role = svc.get_contributor_role(user_id)
        except Exception as e:
            logger.warning("Failed to get contributor role for user %s: %s", user_id, e)

        return JSONResponse(
            status_code=200,
            content={
                "user": user,
                "stats": {
                    "completed_count": stats.get("completed_count", 0),
                    "overall_completion": stats.get("overall_completion", 0),
                    "quizzes_passed": stats.get("quizzes_passed", 0),
                    "walkthroughs_completed": stats.get("walkthroughs_completed", 0),
                    "capstone_submissions": stats.get("capstone_submissions", 0),
                    "current_streak": stats.get("current_streak", 0),
                    "longest_streak": stats.get("longest_streak", 0),
                },
                "badges": badges,
                "walkthrough_progress": walkthrough_progress,
                "contributor_role": contributor_role,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user profile: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Active Sessions (from main Lambda)
# ---------------------------------------------------------------------------


@router.get("/sessions")
async def get_active_sessions(
    request: Request,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get all active sessions (latest session per user, newest first)."""
    try:
        table_name = settings.progress_table
        if not table_name:
            raise HTTPException(status_code=503, detail="Service unavailable")

        dynamodb = boto3_mod.client("dynamodb")
        now = int(time_mod.time())

        all_sessions: list[dict] = []
        scan_kwargs: dict[str, Any] = {
            "TableName": table_name,
            "FilterExpression": "begins_with(SK, :sk_prefix) AND expires_at > :now",
            "ExpressionAttributeValues": {
                ":sk_prefix": {"S": "SESSION#"},
                ":now": {"N": str(now)},
            },
        }

        while True:
            response = dynamodb.scan(**scan_kwargs)
            for item in response.get("Items", []):
                all_sessions.append(
                    {
                        "user_id": item.get("user_id", {}).get("S", "unknown"),
                        "created_at": int(item.get("created_at", {}).get("N", "0")),
                        "expires_at": int(item.get("expires_at", {}).get("N", "0")),
                    }
                )
            if "LastEvaluatedKey" in response:
                scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            else:
                break

        # Keep only latest session per user
        latest_by_user: dict[str, dict] = {}
        for session in all_sessions:
            uid = session["user_id"]
            if (
                uid not in latest_by_user
                or session["created_at"] > latest_by_user[uid]["created_at"]
            ):
                latest_by_user[uid] = session

        # Resolve usernames via PROFILE records
        user_ids = list(latest_by_user.keys())
        username_map: dict[str, str] = {}
        for i in range(0, len(user_ids), 100):
            batch = user_ids[i : i + 100]
            keys = [
                {"PK": {"S": f"USER#{uid}"}, "SK": {"S": "PROFILE"}} for uid in batch
            ]
            try:
                batch_response = dynamodb.batch_get_item(
                    RequestItems={table_name: {"Keys": keys}}
                )
                for profile in batch_response.get("Responses", {}).get(table_name, []):
                    pk = profile.get("PK", {}).get("S", "")
                    uid = pk.removeprefix("USER#")
                    display_name = (
                        profile.get("github_username", {}).get("S", "")
                        or profile.get("gitlab_username", {}).get("S", "")
                        or profile.get("bitbucket_username", {}).get("S", "")
                        or profile.get("username", {}).get("S", "")
                    )
                    if display_name:
                        username_map[uid] = display_name
            except Exception as e:
                logger.warning("Failed to batch-get profiles: %s", e)

        for session in latest_by_user.values():
            uid = session["user_id"]
            session["username"] = username_map.get(uid, uid)

        sessions = sorted(
            latest_by_user.values(), key=lambda s: s["created_at"], reverse=True
        )

        return JSONResponse(
            status_code=200,
            content={"sessions": sessions, "total_active": len(sessions)},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in get_active_sessions: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Export Routes (from main Lambda)
# ---------------------------------------------------------------------------


@router.get("/export/users")
async def export_users(
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> Response:
    """Export all users with their stats as CSV."""
    try:
        svc = AdminService(settings)

        all_users = svc.get_all_registered_users()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "user_id",
                "username",
                "github_username",
                "registered_at",
                "completed_count",
                "overall_completion",
                "current_streak",
                "quizzes_passed",
            ]
        )

        for user in all_users:
            try:
                stats = svc.get_user_stats(user["user_id"])
                writer.writerow(
                    [
                        user["user_id"],
                        user.get("username", ""),
                        user.get("github_username", ""),
                        user.get("registered_at", ""),
                        stats.get("completed_count", 0),
                        stats.get("overall_completion", 0),
                        0,  # current_streak not tracked in admin_service stats
                        stats.get("quizzes_passed", 0),
                    ]
                )
            except Exception:
                writer.writerow(
                    [
                        user["user_id"],
                        user.get("username", ""),
                        user.get("github_username", ""),
                        user.get("registered_at", ""),
                        0,
                        0,
                        0,
                        0,
                    ]
                )

        csv_content = output.getvalue()
        output.close()

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="users_export.csv"',
            },
        )

    except Exception as e:
        logger.error("Error exporting users: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/export/capstone-submissions")
async def export_capstone_submissions(
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> Response:
    """Export all capstone submissions as CSV."""
    try:
        svc = AdminService(settings)

        submissions, _ = svc.get_capstone_submissions(1, 10000)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "user_id",
                "github_username",
                "content_id",
                "repo_url",
                "submitted_at",
            ]
        )

        for sub in submissions:
            writer.writerow(
                [
                    sub.get("user_id", ""),
                    sub.get("github_username", ""),
                    sub.get("content_id", ""),
                    sub.get("repo_url", ""),
                    sub.get("submitted_at", ""),
                ]
            )

        csv_content = output.getvalue()
        output.close()

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="capstone_submissions.csv"',
            },
        )

    except Exception as e:
        logger.error("Error exporting capstone submissions: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Capstone Review Routes (from main Lambda)
# ---------------------------------------------------------------------------


@router.post("/submissions/{target_user_id}/{content_id}/review")
async def submit_review(
    target_user_id: str,
    content_id: str,
    request: Request,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Submit qualitative feedback for a capstone submission.

    Validates submission exists and is in pending_review state, creates
    the review record, transitions submission status, creates in-app
    notification, and sends an email to the learner.
    """
    try:
        svc = AdminService(settings)

        username = (
            admin.get("github_login")
            or admin.get("gitlab_login")
            or admin.get("bitbucket_login")
            or admin.get("sub")
        )

        # Parse request body
        try:
            body = await request.body()
            body_data = json.loads(body.decode("utf-8")) if body else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="Invalid request body")

        feedback = body_data.get("feedback", "").strip()
        if not feedback:
            raise HTTPException(status_code=400, detail="Feedback is required")

        # Optional certification grade (passed, failed, revisions_required)
        grade = body_data.get("grade", "").strip().lower()

        # Verify submission exists
        submission = svc.get_capstone_submission(target_user_id, content_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Verify submission is in pending_review state
        if submission.get("status") != "pending_review":
            raise HTTPException(
                status_code=400, detail="Submission is not in a reviewable state"
            )

        # Create review record
        svc.save_capstone_review(target_user_id, content_id, feedback, username)

        # Update submission status
        # Use the grade as the submission status if provided, otherwise default to "reviewed"
        submission_status = (
            grade if grade in ("passed", "revisions_required") else "reviewed"
        )
        svc.update_capstone_submission_status(
            target_user_id, content_id, submission_status
        )

        # If the grade is "passed", mark the capstone as complete in the user's progress
        if submission_status == "passed":
            progress_db = ProgressDB(settings)
            try:
                progress_db.save_progress(target_user_id, content_id)
            except Exception:
                logger.error(
                    "Failed to mark capstone %s complete for user %s",
                    content_id,
                    target_user_id,
                )

        # Create in-app notification (fire-and-forget)
        try:
            capstone_paths = {
                "devsecops-capstone": "/learn/devsecops/capstone/index",
                "cloud_security_development-capstone": "/learn/cloud_security_development/capstone/index",
            }
            notification_link = capstone_paths.get(
                content_id,
                f"/learn/{content_id.replace('-capstone', '')}/capstone/index",
            )
            capstone_names = {
                "devsecops-capstone": "DevSecOps",
                "cloud_security_development-capstone": "Cloud Security Development",
            }
            capstone_display_name = capstone_names.get(
                content_id,
                content_id.replace("-capstone", "")
                .replace("_", " ")
                .replace("-", " ")
                .title(),
            )
            create_notification(
                user_id=target_user_id,
                message=f"Your {capstone_display_name} capstone has been reviewed. Feedback is now available.",
                link=notification_link,
            )
        except Exception as e:
            logger.error("Failed to create notification: %s", e)

        # Send email to learner (fire-and-forget)
        try:
            profile = svc.get_user_profile(target_user_id)
            if profile and profile.get("email"):
                send_review_notification_to_learner(
                    email=profile["email"],
                    username=profile.get("username", ""),
                    content_id=content_id,
                    feedback=feedback,
                )
        except Exception as e:
            logger.error("Failed to send review email: %s", e)

        return JSONResponse(
            status_code=200, content={"message": "Review submitted successfully"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in submit_review: %s", e)
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")


@router.get("/submissions/{target_user_id}/{content_id}/review")
async def get_review_admin(
    target_user_id: str,
    content_id: str,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get the review for a specific learner's capstone submission (admin view)."""
    try:
        svc = AdminService(settings)

        review = svc.get_capstone_review(target_user_id, content_id)

        if not review:
            return JSONResponse(status_code=200, content={"review": None})

        return JSONResponse(status_code=200, content={"review": review})

    except Exception as e:
        logger.error("Error in get_review_admin: %s", e)
        raise HTTPException(status_code=500, detail="Service temporarily unavailable")


# ---------------------------------------------------------------------------
# Contributor Role Mapping (admin override)
# ---------------------------------------------------------------------------


@router.get("/users/{user_id}/contributor-role")
async def get_contributor_role(
    user_id: str,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get the contributor role for a user (admin view)."""
    try:
        svc = AdminService(settings)
        role_data = svc.get_contributor_role(user_id)
        return JSONResponse(
            status_code=200,
            content={"contributor_role": role_data},
        )
    except Exception as e:
        logger.error("Error getting contributor role for %s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/users/{user_id}/contributor-role")
async def set_contributor_role(
    user_id: str,
    request: Request,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Assign or update a contributor role for a user.

    Body: { "role": "contributor"|"maintainer"|"reviewer"|"mentor", "note": "optional" }
    """
    try:
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Request body is required")

        try:
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="Invalid request body")

        role = payload.get("role", "").strip()
        note = payload.get("note", "").strip()

        if not role:
            raise HTTPException(status_code=400, detail="Role is required")

        admin_user_id = (
            admin.get("github_login")
            or admin.get("gitlab_login")
            or admin.get("bitbucket_login")
            or admin.get("sub", "unknown")
        )

        svc = AdminService(settings)

        try:
            result = svc.set_contributor_role(
                user_id=user_id,
                role=role,
                assigned_by=admin_user_id,
                note=note,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Assign the Discord contributor role if configured
        contributor_role_id = settings.discord_role_contributor_id
        if contributor_role_id:
            try:
                discord_svc = AdminDiscordService(settings)
                detail = discord_svc.get_user_detail(user_id)
                discord_user_id = detail.get("discord_user_id") if detail else None
                if discord_user_id:
                    import httpx

                    bot_token = discord_svc._get_bot_token()
                    if bot_token:
                        guild_id = settings.discord_guild_id
                        url = (
                            f"https://discord.com/api/v10/guilds/{guild_id}"
                            f"/members/{discord_user_id}/roles/{contributor_role_id}"
                        )
                        resp = httpx.put(
                            url,
                            headers={"Authorization": f"Bot {bot_token}"},
                            timeout=10,
                        )
                        if resp.status_code not in (204, 200):
                            logger.warning(
                                "Failed to add contributor Discord role to %s: %s",
                                discord_user_id,
                                resp.status_code,
                            )
            except Exception as e:
                logger.warning("Discord contributor role assignment failed: %s", e)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Contributor role assigned",
                "contributor_role": result,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error setting contributor role for %s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/users/{user_id}/contributor-role")
async def delete_contributor_role(
    user_id: str,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Remove a user's contributor role."""
    try:
        svc = AdminService(settings)
        success = svc.delete_contributor_role(user_id)
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to remove contributor role"
            )

        # Remove the Discord contributor role if configured
        contributor_role_id = settings.discord_role_contributor_id
        if contributor_role_id:
            try:
                discord_svc = AdminDiscordService(settings)
                detail = discord_svc.get_user_detail(user_id)
                discord_user_id = detail.get("discord_user_id") if detail else None
                if discord_user_id:
                    import httpx

                    bot_token = discord_svc._get_bot_token()
                    if bot_token:
                        guild_id = settings.discord_guild_id
                        url = (
                            f"https://discord.com/api/v10/guilds/{guild_id}"
                            f"/members/{discord_user_id}/roles/{contributor_role_id}"
                        )
                        resp = httpx.delete(
                            url,
                            headers={"Authorization": f"Bot {bot_token}"},
                            timeout=10,
                        )
                        if resp.status_code not in (204, 404):
                            logger.warning(
                                "Failed to remove contributor Discord role from %s: %s",
                                discord_user_id,
                                resp.status_code,
                            )
            except Exception as e:
                logger.warning("Discord contributor role removal failed: %s", e)

        return JSONResponse(
            status_code=200,
            content={"message": "Contributor role removed"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting contributor role for %s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Walkthrough Access Tier Management (paywall)
# ---------------------------------------------------------------------------


@router.get("/walkthroughs/access-tiers")
async def get_all_walkthrough_access_tiers(
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get access tiers for all walkthroughs (admin view).

    Returns a dict mapping walkthrough_id -> access_tier for walkthroughs
    with explicit tier records. Unlisted walkthroughs default to FREE.
    """
    try:
        svc = AdminService(settings)
        tiers = svc.get_all_walkthrough_access_tiers()
        return JSONResponse(status_code=200, content={"access_tiers": tiers})
    except Exception as e:
        logger.error("Error fetching walkthrough access tiers: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/walkthroughs/{walkthrough_id}/access-tier")
async def set_walkthrough_access_tier(
    walkthrough_id: str,
    request: Request,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Set the access tier for a walkthrough.

    Body: { "access_tier": "FREE" | "BUILDER" }
    """
    try:
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Request body is required")

        try:
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="Invalid request body")

        access_tier = payload.get("access_tier", "").strip().upper()
        if not access_tier:
            raise HTTPException(status_code=400, detail="access_tier is required")

        admin_user_id = (
            admin.get("github_login")
            or admin.get("gitlab_login")
            or admin.get("bitbucket_login")
            or admin.get("sub", "unknown")
        )

        svc = AdminService(settings)

        try:
            result = svc.set_walkthrough_access_tier(
                walkthrough_id=walkthrough_id,
                access_tier=access_tier,
                set_by=admin_user_id,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        return JSONResponse(
            status_code=200,
            content={"message": "Access tier updated", "data": result},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error setting access tier for walkthrough %s: %s", walkthrough_id, e
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/walkthroughs/{walkthrough_id}/access-tier")
async def delete_walkthrough_access_tier(
    walkthrough_id: str,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Reset a walkthrough's access tier to FREE (removes the record)."""
    try:
        svc = AdminService(settings)
        # Setting to FREE effectively removes the paywall
        admin_user_id = (
            admin.get("github_login")
            or admin.get("gitlab_login")
            or admin.get("bitbucket_login")
            or admin.get("sub", "unknown")
        )
        svc.set_walkthrough_access_tier(
            walkthrough_id=walkthrough_id,
            access_tier="FREE",
            set_by=admin_user_id,
        )
        return JSONResponse(
            status_code=200,
            content={"message": "Access tier reset to FREE"},
        )
    except Exception as e:
        logger.error(
            "Error resetting access tier for walkthrough %s: %s", walkthrough_id, e
        )
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Broadcast Notifications (admin)
# ---------------------------------------------------------------------------


@router.post("/broadcasts")
async def create_broadcast(
    request: Request,
    background_tasks: BackgroundTasks,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Create a broadcast notification and send email to all users.

    Body: { "title": "...", "message": "...(markdown)...", "link": "..." (optional) }
    """
    try:
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Request body is required")

        try:
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="Invalid request body")

        title = payload.get("title", "").strip()
        message = payload.get("message", "").strip()
        link = payload.get("link", "").strip()

        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
        if len(title) > 100:
            raise HTTPException(
                status_code=400, detail="Title must be 100 characters or less"
            )
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        if len(message) > 2000:
            raise HTTPException(
                status_code=400, detail="Message must be 2000 characters or less"
            )

        admin_username = (
            admin.get("github_login")
            or admin.get("gitlab_login")
            or admin.get("bitbucket_login")
            or admin.get("sub", "unknown")
        )

        svc = BroadcastService(settings)
        broadcast = svc.create_broadcast(
            title=title,
            message=message,
            created_by=admin_username,
            link=link,
        )

        # Enqueue email delivery as background task
        background_tasks.add_task(send_broadcast_emails, broadcast, settings)

        return JSONResponse(
            status_code=201,
            content={"message": "Broadcast created", "broadcast": broadcast},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating broadcast: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/broadcasts")
async def list_broadcasts(
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """List all active broadcasts (admin view)."""
    try:
        svc = BroadcastService(settings)
        broadcasts = svc.get_all_broadcasts()
        return JSONResponse(status_code=200, content={"broadcasts": broadcasts})
    except Exception as e:
        logger.error("Error listing broadcasts: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/broadcasts/{broadcast_id:path}")
async def delete_broadcast(
    broadcast_id: str,
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Delete a broadcast permanently."""
    try:
        svc = BroadcastService(settings)
        success = svc.delete_broadcast(broadcast_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete broadcast")
        return JSONResponse(status_code=200, content={"message": "Broadcast deleted"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting broadcast %s: %s", broadcast_id, e)
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Builder Journey Analytics (from builder-journey spec)
# ---------------------------------------------------------------------------


@router.get("/journey-analytics")
async def get_journey_analytics(
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Get aggregated journey metrics for the admin dashboard.

    Scans all JOURNEY# items across all users in the progress table and
    computes totals, phase distribution, funnel, task completion rates,
    key rates, and a 30-day timeline. Includes tier-differentiated metrics
    for Free vs Builder journeys.
    """
    from app.config.journey_tasks import (
        JOURNEY_PHASES,
        VALID_TASK_IDS,
        TOTAL_JOURNEY_TASKS,
        TASK_TO_PHASE,
        FREE_JOURNEY_PHASES,
        FREE_VALID_TASK_IDS,
        FREE_TOTAL_JOURNEY_TASKS,
        BUILDER_JOURNEY_PHASES,
        BUILDER_VALID_TASK_IDS,
        BUILDER_TOTAL_JOURNEY_TASKS,
    )

    try:
        dynamodb = boto3_mod.client("dynamodb")
        table_name = settings.progress_table

        # ------------------------------------------------------------------
        # 1. Scan all JOURNEY# items (with pagination)
        # ------------------------------------------------------------------
        all_items: list[dict] = []
        scan_kwargs: dict[str, Any] = {
            "TableName": table_name,
            "FilterExpression": "begins_with(SK, :sk_prefix)",
            "ExpressionAttributeValues": {
                ":sk_prefix": {"S": "JOURNEY#"},
            },
        }

        while True:
            response = dynamodb.scan(**scan_kwargs)
            all_items.extend(response.get("Items", []))
            if "LastEvaluatedKey" in response:
                scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            else:
                break

        # ------------------------------------------------------------------
        # 1b. Scan membership table to determine user tiers
        # ------------------------------------------------------------------
        user_tier_map: dict[str, str] = {}  # user_id -> "FREE" or "BUILDER"

        membership_scan_kwargs: dict[str, Any] = {
            "TableName": settings.membership_table,
            "FilterExpression": "SK = :mem OR SK = :contrib",
            "ExpressionAttributeValues": {
                ":mem": {"S": "MEMBERSHIP"},
                ":contrib": {"S": "CONTRIBUTOR_ROLE"},
            },
            "ProjectionExpression": "PK, SK, membership_tier, subscription_status",
        }

        builder_users: set[str] = set()
        while True:
            try:
                mem_response = dynamodb.scan(**membership_scan_kwargs)
                for item in mem_response.get("Items", []):
                    pk = item.get("PK", {}).get("S", "")
                    sk = item.get("SK", {}).get("S", "")
                    uid = pk.replace("USER#", "") if pk.startswith("USER#") else ""
                    if not uid:
                        continue
                    if sk == "CONTRIBUTOR_ROLE":
                        builder_users.add(uid)
                    elif sk == "MEMBERSHIP":
                        tier_val = item.get("membership_tier", {}).get("S", "FREE")
                        sub_status = item.get("subscription_status", {}).get("S")
                        if tier_val == "BUILDER" and sub_status in (
                            "active",
                            "past_due",
                        ):
                            builder_users.add(uid)
                last_key = mem_response.get("LastEvaluatedKey")
                if last_key:
                    membership_scan_kwargs["ExclusiveStartKey"] = last_key
                else:
                    break
            except Exception as e:
                logger.warning("Membership scan for tier analytics failed: %s", e)
                break

        # ------------------------------------------------------------------
        # 2. Group items by user
        # ------------------------------------------------------------------
        # user_id -> { "meta": item_or_None, "tasks": {task_id: item} }
        users: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"meta": None, "tasks": {}}
        )

        for item in all_items:
            pk = item.get("PK", {}).get("S", "")
            sk = item.get("SK", {}).get("S", "")
            if not pk.startswith("USER#"):
                continue
            user_id = pk[len("USER#") :]
            task_key = sk[len("JOURNEY#") :]

            if task_key == "_meta":
                users[user_id]["meta"] = item
            else:
                users[user_id]["tasks"][task_key] = item

        # ------------------------------------------------------------------
        # 3. Per-user analysis (overall + per-tier)
        # ------------------------------------------------------------------
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)

        journeys_started = 0
        journeys_completed = 0
        completed_durations: list[float] = []

        # Tier-specific counters
        tier_started: dict[str, int] = {"FREE": 0, "BUILDER": 0}
        tier_completed: dict[str, int] = {"FREE": 0, "BUILDER": 0}
        tier_active: dict[str, int] = {"FREE": 0, "BUILDER": 0}

        # 7-day active tracking
        seven_days_ago = now - timedelta(days=7)
        active_7d_count = 0

        # phase_distribution: phase_number -> count of users currently in that phase
        phase_distribution: dict[int, int] = defaultdict(int)

        # Per-phase completion tracking
        # phase -> list of days-to-complete for users who completed that phase
        phase_durations: dict[int, list[float]] = defaultdict(list)
        phase_completed_counts: dict[int, int] = defaultdict(int)

        # Per-task completion count
        task_completed_counts: dict[str, int] = defaultdict(int)

        # Timeline tracking
        starts_by_date: dict[str, int] = defaultdict(int)
        completions_by_date: dict[str, int] = defaultdict(int)

        for user_id, data in users.items():
            meta = data["meta"]
            completed_tasks = data["tasks"]

            # Determine this user's tier for analytics segmentation
            user_tier = "BUILDER" if user_id in builder_users else "FREE"

            # Count task completions for per-task rates
            for task_id in completed_tasks:
                if task_id in VALID_TASK_IDS:
                    task_completed_counts[task_id] += 1

            # User must have _meta to count as "started"
            if meta is None:
                continue

            journeys_started += 1
            tier_started[user_tier] += 1

            # Check if user had any task completion in last 7 days
            user_active_7d = False
            for task_item in completed_tasks.values():
                cat_str = task_item.get("completed_at", {}).get("S", "")
                if cat_str:
                    try:
                        cat = datetime.fromisoformat(cat_str.replace("Z", "+00:00"))
                        if cat >= seven_days_ago:
                            user_active_7d = True
                            break
                    except Exception:
                        pass
            if user_active_7d:
                active_7d_count += 1

            started_at_str = meta.get("started_at", {}).get("S", "")
            started_at: datetime | None = None
            if started_at_str:
                try:
                    started_at = datetime.fromisoformat(
                        started_at_str.replace("Z", "+00:00")
                    )
                except Exception:
                    pass

            # Timeline: starts in last 30 days
            if started_at and started_at >= thirty_days_ago:
                date_key = started_at.strftime("%Y-%m-%d")
                starts_by_date[date_key] += 1

            # Count completed tasks for this user (only valid task IDs)
            user_completed_count = sum(
                1 for t in completed_tasks if t in VALID_TASK_IDS
            )

            # Check if journey is fully complete (using Builder phases for overall)
            is_complete = user_completed_count >= TOTAL_JOURNEY_TASKS
            if is_complete:
                journeys_completed += 1
                tier_completed[user_tier] += 1

                # Calculate duration (started_at -> last task completed_at)
                if started_at:
                    last_completed_at: datetime | None = None
                    for task_item in completed_tasks.values():
                        cat_str = task_item.get("completed_at", {}).get("S", "")
                        if cat_str:
                            try:
                                cat = datetime.fromisoformat(
                                    cat_str.replace("Z", "+00:00")
                                )
                                if last_completed_at is None or cat > last_completed_at:
                                    last_completed_at = cat
                            except Exception:
                                pass
                    if last_completed_at:
                        duration_days = (
                            last_completed_at - started_at
                        ).total_seconds() / 86400
                        completed_durations.append(duration_days)

                        # Timeline: completions in last 30 days
                        if last_completed_at >= thirty_days_ago:
                            date_key = last_completed_at.strftime("%Y-%m-%d")
                            completions_by_date[date_key] += 1
            else:
                tier_active[user_tier] += 1

            # Determine current phase (first phase with incomplete tasks)
            current_phase = 5  # default to last phase
            for phase_num in sorted(JOURNEY_PHASES.keys()):
                phase_tasks = JOURNEY_PHASES[phase_num]
                if any(t not in completed_tasks for t in phase_tasks):
                    current_phase = phase_num
                    break

            if not is_complete:
                phase_distribution[current_phase] += 1

            # Per-phase completion tracking
            if started_at:
                for phase_num in sorted(JOURNEY_PHASES.keys()):
                    phase_tasks = JOURNEY_PHASES[phase_num]
                    all_phase_done = all(t in completed_tasks for t in phase_tasks)
                    if all_phase_done:
                        phase_completed_counts[phase_num] += 1
                        # Avg days: latest completed_at in phase - started_at
                        latest_in_phase: datetime | None = None
                        for t in phase_tasks:
                            if t in completed_tasks:
                                cat_str = (
                                    completed_tasks[t]
                                    .get("completed_at", {})
                                    .get("S", "")
                                )
                                if cat_str:
                                    try:
                                        cat = datetime.fromisoformat(
                                            cat_str.replace("Z", "+00:00")
                                        )
                                        if (
                                            latest_in_phase is None
                                            or cat > latest_in_phase
                                        ):
                                            latest_in_phase = cat
                                    except Exception:
                                        pass
                        if latest_in_phase:
                            days = (
                                latest_in_phase - started_at
                            ).total_seconds() / 86400
                            phase_durations[phase_num].append(days)

        # ------------------------------------------------------------------
        # 4. Compute aggregates
        # ------------------------------------------------------------------
        completion_rate = (
            round(journeys_completed / journeys_started * 100, 1)
            if journeys_started > 0
            else 0
        )
        average_duration_days = (
            round(sum(completed_durations) / len(completed_durations))
            if completed_durations
            else 0
        )

        # Phase distribution dict (string keys for JSON)
        phase_dist_output: dict[str, int] = {
            str(p): phase_distribution.get(p, 0) for p in sorted(JOURNEY_PHASES.keys())
        }

        # Phase completion funnel
        phase_funnel: list[dict[str, Any]] = []
        for phase_num in sorted(JOURNEY_PHASES.keys()):
            avg_days = 0
            if phase_durations[phase_num]:
                avg_days = round(
                    sum(phase_durations[phase_num]) / len(phase_durations[phase_num])
                )
            phase_funnel.append(
                {
                    "phase": phase_num,
                    "completed_count": phase_completed_counts.get(phase_num, 0),
                    "avg_days": avg_days,
                }
            )

        # Task completion rates
        task_rates: list[dict[str, Any]] = []
        for phase_num in sorted(JOURNEY_PHASES.keys()):
            for task_id in JOURNEY_PHASES[phase_num]:
                rate = (
                    round(task_completed_counts[task_id] / journeys_started * 100, 1)
                    if journeys_started > 0
                    else 0
                )
                task_rates.append(
                    {
                        "task_id": task_id,
                        "phase": phase_num,
                        "completion_rate": rate,
                    }
                )

        # Key rates
        discord_rate = (
            round(
                task_completed_counts.get("connect-discord", 0)
                / journeys_started
                * 100,
                1,
            )
            if journeys_started > 0
            else 0
        )
        prereqs_rate = (
            round(
                task_completed_counts.get("complete-prerequisites-path", 0)
                / journeys_started
                * 100,
                1,
            )
            if journeys_started > 0
            else 0
        )

        # 30-day timeline
        timeline_starts: list[dict[str, Any]] = []
        timeline_completions: list[dict[str, Any]] = []
        for i in range(30):
            date = now - timedelta(days=29 - i)
            date_key = date.strftime("%Y-%m-%d")
            start_count = starts_by_date.get(date_key, 0)
            comp_count = completions_by_date.get(date_key, 0)
            if start_count > 0:
                timeline_starts.append({"date": date_key, "count": start_count})
            if comp_count > 0:
                timeline_completions.append({"date": date_key, "count": comp_count})

        # Tier-specific completion rates
        free_completion_rate = (
            round(tier_completed["FREE"] / tier_started["FREE"] * 100, 1)
            if tier_started["FREE"] > 0
            else 0
        )
        builder_completion_rate = (
            round(tier_completed["BUILDER"] / tier_started["BUILDER"] * 100, 1)
            if tier_started["BUILDER"] > 0
            else 0
        )

        # Phase distribution with names for display
        phase_names: dict[int, str] = {
            1: "Welcome to Builder",
            2: "Join the Community",
            3: "Build Your Foundation",
            4: "Choose Your Engineering Path",
            5: "Build Momentum",
        }

        # 7-day active rate
        seven_day_active_rate = (
            round(active_7d_count / journeys_started * 100, 1)
            if journeys_started > 0
            else 0
        )

        result = {
            "totals": {
                "journeys_started": journeys_started,
                "journeys_completed": journeys_completed,
                "completion_rate": completion_rate,
                "average_duration_days": average_duration_days,
                "seven_day_active_rate": seven_day_active_rate,
                "active_7d_count": active_7d_count,
            },
            "by_tier": {
                "FREE": {
                    "journeys_started": tier_started["FREE"],
                    "journeys_completed": tier_completed["FREE"],
                    "active_users": tier_active["FREE"],
                    "completion_rate": free_completion_rate,
                },
                "BUILDER": {
                    "journeys_started": tier_started["BUILDER"],
                    "journeys_completed": tier_completed["BUILDER"],
                    "active_users": tier_active["BUILDER"],
                    "completion_rate": builder_completion_rate,
                },
            },
            "phase_distribution": phase_dist_output,
            "phase_distribution_named": [
                {
                    "phase": p,
                    "name": phase_names.get(p, f"Phase {p}"),
                    "count": phase_distribution.get(p, 0),
                }
                for p in sorted(JOURNEY_PHASES.keys())
            ],
            "phase_completion_funnel": phase_funnel,
            "task_completion_rates": task_rates,
            "key_rates": {
                "discord_connection_rate": discord_rate,
                "prerequisites_completion_rate": prereqs_rate,
            },
            "timeline_30d": {
                "starts": timeline_starts,
                "completions": timeline_completions,
            },
        }

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        logger.error("Error fetching journey analytics: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch journey analytics")
