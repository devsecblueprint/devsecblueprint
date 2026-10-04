"""Unit tests for app.services.certification.credential_lifecycle.

CredentialLifecycleService constructs a CertificationDB in __init__ (which
creates boto3 clients). Tests patch mod.CertificationDB during construction,
then reassign svc._db with a MagicMock for direct control. The pathway config
lookup (imported as mod.get_pathway_config) is patched per-test. Covers
issue/grant/check_expiry/revoke/verify_course_completion plus guard and error
paths.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.models.certification import CredentialStatus
from app.services.certification import credential_lifecycle as mod
from app.services.certification.credential_lifecycle import CredentialLifecycleService


def _conditional_error() -> ClientError:
    return ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException", "Message": "dup"}},
        "PutItem",
    )


def _pathway(**extra):
    p = {
        "pathway_id": "devsecops-engineering",
        "version": "v1",
        "pathway_code": "DSEP",
        "learning_requirements": ["a", "b"],
    }
    p.update(extra)
    return p


@pytest.fixture
def service():
    settings = MagicMock(credential_validity_months=12)
    with patch.object(mod, "CertificationDB", return_value=MagicMock()):
        svc = CredentialLifecycleService(settings)
    svc._db = MagicMock()
    return svc


def _iso_now():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# issue_credential
# ---------------------------------------------------------------------------


class TestIssueCredential:
    def test_success_awards_and_returns_credential(self, service):
        service._db.get_user_full_name.return_value = "Jane Doe"
        with patch.object(mod, "get_pathway_config", return_value=_pathway()):
            cred = service.issue_credential("u1", "devsecops-engineering", "v1")

        assert cred.credential_status == CredentialStatus.ACTIVE
        assert cred.full_name_at_issuance == "Jane Doe"
        assert cred.credential_id.startswith("DSB-DSEP-")
        # Credential written then candidate record updated to AWARDED.
        service._db.put_credential.assert_called_once()
        cand = service._db.put_candidate_record.call_args.args[1]
        assert cand["candidate_status"] == "AWARDED"
        assert cand["credential_id"] == cred.credential_id

    def test_recertification_passes_prior_id(self, service):
        service._db.get_user_full_name.return_value = "Jane Doe"
        with patch.object(mod, "get_pathway_config", return_value=_pathway()):
            cred = service.issue_credential(
                "u1",
                "devsecops-engineering",
                "v1",
                is_recertification=True,
                prior_credential_id="DSB-DSEP-OLD",
            )
        assert cred.is_recertification is True
        written = service._db.put_credential.call_args.args[1]
        assert written["prior_credential_id"] == "DSB-DSEP-OLD"

    def test_raises_when_pathway_missing(self, service):
        with patch.object(mod, "get_pathway_config", return_value=None):
            with pytest.raises(ValueError, match="No pathway definition"):
                service.issue_credential("u1", "x", "v1")

    def test_raises_when_no_full_name(self, service):
        service._db.get_user_full_name.return_value = "   "
        with patch.object(mod, "get_pathway_config", return_value=_pathway()):
            with pytest.raises(ValueError, match="valid full_name"):
                service.issue_credential("u1", "devsecops-engineering", "v1")

    def test_raises_when_full_name_none(self, service):
        service._db.get_user_full_name.return_value = None
        with patch.object(mod, "get_pathway_config", return_value=_pathway()):
            with pytest.raises(ValueError, match="valid full_name"):
                service.issue_credential("u1", "devsecops-engineering", "v1")

    def test_duplicate_returns_existing(self, service):
        service._db.get_user_full_name.return_value = "Jane Doe"
        service._db.put_credential.side_effect = _conditional_error()
        existing = {
            "credential_id": "DSB-DSEP-EXIST",
            "pathway_id": "devsecops-engineering",
            "pathway_version": "v1",
            "credential_status": "ACTIVE",
            "issued_at": "2026-01-01",
            "expires_at": "2027-01-01",
            "full_name_at_issuance": "Jane Doe",
        }
        service._db.get_credential.return_value = existing
        with patch.object(mod, "get_pathway_config", return_value=_pathway()):
            cred = service.issue_credential("u1", "devsecops-engineering", "v1")
        assert cred.credential_id == "DSB-DSEP-EXIST"
        service._db.put_candidate_record.assert_not_called()

    def test_duplicate_but_no_existing_reraises(self, service):
        service._db.get_user_full_name.return_value = "Jane Doe"
        service._db.put_credential.side_effect = _conditional_error()
        service._db.get_credential.return_value = None
        with patch.object(mod, "get_pathway_config", return_value=_pathway()):
            with pytest.raises(ClientError):
                service.issue_credential("u1", "devsecops-engineering", "v1")

    def test_non_conditional_put_error_reraises(self, service):
        service._db.get_user_full_name.return_value = "Jane Doe"
        service._db.put_credential.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError"}}, "PutItem"
        )
        with patch.object(mod, "get_pathway_config", return_value=_pathway()):
            with pytest.raises(ClientError):
                service.issue_credential("u1", "devsecops-engineering", "v1")

    def test_plain_exception_without_response_reraises(self, service):
        # Exception lacking a .response dict hits the `else: error_code = ""`
        # branch and is re-raised unchanged.
        service._db.get_user_full_name.return_value = "Jane Doe"
        service._db.put_credential.side_effect = RuntimeError("no response attr")
        with patch.object(mod, "get_pathway_config", return_value=_pathway()):
            with pytest.raises(RuntimeError):
                service.issue_credential("u1", "devsecops-engineering", "v1")

    def test_candidate_record_failure_does_not_fail_issuance(self, service):
        service._db.get_user_full_name.return_value = "Jane Doe"
        service._db.put_candidate_record.side_effect = RuntimeError("db down")
        with patch.object(mod, "get_pathway_config", return_value=_pathway()):
            cred = service.issue_credential("u1", "devsecops-engineering", "v1")
        assert cred.credential_status == CredentialStatus.ACTIVE


# ---------------------------------------------------------------------------
# grant_credential
# ---------------------------------------------------------------------------


class TestGrantCredential:
    def test_success_grandfathered(self, service):
        service._db.get_user_full_name.return_value = "Jane Doe"
        with (
            patch.object(mod, "get_pathway_config", return_value=_pathway()),
            patch.object(service, "verify_course_completion", return_value=(True, [])),
        ):
            cred = service.grant_credential("admin", "u1", "devsecops-engineering")
        assert cred.is_grandfathered is True
        assert cred.credential_status == CredentialStatus.ACTIVE
        cand = service._db.put_candidate_record.call_args.args[1]
        assert cand["candidate_status"] == "AWARDED"

    def test_raises_when_no_full_name(self, service):
        service._db.get_user_full_name.return_value = ""
        with pytest.raises(ValueError, match="full name"):
            service.grant_credential("admin", "u1", "devsecops-engineering")

    def test_raises_when_incomplete(self, service):
        service._db.get_user_full_name.return_value = "Jane Doe"
        with patch.object(
            service, "verify_course_completion", return_value=(False, ["a", "b"])
        ):
            with pytest.raises(ValueError, match="not completed"):
                service.grant_credential("admin", "u1", "devsecops-engineering")

    def test_incomplete_message_truncates_many(self, service):
        service._db.get_user_full_name.return_value = "Jane Doe"
        missing = [f"m{i}" for i in range(8)]
        with patch.object(
            service, "verify_course_completion", return_value=(False, missing)
        ):
            with pytest.raises(ValueError, match="and 3 more"):
                service.grant_credential("admin", "u1", "devsecops-engineering")

    def test_raises_when_pathway_missing(self, service):
        service._db.get_user_full_name.return_value = "Jane Doe"
        with (
            patch.object(service, "verify_course_completion", return_value=(True, [])),
            patch.object(mod, "get_pathway_config", return_value=None),
        ):
            with pytest.raises(ValueError, match="No pathway definition"):
                service.grant_credential("admin", "u1", "x")

    def test_duplicate_returns_existing(self, service):
        service._db.get_user_full_name.return_value = "Jane Doe"
        service._db.put_credential.side_effect = _conditional_error()
        service._db.get_credential.return_value = {
            "credential_id": "DSB-DSEP-EXIST",
            "pathway_id": "devsecops-engineering",
            "pathway_version": "v1",
            "credential_status": "ACTIVE",
            "issued_at": "2026-01-01",
            "expires_at": "2027-01-01",
            "full_name_at_issuance": "Jane Doe",
        }
        with (
            patch.object(mod, "get_pathway_config", return_value=_pathway()),
            patch.object(service, "verify_course_completion", return_value=(True, [])),
        ):
            cred = service.grant_credential("admin", "u1", "devsecops-engineering")
        assert cred.credential_id == "DSB-DSEP-EXIST"

    def test_non_conditional_error_reraises(self, service):
        service._db.get_user_full_name.return_value = "Jane Doe"
        service._db.put_credential.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError"}}, "PutItem"
        )
        with (
            patch.object(mod, "get_pathway_config", return_value=_pathway()),
            patch.object(service, "verify_course_completion", return_value=(True, [])),
        ):
            with pytest.raises(ClientError):
                service.grant_credential("admin", "u1", "devsecops-engineering")

    def test_plain_exception_without_response_reraises(self, service):
        # Exception without a .response dict -> error_code stays "" (236->239).
        service._db.get_user_full_name.return_value = "Jane Doe"
        service._db.put_credential.side_effect = RuntimeError("no response attr")
        with (
            patch.object(mod, "get_pathway_config", return_value=_pathway()),
            patch.object(service, "verify_course_completion", return_value=(True, [])),
        ):
            with pytest.raises(RuntimeError):
                service.grant_credential("admin", "u1", "devsecops-engineering")

    def test_duplicate_but_no_existing_reraises(self, service):
        # Conditional error but get_credential returns None -> `if existing`
        # is falsy (246->248) and the error is re-raised.
        service._db.get_user_full_name.return_value = "Jane Doe"
        service._db.put_credential.side_effect = _conditional_error()
        service._db.get_credential.return_value = None
        with (
            patch.object(mod, "get_pathway_config", return_value=_pathway()),
            patch.object(service, "verify_course_completion", return_value=(True, [])),
        ):
            with pytest.raises(ClientError):
                service.grant_credential("admin", "u1", "devsecops-engineering")


# ---------------------------------------------------------------------------
# check_expiry
# ---------------------------------------------------------------------------


class TestCheckExpiry:
    def _cred(self, status="ACTIVE", expires_at=None):
        return {"credential_status": status, "expires_at": expires_at}

    def test_none_when_not_found(self, service):
        service._db.get_credential_by_id.return_value = None
        assert service.check_expiry("c1") is None

    def test_none_for_non_active_status(self, service):
        service._db.get_credential_by_id.return_value = self._cred(status="REVOKED")
        assert service.check_expiry("c1") is None

    def test_none_when_no_expiry(self, service):
        service._db.get_credential_by_id.return_value = self._cred(expires_at=None)
        assert service.check_expiry("c1") is None

    def test_returns_expired_when_past(self, service):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        service._db.get_credential_by_id.return_value = self._cred(expires_at=past)
        assert service.check_expiry("c1") == CredentialStatus.EXPIRED.value

    def test_returns_renewal_eligible_within_window(self, service):
        soon = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
        service._db.get_credential_by_id.return_value = self._cred(expires_at=soon)
        assert service.check_expiry("c1") == CredentialStatus.RENEWAL_ELIGIBLE.value

    def test_none_when_far_future(self, service):
        future = (datetime.now(timezone.utc) + timedelta(days=200)).isoformat()
        service._db.get_credential_by_id.return_value = self._cred(expires_at=future)
        assert service.check_expiry("c1") is None

    def test_already_renewal_eligible_within_window_no_change(self, service):
        soon = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
        service._db.get_credential_by_id.return_value = self._cred(
            status="RENEWAL_ELIGIBLE", expires_at=soon
        )
        assert service.check_expiry("c1") is None

    def test_naive_expiry_treated_as_utc(self, service):
        # Naive timestamp (no tzinfo) in the past -> treated as UTC, expired.
        past_naive = (
            (datetime.now(timezone.utc) - timedelta(days=5))
            .replace(tzinfo=None)
            .isoformat()
        )
        service._db.get_credential_by_id.return_value = self._cred(
            expires_at=past_naive
        )
        assert service.check_expiry("c1") == CredentialStatus.EXPIRED.value


# ---------------------------------------------------------------------------
# revoke_credential
# ---------------------------------------------------------------------------


class TestRevokeCredential:
    def _active_cred(self, **extra):
        c = {
            "credential_id": "DSB-DSEP-ABCD1234",
            "user_id": "u1",
            "pathway_id": "devsecops-engineering",
            "pathway_version": "v1",
            "credential_status": "ACTIVE",
            "issued_at": "2026-01-01",
            "expires_at": "2027-01-01",
            "full_name_at_issuance": "Jane Doe",
        }
        c.update(extra)
        return c

    def test_success_updates_records(self, service):
        service._db.get_credential_by_id.return_value = self._active_cred()
        cred = service.revoke_credential("DSB-DSEP-ABCD1234", "fraud", "admin")
        assert cred.credential_status == CredentialStatus.REVOKED
        assert cred.revocation_reason == "fraud"
        assert cred.revoked_by == "admin"
        service._db._dynamodb.update_item.assert_called_once()
        service._db.update_candidate_status.assert_called_once()

    def test_raises_when_not_found(self, service):
        service._db.get_credential_by_id.return_value = None
        with pytest.raises(ValueError, match="not found"):
            service.revoke_credential("c1", "fraud", "admin")

    def test_raises_when_already_revoked(self, service):
        service._db.get_credential_by_id.return_value = self._active_cred(
            credential_status="REVOKED"
        )
        with pytest.raises(ValueError, match="already revoked"):
            service.revoke_credential("c1", "fraud", "admin")

    def test_raises_when_no_user_id(self, service):
        service._db.get_credential_by_id.return_value = self._active_cred(user_id=None)
        with pytest.raises(ValueError, match="user_id"):
            service.revoke_credential("c1", "fraud", "admin")

    def test_update_item_failure_reraises(self, service):
        service._db.get_credential_by_id.return_value = self._active_cred()
        service._db._dynamodb.update_item.side_effect = RuntimeError("boom")
        with pytest.raises(RuntimeError):
            service.revoke_credential("c1", "fraud", "admin")

    def test_candidate_status_failure_is_swallowed(self, service):
        service._db.get_credential_by_id.return_value = self._active_cred()
        service._db.update_candidate_status.side_effect = RuntimeError("boom")
        cred = service.revoke_credential("DSB-DSEP-ABCD1234", "fraud", "admin")
        assert cred.credential_status == CredentialStatus.REVOKED

    def test_no_pathway_skips_candidate_update(self, service):
        # Empty pathway_id is falsy -> candidate update is skipped, but the
        # final Credential model still builds (pathway_id must be a string).
        service._db.get_credential_by_id.return_value = self._active_cred(pathway_id="")
        service.revoke_credential("DSB-DSEP-ABCD1234", "fraud", "admin")
        service._db.update_candidate_status.assert_not_called()


# ---------------------------------------------------------------------------
# verify_course_completion
# ---------------------------------------------------------------------------


class TestVerifyCourseCompletion:
    def test_no_pathway_is_complete(self, service):
        with patch.object(mod, "get_pathway_config", return_value=None):
            complete, missing = service.verify_course_completion("u1", "x")
        assert complete is True
        assert missing == []

    def test_no_requirements_is_complete(self, service):
        with patch.object(
            mod, "get_pathway_config", return_value=_pathway(learning_requirements=[])
        ):
            complete, missing = service.verify_course_completion(
                "u1", "devsecops-engineering"
            )
        assert complete is True
        assert missing == []

    def test_all_completed(self, service):
        service._db._dynamodb.query.return_value = {
            "Items": [{"SK": {"S": "CONTENT#a"}}, {"SK": {"S": "CONTENT#b"}}]
        }
        with patch.object(mod, "get_pathway_config", return_value=_pathway()):
            complete, missing = service.verify_course_completion(
                "u1", "devsecops-engineering"
            )
        assert complete is True
        assert missing == []

    def test_missing_requirements(self, service):
        service._db._dynamodb.query.return_value = {
            "Items": [{"SK": {"S": "CONTENT#a"}}]
        }
        with patch.object(mod, "get_pathway_config", return_value=_pathway()):
            complete, missing = service.verify_course_completion(
                "u1", "devsecops-engineering"
            )
        assert complete is False
        assert missing == ["b"]

    def test_query_exception_returns_empty_completed(self, service):
        service._db._dynamodb.query.side_effect = RuntimeError("boom")
        with patch.object(mod, "get_pathway_config", return_value=_pathway()):
            complete, missing = service.verify_course_completion(
                "u1", "devsecops-engineering"
            )
        # No completed content -> all requirements missing.
        assert complete is False
        assert set(missing) == {"a", "b"}


# ---------------------------------------------------------------------------
# private helpers
# ---------------------------------------------------------------------------


class TestPrivateHelpers:
    def test_generate_credential_id_format(self, service):
        cid = service._generate_credential_id("DSEP")
        assert cid.startswith("DSB-DSEP-")
        suffix = cid.rsplit("-", 1)[1]
        assert len(suffix) == 8
        assert suffix == suffix.upper()

    def test_compute_expires_at_adds_months(self, service):
        issued = "2026-01-15T00:00:00+00:00"
        expires = service._compute_expires_at(issued)
        assert expires.startswith("2027-01-15")
