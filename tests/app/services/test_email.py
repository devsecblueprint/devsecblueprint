"""Unit tests for app.services.email.

The low-level _send_email (SES) is tested directly with a mocked boto3 SES
client. The higher-level send_* helpers are tested with _send_email patched,
asserting they render their template and dispatch (and honor empty-email
guards and CC/BCC/reply-to behavior).
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import email as mod


@pytest.fixture
def mock_settings():
    with patch.object(mod, "get_settings") as get_settings:
        get_settings.return_value = MagicMock(
            ses_sender_email="noreply@devsecblueprint.com",
            ses_region="us-east-2",
            testimonial_notify_email="admin@dsb.com",
            contact_notify_email="support@dsb.com",
            certificate_bucket="cert-bucket",
        )
        yield get_settings


class TestSendEmail:
    def test_success_builds_destination_and_sends(self, mock_settings):
        ses = MagicMock()
        with patch.object(mod.boto3, "client", return_value=ses):
            ok = mod._send_email("to@x.com", "Subj", "<p>hi</p>")
        assert ok is True
        kwargs = ses.send_email.call_args.kwargs
        assert kwargs["Destination"]["ToAddresses"] == ["to@x.com"]
        assert "The DevSec Blueprint <noreply@devsecblueprint.com>" == kwargs["Source"]

    def test_includes_cc_bcc_reply_to(self, mock_settings):
        ses = MagicMock()
        with patch.object(mod.boto3, "client", return_value=ses):
            mod._send_email(
                "to@x.com",
                "Subj",
                "<p>hi</p>",
                sender_email="s@x.com",
                ses_region="us-east-1",
                cc=["cc@x.com"],
                bcc=["bcc@x.com"],
                reply_to=["reply@x.com"],
            )
        kwargs = ses.send_email.call_args.kwargs
        assert kwargs["Destination"]["CcAddresses"] == ["cc@x.com"]
        assert kwargs["Destination"]["BccAddresses"] == ["bcc@x.com"]
        assert kwargs["ReplyToAddresses"] == ["reply@x.com"]

    def test_client_error_returns_false(self, mock_settings):
        ses = MagicMock()
        ses.send_email.side_effect = ClientError(
            {"Error": {"Code": "MessageRejected", "Message": "bad"}}, "SendEmail"
        )
        with patch.object(mod.boto3, "client", return_value=ses):
            assert mod._send_email("to@x.com", "s", "b") is False

    def test_unexpected_error_returns_false(self, mock_settings):
        with patch.object(mod.boto3, "client", side_effect=RuntimeError("boom")):
            assert mod._send_email("to@x.com", "s", "b") is False


class TestNotificationHelpers:
    """Each helper should render its template and dispatch via _send_email."""

    def test_capstone_notification(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            ok = mod.send_capstone_notification("jane", "https://repo", "cap-1", "now")
        assert ok is True
        args = send.call_args.args
        assert args[0] == "admin@dsb.com"
        assert args[1] == "New Capstone Submission"

    def test_testimonial_notification(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            ok = mod.send_testimonial_notification("Jane", "https://li", "great")
        assert ok is True
        assert send.call_args.args[1] == "New Testimonial Submission"

    def test_review_notification_requires_email(self, mock_settings):
        assert (
            mod.send_review_notification_to_learner("", "u", "devsecops-capstone")
            is False
        )

    def test_review_notification_renders_feedback_markdown(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            ok = mod.send_review_notification_to_learner(
                "u@x.com", "user", "devsecops-capstone", feedback="**bold**"
            )
        assert ok is True
        assert send.call_args.args[0] == "u@x.com"

    def test_welcome_email_requires_email(self, mock_settings):
        assert mod.send_welcome_email("user", "") is False

    def test_welcome_email_sends(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            assert mod.send_welcome_email("user", "u@x.com") is True
        assert "Welcome" in send.call_args.args[1]

    def test_subscription_expired_requires_email(self, mock_settings):
        assert mod.send_subscription_expired_email("u", "", "BUILDER") is False

    def test_subscription_expired_sends(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            assert (
                mod.send_subscription_expired_email("u", "u@x.com", "BUILDER") is True
            )
        assert send.called

    def test_payment_failed_ccs_support_and_sets_reply_to(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            ok = mod.send_payment_failed_email("u", "u@x.com", "BUILDER")
        assert ok is True
        kwargs = send.call_args.kwargs
        assert kwargs["cc"] == ["support@dsb.com"]
        assert kwargs["reply_to"] == ["support@dsb.com"]

    def test_payment_failed_requires_email(self, mock_settings):
        assert mod.send_payment_failed_email("u", "", "BUILDER") is False

    def test_subscription_welcome_builder_ccs_community(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            ok = mod.send_subscription_welcome_email("u", "u@x.com", "BUILDER")
        assert ok is True
        assert send.call_args.kwargs["cc"] == [mod._COMMUNITY_EMAIL]

    def test_subscription_welcome_non_builder_no_cc(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            mod.send_subscription_welcome_email("u", "u@x.com", "EXPLORER")
        assert send.call_args.kwargs["cc"] is None

    def test_contact_notification_uses_inquiry_label(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            ok = mod.send_contact_notification(
                "Jane", "j@x.com", "Acme", "partnerships", "Hi", "Body"
            )
        assert ok is True
        assert "Partnerships" in send.call_args.args[1]

    def test_contact_notification_unknown_inquiry_falls_back(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            mod.send_contact_notification("Jane", "j@x.com", "", "weird", "Hi", "Body")
        assert "weird" in send.call_args.args[1]


class TestCertificationHelpers:
    def test_submission_received_requires_email(self, mock_settings):
        assert mod.send_submission_received_notification("", "u", "DevSecOps") is False

    def test_submission_received_sends(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            assert (
                mod.send_submission_received_notification("u@x.com", "u", "DevSecOps")
                is True
            )
        assert send.called

    def test_new_submission_admin_requires_reviewers(self, mock_settings):
        assert (
            mod.send_new_submission_admin_notification([], "cand", "DevSecOps") is False
        )

    def test_new_submission_admin_sends_to_each_reviewer(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            ok = mod.send_new_submission_admin_notification(
                ["r1@x.com", "r2@x.com"], "cand", "DevSecOps"
            )
        assert ok is True
        assert send.call_count == 2

    def test_new_submission_admin_partial_failure(self, mock_settings):
        with patch.object(mod, "_send_email", side_effect=[True, False]):
            ok = mod.send_new_submission_admin_notification(
                ["r1@x.com", "r2@x.com"], "cand", "DevSecOps"
            )
        assert ok is False

    def test_review_outcome_sends(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            ok = mod.send_review_outcome_notification(
                "u@x.com", "u", "DevSecOps", "PASSED", "nice work"
            )
        assert ok is True
        assert send.called

    def test_review_outcome_requires_email(self, mock_settings):
        assert (
            mod.send_review_outcome_notification("", "u", "p", "PASSED", "f") is False
        )

    def test_credential_issued_with_certificate_presigns_url(self, mock_settings):
        s3 = MagicMock()
        s3.generate_presigned_url.return_value = "https://signed"
        with (
            patch.object(mod.boto3, "client", return_value=s3),
            patch.object(mod, "_send_email", return_value=True) as send,
        ):
            ok = mod.send_credential_issued_notification(
                "u@x.com", "u", "DevSecOps", "cred-1"
            )
        assert ok is True
        # BCC community on issuance
        assert send.call_args.kwargs["bcc"] == ["community@devsecblueprint.com"]

    def test_credential_issued_missing_certificate_skips_url(self, mock_settings):
        s3 = MagicMock()
        s3.head_object.side_effect = Exception("not found")
        with (
            patch.object(mod.boto3, "client", return_value=s3),
            patch.object(mod, "_send_email", return_value=True) as send,
        ):
            ok = mod.send_credential_issued_notification(
                "u@x.com", "u", "DevSecOps", "cred-1"
            )
        assert ok is True
        assert send.called

    def test_credential_issued_requires_email(self, mock_settings):
        assert mod.send_credential_issued_notification("", "u", "p", "c") is False

    def test_credential_renewal_sends(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            ok = mod.send_credential_renewal_notification(
                "u@x.com", "u", "DevSecOps", "cred-1", "2026-12-31"
            )
        assert ok is True
        assert send.called

    def test_credential_expired_sends(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            ok = mod.send_credential_expired_notification(
                "u@x.com", "u", "DevSecOps", "cred-1"
            )
        assert ok is True

    def test_credential_revoked_sends(self, mock_settings):
        with patch.object(mod, "_send_email", return_value=True) as send:
            ok = mod.send_credential_revoked_notification(
                "u@x.com", "u", "DevSecOps", "cred-1", "policy violation"
            )
        assert ok is True

    def test_credential_renewal_requires_email(self, mock_settings):
        assert mod.send_credential_renewal_notification("", "u", "p", "c", "d") is False
