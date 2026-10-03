"""Unit tests for app.services.certification.certificate_generator.

CertificateGenerator calls the Templated.io API (via requests), downloads the
rendered image, and caches it in S3. Tests patch the module's boto3.client
(reassigning svc._s3), the module-level requests, and get_secret. They cover
the generate/pdf/svg pipelines plus upload, cache, presign, and error paths.
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services.certification import certificate_generator as mod
from app.services.certification.certificate_generator import CertificateGenerator


def _client_error(code: str = "InternalServerError") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


@pytest.fixture
def service():
    s3 = MagicMock()
    settings = MagicMock(
        certificate_bucket="cert-bucket",
        templated_secret_name="templated-secret",
        templated_template_id="tmpl-123",
    )
    with patch.object(mod.boto3, "client", return_value=s3):
        svc = CertificateGenerator(settings)
    svc._s3 = s3
    return svc


_GEN_ARGS = dict(
    credential_id="DSB-DSEP-ABCD1234",
    full_name="Jane Doe",
    pathway_display_name="DevSecOps Engineering",
    pathway_description="A rigorous pathway.",
    issued_at="2026-08-13T00:00:00+00:00",
    expires_at="2027-08-13T00:00:00+00:00",
)


def _ok_response(json_body=None, content=b"img", status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.content = content
    resp.text = "body"
    if json_body is not None:
        resp.json.return_value = json_body
    return resp


# ---------------------------------------------------------------------------
# _get_api_key
# ---------------------------------------------------------------------------


class TestGetApiKey:
    def test_returns_key(self, service):
        with patch.object(mod, "get_secret", return_value={"secret_key": "abc"}):
            assert service._get_api_key() == "abc"

    def test_none_when_no_secret_name(self, service):
        service._secret_name = ""
        assert service._get_api_key() is None

    def test_none_on_exception(self, service):
        with patch.object(mod, "get_secret", side_effect=RuntimeError("boom")):
            assert service._get_api_key() is None


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------


class TestGenerate:
    def test_full_success_pipeline(self, service):
        with patch.object(mod, "get_secret", return_value={"secret_key": "abc"}), patch.object(
            mod.requests, "post", return_value=_ok_response({"render_url": "https://r/img.png"})
        ) as post, patch.object(
            mod.requests, "get", return_value=_ok_response(content=b"PNGDATA")
        ) as get:
            result = service.generate(**_GEN_ARGS)

        assert result == "certificates/DSB-DSEP-ABCD1234.png"
        # Templated API called with template id + layers
        body = post.call_args.kwargs["json"]
        assert body["template"] == "tmpl-123"
        assert body["layers"]["recipient-name"]["text"] == "Jane Doe"
        assert body["layers"]["meta-credential-id-value"]["text"] == "DSB-DSEP-ABCD1234"
        # Downloaded from render url
        get.assert_called_once()
        # Uploaded to S3
        put_kwargs = service._s3.put_object.call_args.kwargs
        assert put_kwargs["Bucket"] == "cert-bucket"
        assert put_kwargs["Key"] == "certificates/DSB-DSEP-ABCD1234.png"
        assert put_kwargs["Body"] == b"PNGDATA"
        assert put_kwargs["ContentType"] == "image/png"

    def test_none_when_no_api_key(self, service):
        with patch.object(service, "_get_api_key", return_value=None):
            assert service.generate(**_GEN_ARGS) is None

    def test_none_when_no_template_id(self, service):
        service._template_id = ""
        with patch.object(service, "_get_api_key", return_value="abc"):
            assert service.generate(**_GEN_ARGS) is None

    def test_none_when_render_fails(self, service):
        with patch.object(service, "_get_api_key", return_value="abc"), patch.object(
            service, "_call_templated_api", return_value=None
        ):
            assert service.generate(**_GEN_ARGS) is None

    def test_none_when_download_fails(self, service):
        with patch.object(service, "_get_api_key", return_value="abc"), patch.object(
            service, "_call_templated_api", return_value="https://r/img.png"
        ), patch.object(service, "_download_render", return_value=None):
            assert service.generate(**_GEN_ARGS) is None

    def test_none_when_upload_fails(self, service):
        with patch.object(service, "_get_api_key", return_value="abc"), patch.object(
            service, "_call_templated_api", return_value="https://r/img.png"
        ), patch.object(service, "_download_render", return_value=b"x"), patch.object(
            service, "_upload_to_s3", return_value=False
        ):
            assert service.generate(**_GEN_ARGS) is None

    def test_none_on_unexpected_exception(self, service):
        with patch.object(service, "_get_api_key", return_value="abc"), patch.object(
            service, "_call_templated_api", side_effect=RuntimeError("boom")
        ):
            assert service.generate(**_GEN_ARGS) is None


# ---------------------------------------------------------------------------
# generate_pdf_bytes
# ---------------------------------------------------------------------------


class TestGeneratePdfBytes:
    def test_returns_cached(self, service):
        with patch.object(service, "_get_from_s3", return_value=b"CACHED"):
            assert service.generate_pdf_bytes(**_GEN_ARGS) == b"CACHED"

    def test_generates_when_not_cached(self, service):
        with patch.object(service, "_get_from_s3", return_value=None), patch.object(
            service, "_get_api_key", return_value="abc"
        ), patch.object(
            service, "_call_templated_api", return_value="https://r/img.png"
        ), patch.object(service, "_download_render", return_value=b"FRESH"), patch.object(
            service, "_upload_to_s3", return_value=True
        ) as upload:
            result = service.generate_pdf_bytes(**_GEN_ARGS)
        assert result == b"FRESH"
        upload.assert_called_once()

    def test_none_when_no_api_key(self, service):
        with patch.object(service, "_get_from_s3", return_value=None), patch.object(
            service, "_get_api_key", return_value=None
        ):
            assert service.generate_pdf_bytes(**_GEN_ARGS) is None

    def test_none_when_render_fails(self, service):
        with patch.object(service, "_get_from_s3", return_value=None), patch.object(
            service, "_get_api_key", return_value="abc"
        ), patch.object(service, "_call_templated_api", return_value=None):
            assert service.generate_pdf_bytes(**_GEN_ARGS) is None

    def test_none_when_download_fails(self, service):
        with patch.object(service, "_get_from_s3", return_value=None), patch.object(
            service, "_get_api_key", return_value="abc"
        ), patch.object(
            service, "_call_templated_api", return_value="https://r/img.png"
        ), patch.object(service, "_download_render", return_value=None):
            assert service.generate_pdf_bytes(**_GEN_ARGS) is None

    def test_none_on_unexpected_exception(self, service):
        with patch.object(service, "_get_from_s3", return_value=None), patch.object(
            service, "_get_api_key", return_value="abc"
        ), patch.object(service, "_call_templated_api", side_effect=RuntimeError("boom")):
            assert service.generate_pdf_bytes(**_GEN_ARGS) is None


# ---------------------------------------------------------------------------
# generate_svg_content
# ---------------------------------------------------------------------------


class TestGenerateSvgContent:
    def test_returns_cached_presigned(self, service):
        with patch.object(service, "_get_presigned_url", return_value="https://signed"):
            assert service.generate_svg_content(**_GEN_ARGS) == "https://signed"

    def test_generates_then_presigns(self, service):
        presign = MagicMock(side_effect=[None, "https://signed-after"])
        with patch.object(service, "_get_presigned_url", presign), patch.object(
            service, "generate", return_value="certificates/x.png"
        ):
            assert service.generate_svg_content(**_GEN_ARGS) == "https://signed-after"
        assert presign.call_count == 2

    def test_none_when_generate_fails(self, service):
        with patch.object(service, "_get_presigned_url", return_value=None), patch.object(
            service, "generate", return_value=None
        ):
            assert service.generate_svg_content(**_GEN_ARGS) is None


# ---------------------------------------------------------------------------
# _call_templated_api
# ---------------------------------------------------------------------------


class TestCallTemplatedApi:
    def test_success_render_url(self, service):
        with patch.object(
            mod.requests, "post", return_value=_ok_response({"render_url": "https://r/img"})
        ):
            assert service._call_templated_api(api_key="abc", **_GEN_ARGS) == "https://r/img"

    def test_success_url_fallback(self, service):
        with patch.object(mod.requests, "post", return_value=_ok_response({"url": "https://u"})):
            assert service._call_templated_api(api_key="abc", **_GEN_ARGS) == "https://u"

    def test_non_200_returns_none(self, service):
        with patch.object(mod.requests, "post", return_value=_ok_response({}, status=500)):
            assert service._call_templated_api(api_key="abc", **_GEN_ARGS) is None

    def test_missing_render_url_returns_none(self, service):
        with patch.object(mod.requests, "post", return_value=_ok_response({"other": 1})):
            assert service._call_templated_api(api_key="abc", **_GEN_ARGS) is None

    def test_request_exception_returns_none(self, service):
        with patch.object(mod.requests, "post", side_effect=mod.requests.RequestException("x")):
            assert service._call_templated_api(api_key="abc", **_GEN_ARGS) is None


# ---------------------------------------------------------------------------
# _download_render
# ---------------------------------------------------------------------------


class TestDownloadRender:
    def test_success(self, service):
        with patch.object(mod.requests, "get", return_value=_ok_response(content=b"DATA")):
            assert service._download_render("https://r/img") == b"DATA"

    def test_non_200_returns_none(self, service):
        with patch.object(mod.requests, "get", return_value=_ok_response(status=404)):
            assert service._download_render("https://r/img") is None

    def test_request_exception_returns_none(self, service):
        with patch.object(mod.requests, "get", side_effect=mod.requests.RequestException("x")):
            assert service._download_render("https://r/img") is None


# ---------------------------------------------------------------------------
# _upload_to_s3
# ---------------------------------------------------------------------------


class TestUploadToS3:
    def test_success(self, service):
        assert service._upload_to_s3("certificates/x.png", b"data") is True
        service._s3.put_object.assert_called_once()

    def test_no_bucket_returns_false(self, service):
        service._bucket = ""
        assert service._upload_to_s3("certificates/x.png", b"data") is False
        service._s3.put_object.assert_not_called()

    def test_client_error_returns_false(self, service):
        service._s3.put_object.side_effect = _client_error()
        assert service._upload_to_s3("certificates/x.png", b"data") is False


# ---------------------------------------------------------------------------
# _get_from_s3
# ---------------------------------------------------------------------------


class TestGetFromS3:
    def test_success(self, service):
        body = MagicMock()
        body.read.return_value = b"CACHED"
        service._s3.get_object.return_value = {"Body": body}
        assert service._get_from_s3("certificates/x.png") == b"CACHED"

    def test_no_bucket_returns_none(self, service):
        service._bucket = ""
        assert service._get_from_s3("certificates/x.png") is None

    def test_nosuchkey_returns_none(self, service):
        service._s3.get_object.side_effect = _client_error("NoSuchKey")
        assert service._get_from_s3("certificates/x.png") is None

    def test_404_returns_none(self, service):
        service._s3.get_object.side_effect = _client_error("404")
        assert service._get_from_s3("certificates/x.png") is None

    def test_other_client_error_returns_none(self, service):
        service._s3.get_object.side_effect = _client_error("AccessDenied")
        assert service._get_from_s3("certificates/x.png") is None


# ---------------------------------------------------------------------------
# _get_presigned_url
# ---------------------------------------------------------------------------


class TestGetPresignedUrl:
    def test_success(self, service):
        service._s3.generate_presigned_url.return_value = "https://signed"
        assert service._get_presigned_url("certificates/x.png") == "https://signed"
        service._s3.head_object.assert_called_once()

    def test_no_bucket_returns_none(self, service):
        service._bucket = ""
        assert service._get_presigned_url("certificates/x.png") is None

    def test_missing_object_returns_none(self, service):
        service._s3.head_object.side_effect = _client_error("404")
        assert service._get_presigned_url("certificates/x.png") is None


# ---------------------------------------------------------------------------
# _format_date
# ---------------------------------------------------------------------------


class TestFormatDate:
    def test_formats_iso(self):
        assert CertificateGenerator._format_date("2026-08-13T00:00:00+00:00") == "August 13, 2026"

    def test_invalid_returns_input(self):
        assert CertificateGenerator._format_date("not-a-date") == "not-a-date"
