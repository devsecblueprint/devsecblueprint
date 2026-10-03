"""Unit tests for app.services.certification.db.CertificationDB.

Constructs a boto3 DynamoDB client in __init__; tests patch the module's
boto3.client, then reassign svc._dynamodb for direct assertions. Covers CRUD
and query operations for pathways, candidates, review sessions, credentials,
and user profile reads, including success, not-found/None, pagination loops,
and ClientError paths.
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services.certification import db as mod
from app.services.certification.db import CertificationDB


def _client_error(code: str = "InternalServerError") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


@pytest.fixture
def service():
    client = MagicMock()
    settings = MagicMock(progress_table="test-progress")
    with patch.object(mod.boto3, "client", return_value=client):
        svc = CertificationDB(settings)
    svc._dynamodb = client
    return svc


# ---------------------------------------------------------------------------
# Pathway Definition operations
# ---------------------------------------------------------------------------


def _pathway_dict():
    return {
        "pathway_id": "p1",
        "version": "v1",
        "display_name": "DevSecOps",
        "description": "desc",
        "pathway_code": "DSEP",
        "capstone_content_id": "cap",
        "learning_requirements": ["a", "b"],
        "is_active": True,
        "created_at": "2026-01-01T00:00:00+00:00",
        "created_by": "admin",
    }


def _pathway_item():
    return {
        "pathway_id": {"S": "p1"},
        "version": {"S": "v1"},
        "display_name": {"S": "DevSecOps"},
        "description": {"S": "desc"},
        "pathway_code": {"S": "DSEP"},
        "capstone_content_id": {"S": "cap"},
        "learning_requirements": {"L": [{"S": "a"}, {"S": "b"}]},
        "is_active": {"BOOL": True},
        "created_at": {"S": "2026-01-01T00:00:00+00:00"},
        "created_by": {"S": "admin"},
    }


class TestPutPathwayVersion:
    def test_puts_item(self, service):
        service.put_pathway_version(_pathway_dict())
        kwargs = service._dynamodb.put_item.call_args.kwargs
        assert kwargs["TableName"] == "test-progress"
        item = kwargs["Item"]
        assert item["PK"] == {"S": "PATHWAY#p1"}
        assert item["SK"] == {"S": "VERSION#v1"}
        assert item["learning_requirements"] == {"L": [{"S": "a"}, {"S": "b"}]}
        assert item["is_active"] == {"BOOL": True}

    def test_client_error_raises(self, service):
        service._dynamodb.put_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.put_pathway_version(_pathway_dict())


class TestGetActivePathway:
    def test_returns_unmarshalled(self, service):
        service._dynamodb.query.return_value = {"Items": [_pathway_item()]}
        result = service.get_active_pathway("p1")
        assert result["pathway_id"] == "p1"
        assert result["learning_requirements"] == ["a", "b"]
        assert result["is_active"] is True
        values = service._dynamodb.query.call_args.kwargs["ExpressionAttributeValues"]
        assert values[":pk"] == {"S": "PATHWAY#p1"}
        assert values[":active"] == {"BOOL": True}

    def test_none_when_empty(self, service):
        service._dynamodb.query.return_value = {"Items": []}
        assert service.get_active_pathway("p1") is None

    def test_client_error_raises(self, service):
        service._dynamodb.query.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_active_pathway("p1")


class TestGetPathwayVersion:
    def test_returns_item(self, service):
        service._dynamodb.get_item.return_value = {"Item": _pathway_item()}
        result = service.get_pathway_version("p1", "v1")
        assert result["version"] == "v1"
        key = service._dynamodb.get_item.call_args.kwargs["Key"]
        assert key == {"PK": {"S": "PATHWAY#p1"}, "SK": {"S": "VERSION#v1"}}

    def test_none_when_absent(self, service):
        service._dynamodb.get_item.return_value = {}
        assert service.get_pathway_version("p1", "v1") is None

    def test_client_error_raises(self, service):
        service._dynamodb.get_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_pathway_version("p1", "v1")


class TestListActivePathways:
    def test_returns_list(self, service):
        service._dynamodb.scan.return_value = {"Items": [_pathway_item(), _pathway_item()]}
        result = service.list_active_pathways()
        assert len(result) == 2
        assert result[0]["pathway_code"] == "DSEP"

    def test_empty(self, service):
        service._dynamodb.scan.return_value = {}
        assert service.list_active_pathways() == []

    def test_client_error_raises(self, service):
        service._dynamodb.scan.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.list_active_pathways()


class TestDeactivatePathwayVersion:
    def test_updates_item(self, service):
        service.deactivate_pathway_version("p1", "v1")
        kwargs = service._dynamodb.update_item.call_args.kwargs
        assert kwargs["Key"] == {"PK": {"S": "PATHWAY#p1"}, "SK": {"S": "VERSION#v1"}}
        assert kwargs["ExpressionAttributeValues"][":inactive"] == {"BOOL": False}

    def test_client_error_raises(self, service):
        service._dynamodb.update_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.deactivate_pathway_version("p1", "v1")


# ---------------------------------------------------------------------------
# Candidate Record operations
# ---------------------------------------------------------------------------


def _candidate_record(**extra):
    rec = {
        "pathway_id": "p1",
        "pathway_version": "v1",
        "candidate_status": "IN_PROGRESS",
        "review_gate": {"status": "PENDING_SUBMISSION"},
        "started_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-02T00:00:00+00:00",
    }
    rec.update(extra)
    return rec


def _candidate_item(**extra):
    item = {
        "PK": {"S": "USER#u1"},
        "SK": {"S": "CERT_CANDIDATE#p1"},
        "pathway_id": {"S": "p1"},
        "pathway_version": {"S": "v1"},
        "candidate_status": {"S": "IN_PROGRESS"},
        "review_gate": {
            "M": {
                "status": {"S": "PENDING_REVIEW"},
                "reviewed_at": {"S": "2026-01-03"},
                "reviewer_id": {"S": "rev1"},
            }
        },
        "started_at": {"S": "2026-01-01"},
        "updated_at": {"S": "2026-01-02"},
    }
    item.update(extra)
    return item


class TestPutCandidateRecord:
    def test_puts_minimal_item(self, service):
        service.put_candidate_record("u1", _candidate_record())
        item = service._dynamodb.put_item.call_args.kwargs["Item"]
        assert item["PK"] == {"S": "USER#u1"}
        assert item["SK"] == {"S": "CERT_CANDIDATE#p1"}
        assert item["review_gate"] == {"M": {"status": {"S": "PENDING_SUBMISSION"}}}
        assert "credential_id" not in item
        assert "prior_credential_id" not in item

    def test_puts_with_optional_fields(self, service):
        rec = _candidate_record(
            credential_id="cred1",
            prior_credential_id="cred0",
            review_gate={
                "status": "PASSED",
                "reviewed_at": "2026-01-03",
                "reviewer_id": "rev1",
            },
        )
        service.put_candidate_record("u1", rec)
        item = service._dynamodb.put_item.call_args.kwargs["Item"]
        assert item["credential_id"] == {"S": "cred1"}
        assert item["prior_credential_id"] == {"S": "cred0"}
        gate = item["review_gate"]["M"]
        assert gate["reviewed_at"] == {"S": "2026-01-03"}
        assert gate["reviewer_id"] == {"S": "rev1"}

    def test_client_error_raises(self, service):
        service._dynamodb.put_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.put_candidate_record("u1", _candidate_record())


class TestGetCandidateRecord:
    def test_returns_unmarshalled(self, service):
        service._dynamodb.get_item.return_value = {"Item": _candidate_item()}
        result = service.get_candidate_record("u1", "p1")
        assert result["user_id"] == "u1"
        assert result["candidate_status"] == "IN_PROGRESS"
        assert result["review_gate"]["status"] == "PENDING_REVIEW"
        assert result["review_gate"]["reviewer_id"] == "rev1"

    def test_with_optional_credential_ids(self, service):
        item = _candidate_item(
            credential_id={"S": "cred1"},
            prior_credential_id={"S": "cred0"},
        )
        service._dynamodb.get_item.return_value = {"Item": item}
        result = service.get_candidate_record("u1", "p1")
        assert result["credential_id"] == "cred1"
        assert result["prior_credential_id"] == "cred0"

    def test_none_when_absent(self, service):
        service._dynamodb.get_item.return_value = {}
        assert service.get_candidate_record("u1", "p1") is None

    def test_client_error_raises(self, service):
        service._dynamodb.get_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_candidate_record("u1", "p1")


class TestUpdateCandidateStatus:
    def test_without_condition(self, service):
        service.update_candidate_status("u1", "p1", "AWARDED")
        kwargs = service._dynamodb.update_item.call_args.kwargs
        assert "ConditionExpression" not in kwargs
        assert kwargs["ExpressionAttributeValues"][":new_status"] == {"S": "AWARDED"}
        assert ":now" in kwargs["ExpressionAttributeValues"]

    def test_with_expected_status_adds_condition(self, service):
        service.update_candidate_status("u1", "p1", "AWARDED", expected_status="IN_PROGRESS")
        kwargs = service._dynamodb.update_item.call_args.kwargs
        assert kwargs["ConditionExpression"] == "candidate_status = :expected"
        assert kwargs["ExpressionAttributeValues"][":expected"] == {"S": "IN_PROGRESS"}

    def test_client_error_raises(self, service):
        service._dynamodb.update_item.side_effect = _client_error("ConditionalCheckFailedException")
        with pytest.raises(ClientError):
            service.update_candidate_status("u1", "p1", "AWARDED")


class TestUpdateReviewGate:
    def test_updates_gate(self, service):
        service.update_review_gate(
            "u1", "p1", {"status": "PASSED", "reviewed_at": "2026-01-03", "reviewer_id": "rev1"}
        )
        kwargs = service._dynamodb.update_item.call_args.kwargs
        gate = kwargs["ExpressionAttributeValues"][":gate"]["M"]
        assert gate["status"] == {"S": "PASSED"}
        assert gate["reviewer_id"] == {"S": "rev1"}

    def test_client_error_raises(self, service):
        service._dynamodb.update_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.update_review_gate("u1", "p1", {"status": "PASSED"})


class TestListCandidates:
    def test_single_page_under_limit(self, service):
        service._dynamodb.scan.return_value = {"Items": [_candidate_item(), _candidate_item()]}
        candidates, next_key = service.list_candidates(limit=20)
        assert len(candidates) == 2
        assert next_key is None
        # No filters beyond SK prefix
        expr = service._dynamodb.scan.call_args.kwargs["FilterExpression"]
        assert "begins_with(SK, :sk_prefix)" in expr

    def test_filters_by_pathway_and_status(self, service):
        service._dynamodb.scan.return_value = {"Items": []}
        service.list_candidates(pathway_id="p1", status="AWARDED", limit=20)
        kwargs = service._dynamodb.scan.call_args.kwargs
        assert "pathway_id = :pathway_id" in kwargs["FilterExpression"]
        assert "candidate_status = :status" in kwargs["FilterExpression"]
        assert kwargs["ExpressionAttributeValues"][":pathway_id"] == {"S": "p1"}
        assert kwargs["ExpressionAttributeValues"][":status"] == {"S": "AWARDED"}

    def test_pagination_loop_accumulates_until_limit(self, service):
        # First page returns 1 item + LastEvaluatedKey, second returns 1 more.
        service._dynamodb.scan.side_effect = [
            {"Items": [_candidate_item()], "LastEvaluatedKey": {"PK": {"S": "k1"}}},
            {"Items": [_candidate_item()], "LastEvaluatedKey": {"PK": {"S": "k2"}}},
        ]
        candidates, next_key = service.list_candidates(limit=2)
        assert len(candidates) == 2
        assert next_key == {"PK": {"S": "k2"}}
        assert service._dynamodb.scan.call_count == 2
        # Second call should pass ExclusiveStartKey from first page.
        second_kwargs = service._dynamodb.scan.call_args_list[1].kwargs
        assert second_kwargs["ExclusiveStartKey"] == {"PK": {"S": "k1"}}

    def test_pagination_exhausts_table(self, service):
        service._dynamodb.scan.side_effect = [
            {"Items": [_candidate_item()], "LastEvaluatedKey": {"PK": {"S": "k1"}}},
            {"Items": [_candidate_item()]},  # no LastEvaluatedKey -> stop
        ]
        candidates, next_key = service.list_candidates(limit=10)
        assert len(candidates) == 2
        assert next_key is None

    def test_breaks_within_page_at_limit(self, service):
        # One scan page returns more than limit; inner loop breaks at limit.
        service._dynamodb.scan.return_value = {
            "Items": [_candidate_item(), _candidate_item(), _candidate_item()],
            "LastEvaluatedKey": {"PK": {"S": "k1"}},
        }
        candidates, next_key = service.list_candidates(limit=2)
        assert len(candidates) == 2
        assert next_key == {"PK": {"S": "k1"}}
        assert service._dynamodb.scan.call_count == 1

    def test_client_error_raises(self, service):
        service._dynamodb.scan.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.list_candidates()


# ---------------------------------------------------------------------------
# Review session operations
# ---------------------------------------------------------------------------


def _review_session(**extra):
    s = {
        "pathway_id": "p1",
        "revision_number": 2,
        "status": "PENDING_REVIEW",
        "rubric_scores": {"design": {"score": 5, "comment": "ok"}},
        "evaluation_dimensions": {"defense": "strong"},
        "submission_url": "https://example.com/sub",
        "submitted_at": "2026-01-01",
    }
    s.update(extra)
    return s


def _review_item(**extra):
    item = {
        "PK": {"S": "USER#u1"},
        "SK": {"S": "CERT_REVIEW#p1#REV#2"},
        "pathway_id": {"S": "p1"},
        "revision_number": {"N": "2"},
        "status": {"S": "PASSED"},
        "rubric_scores": {"M": {"design": {"M": {"score": {"N": "5"}, "comment": {"S": "ok"}}}}},
        "evaluation_dimensions": {"M": {"defense": {"S": "strong"}}},
        "submission_url": {"S": "https://example.com/sub"},
        "submitted_at": {"S": "2026-01-01"},
    }
    item.update(extra)
    return item


class TestPutReviewSession:
    def test_puts_minimal(self, service):
        service.put_review_session("u1", _review_session())
        item = service._dynamodb.put_item.call_args.kwargs["Item"]
        assert item["SK"] == {"S": "CERT_REVIEW#p1#REV#2"}
        assert item["revision_number"] == {"N": "2"}
        assert item["rubric_scores"]["M"]["design"]["M"]["score"] == {"N": "5"}
        assert item["evaluation_dimensions"]["M"]["defense"] == {"S": "strong"}
        assert "reviewer_id" not in item
        assert "reviewed_at" not in item

    def test_puts_with_optional_fields(self, service):
        s = _review_session(
            reviewer_id="rev1", reviewer_notes="note", reviewed_at="2026-01-05"
        )
        service.put_review_session("u1", s)
        item = service._dynamodb.put_item.call_args.kwargs["Item"]
        assert item["reviewer_id"] == {"S": "rev1"}
        assert item["reviewer_notes"] == {"S": "note"}
        assert item["reviewed_at"] == {"S": "2026-01-05"}

    def test_defaults_missing_score_maps(self, service):
        s = _review_session()
        del s["rubric_scores"]
        del s["evaluation_dimensions"]
        service.put_review_session("u1", s)
        item = service._dynamodb.put_item.call_args.kwargs["Item"]
        assert item["rubric_scores"] == {"M": {}}
        assert item["evaluation_dimensions"] == {"M": {}}

    def test_client_error_raises(self, service):
        service._dynamodb.put_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.put_review_session("u1", _review_session())


class TestGetLatestReviewSession:
    def test_returns_unmarshalled(self, service):
        service._dynamodb.query.return_value = {"Items": [_review_item()]}
        result = service.get_latest_review_session("u1", "p1")
        assert result["revision_number"] == 2
        assert result["status"] == "PASSED"
        assert result["rubric_scores"]["design"]["score"] == 5
        assert result["evaluation_dimensions"]["defense"] == "strong"
        kwargs = service._dynamodb.query.call_args.kwargs
        assert kwargs["ScanIndexForward"] is False
        assert kwargs["Limit"] == 1

    def test_none_when_empty(self, service):
        service._dynamodb.query.return_value = {"Items": []}
        assert service.get_latest_review_session("u1", "p1") is None

    def test_client_error_raises(self, service):
        service._dynamodb.query.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_latest_review_session("u1", "p1")


class TestGetReviewHistory:
    def test_returns_list_ascending(self, service):
        service._dynamodb.query.return_value = {"Items": [_review_item(), _review_item()]}
        result = service.get_review_history("u1", "p1")
        assert len(result) == 2
        assert service._dynamodb.query.call_args.kwargs["ScanIndexForward"] is True

    def test_empty(self, service):
        service._dynamodb.query.return_value = {}
        assert service.get_review_history("u1", "p1") == []

    def test_client_error_raises(self, service):
        service._dynamodb.query.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_review_history("u1", "p1")


# ---------------------------------------------------------------------------
# Credential operations
# ---------------------------------------------------------------------------


def _credential(**extra):
    c = {
        "credential_id": "DSB-DSEP-ABCD1234",
        "pathway_id": "p1",
        "pathway_version": "v1",
        "credential_status": "ACTIVE",
        "issued_at": "2026-01-01",
        "expires_at": "2027-01-01",
        "full_name_at_issuance": "Jane Doe",
    }
    c.update(extra)
    return c


def _credential_item(**extra):
    item = {
        "PK": {"S": "USER#u1"},
        "SK": {"S": "CREDENTIAL#DSB-DSEP-ABCD1234"},
        "credential_id": {"S": "DSB-DSEP-ABCD1234"},
        "pathway_id": {"S": "p1"},
        "pathway_version": {"S": "v1"},
        "credential_status": {"S": "ACTIVE"},
        "issued_at": {"S": "2026-01-01"},
        "expires_at": {"S": "2027-01-01"},
        "full_name_at_issuance": {"S": "Jane Doe"},
        "is_recertification": {"BOOL": False},
        "is_grandfathered": {"BOOL": False},
    }
    item.update(extra)
    return item


class TestPutCredential:
    def test_puts_with_conditional(self, service):
        service.put_credential("u1", _credential())
        kwargs = service._dynamodb.put_item.call_args.kwargs
        assert kwargs["ConditionExpression"] == "attribute_not_exists(SK)"
        item = kwargs["Item"]
        assert item["SK"] == {"S": "CREDENTIAL#DSB-DSEP-ABCD1234"}
        assert item["GSI_PK"] == {"S": "CRED#DSB-DSEP-ABCD1234"}
        assert item["GSI_EXPIRY_PK"] == {"S": "ACTIVE"}
        assert item["GSI_EXPIRY_SK"] == {"S": "2027-01-01"}
        assert "certificate_s3_key" not in item
        assert "revoked_at" not in item

    def test_puts_with_optional_fields(self, service):
        c = _credential(
            certificate_s3_key="certificates/x.png",
            prior_credential_id="cred0",
            revoked_at="2026-06-01",
            revocation_reason="fraud",
            revoked_by="admin",
            is_recertification=True,
            is_grandfathered=True,
        )
        service.put_credential("u1", c)
        item = service._dynamodb.put_item.call_args.kwargs["Item"]
        assert item["certificate_s3_key"] == {"S": "certificates/x.png"}
        assert item["prior_credential_id"] == {"S": "cred0"}
        assert item["revoked_at"] == {"S": "2026-06-01"}
        assert item["revocation_reason"] == {"S": "fraud"}
        assert item["revoked_by"] == {"S": "admin"}
        assert item["is_recertification"] == {"BOOL": True}
        assert item["is_grandfathered"] == {"BOOL": True}

    def test_client_error_raises(self, service):
        service._dynamodb.put_item.side_effect = _client_error("ConditionalCheckFailedException")
        with pytest.raises(ClientError):
            service.put_credential("u1", _credential())


class TestGetCredential:
    def test_returns_unmarshalled(self, service):
        service._dynamodb.get_item.return_value = {"Item": _credential_item()}
        result = service.get_credential("u1", "DSB-DSEP-ABCD1234")
        assert result["user_id"] == "u1"
        assert result["credential_status"] == "ACTIVE"
        assert result["is_recertification"] is False

    def test_with_optional_fields(self, service):
        item = _credential_item(
            certificate_s3_key={"S": "certificates/x.png"},
            prior_credential_id={"S": "cred0"},
            revoked_at={"S": "2026-06-01"},
            revocation_reason={"S": "fraud"},
            revoked_by={"S": "admin"},
        )
        service._dynamodb.get_item.return_value = {"Item": item}
        result = service.get_credential("u1", "DSB-DSEP-ABCD1234")
        assert result["certificate_s3_key"] == "certificates/x.png"
        assert result["prior_credential_id"] == "cred0"
        assert result["revoked_at"] == "2026-06-01"
        assert result["revocation_reason"] == "fraud"
        assert result["revoked_by"] == "admin"

    def test_none_when_absent(self, service):
        service._dynamodb.get_item.return_value = {}
        assert service.get_credential("u1", "cred") is None

    def test_client_error_raises(self, service):
        service._dynamodb.get_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_credential("u1", "cred")


class TestGetCredentialById:
    def test_returns_via_gsi(self, service):
        service._dynamodb.query.return_value = {"Items": [_credential_item()]}
        result = service.get_credential_by_id("DSB-DSEP-ABCD1234")
        assert result["credential_id"] == "DSB-DSEP-ABCD1234"
        kwargs = service._dynamodb.query.call_args.kwargs
        assert kwargs["IndexName"] == "CredentialLookup"
        assert kwargs["ExpressionAttributeValues"][":pk"] == {"S": "CRED#DSB-DSEP-ABCD1234"}

    def test_none_when_empty(self, service):
        service._dynamodb.query.return_value = {"Items": []}
        assert service.get_credential_by_id("x") is None

    def test_client_error_raises(self, service):
        service._dynamodb.query.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_credential_by_id("x")


class TestListUserCredentials:
    def test_returns_list(self, service):
        service._dynamodb.query.return_value = {"Items": [_credential_item()]}
        result = service.list_user_credentials("u1")
        assert len(result) == 1
        kwargs = service._dynamodb.query.call_args.kwargs
        assert kwargs["ExpressionAttributeValues"][":pk"] == {"S": "USER#u1"}
        assert kwargs["ExpressionAttributeValues"][":sk_prefix"] == {"S": "CREDENTIAL#"}

    def test_empty(self, service):
        service._dynamodb.query.return_value = {}
        assert service.list_user_credentials("u1") == []

    def test_client_error_raises(self, service):
        service._dynamodb.query.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.list_user_credentials("u1")


class TestUpdateCredentialStatus:
    def test_without_condition(self, service):
        service.update_credential_status("u1", "cred", "EXPIRED")
        kwargs = service._dynamodb.update_item.call_args.kwargs
        assert "ConditionExpression" not in kwargs
        values = kwargs["ExpressionAttributeValues"]
        assert values[":new_status"] == {"S": "EXPIRED"}
        assert "GSI_EXPIRY_PK = :new_status" in kwargs["UpdateExpression"]

    def test_with_condition(self, service):
        service.update_credential_status("u1", "cred", "EXPIRED", condition="credential_status = :x")
        kwargs = service._dynamodb.update_item.call_args.kwargs
        assert kwargs["ConditionExpression"] == "credential_status = :x"

    def test_client_error_raises(self, service):
        service._dynamodb.update_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.update_credential_status("u1", "cred", "EXPIRED")


class TestQueryCredentialsByStatusAndExpiry:
    def test_returns_list(self, service):
        service._dynamodb.query.return_value = {"Items": [_credential_item()]}
        result = service.query_credentials_by_status_and_expiry("ACTIVE", "2026-12-01")
        assert len(result) == 1
        kwargs = service._dynamodb.query.call_args.kwargs
        assert kwargs["IndexName"] == "CredentialExpiry"
        assert kwargs["ExpressionAttributeValues"][":status"] == {"S": "ACTIVE"}
        assert kwargs["ExpressionAttributeValues"][":expires_before"] == {"S": "2026-12-01"}

    def test_empty(self, service):
        service._dynamodb.query.return_value = {}
        assert service.query_credentials_by_status_and_expiry("ACTIVE", "2026-12-01") == []

    def test_client_error_raises(self, service):
        service._dynamodb.query.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.query_credentials_by_status_and_expiry("ACTIVE", "2026-12-01")


# ---------------------------------------------------------------------------
# User profile reads
# ---------------------------------------------------------------------------


class TestGetUserFullName:
    def test_returns_name(self, service):
        service._dynamodb.get_item.return_value = {"Item": {"full_name": {"S": "Jane Doe"}}}
        assert service.get_user_full_name("u1") == "Jane Doe"
        kwargs = service._dynamodb.get_item.call_args.kwargs
        assert kwargs["ProjectionExpression"] == "full_name"
        assert kwargs["Key"]["SK"] == {"S": "PROFILE"}

    def test_none_when_no_item(self, service):
        service._dynamodb.get_item.return_value = {}
        assert service.get_user_full_name("u1") is None

    def test_none_when_attr_absent(self, service):
        service._dynamodb.get_item.return_value = {"Item": {"other": {"S": "x"}}}
        assert service.get_user_full_name("u1") is None

    def test_client_error_raises(self, service):
        service._dynamodb.get_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_user_full_name("u1")


class TestGetUserEmail:
    def test_returns_email(self, service):
        service._dynamodb.get_item.return_value = {"Item": {"email": {"S": "j@x.com"}}}
        assert service.get_user_email("u1") == "j@x.com"
        assert service._dynamodb.get_item.call_args.kwargs["ProjectionExpression"] == "email"

    def test_none_when_no_item(self, service):
        service._dynamodb.get_item.return_value = {}
        assert service.get_user_email("u1") is None

    def test_client_error_raises(self, service):
        service._dynamodb.get_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_user_email("u1")


class TestGetUserUsername:
    def test_returns_username(self, service):
        service._dynamodb.get_item.return_value = {"Item": {"username": {"S": "jdoe"}}}
        assert service.get_user_username("u1") == "jdoe"
        assert service._dynamodb.get_item.call_args.kwargs["ProjectionExpression"] == "username"

    def test_empty_when_no_item(self, service):
        service._dynamodb.get_item.return_value = {}
        assert service.get_user_username("u1") == ""

    def test_empty_when_attr_absent(self, service):
        service._dynamodb.get_item.return_value = {"Item": {"other": {"S": "x"}}}
        assert service.get_user_username("u1") == ""

    def test_client_error_raises(self, service):
        service._dynamodb.get_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.get_user_username("u1")


class TestUpdateCertificateS3Key:
    def test_updates(self, service):
        service.update_certificate_s3_key("u1", "cred", "certificates/x.png")
        kwargs = service._dynamodb.update_item.call_args.kwargs
        assert kwargs["Key"]["SK"] == {"S": "CREDENTIAL#cred"}
        assert kwargs["ExpressionAttributeValues"][":s3_key"] == {"S": "certificates/x.png"}

    def test_client_error_raises(self, service):
        service._dynamodb.update_item.side_effect = _client_error()
        with pytest.raises(ClientError):
            service.update_certificate_s3_key("u1", "cred", "certificates/x.png")


# ---------------------------------------------------------------------------
# Marshalling helpers (edge cases)
# ---------------------------------------------------------------------------


class TestMarshalHelpers:
    def test_marshal_map_types(self):
        data = {
            "s": "text",
            "b": True,
            "i": 3,
            "f": 1.5,
            "nested": {"x": "y", "flag": False, "n": 2},
        }
        result = CertificationDB._marshal_map(data)
        assert result["s"] == {"S": "text"}
        assert result["b"] == {"BOOL": True}
        assert result["i"] == {"N": "3"}
        assert result["f"] == {"N": "1.5"}
        assert result["nested"]["M"]["x"] == {"S": "y"}
        assert result["nested"]["M"]["flag"] == {"BOOL": False}
        assert result["nested"]["M"]["n"] == {"N": "2"}

    def test_unmarshal_nested_map_scalars_and_nested(self):
        dynamo_map = {
            "top_s": {"S": "v"},
            "top_n": {"N": "7"},
            "top_b": {"BOOL": True},
            "grp": {"M": {"a": {"S": "x"}, "b": {"N": "9"}, "c": {"BOOL": False}}},
        }
        result = CertificationDB._unmarshal_nested_map(dynamo_map)
        assert result["top_s"] == "v"
        assert result["top_n"] == 7
        assert result["top_b"] is True
        assert result["grp"] == {"a": "x", "b": 9, "c": False}

    def test_unmarshal_candidate_pk_without_prefix(self):
        item = {"PK": {"S": "WEIRD"}, "pathway_id": {"S": "p1"}}
        result = CertificationDB._unmarshal_candidate(item)
        assert result["user_id"] == ""

    def test_unmarshal_review_session_without_pk_prefix(self):
        item = {"PK": {"S": "nope"}, "revision_number": {"N": "4"}}
        result = CertificationDB._unmarshal_review_session(item)
        assert result["user_id"] == ""
        assert result["revision_number"] == 4
