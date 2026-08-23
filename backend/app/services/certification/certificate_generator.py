"""Certificate Generator for the DSB Certification & Credentialing Program.

Uses the Templated.io API to generate certificates from a pre-designed template.
Generated certificates are cached in S3 to avoid repeated API calls (50/month limit).

Pipeline:
1. Call Templated.io API with credential data (layers)
2. Templated returns a render URL (image/PDF)
3. Download the rendered certificate
4. Upload to S3 for caching
5. Return the S3 key

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

import logging
from datetime import datetime

import boto3
import requests
from botocore.exceptions import ClientError

from app.config import Settings
from app.services.secrets import get_secret

logger = logging.getLogger(__name__)


class CertificateGenerator:
    """Generates certificates via the Templated.io API with S3 caching.

    Calls Templated.io to render the certificate with credential-specific
    data, downloads the result, and caches it in S3. Subsequent requests
    serve from the S3 cache without calling the API again.
    """

    def __init__(self, settings: Settings) -> None:
        self._bucket = settings.certificate_bucket
        self._secret_name = settings.templated_secret_name
        self._template_id = settings.templated_template_id
        self._s3 = boto3.client("s3")

    def _get_api_key(self) -> str | None:
        """Retrieve the Templated.io API key from Secrets Manager.

        Returns:
            The API key string, or None if not configured or retrieval fails.
        """
        if not self._secret_name:
            return None
        try:
            secret_data = get_secret(self._secret_name)
            return secret_data.get("secret_key")
        except Exception:
            logger.error(
                "Failed to retrieve Templated.io API key from secret '%s'",
                self._secret_name,
                exc_info=True,
            )
            return None

    def generate(
        self,
        credential_id: str,
        full_name: str,
        pathway_display_name: str,
        pathway_description: str,
        issued_at: str,
        expires_at: str,
    ) -> str | None:
        """Generate a certificate and cache it in S3.

        Calls the Templated.io API to render the certificate, downloads
        the result, and uploads to S3.

        Args:
            credential_id: The unique credential identifier.
            full_name: The credential holder's full name.
            pathway_display_name: The pathway display name.
            pathway_description: Pathway description text for the certificate lead-in.
            issued_at: ISO 8601 timestamp of issuance.
            expires_at: ISO 8601 timestamp of expiration.

        Returns:
            The S3 key of the cached certificate on success, None on failure.
        """
        api_key = self._get_api_key()
        if not api_key or not self._template_id:
            logger.error("Templated.io API key or template ID not configured")
            return None

        try:
            # Step 1: Call Templated.io API
            render_url = self._call_templated_api(
                api_key=api_key,
                credential_id=credential_id,
                full_name=full_name,
                pathway_display_name=pathway_display_name,
                pathway_description=pathway_description,
                issued_at=issued_at,
                expires_at=expires_at,
            )
            if render_url is None:
                return None

            # Step 2: Download the rendered certificate
            cert_bytes = self._download_render(render_url)
            if cert_bytes is None:
                return None

            # Step 3: Upload to S3
            s3_key = f"certificates/{credential_id}.png"
            if not self._upload_to_s3(s3_key, cert_bytes):
                return None

            logger.info(
                "Generated certificate for credential %s via Templated.io, cached at s3://%s/%s",
                credential_id,
                self._bucket,
                s3_key,
            )
            return s3_key

        except Exception:
            logger.error(
                "Unexpected error generating certificate for credential %s",
                credential_id,
                exc_info=True,
            )
            return None

    def generate_pdf_bytes(
        self,
        credential_id: str,
        full_name: str,
        pathway_display_name: str,
        pathway_description: str,
        issued_at: str,
        expires_at: str,
    ) -> bytes | None:
        """Generate certificate and return bytes directly (for download endpoint).

        First checks S3 cache. If not cached, generates via Templated.io,
        caches, then returns the bytes.

        Returns:
            Certificate image bytes on success, None on failure.
        """
        # Check S3 cache first
        s3_key = f"certificates/{credential_id}.png"
        cached = self._get_from_s3(s3_key)
        if cached is not None:
            return cached

        # Not cached — generate and cache
        api_key = self._get_api_key()
        if not api_key or not self._template_id:
            logger.error("Templated.io API key or template ID not configured")
            return None

        try:
            render_url = self._call_templated_api(
                api_key=api_key,
                credential_id=credential_id,
                full_name=full_name,
                pathway_display_name=pathway_display_name,
                pathway_description=pathway_description,
                issued_at=issued_at,
                expires_at=expires_at,
            )
            if render_url is None:
                return None

            cert_bytes = self._download_render(render_url)
            if cert_bytes is None:
                return None

            # Cache to S3 (fire-and-forget, don't fail if S3 upload fails)
            self._upload_to_s3(s3_key, cert_bytes)

            return cert_bytes

        except Exception:
            logger.error(
                "Unexpected error generating certificate for credential %s",
                credential_id,
                exc_info=True,
            )
            return None

    def generate_svg_content(
        self,
        credential_id: str,
        full_name: str,
        pathway_display_name: str,
        pathway_description: str,
        issued_at: str,
        expires_at: str,
    ) -> str | None:
        """Generate certificate preview URL for rendering in the browser.

        Returns the Templated.io render URL (or cached S3 presigned URL)
        that can be displayed as an image.

        Note: Returns a URL string, not SVG content. The frontend renders
        it as an <img src>.
        """
        # Check S3 cache first
        s3_key = f"certificates/{credential_id}.png"
        presigned_url = self._get_presigned_url(s3_key)
        if presigned_url is not None:
            return presigned_url

        # Not cached — generate, cache, return presigned URL
        s3_result = self.generate(
            credential_id=credential_id,
            full_name=full_name,
            pathway_display_name=pathway_display_name,
            pathway_description=pathway_description,
            issued_at=issued_at,
            expires_at=expires_at,
        )
        if s3_result is None:
            return None

        return self._get_presigned_url(s3_key)

    def _call_templated_api(
        self,
        api_key: str,
        credential_id: str,
        full_name: str,
        pathway_display_name: str,
        pathway_description: str,
        issued_at: str,
        expires_at: str,
    ) -> str | None:
        """Call the Templated.io API to render the certificate.

        Returns:
            The render URL on success, None on failure.
        """
        url = "https://api.templated.io/v1/render"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        # Format dates for display
        formatted_issued = self._format_date(issued_at)
        formatted_expires = self._format_date(expires_at)

        data = {
            "template": self._template_id,
            "layers": {
                "recipient-name": {
                    "text": full_name,
                },
                "course-title": {
                    "text": pathway_display_name,
                },
                "lead-in-text-2": {
                    "text": pathway_description,
                },
                "meta-issue-date-value": {
                    "text": formatted_issued,
                },
                "meta-expiration-date-value": {
                    "text": formatted_expires,
                },
                "meta-credential-id-value": {
                    "text": credential_id,
                },
            },
        }

        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)

            if response.status_code != 200:
                logger.error(
                    "Templated.io API returned status %d for credential %s: %s",
                    response.status_code,
                    credential_id,
                    response.text,
                )
                return None

            result = response.json()
            render_url = result.get("render_url") or result.get("url")
            if not render_url:
                logger.error(
                    "Templated.io response missing render URL for credential %s: %s",
                    credential_id,
                    result,
                )
                return None

            return render_url

        except requests.RequestException as e:
            logger.error(
                "Templated.io API request failed for credential %s: %s",
                credential_id,
                e,
            )
            return None

    def _download_render(self, render_url: str) -> bytes | None:
        """Download the rendered certificate from the Templated.io URL.

        Returns:
            The certificate image bytes, or None on failure.
        """
        try:
            response = requests.get(render_url, timeout=30)
            if response.status_code != 200:
                logger.error(
                    "Failed to download certificate render from %s: status %d",
                    render_url,
                    response.status_code,
                )
                return None
            return response.content
        except requests.RequestException as e:
            logger.error("Failed to download certificate render: %s", e)
            return None

    def _upload_to_s3(self, s3_key: str, cert_bytes: bytes) -> bool:
        """Upload certificate bytes to S3.

        Returns:
            True on success, False on failure.
        """
        if not self._bucket:
            logger.warning("Certificate bucket not configured, skipping S3 upload")
            return False

        try:
            self._s3.put_object(
                Bucket=self._bucket,
                Key=s3_key,
                Body=cert_bytes,
                ContentType="image/png",
            )
            return True
        except ClientError:
            logger.error(
                "Failed to upload certificate to s3://%s/%s",
                self._bucket,
                s3_key,
                exc_info=True,
            )
            return False

    def _get_from_s3(self, s3_key: str) -> bytes | None:
        """Get cached certificate from S3.

        Returns:
            The certificate bytes if cached, None if not found.
        """
        if not self._bucket:
            return None

        try:
            response = self._s3.get_object(Bucket=self._bucket, Key=s3_key)
            return response["Body"].read()
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("NoSuchKey", "404"):
                return None
            logger.error("Error reading certificate from S3: %s", e, exc_info=True)
            return None

    def _get_presigned_url(self, s3_key: str) -> str | None:
        """Generate a presigned URL for a cached certificate in S3.

        Returns:
            Presigned URL string, or None if the object doesn't exist.
        """
        if not self._bucket:
            return None

        try:
            # Check if object exists first
            self._s3.head_object(Bucket=self._bucket, Key=s3_key)
            # Generate presigned URL
            return self._s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": s3_key},
                ExpiresIn=3600,
            )
        except ClientError:
            return None

    @staticmethod
    def _format_date(iso_timestamp: str) -> str:
        """Format an ISO 8601 timestamp to a human-friendly format.

        Returns a string like 'August 13, 2026'.
        """
        try:
            dt = datetime.fromisoformat(iso_timestamp)
            return dt.strftime("%B %d, %Y")
        except (ValueError, TypeError):
            return iso_timestamp
