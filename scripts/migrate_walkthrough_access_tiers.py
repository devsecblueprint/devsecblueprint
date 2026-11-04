"""Keep today's free walkthroughs free before the default tier becomes Builder.

Walkthroughs used to be free unless an admin saved a Builder record. The default
is now Builder, so every walkthrough that is currently free needs an explicit
FREE record first. Run this BEFORE deploying the new default.

It reads the walkthrough IDs from the content registry in S3 and adds a FREE
record for each one that has no record yet. It never changes an existing record,
and it is safe to run more than once.

Dry run by default: it prints what it would do and writes nothing.

Usage:
    python scripts/migrate_walkthrough_access_tiers.py <progress_table> <registry_bucket> [--apply]

Example:
    python scripts/migrate_walkthrough_access_tiers.py dsb-progress-table-prod dsb-content-registry-prod
    python scripts/migrate_walkthrough_access_tiers.py dsb-progress-table-prod dsb-content-registry-prod --apply

Then check Admin > Learning & Content > Walkthrough Access Tiers: the walkthroughs
you want to stay free should show Free, and none should say "Default".
"""

import json
import sys
from pathlib import Path

import boto3

# Reuse the tested migration logic from the backend package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app.services.walkthrough_tier_migration import backfill_free_tiers  # noqa: E402

REGISTRY_KEY = "content-registry/latest.json"


def load_walkthrough_ids(s3_client, bucket: str) -> list[str]:
    """Return the IDs of all walkthroughs in the content registry."""
    body = s3_client.get_object(Bucket=bucket, Key=REGISTRY_KEY)["Body"].read()
    registry = json.loads(body.decode("utf-8"))
    return sorted(
        entry_id
        for entry_id, entry in registry.get("entries", {}).items()
        if entry.get("content_type") == "walkthrough"
    )


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    apply = "--apply" in argv
    if len(args) != 2:
        print(__doc__)
        return 2
    table, bucket = args

    ids = load_walkthrough_ids(boto3.client("s3"), bucket)
    if not ids:
        print(f"No walkthroughs found in s3://{bucket}/{REGISTRY_KEY}. Nothing to do.")
        return 1

    result = backfill_free_tiers(boto3.client("dynamodb"), table, ids, apply=apply)

    print(f"Walkthroughs in registry: {len(ids)}")
    print(f"Already have a record (left alone): {len(result['already_set'])}")
    print(f"Need an explicit FREE record: {len(result['to_free'])}")
    for wid in result["to_free"]:
        print(f"  FREE  {wid}")
    if apply:
        print(f"Written: {len(result['written'])}")
        if result["raced"]:
            print(f"Skipped (record appeared while running): {result['raced']}")
    else:
        print("\nDry run only. Re-run with --apply to write these records.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
