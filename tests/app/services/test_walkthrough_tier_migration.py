"""Tests for the one-time "keep free walkthroughs free" migration.

Runs against moto's DynamoDB so conditional writes behave like the real thing.
"""

import importlib.util
import io
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from app.services.walkthrough_tier_migration import (
    backfill_free_tiers,
    list_existing_tiers,
)

TABLE = "progress"


@pytest.fixture
def ddb():
    env = {
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_DEFAULT_REGION": "us-east-2",
    }
    with patch.dict(os.environ, env), mock_aws():
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
        yield client


def put_tier(client, wid, tier, set_by="admin"):
    client.put_item(
        TableName=TABLE,
        Item={
            "PK": {"S": "WALKTHROUGH_ACCESS"},
            "SK": {"S": f"WT#{wid}"},
            "access_tier": {"S": tier},
            "set_by": {"S": set_by},
            "updated_at": {"S": "2026-01-01T00:00:00+00:00"},
        },
    )


def record(client, wid):
    item = client.get_item(
        TableName=TABLE,
        Key={"PK": {"S": "WALKTHROUGH_ACCESS"}, "SK": {"S": f"WT#{wid}"}},
    ).get("Item")
    return item


class TestBackfill:
    def test_dry_run_writes_nothing(self, ddb):
        result = backfill_free_tiers(ddb, TABLE, ["a", "b"])
        assert result["to_free"] == ["a", "b"]
        assert result["written"] == []
        assert record(ddb, "a") is None
        assert record(ddb, "b") is None

    def test_apply_writes_free_records_for_walkthroughs_without_one(self, ddb):
        result = backfill_free_tiers(ddb, TABLE, ["a", "b"], apply=True)
        assert result["written"] == ["a", "b"]
        for wid in ("a", "b"):
            item = record(ddb, wid)
            assert item["access_tier"] == {"S": "FREE"}
            assert item["set_by"] == {"S": "migration:default-tier"}
            assert item["updated_at"]["S"]

    def test_never_overwrites_an_existing_builder_record(self, ddb):
        put_tier(ddb, "paid", "BUILDER")
        result = backfill_free_tiers(ddb, TABLE, ["paid", "open"], apply=True)
        assert record(ddb, "paid")["access_tier"] == {"S": "BUILDER"}
        assert record(ddb, "paid")["set_by"] == {"S": "admin"}  # untouched
        assert result["already_set"] == ["paid"]
        assert result["written"] == ["open"]

    def test_never_overwrites_an_existing_free_record(self, ddb):
        put_tier(ddb, "open", "FREE", set_by="damien")
        backfill_free_tiers(ddb, TABLE, ["open"], apply=True)
        assert record(ddb, "open")["set_by"] == {"S": "damien"}

    def test_is_safe_to_run_twice(self, ddb):
        first = backfill_free_tiers(ddb, TABLE, ["a", "b"], apply=True)
        second = backfill_free_tiers(ddb, TABLE, ["a", "b"], apply=True)
        assert first["written"] == ["a", "b"]
        assert second["written"] == []
        assert second["to_free"] == []
        assert second["already_set"] == ["a", "b"]

    def test_a_record_created_mid_run_is_not_overwritten(self, ddb):
        """An admin marks one Builder between the check and the write."""
        real_put = ddb.put_item
        calls = {"n": 0}

        def racing_put(**kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                put_tier(ddb, "a", "BUILDER", set_by="admin-race")
            return real_put(**kwargs)

        wrapper = MagicMock(wraps=ddb)
        wrapper.put_item.side_effect = racing_put
        result = backfill_free_tiers(wrapper, TABLE, ["a", "b"], apply=True)

        assert result["raced"] == ["a"]
        assert result["written"] == ["b"]
        assert record(ddb, "a")["access_tier"] == {"S": "BUILDER"}
        assert record(ddb, "a")["set_by"] == {"S": "admin-race"}

    def test_other_errors_are_raised(self, ddb):
        wrapper = MagicMock(wraps=ddb)
        wrapper.put_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ProvisionedThroughputExceededException",
                    "Message": "x",
                }
            },
            "PutItem",
        )
        with pytest.raises(ClientError):
            backfill_free_tiers(wrapper, TABLE, ["a"], apply=True)

    def test_ignores_blank_and_duplicate_ids(self, ddb):
        result = backfill_free_tiers(ddb, TABLE, ["a", "", "a", "b"], apply=True)
        assert result["written"] == ["a", "b"]

    def test_empty_input(self, ddb):
        result = backfill_free_tiers(ddb, TABLE, [], apply=True)
        assert result == {
            "already_set": [],
            "to_free": [],
            "written": [],
            "raced": [],
        }

    def test_does_not_touch_other_records_in_the_table(self, ddb):
        ddb.put_item(
            TableName=TABLE,
            Item={"PK": {"S": "USER#1"}, "SK": {"S": "WT#a"}, "x": {"S": "keep"}},
        )
        backfill_free_tiers(ddb, TABLE, ["a"], apply=True)
        other = ddb.get_item(
            TableName=TABLE, Key={"PK": {"S": "USER#1"}, "SK": {"S": "WT#a"}}
        )["Item"]
        assert other["x"] == {"S": "keep"}
        assert "access_tier" not in other

    def test_handles_more_than_one_page_of_existing_records(self, ddb):
        for i in range(60):
            put_tier(ddb, f"wt{i:03d}", "BUILDER")
        existing = list_existing_tiers(ddb, TABLE)
        assert len(existing) == 60
        result = backfill_free_tiers(
            ddb, TABLE, [f"wt{i:03d}" for i in range(62)], apply=True
        )
        assert result["written"] == ["wt060", "wt061"]


