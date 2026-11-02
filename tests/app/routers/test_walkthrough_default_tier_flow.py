"""End-to-end: the walkthrough default tier is Builder.

Real AdminService + real DynamoDB semantics (moto) behind the real endpoints
and the real migration. Only membership and the progress writer are stubbed.
"""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import boto3
import pytest
from fastapi.testclient import TestClient
from jose import jwt
from moto import mock_aws

from app.config import Settings
from app.main import app
from app.services.walkthrough_tier_migration import backfill_free_tiers

SECRET = "test-secret-key-for-jwt-signing-32chars"
TABLE = "progress"


def settings(**overrides) -> Settings:
    values = dict(
        membership_table="membership",
        progress_table=TABLE,
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
        admin_users="github:adminuser",
    )
    values.update(overrides)
    return Settings(**values)


def headers(login="member", sub="user-1"):
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": sub,
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
    """moto progress table plus an app whose settings point at it."""
    from app.auth.jwt import _jwt_secret_cache
    from app.dependencies import get_settings

    env = {
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_DEFAULT_REGION": "us-east-2",
    }
    _jwt_secret_cache["secret_key"] = SECRET
    _jwt_secret_cache["fetched_at"] = 9999999999.0
    current = {"settings": settings()}
    app.dependency_overrides[get_settings] = lambda: current["settings"]

    with (
        patch.dict(os.environ, env),
        mock_aws(),
        patch("app.routers.content.get_settings", lambda: current["settings"]),
        patch("app.routers.content.MembershipDB") as membership,
        patch("app.routers.content._update_progress") as update,
    ):
        client = boto3.client("dynamodb", region_name="us-east-2")
        client.create_table(
            TableName=TABLE,
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
        membership.return_value.get_membership.return_value = None  # free member
        yield type(
            "World",
            (),
            {
                "http": TestClient(app),
                "ddb": client,
                "membership": membership.return_value,
                "update": update,
                "current": current,
            },
        )

    app.dependency_overrides.clear()
    _jwt_secret_cache["secret_key"] = None
    _jwt_secret_cache["fetched_at"] = 0.0


def set_tier(world, wid, tier):
    resp = world.http.put(
        f"/admin/walkthroughs/{wid}/access-tier",
        headers=headers("adminuser", "admin-1"),
        json={"access_tier": tier},
    )
    assert resp.status_code == 200
    return resp


def post_progress(world, wid):
    return world.http.post(
        f"/api/walkthroughs/{wid}/progress",
        headers=headers(),
        json={"status": "in_progress"},
    )


def public_tiers(world):
    return world.http.get("/api/walkthroughs/access-tiers", headers=headers()).json()


class TestDefaultIsBuilder:
    def test_new_walkthrough_with_no_record_is_locked_for_a_free_member(self, world):
        resp = post_progress(world, "brand-new-walkthrough")
        assert resp.status_code == 403
        assert "Builder" in resp.json()["detail"]
        world.update.assert_not_called()

    def test_admin_marking_it_free_opens_it(self, world):
        assert post_progress(world, "new-one").status_code == 403
        set_tier(world, "new-one", "FREE")
        assert post_progress(world, "new-one").status_code == 200
        world.update.assert_called_once()

    def test_marking_free_does_not_open_other_new_walkthroughs(self, world):
        set_tier(world, "opened", "FREE")
        assert post_progress(world, "opened").status_code == 200
        assert post_progress(world, "another-new-one").status_code == 403

    def test_builder_members_can_use_unlisted_walkthroughs(self, world):
        world.membership.get_membership.return_value = {
            "membership_tier": {"S": "BUILDER"},
            "subscription_status": {"S": "active"},
        }
        assert post_progress(world, "brand-new-walkthrough").status_code == 200

    def test_public_endpoint_reports_default_and_explicit_records(self, world):
        set_tier(world, "paid", "BUILDER")
        set_tier(world, "open", "FREE")
        body = public_tiers(world)
        assert body == {
            "access_tiers": {"paid": "BUILDER", "open": "FREE"},
            "default_tier": "BUILDER",
        }

    def test_admin_endpoint_reports_the_same_default(self, world):
        set_tier(world, "open", "FREE")
        resp = world.http.get(
            "/admin/walkthroughs/access-tiers",
            headers=headers("adminuser", "admin-1"),
        )
        assert resp.json() == {
            "access_tiers": {"open": "FREE"},
            "default_tier": "BUILDER",
        }

    def test_resetting_to_free_keeps_an_explicit_free_record(self, world):
        set_tier(world, "wt", "BUILDER")
        resp = world.http.delete(
            "/admin/walkthroughs/wt/access-tier",
            headers=headers("adminuser", "admin-1"),
        )
        assert resp.status_code == 200
        assert public_tiers(world)["access_tiers"] == {"wt": "FREE"}
        assert post_progress(world, "wt").status_code == 200


class TestRollbackSetting:
    def test_free_default_setting_restores_the_old_behavior(self, world):
        world.current["settings"] = settings(walkthrough_default_tier="FREE")
        assert post_progress(world, "unlisted").status_code == 200
        assert public_tiers(world)["default_tier"] == "FREE"

    def test_free_default_still_honors_explicit_builder_records(self, world):
        world.current["settings"] = settings(walkthrough_default_tier="FREE")
        set_tier(world, "paid", "BUILDER")
        assert post_progress(world, "paid").status_code == 403

    def test_garbage_setting_fails_closed(self, world):
        world.current["settings"] = settings(walkthrough_default_tier="nonsense")
        assert post_progress(world, "unlisted").status_code == 403
        assert public_tiers(world)["default_tier"] == "BUILDER"


class TestMigrationThenDefault:
    """The real rollout: migrate first, then the default flips."""

    def test_existing_free_walkthroughs_stay_free_and_new_ones_lock(self, world):
        # Before the migration: one walkthrough was marked Builder by an admin,
        # two others were simply free because they had no record.
        set_tier(world, "paid-existing", "BUILDER")

        backfill_free_tiers(
            world.ddb, TABLE, ["paid-existing", "free-a", "free-b"], apply=True
        )

        # The free ones are still free, the paid one is still paid.
        assert post_progress(world, "free-a").status_code == 200
        assert post_progress(world, "free-b").status_code == 200
        assert post_progress(world, "paid-existing").status_code == 403

        # A walkthrough published after the migration is Builder by default.
        assert post_progress(world, "published-next-week").status_code == 403

        tiers = public_tiers(world)
        assert tiers["access_tiers"] == {
            "paid-existing": "BUILDER",
            "free-a": "FREE",
            "free-b": "FREE",
        }

    def test_without_the_migration_existing_free_walkthroughs_would_lock(self, world):
        """Documents why the migration must run before the new default ships."""
        assert post_progress(world, "free-a").status_code == 403


class TestFailsClosed:
    def test_progress_is_refused_when_the_tier_cannot_be_read(self, world):
        with patch(
            "app.services.admin_service.AdminService.get_walkthrough_access_tier",
            side_effect=RuntimeError("dynamodb down"),
        ):
            resp = post_progress(world, "anything")
        assert resp.status_code == 503
        world.update.assert_not_called()

    def test_public_endpoint_does_not_claim_everything_is_free_on_error(self, world):
        with patch(
            "app.services.admin_service.AdminService.get_all_walkthrough_access_tiers",
            side_effect=RuntimeError("dynamodb down"),
        ):
            resp = world.http.get("/api/walkthroughs/access-tiers", headers=headers())
        assert resp.status_code == 503
        assert "access_tiers" not in resp.json()
