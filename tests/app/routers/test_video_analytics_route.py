"""Tests for GET /admin/videos/analytics.

Includes the properties that keep the endpoint from hurting the rest of the
API: it is registered above GET /{video_id}, it runs off the event loop, and a
slow computation does not delay other requests.
"""

import asyncio
import inspect
import os
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import boto3
import httpx
import pytest
from fastapi.testclient import TestClient
from jose import jwt
from moto import mock_aws

from app.config import Settings
from app.main import app
from app.services import video_analytics_service as svc_mod
from app.services.video_analytics_service import AnalyticsUnavailable

SECRET = "test-secret-key-for-jwt-signing-32chars"

SETTINGS = Settings(
    membership_table="m",
    progress_table="progress",
    user_state_table="u",
    testimonials_table="t",
    notifications_table="n",
    discord_secret_name="d",
    discord_bot_secret_name="db",
    stripe_secret_name="s",
    stripe_webhook_secret_name="sw",
    jwt_secret_name="j",
    github_secret_name="g",
    gitlab_secret_name="gl",
    bitbucket_secret_name="bb",
    discord_guild_id="1",
    discord_role_free_id="1",
    discord_role_explorer_id="2",
    discord_role_builder_id="3",
    discord_role_builder_academy_id="4",
    discord_callback_url="https://example.com/cb",
    frontend_url="https://example.com",
    frontend_origin="https://example.com",
    github_callback_url="https://example.com/g",
    gitlab_callback_url="https://example.com/gl",
    bitbucket_callback_url="https://example.com/bb",
    admin_users="github:testadmin",
    videos_table="videos",
)

PAYLOAD = {
    "generated_at": "2026-06-15T12:00:00+00:00",
    "stale": False,
    "totals": {
        "distinct_viewers": 3,
        "active_7d": 2,
        "active_30d": 3,
        "completions": 1,
        "completion_rate": 33,
    },
    "by_tier": {
        "FREE": {"viewers": 1, "completions": 0, "completion_rate": 0},
        "BUILDER": {"viewers": 2, "completions": 1, "completion_rate": 50},
    },
    "top_videos": [],
    "videos": [],
}


def headers(login="testadmin"):
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": f"user-{login}",
            "provider": "github",
            "github_login": login,
            "iat": now,
            "exp": now + timedelta(hours=1),
        },
        SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def auth_and_settings():
    from app.auth.jwt import _jwt_secret_cache
    from app.dependencies import get_settings

    _jwt_secret_cache["secret_key"] = SECRET
    _jwt_secret_cache["fetched_at"] = 9999999999.0
    app.dependency_overrides[get_settings] = lambda: SETTINGS
    svc_mod.reset_cache()
    yield
    app.dependency_overrides.clear()
    svc_mod.reset_cache()
    _jwt_secret_cache["secret_key"] = None
    _jwt_secret_cache["fetched_at"] = 0.0


@pytest.fixture
def client():
    return TestClient(app)


class TestAccess:
    def test_requires_auth(self, client):
        assert client.get("/admin/videos/analytics").status_code == 401

    def test_forbidden_for_non_admin(self, client):
        resp = client.get("/admin/videos/analytics", headers=headers("regular"))
        assert resp.status_code == 403


class TestResponses:
    def test_success_returns_service_result(self, client):
        with patch.object(
            svc_mod.VideoAnalyticsService, "get_analytics", return_value=PAYLOAD
        ):
            resp = client.get("/admin/videos/analytics", headers=headers())
        assert resp.status_code == 200
        assert resp.json() == PAYLOAD

    def test_unavailable_returns_503_with_friendly_message(self, client):
        with patch.object(
            svc_mod.VideoAnalyticsService,
            "get_analytics",
            side_effect=AnalyticsUnavailable("boom"),
        ):
            resp = client.get("/admin/videos/analytics", headers=headers())
        assert resp.status_code == 503
        assert "try again" in resp.json()["detail"].lower()
        assert "boom" not in resp.text  # internal detail is not leaked

    def test_unexpected_error_returns_500_without_detail(self, client):
        with patch.object(
            svc_mod.VideoAnalyticsService,
            "get_analytics",
            side_effect=RuntimeError("secret internals"),
        ):
            resp = client.get("/admin/videos/analytics", headers=headers())
        assert resp.status_code == 500
        assert "secret internals" not in resp.text


