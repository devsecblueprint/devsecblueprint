"""Fetch all Discord users registered/mapped in the DSB platform.

Scans the dsb-platform-membership DynamoDB table for items with
SK = DISCORD_ACTIVE, which represent confirmed Discord connections.

Usage:
    python scripts/get_discord_users.py [--table TABLE_NAME] [--region REGION] [--csv output.csv]

Requirements:
    - boto3
    - Valid AWS credentials with DynamoDB read access
"""

import argparse
import csv
import sys

import boto3
from botocore.exceptions import ClientError

DEFAULT_TABLE = "dsb-platform-membership"
DEFAULT_REGION = "us-east-1"


def scan_discord_users(table_name: str, region: str) -> list[dict]:
    """Scan the membership table for all active Discord connections."""
    dynamodb = boto3.client("dynamodb", region_name=region)

    users = []
    scan_kwargs = {
        "TableName": table_name,
        "FilterExpression": "SK = :sk",
        "ExpressionAttributeValues": {
            ":sk": {"S": "DISCORD_ACTIVE"},
        },
    }

    while True:
        try:
            response = dynamodb.scan(**scan_kwargs)
        except ClientError as e:
            print(f"Error scanning table: {e.response['Error']['Message']}")
            sys.exit(1)

        for item in response.get("Items", []):
            user_id = item.get("PK", {}).get("S", "").replace("USER#", "")
            discord_user_id = item.get("discord_user_id", {}).get("S", "")
            username = item.get("username", {}).get("S", "")
            display_name = item.get("display_name", {}).get("S", "")
            avatar_url = item.get("avatar_url", {}).get("S", "")
            platform_state = item.get("platform_state", {}).get("S", "")
            connected_at = item.get("connected_at", {}).get("S", "")
            last_synced_at = item.get("last_synced_at", {}).get("S", "")
            last_sync_status = item.get("last_sync_status", {}).get("S", "")

            users.append(
                {
                    "user_id": user_id,
                    "discord_user_id": discord_user_id,
                    "username": username,
                    "display_name": display_name,
                    "avatar_url": avatar_url,
                    "platform_state": platform_state,
                    "connected_at": connected_at,
                    "last_synced_at": last_synced_at,
                    "last_sync_status": last_sync_status,
                }
            )

        # Handle pagination
        last_key = response.get("LastEvaluatedKey")
        if not last_key:
            break
        scan_kwargs["ExclusiveStartKey"] = last_key

    return users


def main():
    parser = argparse.ArgumentParser(
        description="Get all Discord users registered on the DSB platform"
    )
    parser.add_argument(
        "--table",
        default=DEFAULT_TABLE,
        help=f"DynamoDB table name (default: {DEFAULT_TABLE})",
    )
    parser.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help=f"AWS region (default: {DEFAULT_REGION})",
    )
    parser.add_argument(
        "--csv",
        dest="csv_file",
        help="Export results to a CSV file",
    )
    args = parser.parse_args()

    print(f"Scanning table '{args.table}' in {args.region}...")
    users = scan_discord_users(args.table, args.region)
    print(f"Found {len(users)} Discord-connected users.\n")

    if not users:
        return

    # Print to stdout
    print(
        f"{'User ID':<40} {'Discord ID':<20} {'Username':<25} {'Display Name':<25} {'State':<15} {'Connected At'}"
    )
    print("-" * 160)
    for u in users:
        print(
            f"{u['user_id']:<40} {u['discord_user_id']:<20} {u['username']:<25} "
            f"{u['display_name']:<25} {u['platform_state']:<15} {u['connected_at']}"
        )

    # Export to CSV if requested
    if args.csv_file:
        with open(args.csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=users[0].keys())
            writer.writeheader()
            writer.writerows(users)
        print(f"\nExported to {args.csv_file}")


if __name__ == "__main__":
    main()
