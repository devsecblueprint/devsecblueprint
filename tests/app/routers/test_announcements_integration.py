"""End-to-end tests for the announcement admin API against a moto ledger.

These go through real HTTP routing, auth, the background-task wiring, and the
real AnnouncementService + DynamoDB semantics. Only the outside world
(broadcast storage, SES emails, the videos table, and the content registry)
is mocked.
"""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import boto3
import pytest
from fastapi.testclient import TestClient
from jose import jwt
from moto import mock_aws

from app.config import Settings
from app.main import app
from app.services import announcement_service as svc_mod

TABLE = "integration-announcements"
SECRET = "test-secret-key-for-jwt-signing-32chars"

SETTINGS = Settings(
    membership_table="m",
    progress_table="p",
    user_state_table="u",
    testimonials_table="t",
    notifications_table="n",
    broadcasts_table="b",
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
    frontend_origin="https://dsb.example",
    github_callback_url="https://example.com/g",
    gitlab_callback_url="https://example.com/gl",
    bitbucket_callback_url="https://example.com/bb",
    admin_users="github:adminuser",
    announcements_table=TABLE,
    announcements_enabled=True,
    content_registry_bucket="registry-bucket",
)


def _headers(login: str = "adminuser") -> dict[str, str]:
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


@pytest.fixture
def world():
    """A moto-backed ledger plus a TestClient with admin auth wired up."""
    from app.auth.jwt import _jwt_secret_cache
    from app.dependencies import get_settings

    env = {
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_DEFAULT_REGION": "us-east-2",
    }
    _jwt_secret_cache["secret_key"] = SECRET
    _jwt_secret_cache["fetched_at"] = 9999999999.0
    app.dependency_overrides[get_settings] = lambda: SETTINGS

    with patch.dict(os.environ, env), mock_aws():
        boto3.client("dynamodb", region_name="us-east-2").create_table(
            TableName=TABLE,
            BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[
                {"AttributeName": n, "AttributeType": "S"}
                for n in ("PK", "SK", "GSI1PK", "GSI1SK")
            ],
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI1",
                    "KeySchema": [
                        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        )
        broadcasts = MagicMock()
        broadcasts.create_broadcast.side_effect = lambda **kw: {
            "broadcast_id": "bc-1",
            **kw,
        }
        emails = MagicMock(return_value={"sent": 3, "failed": 0, "total": 3})
        with (
            patch.object(svc_mod, "BroadcastService", return_value=broadcasts),
            patch.object(svc_mod, "send_broadcast_emails", emails),
        ):
            yield MagicMock(
                client=TestClient(app), broadcasts=broadcasts, emails=emails
            )

    app.dependency_overrides.clear()
    _jwt_secret_cache["secret_key"] = None
    _jwt_secret_cache["fetched_at"] = 0.0


def _registry(*ids):
    registry = MagicMock()
    registry.get_all_walkthrough_entries.return_value = [
        {
            "id": i,
            "title": f"WT {i}",
            "description": "desc",
            "difficulty": "Beginner",
            "topics": ["a"],
            "estimated_time": 30,
        }
        for i in ids
    ]
    return patch.object(svc_mod, "get_registry_service", return_value=registry)


def _video_item(status="PUBLISHED"):
    return {
        "id": {"S": "v1"},
        "title": {"S": "Intro"},
        "slug": {"S": "intro"},
        "description": {"S": "d"},
        "instructor": {"S": "Jane"},
        "durationSeconds": {"N": "600"},
        "tags": {"L": []},
        "accessTier": {"S": "FREE"},
        "status": {"S": status},
    }


def test_requires_admin(world):
    assert world.client.get("/admin/announcements").status_code == 401
    assert (
        world.client.get(
            "/admin/announcements", headers=_headers("regular")
        ).status_code
        == 403
    )


def test_empty_ledger(world):
    resp = world.client.get("/admin/announcements", headers=_headers())
    assert resp.status_code == 200
    assert resp.json() == {"enabled": True, "failed_count": 0, "announcements": []}


def test_baseline_then_only_new_walkthroughs_are_announced(world):
    headers = _headers()
    with _registry("old-a", "old-b"):
        resp = world.client.post("/admin/announcements/baseline", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["baselined"] == 2

    listed = world.client.get("/admin/announcements", headers=headers).json()
    assert {a["status"] for a in listed["announcements"]} == {"BASELINED"}

    # A scan with one brand new walkthrough records it as PENDING (settle delay)
    with _registry("old-a", "old-b", "new-c"):
        stats = svc_mod.AnnouncementService(SETTINGS).scan_walkthroughs()
    assert stats["baselined"] == 0 and stats["recorded"] == 1
    world.broadcasts.create_broadcast.assert_not_called()

    pending = world.client.get(
        "/admin/announcements?status=pending", headers=headers
    ).json()["announcements"]
    assert [a["content_key"] for a in pending] == ["WALKTHROUGH#new-c"]


def test_failed_video_retry_end_to_end(world):
    headers = _headers()
    service = svc_mod.AnnouncementService(SETTINGS)
    service._record_new("VIDEO#v1", "video", "v1", "Intro", "SENDING")
    service._mark_failed("VIDEO#v1", "SES was down")

    listed = world.client.get("/admin/announcements", headers=headers).json()
    assert listed["failed_count"] == 1
    assert listed["announcements"][0]["last_error"] == "SES was down"

    db = MagicMock()
    db.get_video.return_value = _video_item()
    with patch.object(svc_mod, "VideoMetadataDB", return_value=db):
        # '#' must be URL-encoded as the frontend does
        resp = world.client.post(
            "/admin/announcements/VIDEO%23v1/retry", headers=headers
        )
    assert resp.status_code == 200

    # The background task ran: broadcast created, emails sent, ledger updated
    world.broadcasts.create_broadcast.assert_called_once()
    kwargs = world.broadcasts.create_broadcast.call_args.kwargs
    assert kwargs["title"] == "New video: Intro"
    assert kwargs["created_by"] == "system:auto-announce"
    assert kwargs["link"] == "https://dsb.example/videos/preview/intro"
    world.emails.assert_called_once()

    after = world.client.get("/admin/announcements", headers=headers).json()
    assert after["failed_count"] == 0
    assert after["announcements"][0]["status"] == "SENT"
    assert after["announcements"][0]["broadcast_id"] == "bc-1"


def test_retry_error_statuses(world):
    headers = _headers()
    assert (
        world.client.post(
            "/admin/announcements/VIDEO%23nope/retry", headers=headers
        ).status_code
        == 404
    )

    service = svc_mod.AnnouncementService(SETTINGS)
    service._record_new("VIDEO#v1", "video", "v1", "Intro", "SENT")
    resp = world.client.post("/admin/announcements/VIDEO%23v1/retry", headers=headers)
    assert resp.status_code == 409

    service._record_new("VIDEO#v2", "video", "v2", "Gone", "SENDING")
    service._mark_failed("VIDEO#v2", "x")
    db = MagicMock()
    db.get_video.return_value = _video_item(status="ARCHIVED")
    with patch.object(svc_mod, "VideoMetadataDB", return_value=db):
        resp = world.client.post(
            "/admin/announcements/VIDEO%23v2/retry", headers=headers
        )
    assert resp.status_code == 409
    assert "no longer published" in resp.json()["detail"]
    world.broadcasts.create_broadcast.assert_not_called()


def test_double_retry_only_delivers_once(world):
    headers = _headers()
    service = svc_mod.AnnouncementService(SETTINGS)
    service._record_new("VIDEO#v1", "video", "v1", "Intro", "SENDING")
    service._mark_failed("VIDEO#v1", "x")
    db = MagicMock()
    db.get_video.return_value = _video_item()
    with patch.object(svc_mod, "VideoMetadataDB", return_value=db):
        first = world.client.post(
            "/admin/announcements/VIDEO%23v1/retry", headers=headers
        )
        second = world.client.post(
            "/admin/announcements/VIDEO%23v1/retry", headers=headers
        )
    assert first.status_code == 200
    assert second.status_code == 409  # already SENT by the first retry
    assert world.broadcasts.create_broadcast.call_count == 1
