"""DynamoDB access layer for certification records.

Provides helper functions for all certification-related DynamoDB operations
using the existing single-table design with PK/SK prefix conventions.

All certification records live in the progress_table alongside existing
user progress, capstone, and journey data.

Requirements: 16.1, 16.2, 16.3
"""

import logging
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings

logger = logging.getLogger(__name__)


class CertificationDB:
    """DynamoDB access layer for certification records.

    Follows the same patterns as ProgressDB: accepts a Settings instance,
    creates its own boto3 client, and uses typed attribute values for
    marshalling/unmarshalling.
    """

    def __init__(self, settings: Settings) -> None:
        self._table_name = settings.progress_table
        self._dynamodb = boto3.client("dynamodb")

    # ------------------------------------------------------------------
    # Pathway Definition operations
    # ------------------------------------------------------------------

    def put_pathway_version(self, pathway: dict) -> None:
        """Write a pathway definition version to DynamoDB.

        Args:
            pathway: Dict containing pathway_id, version, display_name,
                description, pathway_code, capstone_content_id,
                learning_requirements, is_active, created_at, created_by.
        """
        item: dict[str, Any] = {
            "PK": {"S": f"PATHWAY#{pathway['pathway_id']}"},
            "SK": {"S": f"VERSION#{pathway['version']}"},
            "pathway_id": {"S": pathway["pathway_id"]},
            "version": {"S": pathway["version"]},
            "display_name": {"S": pathway["display_name"]},
            "description": {"S": pathway["description"]},
            "pathway_code": {"S": pathway["pathway_code"]},
            "capstone_content_id": {"S": pathway["capstone_content_id"]},
            "learning_requirements": {
                "L": [{"S": req} for req in pathway["learning_requirements"]]
            },
            "is_active": {"BOOL": pathway["is_active"]},
            "created_at": {"S": pathway["created_at"]},
            "created_by": {"S": pathway["created_by"]},
        }

        try:
            self._dynamodb.put_item(TableName=self._table_name, Item=item)
        except ClientError as e:
            logger.error(
                "Failed to put pathway version %s/%s: %s",
                pathway["pathway_id"],
                pathway["version"],
                e.response["Error"]["Code"],
            )
            raise

    def get_active_pathway(self, pathway_id: str) -> dict | None:
        """Get the currently active version of a pathway.

        Queries all versions for the pathway and filters for is_active=true.

        Returns:
            Dict with pathway fields or None if no active version exists.
        """
        try:
            response = self._dynamodb.query(
                TableName=self._table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                FilterExpression="is_active = :active",
                ExpressionAttributeValues={
                    ":pk": {"S": f"PATHWAY#{pathway_id}"},
                    ":sk_prefix": {"S": "VERSION#"},
                    ":active": {"BOOL": True},
                },
            )

            items = response.get("Items", [])
            if not items:
                return None

            return self._unmarshal_pathway(items[0])

        except ClientError as e:
            logger.error(
                "Failed to get active pathway %s: %s",
                pathway_id,
                e.response["Error"]["Code"],
            )
            raise

    def get_pathway_version(self, pathway_id: str, version: str) -> dict | None:
        """Get a specific version of a pathway definition.

        Returns:
            Dict with pathway fields or None if not found.
        """
        try:
            response = self._dynamodb.get_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"PATHWAY#{pathway_id}"},
                    "SK": {"S": f"VERSION#{version}"},
                },
            )

            item = response.get("Item")
            if not item:
                return None

            return self._unmarshal_pathway(item)

        except ClientError as e:
            logger.error(
                "Failed to get pathway version %s/%s: %s",
                pathway_id,
                version,
                e.response["Error"]["Code"],
            )
            raise

    def list_active_pathways(self) -> list[dict]:
        """List all active pathway definitions.

        Uses a scan with filter for items with PK prefix PATHWAY# and
        is_active=true. Acceptable for small number of pathways.

        Returns:
            List of dicts with pathway fields.
        """
        try:
            response = self._dynamodb.scan(
                TableName=self._table_name,
                FilterExpression="begins_with(PK, :pk_prefix) AND is_active = :active",
                ExpressionAttributeValues={
                    ":pk_prefix": {"S": "PATHWAY#"},
                    ":active": {"BOOL": True},
                },
            )

            return [self._unmarshal_pathway(item) for item in response.get("Items", [])]

        except ClientError as e:
            logger.error(
                "Failed to list active pathways: %s",
                e.response["Error"]["Code"],
            )
            raise

    def deactivate_pathway_version(self, pathway_id: str, version: str) -> None:
        """Mark a pathway version as inactive.

        Args:
            pathway_id: Pathway identifier.
            version: Version string to deactivate.
        """
        try:
            self._dynamodb.update_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"PATHWAY#{pathway_id}"},
                    "SK": {"S": f"VERSION#{version}"},
                },
                UpdateExpression="SET is_active = :inactive",
                ExpressionAttributeValues={":inactive": {"BOOL": False}},
            )
        except ClientError as e:
            logger.error(
                "Failed to deactivate pathway %s/%s: %s",
                pathway_id,
                version,
                e.response["Error"]["Code"],
            )
            raise

    # ------------------------------------------------------------------
    # Candidate Record operations
    # ------------------------------------------------------------------

    def put_candidate_record(self, user_id: str, record: dict) -> None:
        """Write a candidate record to DynamoDB.

        Args:
            user_id: User identifier.
            record: Dict containing pathway_id, pathway_version,
                candidate_status, review_gate, started_at, updated_at,
                and optional credential_id / prior_credential_id.
        """
        item: dict[str, Any] = {
            "PK": {"S": f"USER#{user_id}"},
            "SK": {"S": f"CERT_CANDIDATE#{record['pathway_id']}"},
            "pathway_id": {"S": record["pathway_id"]},
            "pathway_version": {"S": record["pathway_version"]},
            "candidate_status": {"S": record["candidate_status"]},
            "review_gate": {"M": self._marshal_review_gate(record["review_gate"])},
            "started_at": {"S": record["started_at"]},
            "updated_at": {"S": record["updated_at"]},
        }

        if record.get("credential_id"):
            item["credential_id"] = {"S": record["credential_id"]}
        if record.get("prior_credential_id"):
            item["prior_credential_id"] = {"S": record["prior_credential_id"]}

        try:
            self._dynamodb.put_item(TableName=self._table_name, Item=item)
        except ClientError as e:
            logger.error(
                "Failed to put candidate record for user %s pathway %s: %s",
                user_id,
                record["pathway_id"],
                e.response["Error"]["Code"],
            )
            raise

    def get_candidate_record(self, user_id: str, pathway_id: str) -> dict | None:
        """Get a candidate record for a user and pathway.

        Returns:
            Dict with candidate fields or None if not found.
        """
        try:
            response = self._dynamodb.get_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": f"CERT_CANDIDATE#{pathway_id}"},
                },
            )

            item = response.get("Item")
            if not item:
                return None

            return self._unmarshal_candidate(item)

        except ClientError as e:
            logger.error(
                "Failed to get candidate record for user %s pathway %s: %s",
                user_id,
                pathway_id,
                e.response["Error"]["Code"],
            )
            raise

    def update_candidate_status(
        self,
        user_id: str,
        pathway_id: str,
        new_status: str,
        expected_status: str | None = None,
    ) -> None:
        """Update the candidate_status field with optional conditional check.

        Args:
            user_id: User identifier.
            pathway_id: Pathway identifier.
            new_status: New status value to set.
            expected_status: If provided, the update only succeeds if the
                current status matches this value (conditional write).

        Raises:
            ClientError: On DynamoDB failure or condition check failure.
        """
        update_expr = "SET candidate_status = :new_status, updated_at = :now"
        expr_values: dict[str, Any] = {
            ":new_status": {"S": new_status},
            ":now": {"S": _now_iso()},
        }

        condition_expr = None
        if expected_status is not None:
            condition_expr = "candidate_status = :expected"
            expr_values[":expected"] = {"S": expected_status}

        try:
            params: dict[str, Any] = {
                "TableName": self._table_name,
                "Key": {
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": f"CERT_CANDIDATE#{pathway_id}"},
                },
                "UpdateExpression": update_expr,
                "ExpressionAttributeValues": expr_values,
            }
            if condition_expr:
                params["ConditionExpression"] = condition_expr

            self._dynamodb.update_item(**params)

        except ClientError as e:
            logger.error(
                "Failed to update candidate status for user %s pathway %s: %s",
                user_id,
                pathway_id,
                e.response["Error"]["Code"],
            )
            raise

    def update_review_gate(
        self, user_id: str, pathway_id: str, gate_data: dict
    ) -> None:
        """Update the review_gate map on a candidate record.

        Args:
            user_id: User identifier.
            pathway_id: Pathway identifier.
            gate_data: Dict with status, and optionally reviewed_at, reviewer_id.
        """
        try:
            self._dynamodb.update_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": f"CERT_CANDIDATE#{pathway_id}"},
                },
                UpdateExpression="SET review_gate = :gate, updated_at = :now",
                ExpressionAttributeValues={
                    ":gate": {"M": self._marshal_review_gate(gate_data)},
                    ":now": {"S": _now_iso()},
                },
            )
        except ClientError as e:
            logger.error(
                "Failed to update review gate for user %s pathway %s: %s",
                user_id,
                pathway_id,
                e.response["Error"]["Code"],
            )
            raise

    def list_candidates(
        self,
        pathway_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
        last_key: dict | None = None,
    ) -> tuple[list[dict], dict | None]:
        """List candidate records with optional filters.

        Uses a scan with filters — acceptable for admin views with small
        data volumes.

        Args:
            pathway_id: Optional filter by pathway.
            status: Optional filter by candidate_status.
            limit: Maximum number of results per page.
            last_key: Pagination key from previous call.

        Returns:
            Tuple of (list of candidate dicts, next pagination key or None).
        """
        filter_parts: list[str] = ["begins_with(SK, :sk_prefix)"]
        expr_values: dict[str, Any] = {":sk_prefix": {"S": "CERT_CANDIDATE#"}}

        if pathway_id:
            filter_parts.append("pathway_id = :pathway_id")
            expr_values[":pathway_id"] = {"S": pathway_id}

        if status:
            filter_parts.append("candidate_status = :status")
            expr_values[":status"] = {"S": status}

        filter_expression = " AND ".join(filter_parts)

        try:
            params: dict[str, Any] = {
                "TableName": self._table_name,
                "FilterExpression": filter_expression,
                "ExpressionAttributeValues": expr_values,
                "Limit": limit,
            }
            if last_key:
                params["ExclusiveStartKey"] = last_key

            response = self._dynamodb.scan(**params)

            candidates = [
                self._unmarshal_candidate(item) for item in response.get("Items", [])
            ]
            next_key = response.get("LastEvaluatedKey")

            return candidates, next_key

        except ClientError as e:
            logger.error(
                "Failed to list candidates: %s",
                e.response["Error"]["Code"],
            )
            raise

    # ------------------------------------------------------------------
    # Combined Review Session operations
    # ------------------------------------------------------------------

    def put_review_session(self, user_id: str, session: dict) -> None:
        """Write a combined review session record to DynamoDB.

        Args:
            user_id: User identifier.
            session: Dict containing pathway_id, revision_number, status,
                rubric_scores, evaluation_dimensions, reviewer_id,
                reviewer_notes, submission_url, submitted_at, reviewed_at.
        """
        revision_number = session["revision_number"]
        item: dict[str, Any] = {
            "PK": {"S": f"USER#{user_id}"},
            "SK": {"S": f"CERT_REVIEW#{session['pathway_id']}#REV#{revision_number}"},
            "pathway_id": {"S": session["pathway_id"]},
            "revision_number": {"N": str(revision_number)},
            "status": {"S": session["status"]},
            "rubric_scores": {"M": self._marshal_map(session.get("rubric_scores", {}))},
            "evaluation_dimensions": {
                "M": self._marshal_map(session.get("evaluation_dimensions", {}))
            },
            "submission_url": {"S": session["submission_url"]},
            "submitted_at": {"S": session["submitted_at"]},
        }

        if session.get("reviewer_id"):
            item["reviewer_id"] = {"S": session["reviewer_id"]}
        if session.get("reviewer_notes"):
            item["reviewer_notes"] = {"S": session["reviewer_notes"]}
        if session.get("reviewed_at"):
            item["reviewed_at"] = {"S": session["reviewed_at"]}

        try:
            self._dynamodb.put_item(TableName=self._table_name, Item=item)
        except ClientError as e:
            logger.error(
                "Failed to put review session for user %s pathway %s rev %s: %s",
                user_id,
                session["pathway_id"],
                revision_number,
                e.response["Error"]["Code"],
            )
            raise

    def get_latest_review_session(self, user_id: str, pathway_id: str) -> dict | None:
        """Get the most recent review session for a user and pathway.

        Queries all review sessions and returns the one with highest
        revision_number.

        Returns:
            Dict with session fields or None if no sessions exist.
        """
        try:
            response = self._dynamodb.query(
                TableName=self._table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk_prefix": {"S": f"CERT_REVIEW#{pathway_id}#REV#"},
                },
                ScanIndexForward=False,
                Limit=1,
            )

            items = response.get("Items", [])
            if not items:
                return None

            return self._unmarshal_review_session(items[0])

        except ClientError as e:
            logger.error(
                "Failed to get latest review session for user %s pathway %s: %s",
                user_id,
                pathway_id,
                e.response["Error"]["Code"],
            )
            raise

    def get_review_history(self, user_id: str, pathway_id: str) -> list[dict]:
        """Get all review sessions for a user and pathway, ordered by revision.

        Returns:
            List of dicts with session fields, sorted ascending by revision.
        """
        try:
            response = self._dynamodb.query(
                TableName=self._table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk_prefix": {"S": f"CERT_REVIEW#{pathway_id}#REV#"},
                },
                ScanIndexForward=True,
            )

            return [
                self._unmarshal_review_session(item)
                for item in response.get("Items", [])
            ]

        except ClientError as e:
            logger.error(
                "Failed to get review history for user %s pathway %s: %s",
                user_id,
                pathway_id,
                e.response["Error"]["Code"],
            )
            raise

    # ------------------------------------------------------------------
    # Credential operations
    # ------------------------------------------------------------------

    def put_credential(self, user_id: str, credential: dict) -> None:
        """Write a credential record with conditional write to prevent duplicates.

        Uses ConditionExpression: attribute_not_exists(SK) to ensure
        no duplicate credentials are created.

        Args:
            user_id: User identifier.
            credential: Dict containing credential_id, pathway_id,
                pathway_version, credential_status, issued_at, expires_at,
                full_name_at_issuance, and optional fields.
        """
        credential_id = credential["credential_id"]
        item: dict[str, Any] = {
            "PK": {"S": f"USER#{user_id}"},
            "SK": {"S": f"CREDENTIAL#{credential_id}"},
            "credential_id": {"S": credential_id},
            "pathway_id": {"S": credential["pathway_id"]},
            "pathway_version": {"S": credential["pathway_version"]},
            "credential_status": {"S": credential["credential_status"]},
            "issued_at": {"S": credential["issued_at"]},
            "expires_at": {"S": credential["expires_at"]},
            "full_name_at_issuance": {"S": credential["full_name_at_issuance"]},
            "is_recertification": {"BOOL": credential.get("is_recertification", False)},
            "is_grandfathered": {"BOOL": credential.get("is_grandfathered", False)},
            # GSI attributes for CredentialLookup
            "GSI_PK": {"S": f"CRED#{credential_id}"},
            "GSI_SK": {"S": f"CRED#{credential_id}"},
            # GSI attributes for CredentialExpiry
            "GSI_EXPIRY_PK": {"S": credential["credential_status"]},
            "GSI_EXPIRY_SK": {"S": credential["expires_at"]},
        }

        if credential.get("certificate_s3_key"):
            item["certificate_s3_key"] = {"S": credential["certificate_s3_key"]}
        if credential.get("prior_credential_id"):
            item["prior_credential_id"] = {"S": credential["prior_credential_id"]}
        if credential.get("revoked_at"):
            item["revoked_at"] = {"S": credential["revoked_at"]}
        if credential.get("revocation_reason"):
            item["revocation_reason"] = {"S": credential["revocation_reason"]}
        if credential.get("revoked_by"):
            item["revoked_by"] = {"S": credential["revoked_by"]}

        try:
            self._dynamodb.put_item(
                TableName=self._table_name,
                Item=item,
                ConditionExpression="attribute_not_exists(SK)",
            )
        except ClientError as e:
            logger.error(
                "Failed to put credential %s for user %s: %s",
                credential_id,
                user_id,
                e.response["Error"]["Code"],
            )
            raise

    def get_credential(self, user_id: str, credential_id: str) -> dict | None:
        """Get a specific credential by user_id and credential_id.

        Returns:
            Dict with credential fields or None if not found.
        """
        try:
            response = self._dynamodb.get_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": f"CREDENTIAL#{credential_id}"},
                },
            )

            item = response.get("Item")
            if not item:
                return None

            return self._unmarshal_credential(item)

        except ClientError as e:
            logger.error(
                "Failed to get credential %s for user %s: %s",
                credential_id,
                user_id,
                e.response["Error"]["Code"],
            )
            raise

    def get_credential_by_id(self, credential_id: str) -> dict | None:
        """Look up a credential by credential_id using the CredentialLookup GSI.

        Returns:
            Dict with credential fields or None if not found.
        """
        try:
            response = self._dynamodb.query(
                TableName=self._table_name,
                IndexName="CredentialLookup",
                KeyConditionExpression="GSI_PK = :pk AND GSI_SK = :sk",
                ExpressionAttributeValues={
                    ":pk": {"S": f"CRED#{credential_id}"},
                    ":sk": {"S": f"CRED#{credential_id}"},
                },
                Limit=1,
            )

            items = response.get("Items", [])
            if not items:
                return None

            return self._unmarshal_credential(items[0])

        except ClientError as e:
            logger.error(
                "Failed to get credential by ID %s via GSI: %s",
                credential_id,
                e.response["Error"]["Code"],
            )
            raise

    def list_user_credentials(self, user_id: str) -> list[dict]:
        """List all credentials for a user.

        Returns:
            List of dicts with credential fields.
        """
        try:
            response = self._dynamodb.query(
                TableName=self._table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"USER#{user_id}"},
                    ":sk_prefix": {"S": "CREDENTIAL#"},
                },
            )

            return [
                self._unmarshal_credential(item) for item in response.get("Items", [])
            ]

        except ClientError as e:
            logger.error(
                "Failed to list credentials for user %s: %s",
                user_id,
                e.response["Error"]["Code"],
            )
            raise

    def update_credential_status(
        self,
        user_id: str,
        credential_id: str,
        new_status: str,
        condition: str | None = None,
    ) -> None:
        """Update a credential's status with optional condition.

        Also updates the GSI_EXPIRY_PK attribute so the CredentialExpiry
        GSI reflects the new status.

        Args:
            user_id: User identifier.
            credential_id: Credential identifier.
            new_status: New credential_status value.
            condition: Optional ConditionExpression string.
        """
        try:
            params: dict[str, Any] = {
                "TableName": self._table_name,
                "Key": {
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": f"CREDENTIAL#{credential_id}"},
                },
                "UpdateExpression": (
                    "SET credential_status = :new_status, "
                    "GSI_EXPIRY_PK = :new_status"
                ),
                "ExpressionAttributeValues": {
                    ":new_status": {"S": new_status},
                },
            }
            if condition:
                params["ConditionExpression"] = condition

            self._dynamodb.update_item(**params)

        except ClientError as e:
            logger.error(
                "Failed to update credential status %s for user %s: %s",
                credential_id,
                user_id,
                e.response["Error"]["Code"],
            )
            raise

    def query_credentials_by_status_and_expiry(
        self, status: str, expires_before: str
    ) -> list[dict]:
        """Query credentials by status and expiry date using CredentialExpiry GSI.

        Used by the background expiry job to find credentials approaching
        or past their expiration date.

        Args:
            status: Credential status to query (e.g., "ACTIVE").
            expires_before: ISO 8601 timestamp — returns credentials
                with expires_at <= this value.

        Returns:
            List of dicts with credential fields.
        """
        try:
            response = self._dynamodb.query(
                TableName=self._table_name,
                IndexName="CredentialExpiry",
                KeyConditionExpression=(
                    "GSI_EXPIRY_PK = :status AND GSI_EXPIRY_SK <= :expires_before"
                ),
                ExpressionAttributeValues={
                    ":status": {"S": status},
                    ":expires_before": {"S": expires_before},
                },
            )

            return [
                self._unmarshal_credential(item) for item in response.get("Items", [])
            ]

        except ClientError as e:
            logger.error(
                "Failed to query credentials by status %s expiry before %s: %s",
                status,
                expires_before,
                e.response["Error"]["Code"],
            )
            raise

    # ------------------------------------------------------------------
    # User profile (read full_name)
    # ------------------------------------------------------------------

    def get_user_full_name(self, user_id: str) -> str | None:
        """Read the full_name attribute from the user's PROFILE record.

        Returns:
            The full_name string or None if not set.
        """
        try:
            response = self._dynamodb.get_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": "PROFILE"},
                },
                ProjectionExpression="full_name",
            )

            item = response.get("Item")
            if not item:
                return None

            return item.get("full_name", {}).get("S")

        except ClientError as e:
            logger.error(
                "Failed to get full_name for user %s: %s",
                user_id,
                e.response["Error"]["Code"],
            )
            raise

    def get_user_email(self, user_id: str) -> str | None:
        """Read the email attribute from the user's PROFILE record.

        Returns:
            The email string or None if not set.
        """
        try:
            response = self._dynamodb.get_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": "PROFILE"},
                },
                ProjectionExpression="email",
            )

            item = response.get("Item")
            if not item:
                return None

            return item.get("email", {}).get("S")

        except ClientError as e:
            logger.error(
                "Failed to get email for user %s: %s",
                user_id,
                e.response["Error"]["Code"],
            )
            raise

    def get_user_username(self, user_id: str) -> str:
        """Read the username attribute from the user's PROFILE record.

        Returns:
            The username string or empty string if not found.
        """
        try:
            response = self._dynamodb.get_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": "PROFILE"},
                },
                ProjectionExpression="username",
            )

            item = response.get("Item")
            if not item:
                return ""

            return item.get("username", {}).get("S", "")

        except ClientError as e:
            logger.error(
                "Failed to get username for user %s: %s",
                user_id,
                e.response["Error"]["Code"],
            )
            raise

    def update_certificate_s3_key(
        self, user_id: str, credential_id: str, s3_key: str
    ) -> None:
        """Update the certificate_s3_key field on a credential record.

        Args:
            user_id: User identifier.
            credential_id: Credential identifier.
            s3_key: The S3 key of the generated certificate PDF.
        """
        try:
            self._dynamodb.update_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": f"CREDENTIAL#{credential_id}"},
                },
                UpdateExpression="SET certificate_s3_key = :s3_key",
                ExpressionAttributeValues={
                    ":s3_key": {"S": s3_key},
                },
            )
        except ClientError as e:
            logger.error(
                "Failed to update certificate_s3_key for credential %s user %s: %s",
                credential_id,
                user_id,
                e.response["Error"]["Code"],
            )
            raise

    # ------------------------------------------------------------------
    # Private marshalling helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _marshal_review_gate(gate: dict) -> dict[str, Any]:
        """Marshal a review_gate dict to DynamoDB typed map values."""
        result: dict[str, Any] = {
            "status": {"S": gate["status"]},
        }
        if gate.get("reviewed_at"):
            result["reviewed_at"] = {"S": gate["reviewed_at"]}
        if gate.get("reviewer_id"):
            result["reviewer_id"] = {"S": gate["reviewer_id"]}
        return result

    @staticmethod
    def _marshal_map(data: dict) -> dict[str, Any]:
        """Marshal a nested dict to DynamoDB M (map) typed values.

        Supports string values and nested dicts with string values.
        Note: bool checks must precede int checks because bool is a
        subclass of int in Python.
        """
        result: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, dict):
                inner: dict[str, Any] = {}
                for inner_key, inner_value in value.items():
                    if isinstance(inner_value, bool):
                        inner[inner_key] = {"BOOL": inner_value}
                    elif isinstance(inner_value, (int, float)):
                        inner[inner_key] = {"N": str(inner_value)}
                    else:
                        inner[inner_key] = {"S": str(inner_value)}
                result[key] = {"M": inner}
            elif isinstance(value, bool):
                result[key] = {"BOOL": value}
            elif isinstance(value, (int, float)):
                result[key] = {"N": str(value)}
            else:
                result[key] = {"S": str(value)}
        return result

    @staticmethod
    def _unmarshal_pathway(item: dict) -> dict:
        """Unmarshal a DynamoDB pathway item to a plain dict."""
        learning_reqs = [
            req.get("S", "")
            for req in item.get("learning_requirements", {}).get("L", [])
        ]
        return {
            "pathway_id": item.get("pathway_id", {}).get("S", ""),
            "version": item.get("version", {}).get("S", ""),
            "display_name": item.get("display_name", {}).get("S", ""),
            "description": item.get("description", {}).get("S", ""),
            "pathway_code": item.get("pathway_code", {}).get("S", ""),
            "capstone_content_id": item.get("capstone_content_id", {}).get("S", ""),
            "learning_requirements": learning_reqs,
            "is_active": item.get("is_active", {}).get("BOOL", False),
            "created_at": item.get("created_at", {}).get("S", ""),
            "created_by": item.get("created_by", {}).get("S", ""),
        }

    @staticmethod
    def _unmarshal_candidate(item: dict) -> dict:
        """Unmarshal a DynamoDB candidate item to a plain dict."""
        # Extract user_id from PK
        pk = item.get("PK", {}).get("S", "")
        user_id = pk.replace("USER#", "") if pk.startswith("USER#") else ""

        gate_map = item.get("review_gate", {}).get("M", {})
        review_gate = {
            "status": gate_map.get("status", {}).get("S", ""),
            "reviewed_at": gate_map.get("reviewed_at", {}).get("S"),
            "reviewer_id": gate_map.get("reviewer_id", {}).get("S"),
        }

        result: dict[str, Any] = {
            "user_id": user_id,
            "pathway_id": item.get("pathway_id", {}).get("S", ""),
            "pathway_version": item.get("pathway_version", {}).get("S", ""),
            "candidate_status": item.get("candidate_status", {}).get("S", ""),
            "review_gate": review_gate,
            "started_at": item.get("started_at", {}).get("S", ""),
            "updated_at": item.get("updated_at", {}).get("S", ""),
        }

        credential_id = item.get("credential_id", {}).get("S")
        if credential_id:
            result["credential_id"] = credential_id

        prior_credential_id = item.get("prior_credential_id", {}).get("S")
        if prior_credential_id:
            result["prior_credential_id"] = prior_credential_id

        return result

    @staticmethod
    def _unmarshal_review_session(item: dict) -> dict:
        """Unmarshal a DynamoDB review session item to a plain dict."""
        # Extract user_id from PK
        pk = item.get("PK", {}).get("S", "")
        user_id = pk.replace("USER#", "") if pk.startswith("USER#") else ""

        result: dict[str, Any] = {
            "user_id": user_id,
            "pathway_id": item.get("pathway_id", {}).get("S", ""),
            "revision_number": int(item.get("revision_number", {}).get("N", "0")),
            "status": item.get("status", {}).get("S", ""),
            "rubric_scores": CertificationDB._unmarshal_nested_map(
                item.get("rubric_scores", {}).get("M", {})
            ),
            "evaluation_dimensions": CertificationDB._unmarshal_nested_map(
                item.get("evaluation_dimensions", {}).get("M", {})
            ),
            "submission_url": item.get("submission_url", {}).get("S", ""),
            "submitted_at": item.get("submitted_at", {}).get("S", ""),
        }

        reviewer_id = item.get("reviewer_id", {}).get("S")
        if reviewer_id:
            result["reviewer_id"] = reviewer_id

        reviewer_notes = item.get("reviewer_notes", {}).get("S")
        if reviewer_notes:
            result["reviewer_notes"] = reviewer_notes

        reviewed_at = item.get("reviewed_at", {}).get("S")
        if reviewed_at:
            result["reviewed_at"] = reviewed_at

        return result

    @staticmethod
    def _unmarshal_credential(item: dict) -> dict:
        """Unmarshal a DynamoDB credential item to a plain dict."""
        # Extract user_id from PK
        pk = item.get("PK", {}).get("S", "")
        user_id = pk.replace("USER#", "") if pk.startswith("USER#") else ""

        result: dict[str, Any] = {
            "user_id": user_id,
            "credential_id": item.get("credential_id", {}).get("S", ""),
            "pathway_id": item.get("pathway_id", {}).get("S", ""),
            "pathway_version": item.get("pathway_version", {}).get("S", ""),
            "credential_status": item.get("credential_status", {}).get("S", ""),
            "issued_at": item.get("issued_at", {}).get("S", ""),
            "expires_at": item.get("expires_at", {}).get("S", ""),
            "full_name_at_issuance": item.get("full_name_at_issuance", {}).get("S", ""),
            "is_recertification": item.get("is_recertification", {}).get("BOOL", False),
            "is_grandfathered": item.get("is_grandfathered", {}).get("BOOL", False),
        }

        certificate_s3_key = item.get("certificate_s3_key", {}).get("S")
        if certificate_s3_key:
            result["certificate_s3_key"] = certificate_s3_key

        prior_credential_id = item.get("prior_credential_id", {}).get("S")
        if prior_credential_id:
            result["prior_credential_id"] = prior_credential_id

        revoked_at = item.get("revoked_at", {}).get("S")
        if revoked_at:
            result["revoked_at"] = revoked_at

        revocation_reason = item.get("revocation_reason", {}).get("S")
        if revocation_reason:
            result["revocation_reason"] = revocation_reason

        revoked_by = item.get("revoked_by", {}).get("S")
        if revoked_by:
            result["revoked_by"] = revoked_by

        return result

    @staticmethod
    def _unmarshal_nested_map(dynamo_map: dict) -> dict:
        """Unmarshal a DynamoDB nested map (M) to a plain dict.

        Handles one level of nesting: M → {key: M → {inner_key: S/N/BOOL}}.
        """
        result: dict[str, Any] = {}
        for key, value in dynamo_map.items():
            if "M" in value:
                inner: dict[str, Any] = {}
                for inner_key, inner_value in value["M"].items():
                    if "S" in inner_value:
                        inner[inner_key] = inner_value["S"]
                    elif "N" in inner_value:
                        inner[inner_key] = int(inner_value["N"])
                    elif "BOOL" in inner_value:
                        inner[inner_key] = inner_value["BOOL"]
                result[key] = inner
            elif "S" in value:
                result[key] = value["S"]
            elif "N" in value:
                result[key] = int(value["N"])
            elif "BOOL" in value:
                result[key] = value["BOOL"]
        return result


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()