class TestRouting:
    def test_not_captured_by_video_id_route(self, client):
        """GET /{video_id} is registered too; /analytics must win."""
        from app.routers.videos_admin import get_video_service

        video_svc = MagicMock()
        app.dependency_overrides[get_video_service] = lambda: video_svc
        with patch.object(
            svc_mod.VideoAnalyticsService, "get_analytics", return_value=PAYLOAD
        ):
            resp = client.get("/admin/videos/analytics", headers=headers())
        assert resp.json() == PAYLOAD
        video_svc.get_video_admin.assert_not_called()

    def test_video_id_route_still_works(self, client):
        from app.routers.videos_admin import get_video_service

        video_svc = MagicMock()

        async def not_found(_):
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Video not found")

        video_svc.get_video_admin = not_found
        app.dependency_overrides[get_video_service] = lambda: video_svc
        resp = client.get("/admin/videos/some-video-id", headers=headers())
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Video not found"


class TestDoesNotBlockTheApi:
    def test_endpoint_is_a_plain_function_so_it_runs_in_the_thread_pool(self):
        from app.routers import videos_admin

        route = next(
            r
            for r in videos_admin.router.routes
            if getattr(r, "path", "") == "/admin/videos/analytics"
        )
        assert not inspect.iscoroutinefunction(route.endpoint)
        assert route.endpoint is videos_admin.get_video_analytics

    def test_slow_analytics_does_not_delay_other_requests(self):
        """Run both requests on ONE event loop (as in production).

        If the analytics endpoint blocked the loop, /health would wait for it.
        """

        def slow(self):
            time.sleep(1.0)  # a blocking computation
            return PAYLOAD

        async def scenario():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
                t0 = time.monotonic()

                async def timed(request):
                    response = await request
                    return response, time.monotonic() - t0

                # Start the slow request first, then a cheap one, on one loop.
                slow_task = asyncio.create_task(
                    timed(c.get("/admin/videos/analytics", headers=headers()))
                )
                await asyncio.sleep(0)
                health_task = asyncio.create_task(timed(c.get("/health")))
                return await asyncio.gather(slow_task, health_task)

        with patch.object(svc_mod.VideoAnalyticsService, "get_analytics", slow):
            (slow_response, slow_seconds), (health, health_seconds) = asyncio.run(
                scenario()
            )

        assert health.status_code == 200
        assert slow_response.status_code == 200
        assert slow_seconds >= 0.9  # the computation really took ~1 s
        # the cheap request finished long before it, i.e. was not held up
        assert health_seconds < 0.5


class TestEndToEnd:
    def test_through_the_route_with_real_scan_and_no_identifiers(self, client):
        env = {
            "AWS_ACCESS_KEY_ID": "testing",
            "AWS_SECRET_ACCESS_KEY": "testing",
            "AWS_DEFAULT_REGION": "us-east-2",
        }
        with patch.dict(os.environ, env), mock_aws():
            raw = boto3.client("dynamodb", region_name="us-east-2")
            for name in ("progress", "videos"):
                raw.create_table(
                    TableName=name,
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
            raw.put_item(
                TableName="videos",
                Item={
                    "PK": {"S": "VIDEO#v1"},
                    "SK": {"S": "METADATA"},
                    "id": {"S": "v1"},
                    "title": {"S": "Intro"},
                    "slug": {"S": "intro"},
                    "status": {"S": "PUBLISHED"},
                    "accessTier": {"S": "FREE"},
                },
            )
            for user, pct, done in (
                ("member-secret-1", 100, True),
                ("member-secret-2", 20, False),
            ):
                raw.put_item(
                    TableName="progress",
                    Item={
                        "PK": {"S": f"USER#{user}"},
                        "SK": {"S": "VIDEO#v1"},
                        "percentComplete": {"N": str(pct)},
                        "completed": {"BOOL": done},
                        "lastWatchedAt": {"S": datetime.now(timezone.utc).isoformat()},
                    },
                )

            first = client.get("/admin/videos/analytics", headers=headers())
            assert first.status_code == 200
            body = first.json()
            assert body["stale"] is False
            assert body["totals"]["distinct_viewers"] == 2
            assert body["totals"]["completion_rate"] == 50
            assert body["videos"][0]["unique_viewers"] == 2
            assert body["top_videos"][0]["title"] == "Intro"
            assert "member-secret" not in first.text  # aggregates only

            # a second page load is served from the cache without rescanning
            with patch.object(
                svc_mod.VideoAnalyticsService,
                "_compute",
                side_effect=AssertionError("rescanned"),
            ):
                second = client.get("/admin/videos/analytics", headers=headers())
            assert second.status_code == 200
            assert second.json()["generated_at"] == body["generated_at"]
