"""Certificate Generator for the DSB Certification & Credentialing Program.

Generates PDF certificates from an SVG template on the local filesystem. The pipeline:
1. Load SVG template from the local filesystem
2. Substitute dynamic placeholders
3. Validate all placeholders were replaced
4. Convert SVG to PDF via cairosvg
5. Upload PDF to S3
6. Return the S3 key for storage on the Credential record

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

import logging
from datetime import datetime
from pathlib import Path

import boto3
import cairosvg
from botocore.exceptions import ClientError

from app.config import Settings

logger = logging.getLogger(__name__)

_TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "certificate_template.svg"


class CertificateGenerator:
    """Generates PDF certificates from an SVG template.

    Loads an SVG template from the local filesystem, substitutes dynamic
    placeholder fields with credential-specific data, converts to PDF, and
    uploads the result to S3.
    """

    def __init__(self, settings: Settings) -> None:
        self._bucket = settings.certificate_bucket
        self._s3 = boto3.client("s3")

    def generate(
        self,
        credential_id: str,
        full_name: str,
        pathway_display_name: str,
        pathway_description: str,
        issued_at: str,
        expires_at: str,
    ) -> str | None:
        """Generate a certificate PDF and upload to S3.

        Loads the SVG template, substitutes all dynamic placeholders,
        validates no placeholders remain, converts to PDF, and uploads
        to S3.

        Args:
            credential_id: The unique credential identifier (e.g., DSB-DSEP-8F4C92A1).
            full_name: The credential holder's full name.
            pathway_display_name: The pathway display name (e.g., "DevSecOps Engineering").
            pathway_description: A brief pathway description or subtitle.
            issued_at: ISO 8601 timestamp of issuance.
            expires_at: ISO 8601 timestamp of expiration.

        Returns:
            The S3 key of the uploaded PDF on success, None on failure.
            Failures are logged but do not raise — the credential remains
            valid even if certificate generation fails.
        """
        try:
            # Step 1: Load SVG template from the local filesystem
            svg_content = self._load_template()
            if svg_content is None:
                return None

            # Step 2: Substitute dynamic placeholders
            svg_content = self._substitute_placeholders(
                svg_content,
                credential_id=credential_id,
                full_name=full_name,
                pathway_display_name=pathway_display_name,
                pathway_description=pathway_description,
                issued_at=issued_at,
                expires_at=expires_at,
            )

            # Step 3: Validate all placeholders were replaced
            if not self._validate_no_remaining_placeholders(svg_content):
                logger.error(
                    "Certificate template still contains unreplaced placeholders "
                    "for credential %s",
                    credential_id,
                )
                return None

            # Step 4: Convert SVG to PDF
            pdf_bytes = self._convert_svg_to_pdf(svg_content)
            if pdf_bytes is None:
                return None

            # Step 5: Upload PDF to S3
            s3_key = f"certificates/{credential_id}.pdf"
            if not self._upload_pdf(s3_key, pdf_bytes):
                return None

            # Step 6: Return the S3 key
            logger.info(
                "Generated certificate for credential %s at s3://%s/%s",
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

    def _load_template(self) -> str | None:
        """Load the SVG template from the local filesystem.

        Returns:
            The SVG content as a string, or None on failure.
        """
        try:
            return _TEMPLATE_PATH.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError):
            logger.error(
                "Failed to load SVG template from %s",
                _TEMPLATE_PATH,
                exc_info=True,
            )
            return None

    def _substitute_placeholders(
        self,
        svg_content: str,
        credential_id: str,
        full_name: str,
        pathway_display_name: str,
        pathway_description: str,
        issued_at: str,
        expires_at: str,
    ) -> str:
        """Substitute all dynamic placeholders in the SVG content.

        The template contains TWO instances of [Month DD, YYYY]:
        - First occurrence: issue date
        - Second occurrence: expiration date
        These are handled by replacing one at a time using str.replace with count=1.

        Args:
            svg_content: The raw SVG template string.
            credential_id: The unique credential ID.
            full_name: The recipient's full name.
            pathway_display_name: The certification title.
            pathway_description: The pathway description paragraph.
            issued_at: ISO 8601 timestamp for the issue date.
            expires_at: ISO 8601 timestamp for the expiration date.

        Returns:
            The SVG string with all placeholders substituted.
        """
        # Format dates from ISO 8601 to "Month DD, YYYY"
        formatted_issued = self._format_date(issued_at)
        formatted_expires = self._format_date(expires_at)

        # Build the validation URL
        validation_url = f"https://devsecblueprint.com/verify/{credential_id}"

        # Replace single-instance placeholders
        svg_content = svg_content.replace("[Recipient Name]", full_name)
        svg_content = svg_content.replace("[CERTIFICATION TITLE]", pathway_display_name)
        svg_content = svg_content.replace("Your paragraph text", pathway_description)
        svg_content = svg_content.replace("[Credential ID]", credential_id)
        svg_content = svg_content.replace("[Validation URL]", validation_url)

        # Replace the TWO date placeholders one at a time:
        # First occurrence → issue date
        svg_content = svg_content.replace("[Month DD, YYYY]", formatted_issued, 1)
        # Second occurrence → expiration date
        svg_content = svg_content.replace("[Month DD, YYYY]", formatted_expires, 1)

        return svg_content

    def _validate_no_remaining_placeholders(self, svg_content: str) -> bool:
        """Validate that no placeholder brackets remain in the SVG content.

        Checks for common placeholder patterns that should have been
        substituted.

        Args:
            svg_content: The SVG content after substitution.

        Returns:
            True if no placeholders remain, False otherwise.
        """
        known_placeholders = [
            "[Recipient Name]",
            "[CERTIFICATION TITLE]",
            "Your paragraph text",
            "[Month DD, YYYY]",
            "[Credential ID]",
            "[Validation URL]",
        ]
        for placeholder in known_placeholders:
            if placeholder in svg_content:
                logger.warning("Unreplaced placeholder found: %s", placeholder)
                return False
        return True

    def _convert_svg_to_pdf(self, svg_content: str) -> bytes | None:
        """Convert SVG content to PDF bytes using cairosvg.

        Args:
            svg_content: The SVG content string.

        Returns:
            The PDF as bytes, or None on failure.
        """
        try:
            pdf_bytes = cairosvg.svg2pdf(bytestring=svg_content.encode("utf-8"))
            return pdf_bytes
        except Exception:
            logger.error("Failed to convert SVG to PDF via cairosvg", exc_info=True)
            return None

    def _upload_pdf(self, s3_key: str, pdf_bytes: bytes) -> bool:
        """Upload a PDF file to S3.

        Args:
            s3_key: The S3 object key to use.
            pdf_bytes: The PDF content as bytes.

        Returns:
            True on success, False on failure.
        """
        try:
            self._s3.put_object(
                Bucket=self._bucket,
                Key=s3_key,
                Body=pdf_bytes,
                ContentType="application/pdf",
            )
            return True
        except ClientError:
            logger.error(
                "Failed to upload PDF to s3://%s/%s",
                self._bucket,
                s3_key,
                exc_info=True,
            )
            return False

    @staticmethod
    def _format_date(iso_timestamp: str) -> str:
        """Format an ISO 8601 timestamp to 'Month DD, YYYY' format.

        Args:
            iso_timestamp: An ISO 8601 formatted date string.

        Returns:
            A formatted string like 'March 15, 2027'.
        """
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%B %d, %Y")
