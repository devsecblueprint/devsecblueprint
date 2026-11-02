"""One-time migration: keep today's free walkthroughs free.

Walkthroughs used to be free unless an admin saved a Builder record. The
default is now Builder, so every walkthrough that is currently free (no record)
must get an explicit FREE record before the new default ships. Otherwise they
would all become Builder-only at once.

The migration only ever *adds* missing records. It never overwrites an existing
record, so it is safe to re-run, and an admin change made while it runs is not
lost (each write is conditional on the record not existing).

Standalone on purpose (boto3 only) so a script can use it without app settings.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Iterable

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

PK = "WALKTHROUGH_ACCESS"
SET_BY = "migration:default-tier"


def list_existing_tiers(client: Any, table: str) -> dict[str, str]:
    """Return walkthrough_id -> tier for every explicit record."""
    tiers: dict[str, str] = {}
    last_key = None
    while True:
        params: dict[str, Any] = {
            "TableName": table,
            "KeyConditionExpression": "PK = :pk",
            "ExpressionAttributeValues": {":pk": {"S": PK}},
        }
        if last_key:
            params["ExclusiveStartKey"] = last_key
        response = client.query(**params)
        for item in response.get("Items", []):
            sk = item.get("SK", {}).get("S", "")
            if sk.startswith("WT#"):
                tiers[sk[3:]] = item.get("access_tier", {}).get("S", "")
        last_key = response.get("LastEvaluatedKey")
        if not last_key:
            return tiers


def backfill_free_tiers(
    client: Any,
    table: str,
    walkthrough_ids: Iterable[str],
    apply: bool = False,
    set_by: str = SET_BY,
) -> dict[str, list[str]]:
    """Give every walkthrough without a tier record an explicit FREE record.

    Args:
        client: A boto3 DynamoDB client.
        table: The progress table name.
        walkthrough_ids: IDs of all walkthroughs that currently exist.
        apply: When False (the default) nothing is written (dry run).
        set_by: Recorded on each new record.

    Returns:
        ``already_set``: IDs that already had a record (left untouched).
        ``to_free``: IDs that need a FREE record (written when ``apply``).
        ``written``: IDs written by this run.
        ``raced``: IDs that gained a record while the migration ran (skipped).
    """
    ids = sorted({i for i in walkthrough_ids if i})
    existing = list_existing_tiers(client, table)
    already_set = [i for i in ids if i in existing]
    to_free = [i for i in ids if i not in existing]

    written: list[str] = []
    raced: list[str] = []
    if apply:
        now = datetime.now(timezone.utc).isoformat()
        for wid in to_free:
            try:
                client.put_item(
                    TableName=table,
                    Item={
                        "PK": {"S": PK},
                        "SK": {"S": f"WT#{wid}"},
                        "access_tier": {"S": "FREE"},
                        "set_by": {"S": set_by},
                        "updated_at": {"S": now},
                    },
                    ConditionExpression="attribute_not_exists(PK)",
                )
                written.append(wid)
            except ClientError as e:
                if e.response.get("Error", {}).get("Code") == (
                    "ConditionalCheckFailedException"
                ):
                    raced.append(wid)
                else:
                    raise
    return {
        "already_set": already_set,
        "to_free": to_free,
        "written": written,
        "raced": raced,
    }
