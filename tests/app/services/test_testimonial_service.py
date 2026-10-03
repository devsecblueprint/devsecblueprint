"""Unit tests for app.services.testimonial_service.

Covers CRUD + query/scan paths and DynamoDB error handling. DynamoDB is
mocked via patching boto3.client (matching the pattern used elsewhere in the
suite); settings are patched so no real AWS config is needed.
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import testimonial_service as svc


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


@pytest.fixture
def mock_settings():
    with patch.object(svc, "get_settings") as get_settings:
        get_settings.return_value = MagicMock(testimonials_table="test-testimonials")
        yield get_settings


@pytest.fixture
def mock_dynamodb(mock_settings):
    client = MagicMock()
    with patch.object(svc.boto3, "client", return_value=client):
        yield client


class TestCreateTestimonial:
    def test_create_returns_record_and_calls_put(self, mock_dynamodb):
        result = svc.create_testimonial(
            "user-1", "Jane Doe", "https://linkedin.com/in/jane", "Great platform"
        )

        assert result["user_id"] == "user-1"
        assert result["display_name"] == "Jane Doe"
        assert result["linkedin_url"] == "https://linkedin.com/in/jane"
        assert result["quote"] == "Great platform"
        assert result["status"] == "pending"
        assert result["submitted_at"]  # timestamp set

        mock_dynamodb.put_item.assert_called_once()
        item = mock_dynamodb.put_item.call_args.kwargs["Item"]
        assert item["PK"]["S"] == "USER#user-1"
        assert item["SK"]["S"] == "TESTIMONIAL"
        assert item["status"]["S"] == "pending"

    def test_create_blank_linkedin_defaults_empty(self, mock_dynamodb):
        result = svc.create_testimonial("u", "Name", "", "quote")
        assert result["linkedin_url"] == ""

    def test_create_raises_on_client_error(self, mock_dynamodb):
        mock_dynamodb.put_item.side_effect = _client_error("ProvisionedThroughputExceededException")
        with pytest.raises(Exception, match="Failed to create testimonial"):
            svc.create_testimonial("u", "Name", "url", "quote")


class TestGetTestimonial:
    def test_get_returns_parsed_record(self, mock_dynamodb):
        mock_dynamodb.get_item.return_value = {
            "Item": {
                "PK": {"S": "USER#user-2"},
                "SK": {"S": "TESTIMONIAL"},
                "display_name": {"S": "Bob"},
                "linkedin_url": {"S": "https://x"},
                "quote": {"S": "Nice"},
                "status": {"S": "approved"},
                "submitted_at": {"S": "2026-01-01"},
                "updated_at": {"S": "2026-01-02"},
                "reviewed_at": {"S": "2026-01-03"},
                "reviewed_by": {"S": "admin"},
                "admin_note": {"S": "ok"},
            }
        }
        result = svc.get_testimonial("user-2")
        assert result is not None
        assert result["user_id"] == "user-2"
        assert result["display_name"] == "Bob"
        assert result["status"] == "approved"
        assert result["reviewed_by"] == "admin"

    def test_get_returns_none_when_missing(self, mock_dynamodb):
        mock_dynamodb.get_item.return_value = {}
        assert svc.get_testimonial("nobody") is None

    def test_get_raises_on_client_error(self, mock_dynamodb):
        mock_dynamodb.get_item.side_effect = _client_error("InternalServerError")
        with pytest.raises(Exception, match="Failed to get testimonial"):
            svc.get_testimonial("u")


class TestUpdateTestimonial:
    def test_update_returns_parsed_attributes(self, mock_dynamodb):
        mock_dynamodb.update_item.return_value = {
            "Attributes": {
                "PK": {"S": "USER#user-3"},
                "status": {"S": "approved"},
                "display_name": {"S": "Carol"},
            }
        }
        result = svc.update_testimonial("user-3", {"status": "approved"})
        assert result is not None
        assert result["user_id"] == "user-3"
        assert result["status"] == "approved"
        # updated_at is injected automatically
        call = mock_dynamodb.update_item.call_args.kwargs
        assert ":updated_at" in call["ExpressionAttributeValues"]

    def test_update_returns_none_when_record_absent(self, mock_dynamodb):
        mock_dynamodb.update_item.side_effect = _client_error("ConditionalCheckFailedException")
        assert svc.update_testimonial("ghost", {"status": "approved"}) is None

    def test_update_raises_on_other_client_error(self, mock_dynamodb):
        mock_dynamodb.update_item.side_effect = _client_error("ValidationException")
        with pytest.raises(Exception, match="Failed to update testimonial"):
            svc.update_testimonial("u", {"status": "x"})


class TestDeleteTestimonial:
    def test_delete_calls_delete_item(self, mock_dynamodb):
        svc.delete_testimonial("user-4")
        key = mock_dynamodb.delete_item.call_args.kwargs["Key"]
        assert key["PK"]["S"] == "USER#user-4"
        assert key["SK"]["S"] == "TESTIMONIAL"

    def test_delete_raises_on_client_error(self, mock_dynamodb):
        mock_dynamodb.delete_item.side_effect = _client_error("ResourceNotFoundException")
        with pytest.raises(Exception, match="Failed to delete testimonial"):
            svc.delete_testimonial("u")


class TestGetByStatus:
    def test_query_single_page(self, mock_dynamodb):
        mock_dynamodb.query.return_value = {
            "Items": [
                {"PK": {"S": "USER#a"}, "status": {"S": "pending"}},
                {"PK": {"S": "USER#b"}, "status": {"S": "pending"}},
            ]
        }
        result = svc.get_testimonials_by_status("pending")
        assert len(result) == 2
        assert {r["user_id"] for r in result} == {"a", "b"}

    def test_query_paginates(self, mock_dynamodb):
        mock_dynamodb.query.side_effect = [
            {"Items": [{"PK": {"S": "USER#a"}}], "LastEvaluatedKey": {"PK": {"S": "USER#a"}}},
            {"Items": [{"PK": {"S": "USER#b"}}]},
        ]
        result = svc.get_testimonials_by_status("pending")
        assert len(result) == 2
        assert mock_dynamodb.query.call_count == 2

    def test_query_raises_on_client_error(self, mock_dynamodb):
        mock_dynamodb.query.side_effect = _client_error("InternalServerError")
        with pytest.raises(Exception, match="Failed to query testimonials by status"):
            svc.get_testimonials_by_status("pending")


class TestGetAll:
    def test_scan_single_page(self, mock_dynamodb):
        mock_dynamodb.scan.return_value = {
            "Items": [{"PK": {"S": "USER#a"}}, {"PK": {"S": "USER#b"}}]
        }
        result = svc.get_all_testimonials()
        assert len(result) == 2

    def test_scan_paginates(self, mock_dynamodb):
        mock_dynamodb.scan.side_effect = [
            {"Items": [{"PK": {"S": "USER#a"}}], "LastEvaluatedKey": {"PK": {"S": "USER#a"}}},
            {"Items": [{"PK": {"S": "USER#b"}}]},
        ]
        result = svc.get_all_testimonials()
        assert len(result) == 2
        assert mock_dynamodb.scan.call_count == 2

    def test_scan_raises_on_client_error(self, mock_dynamodb):
        mock_dynamodb.scan.side_effect = _client_error("InternalServerError")
        with pytest.raises(Exception, match="Failed to scan testimonials"):
            svc.get_all_testimonials()


class TestParseItem:
    def test_parse_strips_user_prefix(self):
        parsed = svc._parse_item({"PK": {"S": "USER#xyz"}, "quote": {"S": "q"}})
        assert parsed["user_id"] == "xyz"
        assert parsed["quote"] == "q"

    def test_parse_handles_missing_fields(self):
        parsed = svc._parse_item({})
        assert parsed["user_id"] == ""
        assert parsed["display_name"] == ""
