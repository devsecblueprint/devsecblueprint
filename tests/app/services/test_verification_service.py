"""Unit and property tests for app.services.verification_service.

Covers VerificationService.submit / confirm / get_eligibility and the ApyHub
Fail_Closed behaviour. Mocking mirrors tests/app/services/test_stripe_service.py:
construct the service under patch("boto3.client") so no real AWS client is built,
then reassign svc._dynamodb_client to a MagicMock and drive get_item/put_item/
update_item via return values / side effects.

- The academic-domain decision is controlled by patching svc._apyhub.is_academic_domain.
- Email send success/failure is controlled by patching
  mod.send_student_verification_email (imported into the module namespace).
- confirm() tests build matching stored hashes via the module's _hash_token.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.services import verification_service as mod
from app.services.verification_service import (
    ApyHubUnavailable,
    EmailSendError,
    InvalidEmailError,
    InvalidTokenError,
    NotAcademicError,
    VerificationService,
    _hash_token,
)


def _make_settings():
    s = MagicMock()
    s.membership_table = "test-membership"
    s.progress_table = "test-progress"
    s.apyhub_secret_name = "apyhub-secret"
    s.frontend_origin = "https://devsecblueprint.com"
    return s


def _make_service():
    """Construct a VerificationService with all AWS/HTTP boundaries mocked."""
    with patch("boto3.client"):
        svc = VerificationService(_make_settings())
    svc._dynamodb_client = MagicMock()
    # Default: no PROFILE record, so _get_username returns None.
    svc._dynamodb_client.get_item.return_value = {}
    # Default: academic result True (overridden per test as needed).
    svc._apyhub.is_academic_domain = MagicMock(return_value=True)
    return svc


def _token_item(
    token_hash, *, used=False, expiry_epoch=None, academic_email="a@uni.edu"
):
    """Build a STUDENT_VERIFICATION_TOKEN DynamoDB item."""
    if expiry_epoch is None:
        expiry_epoch = int(datetime.now(timezone.utc).timestamp()) + 3600
    return {
        "PK": {"S": "USER#u1"},
        "SK": {"S": mod.VERIFICATION_TOKEN_SK},
        "token_hash": {"S": token_hash},
        "academic_email": {"S": academic_email},
        "used": {"BOOL": used},
        "created_at": {"S": "2024-01-01T00:00:00+00:00"},
        "expires_at": {"N": str(expiry_epoch)},
        "ttl": {"N": str(expiry_epoch)},
    }


def _eligibility_item(expires_at_iso, *, academic_email="a@uni.edu"):
    return {
        "PK": {"S": "USER#u1"},
        "SK": {"S": mod.ELIGIBILITY_SK},
        "academic_email": {"S": academic_email},
        "verified_at": {"S": "2024-01-01T00:00:00+00:00"},
        "expires_at": {"S": expires_at_iso},
    }


# ---------------------------------------------------------------------------
# 9.4 — submit(): syntactic validation
# ---------------------------------------------------------------------------


class TestSubmitEmailValidation:
    @pytest.mark.parametrize(
        "email", ["", "   ", "no-at-sign", "a@b", "a b@c.com", "@c.com"]
    )
    def test_invalid_email_raises_before_any_apyhub_or_write(self, email):
        svc = _make_service()
        with pytest.raises(InvalidEmailError):
            svc.submit("u1", email)
        svc._apyhub.is_academic_domain.assert_not_called()
        svc._dynamodb_client.put_item.assert_not_called()

    def test_none_email_raises(self):
        svc = _make_service()
        with pytest.raises(InvalidEmailError):
            svc.submit("u1", None)
        svc._apyhub.is_academic_domain.assert_not_called()
        svc._dynamodb_client.put_item.assert_not_called()


# ---------------------------------------------------------------------------
# 9.4 — submit(): non-academic rejection
# ---------------------------------------------------------------------------


class TestSubmitNonAcademic:
    def test_non_academic_raises_and_writes_no_token(self):
        svc = _make_service()
        svc._apyhub.is_academic_domain = MagicMock(return_value=False)
        with patch.object(mod, "send_student_verification_email") as send:
            with pytest.raises(NotAcademicError):
                svc.submit("u1", "student@company.com")
        svc._dynamodb_client.put_item.assert_not_called()
        send.assert_not_called()


# ---------------------------------------------------------------------------
# 9.4 — submit(): ApyHub unavailable (fail-closed)
# ---------------------------------------------------------------------------


class TestSubmitApyHubUnavailable:
    def test_apyhub_error_propagates_and_writes_no_token(self):
        svc = _make_service()
        svc._apyhub.is_academic_domain = MagicMock(
            side_effect=ApyHubUnavailable("timeout")
        )
        with patch.object(mod, "send_student_verification_email") as send:
            with pytest.raises(ApyHubUnavailable):
                svc.submit("u1", "student@uni.edu")
        svc._dynamodb_client.put_item.assert_not_called()
        send.assert_not_called()

    def test_missing_or_empty_secret_fails_closed(self):
        # Exercise the real ApyHubClient._get_api_key path: an empty secret_key
        # must fail closed as ApyHubUnavailable before any token is written.
        with patch("boto3.client"):
            svc = VerificationService(_make_settings())
        svc._dynamodb_client = MagicMock()
        with (
            patch.object(mod, "get_secret", return_value={"secret_key": ""}),
            patch.object(mod, "send_student_verification_email") as send,
        ):
            with pytest.raises(ApyHubUnavailable):
                svc.submit("u1", "student@uni.edu")
        svc._dynamodb_client.put_item.assert_not_called()
        send.assert_not_called()


# ---------------------------------------------------------------------------
# 9.4 — submit(): SES send failure retains the token record
# ---------------------------------------------------------------------------


class TestSubmitEmailSend:
    def test_send_failure_raises_but_retains_token(self):
        svc = _make_service()
        with patch.object(mod, "send_student_verification_email", return_value=False):
            with pytest.raises(EmailSendError):
                svc.submit("u1", "student@uni.edu")
        # Token record was still written (retained for retry).
        svc._dynamodb_client.put_item.assert_called_once()
        item = svc._dynamodb_client.put_item.call_args.kwargs["Item"]
        assert item["SK"] == {"S": mod.VERIFICATION_TOKEN_SK}
        assert item["used"] == {"BOOL": False}
        assert "token_hash" in item

    def test_success_writes_token_and_sends_email(self):
        svc = _make_service()
        with patch.object(
            mod, "send_student_verification_email", return_value=True
        ) as send:
            svc.submit("u1", "student@uni.edu")
        svc._dynamodb_client.put_item.assert_called_once()
        item = svc._dynamodb_client.put_item.call_args.kwargs["Item"]
        assert item["academic_email"] == {"S": "student@uni.edu"}
        # The raw token appears only in the emailed link, never persisted.
        send.assert_called_once()
        confirm_url = send.call_args.args[2]
        raw_token = confirm_url.split("token=")[1]
        assert item["token_hash"] == {"S": _hash_token(raw_token)}

    def test_new_submission_supersedes_prior_token_single_sk(self):
        svc = _make_service()
        with patch.object(mod, "send_student_verification_email", return_value=True):
            svc.submit("u1", "first@uni.edu")
            svc.submit("u1", "second@uni.edu")
        # Both writes target the one fixed SK, so the second overwrites the first.
        assert svc._dynamodb_client.put_item.call_count == 2
        for call in svc._dynamodb_client.put_item.call_args_list:
            assert call.kwargs["Item"]["SK"] == {"S": mod.VERIFICATION_TOKEN_SK}


# ---------------------------------------------------------------------------
# 9.4 — confirm()
# ---------------------------------------------------------------------------


class TestConfirm:
    def test_success_writes_eligibility_and_marks_token_used(self):
        svc = _make_service()
        raw = "good-token"
        svc._dynamodb_client.get_item.return_value = {
            "Item": _token_item(_hash_token(raw))
        }
        result = svc.confirm("u1", raw)

        assert result["eligible"] is True
        # Token marked used via a conditional update.
        svc._dynamodb_client.update_item.assert_called_once()
        upd = svc._dynamodb_client.update_item.call_args.kwargs
        assert upd["ConditionExpression"] == "#used = :false"
        # Eligibility record written.
        svc._dynamodb_client.put_item.assert_called_once()
        item = svc._dynamodb_client.put_item.call_args.kwargs["Item"]
        assert item["SK"] == {"S": mod.ELIGIBILITY_SK}
        assert item["academic_email"] == {"S": "a@uni.edu"}

    def test_unknown_token_raises_no_eligibility(self):
        svc = _make_service()
        svc._dynamodb_client.get_item.return_value = {}  # no Item
        with pytest.raises(InvalidTokenError):
            svc.confirm("u1", "whatever")
        svc._dynamodb_client.update_item.assert_not_called()
        svc._dynamodb_client.put_item.assert_not_called()

    def test_already_used_token_raises_no_eligibility(self):
        svc = _make_service()
        raw = "good-token"
        svc._dynamodb_client.get_item.return_value = {
            "Item": _token_item(_hash_token(raw), used=True)
        }
        with pytest.raises(InvalidTokenError):
            svc.confirm("u1", raw)
        svc._dynamodb_client.update_item.assert_not_called()
        svc._dynamodb_client.put_item.assert_not_called()

    def test_expired_token_raises_no_eligibility(self):
        svc = _make_service()
        raw = "good-token"
        past = int(datetime.now(timezone.utc).timestamp()) - 10
        svc._dynamodb_client.get_item.return_value = {
            "Item": _token_item(_hash_token(raw), expiry_epoch=past)
        }
        with pytest.raises(InvalidTokenError):
            svc.confirm("u1", raw)
        svc._dynamodb_client.update_item.assert_not_called()
        svc._dynamodb_client.put_item.assert_not_called()

    def test_hash_mismatch_raises_no_eligibility(self):
        svc = _make_service()
        svc._dynamodb_client.get_item.return_value = {
            "Item": _token_item(_hash_token("the-real-token"))
        }
        with pytest.raises(InvalidTokenError):
            svc.confirm("u1", "a-different-token")
        svc._dynamodb_client.update_item.assert_not_called()
        svc._dynamodb_client.put_item.assert_not_called()

    def test_lost_single_use_race_raises_no_eligibility(self):
        svc = _make_service()
        raw = "good-token"
        svc._dynamodb_client.get_item.return_value = {
            "Item": _token_item(_hash_token(raw))
        }
        svc._dynamodb_client.update_item.side_effect = mod.ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException", "Message": "no"}},
            "UpdateItem",
        )
        with pytest.raises(InvalidTokenError):
            svc.confirm("u1", raw)
        svc._dynamodb_client.put_item.assert_not_called()


# ---------------------------------------------------------------------------
# 9.4 — get_eligibility() examples
# ---------------------------------------------------------------------------


class TestGetEligibility:
    def test_active_record_returned(self):
        svc = _make_service()
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        svc._dynamodb_client.get_item.return_value = {"Item": _eligibility_item(future)}
        result = svc.get_eligibility("u1")
        assert result is not None
        assert result["expires_at"] == future
        assert result["academic_email"] == "a@uni.edu"

    def test_expired_record_returns_none(self):
        svc = _make_service()
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        svc._dynamodb_client.get_item.return_value = {"Item": _eligibility_item(past)}
        assert svc.get_eligibility("u1") is None

    def test_missing_record_returns_none(self):
        svc = _make_service()
        svc._dynamodb_client.get_item.return_value = {}
        assert svc.get_eligibility("u1") is None


# ---------------------------------------------------------------------------
# 9.5 — Property 11: token lifecycle is single-use and expiry-bounded
# Feature: student-builder-membership, Property 11: Token lifecycle is single-use
# and expiry-bounded
#
# Validates: Requirements 4.1, 4.4, 4.5
# ---------------------------------------------------------------------------


@settings(max_examples=200, deadline=None)
@given(
    used=st.booleans(),
    offset_seconds=st.integers(min_value=-100000, max_value=100000),
    correct_token=st.booleans(),
)
def test_property_token_lifecycle_single_use_and_expiry_bounded(
    used, offset_seconds, correct_token
):
    """confirm() succeeds iff the token is unused AND unexpired AND hash-matches;
    otherwise it raises InvalidTokenError and writes no eligibility record. A
    success also consumes the token exactly once (conditional update)."""
    svc = _make_service()
    real_raw = "canonical-token"
    now = datetime.now(timezone.utc)
    expiry_epoch = int(now.timestamp()) + offset_seconds
    svc._dynamodb_client.get_item.return_value = {
        "Item": _token_item(_hash_token(real_raw), used=used, expiry_epoch=expiry_epoch)
    }
    submitted = real_raw if correct_token else "wrong-token"

    unexpired = expiry_epoch > int(now.timestamp())
    should_succeed = (not used) and unexpired and correct_token

    if should_succeed:
        result = svc.confirm("u1", submitted)
        assert result["eligible"] is True
        # Consumed exactly once, and eligibility written exactly once.
        assert svc._dynamodb_client.update_item.call_count == 1
        elig_writes = [
            c
            for c in svc._dynamodb_client.put_item.call_args_list
            if c.kwargs["Item"]["SK"] == {"S": mod.ELIGIBILITY_SK}
        ]
        assert len(elig_writes) == 1
    else:
        with pytest.raises(InvalidTokenError):
            svc.confirm("u1", submitted)
        # No eligibility record created or advanced.
        elig_writes = [
            c
            for c in svc._dynamodb_client.put_item.call_args_list
            if c.kwargs["Item"]["SK"] == {"S": mod.ELIGIBILITY_SK}
        ]
        assert elig_writes == []


# ---------------------------------------------------------------------------
# 9.6 — Property 12: eligibility is exactly the unexpired-record predicate
# Feature: student-builder-membership, Property 12: Eligibility is exactly the
# unexpired-record predicate
#
# Validates: Requirements 4.7, 4.8, 6.7
# ---------------------------------------------------------------------------


@settings(max_examples=200, deadline=None)
@given(
    present=st.booleans(),
    offset_seconds=st.integers(min_value=-1_000_000, max_value=1_000_000),
)
def test_property_eligibility_is_unexpired_record_predicate(present, offset_seconds):
    """get_eligibility returns the record iff a STUDENT_ELIGIBILITY item exists
    with expires_at strictly after now; absence or expires_at <= now => None."""
    svc = _make_service()
    now = datetime.now(timezone.utc)

    if not present:
        svc._dynamodb_client.get_item.return_value = {}
        assert svc.get_eligibility("u1") is None
        return

    expires_dt = now + timedelta(seconds=offset_seconds)
    expires_iso = expires_dt.isoformat()
    svc._dynamodb_client.get_item.return_value = {
        "Item": _eligibility_item(expires_iso)
    }

    result = svc.get_eligibility("u1")
    # Active iff strictly in the future. Re-evaluate "now" at assertion time via
    # the boundary used by the implementation; the offset keeps clear distance
    # from the boundary except at exactly 0, which is treated as expired.
    if expires_dt > datetime.now(timezone.utc):
        assert result is not None
        assert result["expires_at"] == expires_iso
    else:
        assert result is None


# ---------------------------------------------------------------------------
# 9.7 — Property 13: verification fails closed on validation-service problems
# Feature: student-builder-membership, Property 13: Verification fails closed on
# validation-service problems
#
# Validates: Requirements 3.3, 3.4, 3.6
# ---------------------------------------------------------------------------


# Problem modes that must all reject the submission without writing a token:
# - "non_academic": ApyHub reports the domain is not academic.
# - "apyhub_error": the ApyHub call errors / times out (Fail_Closed).
# - "missing_key":  the API key is missing/empty (Fail_Closed).
_PROBLEM_MODES = st.sampled_from(["non_academic", "apyhub_error", "missing_key"])


@settings(max_examples=150, deadline=None)
@given(
    mode=_PROBLEM_MODES,
    local=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
        min_size=1,
        max_size=12,
    ),
)
def test_property_verification_fails_closed_on_validation_problems(mode, local):
    """For any validation-service problem (non-academic / error / timeout /
    missing key), submit() rejects and writes NO verification token (and thus
    never advances toward eligibility)."""
    email = f"{local}@university.edu"

    if mode == "missing_key":
        # Drive the real ApyHubClient path with an empty API key.
        with patch("boto3.client"):
            svc = VerificationService(_make_settings())
        svc._dynamodb_client = MagicMock()
        ctx = patch.object(mod, "get_secret", return_value={"secret_key": ""})
        expected = ApyHubUnavailable
    else:
        svc = _make_service()
        if mode == "non_academic":
            svc._apyhub.is_academic_domain = MagicMock(return_value=False)
            expected = NotAcademicError
        else:  # apyhub_error (covers both errors and the 10s timeout path)
            svc._apyhub.is_academic_domain = MagicMock(
                side_effect=ApyHubUnavailable("timeout")
            )
            expected = ApyHubUnavailable
        ctx = patch.object(mod, "send_student_verification_email")

    with ctx:
        with pytest.raises(expected):
            svc.submit("u1", email)

    # Fail closed: the token SK is never written under any problem mode.
    token_writes = [
        c
        for c in svc._dynamodb_client.put_item.call_args_list
        if c.kwargs.get("Item", {}).get("SK") == {"S": mod.VERIFICATION_TOKEN_SK}
    ]
    assert token_writes == []


# ---------------------------------------------------------------------------
# Coverage extension: ApyHubClient._get_api_key (fail-closed branches)
# ---------------------------------------------------------------------------


class TestApyHubGetApiKey:
    def test_unset_secret_name_fails_closed(self):
        settings = _make_settings()
        settings.apyhub_secret_name = ""
        client = mod.ApyHubClient(settings)
        with patch.object(mod, "get_secret") as get_secret:
            with pytest.raises(ApyHubUnavailable):
                client._get_api_key()
        # Secret name unset: must fail closed before any Secrets Manager read.
        get_secret.assert_not_called()

    def test_get_secret_raises_fails_closed(self):
        client = mod.ApyHubClient(_make_settings())
        with patch.object(mod, "get_secret", side_effect=RuntimeError("secrets boom")):
            with pytest.raises(ApyHubUnavailable):
                client._get_api_key()

    def test_missing_secret_key_fails_closed(self):
        client = mod.ApyHubClient(_make_settings())
        # Dict present but no 'secret_key' entry.
        with patch.object(mod, "get_secret", return_value={"other": "x"}):
            with pytest.raises(ApyHubUnavailable):
                client._get_api_key()

    def test_empty_secret_key_fails_closed(self):
        client = mod.ApyHubClient(_make_settings())
        with patch.object(mod, "get_secret", return_value={"secret_key": ""}):
            with pytest.raises(ApyHubUnavailable):
                client._get_api_key()

    def test_none_secret_payload_fails_closed(self):
        client = mod.ApyHubClient(_make_settings())
        with patch.object(mod, "get_secret", return_value=None):
            with pytest.raises(ApyHubUnavailable):
                client._get_api_key()

    def test_valid_secret_returns_api_key(self):
        client = mod.ApyHubClient(_make_settings())
        with patch.object(mod, "get_secret", return_value={"secret_key": "k"}):
            assert client._get_api_key() == "k"


# ---------------------------------------------------------------------------
# Coverage extension: ApyHubClient.is_academic_domain real HTTP path
# ---------------------------------------------------------------------------


def _apyhub_client():
    """Build an ApyHubClient whose key resolution is stubbed to a valid value."""
    client = mod.ApyHubClient(_make_settings())
    client._get_api_key = MagicMock(return_value="k")
    return client


def _http_response(*, json_return=None, json_side_effect=None):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    if json_side_effect is not None:
        resp.json.side_effect = json_side_effect
    else:
        resp.json.return_value = json_return
    return resp


class TestApyHubIsAcademicDomainHttp:
    def test_data_true_returns_true(self):
        client = _apyhub_client()
        with patch.object(
            mod.httpx, "post", return_value=_http_response(json_return={"data": True})
        ) as post:
            assert client.is_academic_domain("a@uni.edu") is True
        post.assert_called_once()

    def test_posts_to_us_gateway_with_expected_request_shape(self):
        client = _apyhub_client()
        with patch.object(
            mod.httpx, "post", return_value=_http_response(json_return={"data": True})
        ) as post:
            client.is_academic_domain("a@uni.edu")
        args, kwargs = post.call_args
        assert args[0] == mod.APYHUB_ACADEMIC_EMAIL_URL
        assert mod.APYHUB_ACADEMIC_EMAIL_URL.startswith(
            "https://api.us.apyhub.com/apyhub/check-whether-an-email-belongs-to-an-academic"
        )
        assert kwargs["headers"] == {"apy-token": "k"}
        assert kwargs["json"] == {"email": "a@uni.edu"}
        assert kwargs["timeout"] == 10.0

    def test_data_false_returns_false(self):
        client = _apyhub_client()
        with patch.object(
            mod.httpx, "post", return_value=_http_response(json_return={"data": False})
        ):
            assert client.is_academic_domain("a@uni.edu") is False

    def test_academic_fallback_field_returns_true(self):
        client = _apyhub_client()
        # No 'data' key: the tolerant 'academic' fallback field is consulted.
        with patch.object(
            mod.httpx,
            "post",
            return_value=_http_response(json_return={"academic": True}),
        ):
            assert client.is_academic_domain("a@uni.edu") is True

    def test_http_error_fails_closed(self):
        client = _apyhub_client()
        with patch.object(
            mod.httpx, "post", side_effect=mod.httpx.ConnectError("down")
        ):
            with pytest.raises(ApyHubUnavailable):
                client.is_academic_domain("a@uni.edu")

    def test_timeout_fails_closed(self):
        client = _apyhub_client()
        with patch.object(
            mod.httpx, "post", side_effect=mod.httpx.TimeoutException("slow")
        ):
            with pytest.raises(ApyHubUnavailable):
                client.is_academic_domain("a@uni.edu")

    def test_unparseable_json_fails_closed(self):
        client = _apyhub_client()
        with patch.object(
            mod.httpx,
            "post",
            return_value=_http_response(json_side_effect=ValueError("bad json")),
        ):
            with pytest.raises(ApyHubUnavailable):
                client.is_academic_domain("a@uni.edu")

    def test_non_dict_payload_fails_closed(self):
        client = _apyhub_client()
        # A JSON list is a valid JSON value but an unexpected response shape.
        with patch.object(
            mod.httpx, "post", return_value=_http_response(json_return=[1, 2, 3])
        ):
            with pytest.raises(ApyHubUnavailable):
                client.is_academic_domain("a@uni.edu")


# ---------------------------------------------------------------------------
# Coverage extension: submit() put_item ClientError propagation
# ---------------------------------------------------------------------------


class TestSubmitPutItemError:
    def test_put_item_client_error_propagates(self):
        svc = _make_service()
        svc._dynamodb_client.put_item.side_effect = mod.ClientError(
            {
                "Error": {
                    "Code": "ProvisionedThroughputExceededException",
                    "Message": "x",
                }
            },
            "PutItem",
        )
        with patch.object(mod, "send_student_verification_email") as send:
            with pytest.raises(mod.ClientError):
                svc.submit("u1", "student@uni.edu")
        # The write failed before the email could ever be sent.
        send.assert_not_called()


# ---------------------------------------------------------------------------
# Coverage extension: confirm() DynamoDB error branches
# ---------------------------------------------------------------------------


class TestConfirmDynamoErrors:
    def test_get_item_client_error_propagates(self):
        svc = _make_service()
        svc._dynamodb_client.get_item.side_effect = mod.ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "x"}},
            "GetItem",
        )
        with pytest.raises(mod.ClientError):
            svc.confirm("u1", "whatever")
        svc._dynamodb_client.update_item.assert_not_called()
        svc._dynamodb_client.put_item.assert_not_called()

    def test_update_item_non_conditional_error_propagates(self):
        svc = _make_service()
        raw = "good-token"
        svc._dynamodb_client.get_item.return_value = {
            "Item": _token_item(_hash_token(raw))
        }
        svc._dynamodb_client.update_item.side_effect = mod.ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "x"}},
            "UpdateItem",
        )
        # A non-ConditionalCheckFailed error is NOT an InvalidTokenError; it
        # propagates as the underlying ClientError.
        with pytest.raises(mod.ClientError):
            svc.confirm("u1", raw)
        svc._dynamodb_client.put_item.assert_not_called()

    def test_eligibility_put_item_client_error_propagates(self):
        svc = _make_service()
        raw = "good-token"
        svc._dynamodb_client.get_item.return_value = {
            "Item": _token_item(_hash_token(raw))
        }
        svc._dynamodb_client.put_item.side_effect = mod.ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "x"}},
            "PutItem",
        )
        with pytest.raises(mod.ClientError):
            svc.confirm("u1", raw)
        # The token was consumed before the eligibility write failed.
        svc._dynamodb_client.update_item.assert_called_once()


# ---------------------------------------------------------------------------
# Coverage extension: get_eligibility() remaining branches
# ---------------------------------------------------------------------------


class TestGetEligibilityBranches:
    def test_get_item_client_error_propagates(self):
        svc = _make_service()
        svc._dynamodb_client.get_item.side_effect = mod.ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "x"}},
            "GetItem",
        )
        with pytest.raises(mod.ClientError):
            svc.get_eligibility("u1")

    def test_missing_expires_at_returns_none(self):
        svc = _make_service()
        item = _eligibility_item("placeholder")
        del item["expires_at"]
        svc._dynamodb_client.get_item.return_value = {"Item": item}
        assert svc.get_eligibility("u1") is None

    def test_empty_expires_at_returns_none(self):
        svc = _make_service()
        svc._dynamodb_client.get_item.return_value = {"Item": _eligibility_item("")}
        assert svc.get_eligibility("u1") is None

    def test_unparseable_expires_at_returns_none(self):
        svc = _make_service()
        svc._dynamodb_client.get_item.return_value = {
            "Item": _eligibility_item("not-a-date")
        }
        assert svc.get_eligibility("u1") is None

    def test_naive_future_timestamp_treated_as_active(self):
        svc = _make_service()
        # Naive (no tzinfo) future timestamp: implementation assumes UTC and
        # treats it as an active record.
        naive_future = (
            (datetime.now(timezone.utc) + timedelta(days=30))
            .replace(tzinfo=None)
            .isoformat()
        )
        assert "+" not in naive_future  # sanity: no offset in the string
        svc._dynamodb_client.get_item.return_value = {
            "Item": _eligibility_item(naive_future)
        }
        result = svc.get_eligibility("u1")
        assert result is not None
        assert result["expires_at"] == naive_future


# ---------------------------------------------------------------------------
# Coverage extension: _get_username() swallows read failures
# ---------------------------------------------------------------------------


class TestGetUsername:
    def test_client_error_returns_none(self):
        svc = _make_service()
        svc._dynamodb_client.get_item.side_effect = mod.ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "x"}},
            "GetItem",
        )
        # A profile read failure must never bubble up; callers fall back to a
        # generic greeting.
        assert svc._get_username("u1") is None

    def test_username_returned_when_present(self):
        svc = _make_service()
        svc._dynamodb_client.get_item.return_value = {
            "Item": {"username": {"S": "Ada"}}
        }
        assert svc._get_username("u1") == "Ada"