def load_script():
    path = (
        Path(__file__).resolve().parents[3]
        / "scripts"
        / "migrate_walkthrough_access_tiers.py"
    )
    spec = importlib.util.spec_from_file_location("migrate_tiers_script", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestScript:
    def registry(self):
        return {
            "schema_version": "1.0.0",
            "entries": {
                "k8s-nginx": {"content_type": "walkthrough"},
                "docker-basics": {"content_type": "walkthrough"},
                "some-quiz": {"content_type": "quiz"},
                "some-module": {"content_type": "module"},
            },
        }

    def s3(self, registry):
        client = MagicMock()
        client.get_object.return_value = {
            "Body": io.BytesIO(json.dumps(registry).encode())
        }
        return client

    def test_reads_only_walkthrough_ids_from_the_registry(self):
        script = load_script()
        s3 = self.s3(self.registry())
        assert script.load_walkthrough_ids(s3, "bucket") == [
            "docker-basics",
            "k8s-nginx",
        ]
        s3.get_object.assert_called_once_with(
            Bucket="bucket", Key="content-registry/latest.json"
        )

    def run_main(self, ddb, argv, capsys):
        script = load_script()
        clients = {"s3": self.s3(self.registry()), "dynamodb": ddb}
        with patch.object(script.boto3, "client", side_effect=lambda n: clients[n]):
            code = script.main(argv)
        return code, capsys.readouterr().out

    def test_default_run_is_a_dry_run(self, ddb, capsys):
        code, out = self.run_main(ddb, [TABLE, "bucket"], capsys)
        assert code == 0
        assert "Need an explicit FREE record: 2" in out
        assert "FREE  k8s-nginx" in out
        assert "Dry run only" in out
        assert record(ddb, "k8s-nginx") is None

    def test_apply_writes_records_and_reports(self, ddb, capsys):
        put_tier(ddb, "docker-basics", "BUILDER")
        code, out = self.run_main(ddb, [TABLE, "bucket", "--apply"], capsys)
        assert code == 0
        assert "Already have a record (left alone): 1" in out
        assert "Written: 1" in out
        assert record(ddb, "k8s-nginx")["access_tier"] == {"S": "FREE"}
        assert record(ddb, "docker-basics")["access_tier"] == {"S": "BUILDER"}

    def test_wrong_arguments_print_usage(self, ddb, capsys):
        code, out = self.run_main(ddb, [TABLE], capsys)
        assert code == 2
        assert "Usage" in out

    def test_empty_registry_stops_without_writing(self, ddb, capsys):
        script = load_script()
        clients = {
            "s3": self.s3({"schema_version": "1.0.0", "entries": {}}),
            "dynamodb": ddb,
        }
        with patch.object(script.boto3, "client", side_effect=lambda n: clients[n]):
            code = script.main([TABLE, "bucket", "--apply"])
        assert code == 1
        assert "Nothing to do" in capsys.readouterr().out
